## 01_select_where
```sql
SELECT title, price_gbp, rating FROM books WHERE rating >= 4;
```
| title                                                                    |   price_gbp |   rating |
|:-------------------------------------------------------------------------|------------:|---------:|
| Full Moon over Noahâs Ark: An Odyssey to Mount Ararat and Beyond                                                                          |       49.43 |        4 |
| A Year in Provence (Provence #1)                                         |       56.88 |        4 |
| 1,000 Places to See Before You Die                                       |       26.08 |        5 |
| Sharp Objects                                                            |       47.82 |        4 |
| The Past Never Ends                                                      |       56.5  |        4 |
| The Murder of Roger Ackroyd (Hercule Poirot #4)                          |       44.1  |        4 |
| A Time of Torment (Charlie Parker #14)                                   |       48.35 |        5 |
| Murder at the 42nd Street Library (Raymond Ambler #1)                    |       54.36 |        4 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |       25.37 |        5 |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |       52.3  |        5 |
| Delivering the Truth (Quaker Midwife Mystery #1)                         |       20.89 |        4 |
| The Mysterious Affair at Styles (Hercule Poirot #1)                      |       24.8  |        4 |
| The Silkworm (Cormoran Strike #2)                                        |       23.05 |        5 |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |       57.7  |        4 |
| The Girl You Lost                                                        |       12.29 |        5 |
| A Flight of Arrows (The Pathfinders #2)                                  |       55.53 |        5 |
| Mrs. Houdini                                                             |       30.25 |        5 |
| The Marriage of Opposites                                                |       28.08 |        4 |
| A Paris Apartment                                                        |       39.01 |        4 |
| World Without End (The Pillars of the Earth #2)                          |       32.97 |        4 |
| The Passion of Dolssa                                                    |       28.32 |        5 |
| Voyager (Outlander #3)                                                   |       21.07 |        5 |
| The Red Tent                                                             |       35.66 |        5 |
| Between Shades of Gray                                                   |       20.79 |        5 |
| While You Were Mine                                                      |       41.32 |        5 |
| Lost Among the Living                                                    |       27.7  |        4 |
| A Spy's Devotion (The Regency Spies of London #1)                        |       16.97 |        5 |

## 02_order_by_limit
```sql
SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT 10;
```
| title                                                                  |   price_gbp |
|:-----------------------------------------------------------------------|------------:|
| Boar Island (Anna Pigeon #19)                                          |       59.48 |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1) |       57.7  |
| A Year in Provence (Provence #1)                                       |       56.88 |
| The Past Never Ends                                                    |       56.5  |
| The Last Painting of Sara de Vos                                       |       55.55 |
| A Flight of Arrows (The Pathfinders #2)                                |       55.53 |
| Murder at the 42nd Street Library (Raymond Ambler #1)                  |       54.36 |
| The Last Mile (Amos Decker #2)                                         |       54.21 |
| 1st to Die (Women's Murder Club #1)                                    |       53.98 |
| Tipping the Velvet                                                     |       53.74 |

## 03_distinct
```sql
SELECT DISTINCT rating FROM books ORDER BY rating;
```
|   rating |
|---------:|
|        1 |
|        2 |
|        3 |
|        4 |
|        5 |

## 04_between
```sql
SELECT title, price_inr FROM books WHERE price_gbp BETWEEN 20 AND 40;
```
| title                                                                                             |   price_inr |
|:--------------------------------------------------------------------------------------------------|------------:|
| Vagabonding: An Uncommon Guide to the Art of Long-Term World Travel                               |     3897.17 |
| Under the Tuscan Sun                                                                              |     3938.31 |
| The Great Railway Bazaar                                                                          |     3221.97 |
| The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2) |     2448.66 |
| Neither Here nor There: Travels in Europe                                                         |     4109.23 |
| 1,000 Places to See Before You Die                                                                |     2751.44 |
| Poisonous (Max Revere Novels #3)                                                                  |     2827.4  |
| Most Wanted                                                                                       |     3722.04 |
| The Widow                                                                                         |     2875.93 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)                                 |     2676.54 |
| Delivering the Truth (Quaker Midwife Mystery #1)                                                  |     2203.9  |
| The Mysterious Affair at Styles (Hercule Poirot #1)                                               |     2616.4  |
| In the Woods (Dublin Murder Squad #1)                                                             |     4049.09 |
| The Silkworm (Cormoran Strike #2)                                                                 |     2431.78 |
| Extreme Prey (Lucas Davenport #26)                                                                |     2679.7  |
| Career of Evil (Cormoran Strike #3)                                                               |     2607.96 |
| Blood Defense (Samantha Brinkman #1)                                                              |     2141.65 |
| Forever and Forever: The Courtship of Henry Longfellow and Fanny Appleton                         |     3132.3  |
| The House by the Lake                                                                             |     3898.23 |
| Mrs. Houdini                                                                                      |     3191.38 |
| The Marriage of Opposites                                                                         |     2962.44 |
| Love, Lies and Spies                                                                              |     2168.02 |
| A Paris Apartment                                                                                 |     4115.55 |
| The Invention of Wings                                                                            |     3939.37 |
| World Without End (The Pillars of the Earth #2)                                                   |     3478.34 |
| The Passion of Dolssa                                                                             |     2987.76 |
| Girl With a Pearl Earring                                                                         |     2824.24 |
| Voyager (Outlander #3)                                                                            |     2222.89 |
| The Red Tent                                                                                      |     3762.13 |
| Between Shades of Gray                                                                            |     2193.34 |
| The Secret Healer                                                                                 |     3646.08 |
| Starlark                                                                                          |     2725.06 |
| Lost Among the Living                                                                             |     2922.35 |

## 05_in
```sql
SELECT title, rating FROM books WHERE rating IN (4, 5);
```
| title                                                                    |   rating |
|:-------------------------------------------------------------------------|---------:|
| Full Moon over Noahâs Ark: An Odyssey to Mount Ararat and Beyond                                                                          |        4 |
| A Year in Provence (Provence #1)                                         |        4 |
| 1,000 Places to See Before You Die                                       |        5 |
| Sharp Objects                                                            |        4 |
| The Past Never Ends                                                      |        4 |
| The Murder of Roger Ackroyd (Hercule Poirot #4)                          |        4 |
| A Time of Torment (Charlie Parker #14)                                   |        5 |
| Murder at the 42nd Street Library (Raymond Ambler #1)                    |        4 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |        5 |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |
| Delivering the Truth (Quaker Midwife Mystery #1)                         |        4 |
| The Mysterious Affair at Styles (Hercule Poirot #1)                      |        4 |
| The Silkworm (Cormoran Strike #2)                                        |        5 |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |        4 |
| The Girl You Lost                                                        |        5 |
| A Flight of Arrows (The Pathfinders #2)                                  |        5 |
| Mrs. Houdini                                                             |        5 |
| The Marriage of Opposites                                                |        4 |
| A Paris Apartment                                                        |        4 |
| World Without End (The Pillars of the Earth #2)                          |        4 |
| The Passion of Dolssa                                                    |        5 |
| Voyager (Outlander #3)                                                   |        5 |
| The Red Tent                                                             |        5 |
| Between Shades of Gray                                                   |        5 |
| While You Were Mine                                                      |        5 |
| Lost Among the Living                                                    |        4 |
| A Spy's Devotion (The Regency Spies of London #1)                        |        5 |

## 06_join
```sql
SELECT c.category_name, b.title, b.rating, b.price_inr
        FROM books b JOIN categories c ON b.category_id = c.category_id
        WHERE b.rating >= 4
        ORDER BY c.category_name, b.rating DESC, b.price_inr DESC
        LIMIT 10;
```
| category_name      | title                                             |   rating |   price_inr |
|:-------------------|:--------------------------------------------------|---------:|------------:|
| Historical Fiction | A Flight of Arrows (The Pathfinders #2)           |        5 |     5858.42 |
| Historical Fiction | While You Were Mine                               |        5 |     4359.26 |
| Historical Fiction | The Red Tent                                      |        5 |     3762.13 |
| Historical Fiction | Mrs. Houdini                                      |        5 |     3191.38 |
| Historical Fiction | The Passion of Dolssa                             |        5 |     2987.76 |
| Historical Fiction | Voyager (Outlander #3)                            |        5 |     2222.89 |
| Historical Fiction | Between Shades of Gray                            |        5 |     2193.34 |
| Historical Fiction | A Spy's Devotion (The Regency Spies of London #1) |        5 |     1790.33 |
| Historical Fiction | A Paris Apartment                                 |        4 |     4115.55 |
| Historical Fiction | World Without End (The Pillars of the Earth #2)   |        4 |     3478.34 |

## SQL JOIN vs pandas merge validation
Equivalent result: **True**

### SQL result
| category_name      | title                                             |   rating |   price_inr |
|:-------------------|:--------------------------------------------------|---------:|------------:|
| Historical Fiction | A Flight of Arrows (The Pathfinders #2)           |        5 |     5858.42 |
| Historical Fiction | While You Were Mine                               |        5 |     4359.26 |
| Historical Fiction | The Red Tent                                      |        5 |     3762.13 |
| Historical Fiction | Mrs. Houdini                                      |        5 |     3191.38 |
| Historical Fiction | The Passion of Dolssa                             |        5 |     2987.76 |
| Historical Fiction | Voyager (Outlander #3)                            |        5 |     2222.89 |
| Historical Fiction | Between Shades of Gray                            |        5 |     2193.34 |
| Historical Fiction | A Spy's Devotion (The Regency Spies of London #1) |        5 |     1790.33 |
| Historical Fiction | A Paris Apartment                                 |        4 |     4115.55 |
| Historical Fiction | World Without End (The Pillars of the Earth #2)   |        4 |     3478.34 |

### pandas merge result
| category_name      | title                                             |   rating |   price_inr |
|:-------------------|:--------------------------------------------------|---------:|------------:|
| Historical Fiction | A Flight of Arrows (The Pathfinders #2)           |        5 |     5858.42 |
| Historical Fiction | While You Were Mine                               |        5 |     4359.26 |
| Historical Fiction | The Red Tent                                      |        5 |     3762.13 |
| Historical Fiction | Mrs. Houdini                                      |        5 |     3191.38 |
| Historical Fiction | The Passion of Dolssa                             |        5 |     2987.76 |
| Historical Fiction | Voyager (Outlander #3)                            |        5 |     2222.89 |
| Historical Fiction | Between Shades of Gray                            |        5 |     2193.34 |
| Historical Fiction | A Spy's Devotion (The Regency Spies of London #1) |        5 |     1790.33 |
| Historical Fiction | A Paris Apartment                                 |        4 |     4115.55 |
| Historical Fiction | World Without End (The Pillars of the Earth #2)   |        4 |     3478.34 |