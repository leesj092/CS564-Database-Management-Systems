SELECT item_id
FROM Item
WHERE currently = (
    SELECT currently
    FROM Item
    ORDER BY currently+0 DESC
    LIMIT 1
);