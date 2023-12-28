
"""
FILE: skeleton_parser.py
------------------
Author: Firas Abuzaid (fabuzaid@stanford.edu)
Author: Perth Charernwattanagul (puch@stanford.edu)
Modified: 04/21/2014

Skeleton parser for CS564 programming project 1. Has useful imports and
functions for parsing, including:

1) Directory handling -- the parser takes a list of eBay json files
and opens each file inside of a loop. You just need to fill in the rest.
2) Dollar value conversions -- the json files store dollar value amounts in
a string like $3,453.23 -- we provide a function to convert it to a string
like XXXXX.xx.
3) Date/time conversions -- the json files store dates/ times in the form
Mon-DD-YY HH:MM:SS -- we wrote a function (transformDttm) that converts to the
for YYYY-MM-DD HH:MM:SS, which will sort chronologically in SQL.

Your job is to implement the parseJson function, which is invoked on each file by
the main function. We create the initial Python dictionary object of items for
you; the rest is up to you!
Happy parsing!
"""

import sys
import pprint
from json import loads
from re import sub
import itertools


columnSeparator = "|"
doubleQuote = "\"";
# Dictionary of months used for date transformation
MONTHS = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',\
        'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

"""
Returns true if a file ends in .json
"""
def isJson(f):
    return len(f) > 5 and f[-5:] == '.json'

"""
Converts month to a number, e.g. 'Dec' to '12'
"""
def transformMonth(mon):
    if mon in MONTHS:
        return MONTHS[mon]
    else:
        return mon

"""
Transforms a timestamp from Mon-DD-YY HH:MM:SS to YYYY-MM-DD HH:MM:SS
"""
def transformDttm(dttm):
    dttm = dttm.strip().split(' ')
    dt = dttm[0].split('-')
    date = '20' + dt[2] + '-'
    date += transformMonth(dt[0]) + '-' + dt[1]
    return date + ' ' + dttm[1]

"""
Transform a dollar value amount from a string like $3,453.23 to XXXXX.xx
"""

def transformDollar(money):
    if money == None or len(money) == 0:
        return money
    return sub(r'[^\d.]', '', money)

"""
Parses a single json file. Currently, there's a loop that iterates over each
item in the data set. Your job is to extend this functionality to create all
of the necessary SQL tables for your database.
"""
# create dictionaries to store the data for each table
UserDict = {}
ItemDict = {}
ItemCategoryDict = {}
BidDict = {}
def parseJson(json_file):
    with open(json_file, 'r') as f:
        # create an items dict from the json file
        items = loads(f.read())['Items'] 
        
        for item in items:
            
            #fill the item dict with the item attrubutes
            item_id = item["ItemID"]
            name = item["Name"]
            currently = transformDollar(item["Currently"])
            buy_price = "NULL"
            if "Buy_Price" in item:
                buy_price = transformDollar(item["Buy_Price"])
                buy_price = buy_price if buy_price != None else "NULL"
            first_bid = transformDollar(item["First_Bid"])
            number_of_bids = item["Number_of_Bids"]
            started = transformDttm(item["Started"])
            ends = transformDttm(item["Ends"])
            description = ""
            if "Description" in item and item["Description"] != None:
                description = item["Description"]
            user_id = item["Seller"]["UserID"]
            
            ItemDict[item_id] = []
            ItemDict[item_id].append(name)
            ItemDict[item_id].append(currently)
            ItemDict[item_id].append(buy_price)
            ItemDict[item_id].append(first_bid)
            ItemDict[item_id].append(number_of_bids)
            ItemDict[item_id].append(started)
            ItemDict[item_id].append(ends)
            ItemDict[item_id].append(description)
            ItemDict[item_id].append(user_id)
            
            #fill the ItemCategory dict with the corresponding categoryid(s) with the item id
            ItemCategoryDict[item["ItemID"]] = []
            for category in item["Category"]:
                ItemCategoryDict[item["ItemID"]].append(category)
                
            #fill the user dict with all the seller/bidder information
            
            #consider all the sellers
            seller_id = item["Seller"]["UserID"]
            seller_rating = item["Seller"]["Rating"]
            seller_country = "Null"
            if "Country" in item:
                seller_country = item["Country"]
            seller_location = "Null"
            if "Location" in item:
                seller_location = item["Location"]
            
            seller_location = item["Location"]
            if seller_id not in UserDict:
                UserDict[seller_id] = []
                UserDict[seller_id].append(seller_rating)
                UserDict[seller_id].append(seller_country)
                UserDict[seller_id].append(seller_location)
            else:
                if UserDict[seller_id][0] == "Null":
                    UserDict[seller_id][0] = seller_rating
                if UserDict[seller_id][1] == "Null":
                    UserDict[seller_id][1] = seller_country
                if UserDict[seller_id][2] == "Null":
                    UserDict[seller_id][2] = seller_location
                    
            if item["Bids"] != None:
                for bidDict in item["Bids"]:
                    bid = bidDict["Bid"]
                    #consider all the bidders for user dict
                    bidder = bid["Bidder"]
                    bidder_id = bidder["UserID"]
                    bidder_rating = bidder["Rating"]
                    bidder_country = "NULL"
                    if "Country" in bidder:
                        bidder_country = bidder["Country"]
                    bidder_location = "NULL"
                    if "Location" in bidder:
                        bidder_location = bidder["Location"]

                    if bidder_id not in UserDict:
                        UserDict[bidder_id] = []
                        UserDict[bidder_id].append(bidder_rating)
                        UserDict[bidder_id].append(bidder_country)
                        UserDict[bidder_id].append(bidder_location)
                    else:
                        if UserDict[bidder_id][0] == "Null":
                            UserDict[bidder_id][0] = bidder_rating
                        if UserDict[bidder_id][1] == "Null":
                            UserDict[bidder_id][1] = bidder_country
                        if UserDict[bidder_id][2] == "Null":
                            UserDict[bidder_id][2] = bidder_location


                    #fill the bid dict with all the bid information
                    BidDict[item["ItemID"] + bidder_id + bid["Amount"]] = []
                    currBid = BidDict[item["ItemID"] + bidder_id + bid["Amount"]]
                    time = transformDttm(bid["Time"])
                    amount = transformDollar(bid["Amount"])
                    currBid.append(time)
                    currBid.append(amount)
                    currBid.append(bidder_id)
                    currBid.append(item_id)
    f.close()

