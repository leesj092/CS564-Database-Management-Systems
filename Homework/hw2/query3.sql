SELECT COUNT(*)
FROM (
    SELECT *
    FROM ItemCategory
    GROUP BY item_id
    HAVING COUNT(category) = 4);