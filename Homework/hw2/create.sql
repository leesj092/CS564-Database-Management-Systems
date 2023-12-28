drop table if exists Item;
drop table if exists User;
drop table if exists Bid;
drop table if exists ItemCategory;
CREATE TABLE User(
    user_id TEXT PRIMARY KEY,    
    rating INTEGER,
    country TEXT,
    location TEXT
);

CREATE TABLE Item(
    item_id INTEGER,
    name TEXT,
    currently TEXT,
    buy_price TEXT,
    first_bid TEXT,
    number_of_bids INTEGER,
    started TEXT,
    ends TEXT,
    description TEXT,
    user_id TEXT,
    PRIMARY KEY (item_id, user_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

CREATE TABLE Bid(
    time TEXT,    
    amount TEXT,
    user_id TEXT,
    item_id INTEGER,
    PRIMARY KEY (amount, item_id, user_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);

CREATE TABLE ItemCategory(
    item_id INTEGER,
    category TEXT,
    PRIMARY KEY (item_id, category),
    FOREIGN KEY (item_id) REFERENCES Item(item_id)
);