# helper functions for writeToFile
def quoteString(value):
    return doubleQuote + value + doubleQuote
def stringCol (value):
    return columnSeparator + quoteString(value)
def stringCols (values):
    columns = ""
    for value in values:
        columns = columns + columnSeparator + quoteString(value)
    return columns
def numCol (value):
    return columnSeparator + value
def replaceQuote(list, index):
    list[index] = list[index].replace("\"", "\"\"")
    list[index] = list[index].replace("\'", "\'\'")

def writeToFile(UserDict, ItemDict, ItemCategoryDict, BidDict):
    # create/open files to store .dat info       
    UserFile = open("User.dat", "w")

    for user_id, userVals in UserDict.items():
        for idx in range(len(userVals)):
            replaceQuote(UserDict[user_id], idx)
        UserFile.write(quoteString(user_id) + stringCols([userVals[0], userVals[1], userVals[2]]) + "\n")
    UserFile.close()
    ItemFile = open("Item.dat", "w")
    for item_id, itemVals in ItemDict.items():
        for idx in range(len(itemVals)):
            replaceQuote(ItemDict[item_id], idx)
        ItemFile.write(item_id + stringCols([itemVals[0], itemVals[1], itemVals[2], itemVals[3]]) + 
                       numCol(itemVals[4]) + 
                       stringCols([itemVals[5], itemVals[6], itemVals[7], itemVals[8]]) + "\n")
    ItemFile.close()
    ItemCategoryFile = open("ItemCategory.dat", "w")
    for item_id, itemCategoryVals in ItemCategoryDict.items():
        ItemCategoryDict[item_id] = list(set(ItemCategoryDict[item_id]))
        for idx in range(len(list(set(itemCategoryVals)))):
            replaceQuote(ItemCategoryDict[item_id], idx)
            ItemCategoryFile.write(item_id + stringCol(ItemCategoryDict[item_id][idx]) + "\n")
    ItemCategoryFile.close()
    BidFile = open("Bid.dat", "w")
    for bid_id, bidVals in BidDict.items():
        for idx in range(len(bidVals)):
            replaceQuote(BidDict[bid_id], idx)
        BidFile.write(quoteString(bidVals[0]) + stringCols([bidVals[1], bidVals[2]]) + numCol(bidVals[3]) + "\n")
    BidFile.close()

def main(argv):
    # argv = ["skeleton_parser.py", "ebay_data/items-*.json"]
    if len(argv) < 2:
        print >> sys.stderr, 'Usage: python skeleton_json_parser.py <path to json files>'
        sys.exit(1)
    # loops over all .json files in the argument
    for f in argv[1:]:
        if isJson(f):
            parseJson(f)
            print ("Success parsing " + f)
    writeToFile(UserDict, ItemDict, ItemCategoryDict, BidDict)
if __name__ == '__main__':
    main(sys.argv)