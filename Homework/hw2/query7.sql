WITH Items(item_id) as (
        SELECT item_id
        FROM Bid
        WHERE amount + 0 > 100
    )

    SELECT COUNT(DISTINCT category)
    FROM ItemCategory
    JOIN Items
    WHERE ItemCategory.item_id = Items.item_id;