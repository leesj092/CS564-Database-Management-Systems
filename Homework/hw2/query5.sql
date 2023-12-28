SELECT COUNT(DISTINCT User.user_id)
FROM Item
JOIN User
WHERE Item.user_id = User.user_id AND User.rating > 1000;