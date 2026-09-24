"""Scrape, clean, enrich and store Books to Scrape catalog data."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
GBP_TO_INR = 105.50  # Project-defined fixed baseline; not a live FX rate.
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DB_PATH = OUTPUT_DIR / "books.db"
HEADERS = {"User-Agent": "Mozilla/5.0 (educational capstone project)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_categories() -> list[tuple[str, str]]:
    """Return the first three real category links from the website navigation."""
    soup = get_soup(BASE_URL)
    links = soup.select(".side_categories ul ul a")
    return [
        (link.get_text(strip=True), requests.compat.urljoin(BASE_URL, link["href"]))
        for link in links[:3]
    ]


def scrape_category(category: str, first_url: str) -> list[dict]:
    rows, url = [], first_url
    while url:
        soup = get_soup(url)
        for book in soup.select("article.product_pod"):
            rows.append(
                {
                    "title": book.h3.a["title"],
                    "price_raw": book.select_one(".price_color").get_text(strip=True),
                    "star_rating": book.select_one("p.star-rating")["class"][-1],
                    "availability_raw": book.select_one(".availability").get_text(" ", strip=True),
                    "category": category,
                }
            )
        next_link = soup.select_one("li.next a")
        url = requests.compat.urljoin(url, next_link["href"]) if next_link else None
    return rows


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Convert raw strings to usable types and handle unexpected values safely."""
    df = raw.copy()
    df["price_gbp"] = pd.to_numeric(
        df["price_raw"].str.replace(r"[^0-9.]", "", regex=True), errors="coerce"
    )
    df["rating"] = df["star_rating"].map(RATING_MAP)
    df["in_stock"] = df["availability_raw"].str.contains("in stock", case=False, na=False)

    # Numeric parse failures use median imputation so one malformed price/rating
    # does not stop the batch. Essential text fields are dropped if missing.
    for column in ["price_gbp", "rating"]:
        df[column] = df[column].fillna(df[column].median())
    df = df.dropna(subset=["title", "category"])
    df["rating"] = df["rating"].astype("int64")
    df["in_stock"] = df["in_stock"].astype(bool)
    df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)
    return df[["title", "price_gbp", "price_inr", "rating", "in_stock", "category"]]


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS categories;
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            in_stock INTEGER NOT NULL CHECK (in_stock IN (0, 1)),
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );
        """
    )


def load_database(df: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        create_schema(connection)
        category_df = pd.DataFrame({"category_name": sorted(df["category"].unique())})
        category_df.to_sql("categories", connection, if_exists="append", index=False)
        category_ids = pd.read_sql("SELECT category_id, category_name FROM categories", connection)
        books_df = df.merge(category_ids, left_on="category", right_on="category_name").drop(
            columns=["category", "category_name"]
        )
        books_df["in_stock"] = books_df["in_stock"].astype(int)
        books_df.to_sql("books", connection, if_exists="append", index=False)


QUERIES = {
    "01_select_where": "SELECT title, price_gbp, rating FROM books WHERE rating >= 4;",
    "02_order_by_limit": "SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 10;",
    "03_distinct": "SELECT DISTINCT rating FROM books ORDER BY rating;",
    "04_between": "SELECT title, price_inr FROM books WHERE price_gbp BETWEEN 20 AND 40;",
    "05_in": "SELECT title, rating FROM books WHERE rating IN (4, 5);",
    "06_join": """
        SELECT c.category_name, b.title, b.rating, b.price_inr
        FROM books b JOIN categories c ON b.category_id = c.category_id
        WHERE b.rating >= 4
        ORDER BY c.category_name, b.rating DESC, b.price_inr DESC
        LIMIT 10;
    """,
}


def execute_queries_and_validate(df: pd.DataFrame) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        output_lines = []
        results = {}
        for name, query in QUERIES.items():
            result = pd.read_sql(query, connection)
            results[name] = result
            output_lines += [f"## {name}", "```sql", query.strip(), "```", result.to_markdown(index=False), ""]

        # pd.read_sql is demonstrated above. Reproduce the JOIN in pandas only.
        categories = pd.read_sql("SELECT * FROM categories", connection)
        books = pd.read_sql("SELECT * FROM books", connection)
        pandas_join = (
            books.merge(categories, on="category_id")
            .query("rating >= 4")
            [["category_name", "title", "rating", "price_inr"]]
            .sort_values(["category_name", "rating", "price_inr"], ascending=[True, False, False])
            .head(10)
            .reset_index(drop=True)
        )
        sql_join = results["06_join"].reset_index(drop=True)
        equivalent = sql_join.equals(pandas_join)
        output_lines += [
            "## SQL JOIN vs pandas merge validation",
            f"Equivalent result: **{equivalent}**",
            "", "### SQL result", sql_join.to_markdown(index=False),
            "", "### pandas merge result", pandas_join.to_markdown(index=False),
        ]
        (OUTPUT_DIR / "sql_query_results.md").write_text("\n".join(output_lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    raw_rows = []
    for category, url in get_categories():
        raw_rows.extend(scrape_category(category, url))
    cleaned = clean_data(pd.DataFrame(raw_rows))
    if cleaned.shape[0] < 60 or cleaned["category"].nunique() < 3:
        raise RuntimeError("Expected at least 60 books across three categories.")
    cleaned.to_csv(OUTPUT_DIR / "cleaned_books.csv", index=False)
    load_database(cleaned)
    execute_queries_and_validate(cleaned)
    print(f"Pipeline completed: {len(cleaned)} books, {cleaned['category'].nunique()} categories")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    main()
