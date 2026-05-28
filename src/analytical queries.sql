-- analytical_queries.sql
-- ---------------------------------------------------------
-- Purpose : A collection of SQL queries for exploring and
--           analysing international debt data.
--
-- Difficulty levels are organised into three sections:
--   1. Basic     — simple SELECT and aggregate queries
--   2. Intermediate — JOINs, GROUP BY, subqueries, HAVING
--   3. Advanced  — CTEs, window functions, views, CASE
-- ---------------------------------------------------------


-- ====================================================================
-- SECTION 1: BASIC QUERIES
-- ====================================================================

-- 1. Retrieve all distinct country names
SELECT DISTINCT country_name
FROM countries
ORDER BY country_name ASC;

-- 2. Count the total number of countries in the dataset
SELECT COUNT(*) AS total_countries
FROM countries;

-- 3. Count the total number of debt indicators
SELECT COUNT(*) AS total_indicators
FROM indicators;

-- 4. Preview the first 10 rows of the debt records table
SELECT *
FROM debt_records
LIMIT 10;

-- 5. Calculate total global debt across all countries and years
SELECT SUM(debt_value) AS total_global_debt
FROM debt_records;

-- 6. List all unique indicator names alphabetically
SELECT DISTINCT indicator_name
FROM indicators
ORDER BY indicator_name ASC;

-- 7. Count how many debt records exist for each country
SELECT c.country_name, COUNT(*) AS total_records
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_records DESC;

-- 8. Find all debt records where the value exceeds 1 billion USD
SELECT c.country_name, d.year, d.debt_value
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
WHERE d.debt_value > 1000000000
ORDER BY d.debt_value DESC;

-- 9. Find the minimum, maximum, and average debt value across all records
SELECT
    MIN(debt_value) AS minimum_debt,
    MAX(debt_value) AS maximum_debt,
    AVG(debt_value) AS average_debt
FROM debt_records;

-- 10. Count the total number of rows in the debt records table
SELECT COUNT(*) AS total_records_in_dataset
FROM debt_records;


-- ====================================================================
-- SECTION 2: INTERMEDIATE QUERIES
-- ====================================================================

-- 11. Find the total debt amount for each country
SELECT c.country_name, SUM(d.debt_value) AS total_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_country_debt DESC;

-- 12. Find the top 10 countries with the highest total debt
SELECT c.country_name, SUM(d.debt_value) AS total_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_country_debt DESC
LIMIT 10;

-- 13. Find the average debt value per country
SELECT c.country_name, AVG(d.debt_value) AS average_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY average_country_debt DESC;

-- 14. Calculate the total debt amount attributed to each indicator
SELECT i.indicator_name, SUM(d.debt_value) AS total_indicator_debt
FROM debt_records d
JOIN indicators i ON d.indicator_code = i.indicator_code
GROUP BY i.indicator_name
ORDER BY total_indicator_debt DESC;

-- 15. Find the single indicator that contributes the most to global debt
SELECT i.indicator_name, SUM(d.debt_value) AS total_indicator_debt
FROM debt_records d
JOIN indicators i ON d.indicator_code = i.indicator_code
GROUP BY i.indicator_name
ORDER BY total_indicator_debt DESC
LIMIT 1;

-- 16. Find the country with the lowest total debt
SELECT c.country_name, SUM(d.debt_value) AS total_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_country_debt ASC
LIMIT 1;

-- 17. Show total debt broken down by every country and indicator combination
SELECT c.country_name, i.indicator_name, SUM(d.debt_value) AS combined_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
JOIN indicators i ON d.indicator_code = i.indicator_code
GROUP BY c.country_name, i.indicator_name
ORDER BY c.country_name ASC, combined_debt DESC;

-- 18. Count how many unique indicators each country has data for
SELECT c.country_name, COUNT(DISTINCT d.indicator_code) AS unique_indicators_count
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY unique_indicators_count DESC;

-- 19. Find countries whose total debt is above the global average total debt per country
-- The subquery first calculates each country's total, then we average those totals.
SELECT c.country_name, SUM(d.debt_value) AS total_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
HAVING SUM(d.debt_value) > (
    SELECT AVG(country_total)
    FROM (
        SELECT SUM(debt_value) AS country_total
        FROM debt_records
        GROUP BY country_code
    ) AS country_totals
)
ORDER BY total_country_debt DESC;

-- 20. Rank all countries by total debt using the RANK() window function
SELECT
    c.country_name,
    SUM(d.debt_value) AS total_country_debt,
    RANK() OVER (ORDER BY SUM(d.debt_value) DESC) AS debt_rank
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name;


-- ====================================================================
-- SECTION 3: ADVANCED QUERIES
-- ====================================================================

