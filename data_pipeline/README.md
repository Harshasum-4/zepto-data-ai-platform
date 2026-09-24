# Zepto Data Pipeline

## Objective

This module converts public catalogue data from `books.toscrape.com` into a clean, normalized SQLite database. It is a practice implementation of a catalogue-pricing pipeline: scrape → clean → enrich → store → query.

## Setup and run

```bash
cd data_pipeline
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py
```

The script creates `output/cleaned_books.csv`, `output/books.db`, and `output/sql_query_results.md`.

## Data collection and cleaning

The script discovers and scrapes the first three website categories and follows every page in each category. It captures title, listed GBP price, textual star rating, availability text, and category. This returns at least 60 rows.

`price_gbp` is parsed to float after removing the currency symbol. Ratings are mapped from One–Five to integers 1–5. Availability is converted to boolean `in_stock`. If an unexpected numeric price or rating cannot be parsed, the pipeline replaces it with that column's median so one malformed value does not fail the full batch. A missing title or category is dropped because it would make the record unusable and break the category relationship.

`price_inr` uses the project-defined fixed conversion rate: **1 GBP = 105.50 INR**. This is an assignment baseline, not a live exchange rate, so no external currency API is used.

## Database design

The SQLite schema is normalized into:

- `categories(category_id PRIMARY KEY, category_name UNIQUE)`
- `books(book_id PRIMARY KEY, title, price_gbp, price_inr, rating, in_stock, category_id FOREIGN KEY)`

Each book references exactly one category through `category_id`, preventing repeated category text in the book table.

## Query and pandas validation

## Generated artifacts

After running `python run_pipeline.py`, the `output/` folder contains `books.db`, `cleaned_books.csv`, and `sql_query_results.md`.

The generated `output/sql_query_results.md` records six executed SQL queries and their outputs. Together they demonstrate `SELECT/WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`, `BETWEEN`, `IN`, and a category/books `JOIN`.

All queries are read into pandas using `pd.read_sql`. The JOIN output is also reproduced using `pd.merge` on in-memory `books` and `categories` DataFrames; the script records whether both results are equivalent.
