WITH Sellers(user_id) as (
        SELECT DISTINCT User.user_id
        FROM Item
        JOIN User
        WHERE Item.user_id = User.user_id
    ),
    Buyers(user_id) as (
        SELECT DISTINCT User.user_id
        FROM Bid
        JOIN User
        WHERE Bid.user_id = User.user_id
    )

    SELECT COUNT(Sellers.user_id)
    FROM Sellers
    JOIN Buyers
    WHERE Sellers.user_id = Buyers.user_id;
