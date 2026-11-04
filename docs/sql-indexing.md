# SQL indexing

## Why indexes
An index lets the database find rows without scanning the whole table. Most relational databases use B-tree indexes, which keep keys sorted and support equality and range queries in logarithmic time.

## Composite indexes
A composite index on (country, city) helps queries that filter on country, or on country and city, but not on city alone. Put the most selective, most frequently filtered column first.

## Costs
Every index speeds up reads but slows down INSERT, UPDATE and DELETE and uses disk space. Do not index every column. Check the query plan with `EXPLAIN` to confirm an index is actually used.

## Common pitfalls
Applying a function to an indexed column in the WHERE clause, such as `WHERE LOWER(email) = ...`, prevents index use unless a functional index exists. Leading wildcards like `LIKE '%abc'` also cannot use a B-tree index.