-- 21. Find the top 5 indicators that contribute the most to global debt
SELECT i.indicator_name, SUM(d.debt_value) AS total_indicator_debt
FROM debt_records d
JOIN indicators i ON d.indicator_code = i.indicator_code
GROUP BY i.indicator_name
ORDER BY total_indicator_debt DESC
LIMIT 5;

-- 22. Calculate each country's percentage contribution to total global debt
SELECT
    c.country_name,
    SUM(d.debt_value) AS total_country_debt,
    ROUND(
        (SUM(d.debt_value) / (SELECT SUM(debt_value) FROM debt_records)) * 100,
        2
    ) AS percentage_contribution
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_country_debt DESC;

-- 23. For each indicator, find the top 3 countries with the highest debt
-- Using a CTE (Common Table Expression) to first rank, then filter.
WITH ranked_indicator_debt AS (
    SELECT
        i.indicator_name,
        c.country_name,
        SUM(d.debt_value) AS total_debt,
        DENSE_RANK() OVER (
            PARTITION BY i.indicator_code
            ORDER BY SUM(d.debt_value) DESC
        ) AS ranking
    FROM debt_records d
    JOIN countries c ON d.country_code = c.country_code
    JOIN indicators i ON d.indicator_code = i.indicator_code
    GROUP BY i.indicator_code, i.indicator_name, c.country_name
)
SELECT indicator_name, country_name, total_debt
FROM ranked_indicator_debt
WHERE ranking <= 3;

-- 24. Find the range (max - min) of debt values recorded for each country
SELECT
    c.country_name,
    (MAX(d.debt_value) - MIN(d.debt_value)) AS debt_range
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY debt_range DESC;

-- 25. Create a reusable view for the top 10 highest-debt countries
-- Once created, you can query it with: SELECT * FROM top_10_high_debt_countries_view;
CREATE OR REPLACE VIEW top_10_high_debt_countries_view AS
SELECT c.country_name, SUM(d.debt_value) AS total_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_debt DESC
LIMIT 10;

-- 26. Categorize countries into debt tiers using a CASE statement
SELECT
    c.country_name,
    SUM(d.debt_value) AS total_country_debt,
    CASE
        WHEN SUM(d.debt_value) > 100000000000  THEN 'High Debt'    -- above 100 billion
        WHEN SUM(d.debt_value) > 10000000000   THEN 'Medium Debt'  -- between 10 and 100 billion
        ELSE                                        'Low Debt'      -- below 10 billion
    END AS debt_category
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
ORDER BY total_country_debt DESC;

-- 27. Calculate the running cumulative debt for each country over the years
-- The SUM() OVER() window function accumulates totals year by year per country.
SELECT
    c.country_name,
    d.year,
    SUM(d.debt_value) AS yearly_debt,
    SUM(SUM(d.debt_value)) OVER (
        PARTITION BY c.country_code
        ORDER BY d.year
    ) AS cumulative_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_code, c.country_name, d.year
ORDER BY c.country_name ASC, d.year ASC;

-- 28. Find indicators where the average debt is higher than the global average
SELECT i.indicator_name, AVG(d.debt_value) AS avg_indicator_debt
FROM debt_records d
JOIN indicators i ON d.indicator_code = i.indicator_code
GROUP BY i.indicator_name
HAVING AVG(d.debt_value) > (SELECT AVG(debt_value) FROM debt_records)
ORDER BY avg_indicator_debt DESC;

-- 29. Find countries that account for more than 5% of total global debt
SELECT
    c.country_name,
    SUM(d.debt_value) AS total_country_debt
FROM debt_records d
JOIN countries c ON d.country_code = c.country_code
GROUP BY c.country_name
HAVING SUM(d.debt_value) > (SELECT SUM(debt_value) * 0.05 FROM debt_records)
ORDER BY total_country_debt DESC;

-- 30. Find the single biggest debt category (indicator) for each country
-- Uses ROW_NUMBER() to pick only the top-ranked indicator per country.
WITH country_indicator_totals AS (
    SELECT
        c.country_name,
        i.indicator_name,
        SUM(d.debt_value) AS total_debt,
        ROW_NUMBER() OVER (
            PARTITION BY c.country_code
            ORDER BY SUM(d.debt_value) DESC
        ) AS rank_order
    FROM debt_records d
    JOIN countries c ON d.country_code = c.country_code
    JOIN indicators i ON d.indicator_code = i.indicator_code
    GROUP BY c.country_code, c.country_name, i.indicator_name
)
SELECT country_name, indicator_name, total_debt AS dominant_indicator_debt
FROM country_indicator_totals
WHERE rank_order = 1
ORDER BY dominant_indicator_debt DESC;