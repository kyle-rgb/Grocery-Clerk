from pprint import pprint
import time, re, random, datetime as dt, os, json, urllib, pytz, sys, math
import subprocess, shutil, requests

import pyautogui as pag
import win32gui


from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import pyperclip as clip
from api_keys import DB_ARCHIVE_KEY, EXTENSION_ARCHIVE_KEY, ZIPCODE, PHONE_NUMBER, VERIFICATION_CODE
from tzwhere import tzwhere

# Inside Will Find:
    # Trip Level Data: Total Cost of Purchases, Locations of Store, Order Number, Payment Method, Items/Coupons Together, Tax
    # One Item Level: Link to Kroger's Web Page for Item, Quantity of Item Purchased, Sale Price, Regular Price, Picture of Item;
    # Item Webpage: UPC, Weight, Serving Size, Servings per Container, Ingredients, Nutritional Data
        # Breaks Down Further Nutritional Detail By:
            # Macronutrients (Weight) (% of Daily Recommended Value)
        # Recommendations for Like Products

# User Story => Carts (aka Trips) => Products (Identifying Information, Price, Nutritional Information)
# Analyze Shopping Patterns and How Much I Saved Via Trips

# Meals => Combinations of Purchased Foods => Single Food Products
# Use Purchase History as Gauge for Interest in future promotions and basis for queries for new recipes

# Use API to get prices of past purchases and estimate future trips
# Use API to create same carts for Pickup

# ---------------------------------------------------------------------Python make_datasey.py---------------------------------------------------------------------
# normalizeDay(string); switchUrl(x, y, url); eatThisPage(reset=False); loadExtension(); x
# setUpBrowser(n=0, initialSetup=True, url=None); getStoreData(chain); loadMoreAppears(png); x
# getArrow(sleep=2); scrollDown(sleep=10); insertFilteredData(entries, collection_name, db, uuid)->None;
# insertData(entries, collection_name, db='new'); retrieveData(collection_name, db); createDBSummaries(db='new'); runAndDocument(funcs:list, callNames:list, kwargs: list, callback=None); 
# simulateUser(link); updateGasoline(data); getKrogerTrips(); getFamilyDollarItems(); getScrollingData(chain: str); getPublixCouponData(deals=673); getDGItems(); deconstructDollars(file); backupDatabase(); deconstructExtensions(filename);normalizeStoreData();
# createDecompositions(dataRepoPath: str, wantedPaths: list, additionalPaths: dict = None, setStores: bool = False); queryDB(db, collections, pipeline=None, filterObj=None, stop=0); getCollectionFeatureCounts(db='new', collection='prices'); getCollectionFeatureTypes();
# getStores(); findAndInsertExtraPromotions(head)  
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Data processing helpers for common flaws in data : [ 
#   normalizeDay(string), updateGasoline(data), findAndInsertExtraPromotions(head) 
#  ]
# Data collection helpers for scraping functions : [
#   switchUrl(x,y,url), eatThisPage(reset=False), loadExtension(),
#   setUpBrowser(n, initialSetup, url), loadMoreAppears(png), getArrow(sleep),
#   scrollDown(sleep=10), 
#  ]
# Queries to Database : [
#   retrieveData(collection_name, db),
#   getCollectionFeatureTypes(),
#   getCollectionFeatureCounts(db, collection),
#   queryDB(db, collections, pipeline, filterObj, stop)
# ]
# Data Entry Functions of Processed Data + Data Dumps : [ 
#   insertData(entries, collection_name, db),
#   insertFilteredData(entries, collection_name, db, uuid),
#   runAndDocument(funcs, callNames, kwargs, callback),
#   createDBSummaries(db)
# ]
# Backup DB : [ 
#   backupDatabase(), 
#  ]
# Data Transformation Functions : [
#  deconstructDollars(file), deconstructExtensions(filename), normalizeStoreData(),
#  createDecompositions(dataRepoPath, wantedPaths, additionalPaths, setStores)
# ]
# Data Collection Functions : [
#   getStoreData(chain), simulateUser(link), getKrogerTrips(), getFamilyDollarItems(),
#   getScrollingData(chain), getPublixCouponData, getDGItems(), getStores() 
# ]
# Decomposition AGs: [
    # "krogerTrips": { setUpBrowser >> getKrogerTrips >> createDecompositions:py3.7 },
    # "krogerCoupons": {setUpBrowser >> getKrogerCoupons >> createDecompositions:py3.7},
    # "familyDollarCoupons" : {setUpBrowser >> getFamilyDollarCoupons >> deconstructDollars:py3.7},
    # "dollarGeneralCoupons": {setUpBrowser >> getDollarGeneralCoupons >> deconstructDollars:py3.7},
    # "aldiItems": {setUpBrowser >> getInstacartItems >> processInstacartItems:node16.13.2 },
    # "publixItems" : {setUpBrowser >> getInstacartItems >> processInstacartItems:node16.13.2},
    # "publixCoupons": {setUpBrowser >> getPublixCoupons >> summarizeNewCoupons:node16.13.2},
    # "familyDollarInstacartItems": {setUpBrowser >> getInstacartItems >> processInstacartItems:node16.13.2},
    # "familyDollarItems": {setUpBrowser >> getFamilyDollarItems >> processFamilyDollarItems:node16.13.2},
    # "dollarGeneralItems": {setUpBrowser >> getDollarGeneralItems >> ....}
    # "foodDepotItems": {setUpBrowser >> getFoodDepotItems >> summarizeFoodDepot:node16.13.2}
    # "foodDepotCoupons": {setUpBrowser >> getFoodDepotCoupons >> summarizeNewCoupons:node16.13.2}
# ]

# --------------------------------------------------------------------- Node.js summary.js---------------------------------------------------------------------
# cleanup(object);
# insertData(listOfObjects, collectionName);
# insertFilteredData(id, collectionName, newData = undefined, dbName='new');
# processInstacartItemItems(target, defaultLocation=null, uuid);
# zipUp(); 
# summarizeFoodDepot(target);
# summarizeNewCoupons(target, parser, uuid);
# processFamilyDollarItems(target, defaultLocation="2394");
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Data Cleanup Helpers : [cleanup()]
# Database Insertions : [insertData(listOfObjects, collectionName), insertFilteredData(id, collectionName, newData, dbName)]
# Data Transformations : [
# processInstacartItems(target, defaultLocation, uuid),
# summarizeFoodDepot(target),
# summarizeNewCoupons(target, parser, uuid)
# processFamilyDollarItems(target, defaultLocation)
# ]
# File Management : [zipUp()]
#
#

# helper for normalizeStore function
def normalizeDay(string):
    # REQ : datetime 
    today= dt.datetime.now()
    abbv = today.strftime('%a')
    if len(string)>3:
        string = string[:3]
    while abbv!=string:
        today -= dt.timedelta(days=1)
        abbv = today.strftime('%a')
    return today.strftime('%A').lower()

# helper for browswer based data scraping 
def switchUrl(x=468, y=63, url="https://www.dollargeneral.com/dgpickup/deals/coupons?"):
    # CATEGORY = HELPER Web Interaction Function
    # automate browser request change in switching relevant pages or to new collections
    # REQ : pyperclip, pyautogui, time
    pag.moveTo(x, y, duration=2.2)
    pag.click(clicks=1)
    clip.copy(url)
    time.sleep(1)
    pag.keyDown('ctrlleft')
    pag.keyDown('v')
    pag.keyUp('ctrlleft')
    pag.keyUp('v')
    pag.press('enter')
    time.sleep(5)
    return None    

# helper for browser based scraping to flush remaining results
def eatThisPage(reset=False):
    # flush remaining results after main data call to server using browser context menu
    # REQ : pyautogui, time, subprocess
    pag.moveTo(1410, 1004)
    time.sleep(2)
    pag.click(button='right')
    time.sleep(1)
    pag.moveRel(50, -25, duration=3)
    pag.click()
    time.sleep(15)
    if reset:
        time.sleep(46)
        # add: browser.config : restore_after_crash = false
        subprocess.Popen(['taskkill', '/IM', 'firefox.exe', '/F'])
    return None

# helper for web scraping setup
def loadExtension():
    # load extension via tab
    # REQ : time, switchUrl(), time
    pag.keyDown('ctrlleft')
    pag.keyDown('t')
    pag.keyUp('ctrlleft')
    pag.keyUp('t')
    time.sleep(3)
    clip.copy('about:debugging#/runtime/this-firefox')
    pag.keyDown('ctrlleft')
    pag.keyDown('v')
    pag.keyUp('ctrlleft')
    pag.keyUp('v')
    pag.press('enter')
    time.sleep(2)
    pag.moveTo(x=895, y=300, duration=2)
    pag.click()
    time.sleep(2)
    pag.typewrite("background.js")
    time.sleep(2)
    pag.press('enter')
    time.sleep(2)
    pag.keyDown('ctrlleft')
    pag.keyDown('tab')
    pag.keyUp('ctrlleft')
    pag.keyUp('tab')

    return None

# helper to set up browser scraping 
def setUpBrowser(n=0, initialSetup=True, url=None):
    # create setup for Kroger coupons (digital and cashback)
    # REQ : pyautogui, time, subprocess, loadExtension(), switchUrl()
    if initialSetup:
        p1 = subprocess.Popen(['C:\Program Files\Mozilla Firefox\\firefox.exe'])
        p1.wait(10)
    if n=='kroger-trips':
        # for trips
        switchUrl(url="https://www.kroger.com/")
        time.sleep(3)
        # Nav to Account Button
        pag.moveTo(1785, 153)
        # Nav to My Purchases
        pag.moveRel(0, 195)
        time.sleep(1)
        pag.click()
        time.sleep(8)
        # Load Extension 
        loadExtension()
        time.sleep(2)
        # Unselect SignIn 
        pag.moveTo(736, 625, duration=1)
        pag.click()
        time.sleep(2)
        # move to sign In button with credentials
        pag.moveRel(50, 50)
        # 786, 675
        pag.click()
        time.sleep(2)
    elif n=='kroger-coupons': # @ Kroger Coupons
        # start browser
        # switch to wanted page
        #switchUrl(url="https://www.kroger.com/savings/cl/coupons")
        switchUrl(url=url)
        # exit out of intro modal
        if initialSetup:
            pag.moveTo(x=1214, y=297, duration=1.9)
            pag.click()
            time.sleep(2)
            pag.click()
            time.sleep(2)
            # load extension: background.js
            loadExtension()
            pag.moveTo(1878, 131)
            pag.click()
            # click change store
            pag.moveTo(x=1682, y=160, duration=1.9)
            pag.click()
            time.sleep(2)
            # click find store
            pag.moveTo(x=1731, y=392, duration=1.9)
            pag.click()
            # remove default data
            pag.typewrite(["backspace"]*5, interval=1)
            time.sleep(2)
            # replace with zip and press enter
            pag.typewrite(list(f"{ZIPCODE}"), interval=1)
            time.sleep(2)
            pag.press('enter')
            time.sleep(2)
            # select modality : In-Store
            pag.moveTo(x=1762, y=803, duration=1.9)
            pag.click()
            time.sleep(2)
            # select wanted store {could be variable for different stores}
            pag.moveTo(x=1725, y=675, duration=1.9)
            pag.click()
            time.sleep(10)
            pag.moveTo(1878, 131)
            pag.click()
            # reset filter to get amount of available coupons
            pag.moveTo(1800, 528, duration=2)
            pag.click()
            time.sleep(1)
            pag.press(['down', 'enter'], interval=1)
            time.sleep(3)
        else:
            # extension will have been loaded, correct store&modality chosen, filter reset after eat.  
            pag.moveTo(x=1214, y=297, duration=1.9)
            pag.click()
            time.sleep(10)
    elif n=='aldi-items': # @ ALDI / Instacart Store
    # create setup for Aldi instacart
        switchUrl(url="https://shop.aldi.us/store/aldi/storefront")
        # wait for free delivery modal to load
        time.sleep(12)
        #
        pag.moveTo(1307, 194, duration=3)
        time.sleep(2)
        pag.click()
        time.sleep(6.5)
        #
        pag.moveTo(93, 286, duration=3)
        pag.click()
        time.sleep(5)
        #
        pag.moveRel(0, 50, duration=2)
        pag.click()
        time.sleep(5)
        #
        pag.moveTo(371, 397, duration=3)
        pag.click()
        time.sleep(6.5)
        loadExtension()
        time.sleep(2)
    elif n=="publix-coupons": # publix Coupons
        # location access now occurs automatically
        # load extension then wait for location to be set by site and then send to server
        time.sleep(3)
        loadExtension()
        time.sleep(3)
        # nav to https://www.publix.com/savings/all-deals
        switchUrl(url="https://www.publix.com/savings/all-deals")
        # wait for page to load
        time.sleep(15)
        # send to server
        eatThisPage(reset=True)
    elif n=='publix-items': # publix / instacart site
        switchUrl(url="https://delivery.publix.com/store/publix/collections/")
        time.sleep(7)
        # select input for zip
        pag.moveTo(858, 653, duration=2)
        pag.click()
        pag.typewrite(list(f"{ZIPCODE}"), interval=.35)
        pag.press('enter')
        time.sleep(1)
        # select 1st Party login link @ bottom 
        pag.moveTo(969, 863, duration=2)
        pag.click()
        # Have Browser Profile Save IC user/pass for automatic entry and Press Login 
        pag.moveTo(773, 515, duration=2)
        pag.click()
        time.sleep(10)
        loadExtension()
        time.sleep(2)
    elif n=='food-depot-items': # fooddepot items / internal website
        # can go straight to load extension
        switchUrl(url="https://shop.fooddepot.com/online/fooddepot40-douglasvillehwy5/home")
        loadExtension()
        time.sleep(2)
    elif n=='food-depot-coupons': # food depot coupons  + an Apple/Gmail Shortcut
        switchUrl(url="https://www.fooddepot.com/coupons/")
        pag.moveTo(914, 376)
        pag.click()
        pag.typewrite(list(PHONE_NUMBER), interval=.25)
        pag.press('enter')
        time.sleep(2)
        pag.moveTo(807, 401)
        pag.click()
        pag.typewrite(list(VERIFICATION_CODE), interval=.2)
        time.sleep(5)
        loadExtension()
        time.sleep(2)
        pag.moveTo(787, 937)
        pag.click()
        pag.moveTo(1859, 68)
        pag.click()
        pag.moveRel(0, 70, duration=2.4)
        pag.click()
    elif n=='dollar-general-coupons': # Dollar General Coupons and Items
        # dollar general user tracking id has been whitelisted to prevent website from breaking 
        # amending MalwareBytes for trackers for every session no longer necessary
        # create setup for dollar general
        switchUrl(url="https://www.dollargeneral.com/dgpickup/deals/coupons")
        loadExtension()
        # change store
        # access stores dropdown
        pag.moveTo(73, 222, duration=2)
        pag.click()
        time.sleep(2)
        # Access Store Near Filter
        pag.moveTo(32, 302, duration=2)
        pag.click()
        time.sleep(3)
        # Click Use My Location
        pag.moveTo(82, 410, duration=2)
        pag.click()
        time.sleep(3)
        # Select Closest Store from Resulting Dropdown
        pag.moveTo(239, 440, duration=2)
        pag.click()
        # wait for set iterations
        time.sleep(12)
        response = requests.get("http://127.0.0.1:5000/i").json()
        iterations = response.get('i') // 15
        for i in range(iterations):
            pag.press('end')
            time.sleep(2)
            ix, iy = 929, 365
            pag.moveTo(ix, iy)
            if pag.pixel(ix, iy)!=(0, 0, 0):
                pag.moveRel(0, -20)
                ix, iy = pag.position()

            pag.moveTo(999, 365, duration=2)
            time.sleep(1.5)
            pag.click()
            time.sleep(4)
        pag.press('home')
        time.sleep(2)
    elif n=="dollar-general-items":
        # create setup for dollar general
        switchUrl(url="https://www.dollargeneral.com/c/on-sale")
        # refresh to allow for previously filtered api calls to be allowed
        pag.keyDown("ctrlleft")
        pag.keyDown("r")
        time.sleep(1)
        pag.keyUp("r")
        pag.keyUp("ctrlleft")
        time.sleep(8)
        loadExtension()
        # change store
        # access stores dropdown
        pag.moveTo(73, 222, duration=2)
        pag.click()
        time.sleep(2)
        # Access Store Near Filter
        pag.press(["tab", "enter"], interval=1)
        time.sleep(3)
        # Change Zipcode
        pag.press("tab", interval=1, presses=2)
        pag.typewrite(list(ZIPCODE), interval=.35)
        pag.press("enter")
        time.sleep(5)
        # Select Closest Store from Resulting Dropdown
        pag.press(["tab"]*3+["enter"], interval=1)
        # iterations will be set via subsequent function
        time.sleep(10)
    elif n=='family-dollar-coupons': # family-dollar smart coupons
    # create setup for family dollar coupons
        loadExtension()
        time.sleep(1)
        switchUrl(url="https://www.familydollar.com/smart-coupons")
        time.sleep(5)
        eatThisPage(reset=True)
        # eat
    elif n=='family-dollar-items': # familydollar items
        switchUrl(url="https://www.familydollar.com/categories?N=categories.1%3ADepartment&No=0&Nr=product.active:1")
        time.sleep(3)
        loadExtension()
        time.sleep(2)
        # switch products per page to 96
        pag.press(['end'])
        time.sleep(5)
        pag.moveTo(697, 353, duration=3)
        pag.click()
        pag.press(['down', 'down', 'enter'], interval=1)
        time.sleep(7)
    elif n=='family-dollar-items-instacart':
        switchUrl(url="https://sameday.familydollar.com/store/family-dollar/storefront")
        time.sleep(10)
        pag.moveTo(x=1440, y=198, duration=2)
        pag.click()
        time.sleep(2)
        pag.moveTo(x=770, y=341, duration=2)
        pag.click()
        time.sleep(4)
        pag.press((["tab"]*5)+["enter"], interval=.4)
        time.sleep(5)
        loadExtension()
        time.sleep(4)
    else:
        print('skipping setup')

    return None

# 
def getStoreData(chain):
    # TODO: a function that automates processes to gather store data from the following sites API: aldi, publix, familydollar, fooddepot, dollar general
    # TODO: Amend background.js File to set settingStore variable to 1 
    # REQ: pyautogui, time, switchUrl(), loadExtension()
    if chain=='publix':
        # on publix site :
        # action click: current store icon on head
        # will call https://services.publix.com/api/v1/storelocation?types=R,G,H,N,S&option=&count=15&includeOpenAndCloseDates=true&isWebsite=true&storeNumber=691&distance=15&includeStore=true
        # result has information on 15 closest stores. General information common to stores, hours, etc. 
        # nb: choosing store loses this information
        switchUrl(url='https://www.publix.com/')
        loadExtension()
        time.sleep(2)
        pag.moveTo(1530, 160, duration=3)
        pag.click()
        pag.moveTo(1806, 428, duration=2)
        pag.click()
        eatThisPage()
    elif chain=='aldi':
        # on aldi site:
        # go to aldi.us/en/weekly-specials/our-weekly-ads/
        # https://graphql-cdn-slplatform.liquidus.net/ with payload operationName: "storeDataQuery"
            # returns all store related information

        # click on change store to kickoff
        # https://graphql-cdn-slplatform.liquidus.net/ with payload operationName: "getStoreList"
            # will get top 6 stores near entered zipCode
        switchUrl(url='https://www.aldi.us/en/weekly-specials/our-weekly-ad')
        loadExtension()
        time.sleep(2)
        pag.typewrite(list(ZIPCODE)+['enter'], interval=.5)
        time.sleep(2)
        eatThisPage()
    elif chain=='dollarGeneral':
        # navigate to /dgickup/deals/coupons
        # will set off call to : https://www.dollargeneral.com/bin/omni/pickup/storeDetails
        # will return object with features that require additional parsing : ex hh: thursday store hours
        # click on my store button:
        # will set off : https://www.dollargeneral.com/bin/omni/pickup/storeSearch
        # that gives more store level data
            #  I need data from the 2 closest in my area right now '13141'and '13079'in calls to storeDetails
        switchUrl(url='https://www.dollargeneral.com/dgpickup/deals/coupons')
        loadExtension()
        time.sleep(1)
        pag.moveTo(104, 408, duration=2)
        pag.click()
        time.sleep(2)
        pag.moveTo(1659, 463, duration=2)
        pag.click()
        eatThisPage()
    elif chain=='familyDollar':
        # returns a list of store locations with calls to https://storelocations.familydollar.com/rest/locatorsearch
        switchUrl(url='https://www.familydollar.com/store-locator')
        time.sleep(5)
        loadExtension()
        time.sleep(2)
        pag.moveTo(371, 605, duration=2)
        pag.click()
        time.sleep(4)
        pag.typewrite(list(ZIPCODE)+list('enter'), interval=.5)
        time.sleep(5)
    elif chain=='foodDepot':
        loadExtension()
        time.sleep(5)
        switchUrl(url='https://shop.fooddepot.com/online/fooddepot40-douglasvillehwy5/home')
        time.sleep(2)
        eatThisPage()
    else:
        raise ValueError('chain must be provided')
    

    return None

# web scraping helper specific for dollar general
def loadMoreAppears(png='./requests/server/images/moreContent.png'):
    # Evaluate if Dollar General's Promotional Page of Associated Items Has More Items
    # Returns location of button in y [419, 559] band of standard 1920 x 1080 screen 
    # REQ: pyautogui, OpenCV (sliently), server/images
    pag.scroll(800)
    time.sleep(2.5)
    locations = list(pag.locateAllOnScreen(png, confidence=.6, grayscale=False))
    locations = list(map(lambda x: pag.center(x), locations))
    i = 0
    locations = list(filter(lambda x: x.y>395 and x.y<440, locations))
    if locations:
        loc = locations[i]
        x, y = loc
        color = pag.pixel(int(x), int(y))
        if color==(0, 0, 0):
            return loc
        else:
            i+=1

    return None

# web scraping helper specific for family dollar iternal item catalog
def getArrow(sleep=2):
    # CATEGORY = Helper Web Interaction Function
    # Pagination Helper For Family Dollar Items / Prices Collection
    # REQ : pyautogui, time
    time.sleep(sleep)
    pag.moveTo(1559, 346)
    time.sleep(sleep)
    pag.click() 
    return None

def scrollDown(sleep=10):
    # CATEGORY = Helper Web Interaction Function
    # Helper for scrolling data with api calls linked to pagination (food depot, aldi, publix)
    # pyautogui, sleep
    time.sleep(sleep)
    pag.press('end')
    return None

def insertFilteredData(entries, collection_name, db, uuid) -> None:
    # Database Aggregation Then Entry Function 
    # handles bulk inserts for collections that maintain singular entries for items
    # i.e. : items, promotions, recipes, sellers, stores, trips, users
    # REQ : pymongo, os, 
    print(len(entries), collection_name)
    start = time.perf_counter()
    try:
        getattr(entries, "__len__")
        if type(entries)!=list:
            entries = [entries]
    except AttributeError:
        entries = [x for x in entries]
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    # filter based on specified ID 
    filters = {uuid: {"$exists": True}}
    res = db[collection_name].aggregate(pipeline=[
        {"$match": filters},
        {"$group": {"_id": uuid, "fields": {"$addToSet": f"${uuid}"}}},
        {"$project": {"_id": 0}}
    ])
    currentIds = [tuple(x['fields']) for x in res][0]
    client.close()
    keys = list(filters.keys())

    entriesForDb = filter(lambda x: x[uuid] not in currentIds, entries)
    entriesForDb = [x for x in entriesForDb]
    if len(entriesForDb)==0:
        print("no values to place into {}".format(collection_name))
    else:
        res = db[collection_name].insert_many(entriesForDb).inserted_ids
        print(f"Inserted {len(res)} documents in {collection_name}")
     
    print(f"ended in {time.perf_counter()-start} seconds")

    return None


def insertData(entries, collection_name, db='new'):
    # Database helper for Largest Collections in Database (prices, inventories)
    # Going to add Entries to Locally running DB w/ same structure as Container Application
    # Then migrate them over to Container DB
    # Wrapper to always use insert many
    # REQ : os, pymongo 
    print(len(entries), collection_name)
    try:
        getattr(entries, "__len__")
        if type(entries)!=list:
            entries = [entries]
    except AttributeError:
        entries = [x for x in entries]
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    res = db[collection_name].insert_many(entries)
    res = len(res.inserted_ids)
    print(f"Inserted {res} documents in {collection_name}")
    client.close()

    return None

def retrieveData(collection_name, db='new'):
    # Database Read Function Helper
    # REQ : os, pymongo 
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    res = db[collection_name].find({}, projection={"_id": 0})
    data = [x for x in res]
    client.close()
    print(f"Found {len(data)} documents in {collection_name}")
    

    return data

def createDBSummaries(db='new'):
    # Helper to Create MetaData File for DB In Order Track Database and Collection Evolution Overtime
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    with open('../data/stats.json', 'w') as file:
        dbStats = db.command('dbstats')
        dbStats.setdefault('collectionStats', [])
        for col in db.list_collections():
            dbStats['collectionStats'].append({k:v for k, v in db.command('collstats', col.get('name')).items() if k!='wiredTiger' and k!='indexDetails'})
        file.write(json.dumps(dbStats, indent=3))

    print('updated stats')
    client.close()

    return None

def runAndDocument(funcs:list, callNames:list, kwargs: list, callback=None):
    # document scraping functions via a description and function calls
    # Place into Runs Collections
    # Admin DB to Track and Monitor the Execution of Scraping Functions that Work on Different Schedules Based on Store's Internal Promotion Schedule
    # TODO: Add CPU/resource usage for processes related to the functions (browser/Python Application, Mongo Create Operations) 
    functions = []
    startDateTime = dt.datetime.now(tz=pytz.UTC)
    for name, func, args in zip(callNames, funcs, kwargs):
        if callable(func):
            start = time.perf_counter()
            if bool(args) and type(args)==dict:
                func(**args)
            elif bool(args) and type(args)==list:
                func(*args)
            else:
                func()
            end = round(time.perf_counter() - start, 4)
            funcName = [k for k, v in globals().items() if v==func][0]
            functions.append({'function': funcName, 'time': end, 'description': name, 'variables': kwargs})
    duration = dt.datetime.now(tz=pytz.UTC) - startDateTime
    duration = round(duration.total_seconds(), 4)
    data = {'executeVia': 'call', 'functions': functions, "startedAt": startDateTime, 'duration': duration}
    insertData(data, 'runs')
    if callback:
        callback()

    return None


def simulateUser(link):
    # Scraping Operation
    # Handles Websites with more involved UI elements that Control API requests
    # needLinks contain default args for respective site
    neededLinks = {'cashback': {"no": 12, "button": "./requests/server/images/cashback.png", "confidenceInterval": .66, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -1640, 'initialScroll': -800},\
        'digital': {"no":12, "button": "./requests/server/images/signIn.png", "confidenceInterval": .6, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -1640, 'initialScroll': -740},\
            'dollarGeneral': {'no': 12, "button": "./requests/server/images/addToWallet.png", "confidenceInterval": .7, 'maxCarousel': 3, 'buttonColor': (0, 0, 0), 'scrollAmount': -1750 ,"moreContent": "./requests/server/images/loadMore.png",\
                 'initialScroll': -1750}}
    # browser up start will be setting user location, navigating to the page, and placing mouse on first object
    # from here: the code will commence
    # start at top of the screen 
    # align all items https://www.kroger.com/savings/cl/coupons/
    response = requests.get("http://127.0.0.1:5000/i").json()
    j = 0
    while response.get('i')==None:
        print(f"waiting for i from server for {j} seconds")
        j+=1
        time.sleep(1)
        if j > 50: 
            raise ValueError("I was not defined on the server for {}".format(link))
        response = requests.get("http://127.0.0.1:5000/i").json()

    iterations = (response.get('i') // neededLinks[link]['no'])+2

    if link!='dollarGeneral':
        time.sleep(3)
        pag.scroll(neededLinks[link]['initialScroll'])
        time.sleep(2)
    else:
        iterations = ((response.get('i')-9) // neededLinks[link]['no'])+2

    prevButtonsX = set()
    # find all buttons
    for i in range(iterations):
        buttons = list(pag.locateAllOnScreen(neededLinks[link]['button'], confidence=neededLinks[link]['confidenceInterval'], grayscale=False))
        buttons = [pag.center(y) for i, y in enumerate(buttons) if (abs(buttons[i].left-buttons[i-1].left) > 100) or (abs(buttons[i].top-buttons[i-1].top)>100)] # > 2
        if link=='dollarGeneral':
            buttons = list(filter(lambda x: x.x<1600, buttons))
        if i==0:
            prevButtonsX = set(map(lambda x: x.x, buttons))

        print(f"Located {len(buttons)} Items")
        if len(buttons)>12 or iterations-i<=2:
            yaxis = list(map(lambda b: b.y, buttons))
            if iterations-i<=200: 
                buttons = [x for x in buttons if x.x in prevButtonsX]
            else:
                buttons = [x for x in buttons if (yaxis.count(x.y) >= neededLinks[link]['maxCarousel'] ) and (x.y+1 not in yaxis)]
        print(len(buttons), "buttons")
        for b in buttons:
            pag.moveTo(b)
            x, y = pag.position()
            draws = 0
            direction = 1
            print(pag.position())
            if link!='dollarGeneral':
                pag.moveRel(-186, 0, duration=1.5)
                pag.click()
                # escape out of portal
                time.sleep(7.5)
                pag.press('esc')
                pag.moveRel(186, 0, duration=1.5)
            else:
                pag.moveRel(-160, 0, duration=1.5)
                pag.moveRel(0, -125, duration=1.5)
                issuesCount = requests.get("http://127.0.0.1:5000/issues").json().get('issues')
                # expand to items page
                pag.keyDown('ctrlleft')
                pag.click()
                time.sleep(3)
                pag.keyUp('ctrlleft')
                time.sleep(6)
                # page level activities
                issuesAfterRequest = requests.get("http://127.0.0.1:5000/issues").json().get('issues')
                while issuesCount!=issuesAfterRequest:
                    pag.moveTo(105, 613)
                    pag.click()
                    time.sleep(1)
                    pag.click()
                    time.sleep(1)
                    pag.moveTo(89, 61, duration=1)
                    pag.click()
                    time.sleep(12)
                    prevIssueCt = issuesAfterRequest
                    issuesAfterRequest = requests.get("http://127.0.0.1:5000/issues").json().get('issues')
                    if (issuesCount+5==issuesAfterRequest) or (issuesAfterRequest==prevIssueCt):
                        break
                pag.press('end')
                time.sleep(3)
                # check for load more button (indicating more loadable items) 
                moreItems = loadMoreAppears()
                issuesCt = requests.get("http://127.0.0.1:5000/issues").json().get('issues')
                while bool(moreItems):
                    button = moreItems
                    pag.moveTo(button.x, button.y, duration=0.5)
                    pag.click()
                    time.sleep(7)
                    pag.press("end")
                    time.sleep(3)
                    moreItems = loadMoreAppears()
                pag.keyDown('ctrlleft')
                pag.keyDown('w')
                pag.keyUp('ctrlleft')
                pag.keyUp('w')
                time.sleep(12.5)
                        
        scrollNumber = -20
        if i<=0 and link=='dollarGeneral':
            pag.scroll(neededLinks[link]['initialScroll'])
        elif link=='dollarGeneral':
            pag.scroll(neededLinks[link]['scrollAmount'])
            time.sleep(2)
            pag.scroll(scrollNumber)
            if i>2:
                for j in range(i-2):
                    pag.scroll(scrollNumber)
            prevButtonsX = set(button.x for button in buttons)
            print(prevButtonsX)
        else:
            if i>0 and i%19==0:
                pag.scroll(neededLinks[link]['scrollAmount'])
                time.sleep(2.4)
                pag.scroll(15)
            else:
                pag.scroll(neededLinks[link]['scrollAmount'])
                
        print('finished row {}; {} to go; mouse currently @ {} :: {} seconds left'.format(i, iterations-i, pag.position(), (time.perf_counter()/(i+1))*(iterations-i)))
        time.sleep(2)


    print(f"Processed {iterations} in {time.perf_counter()} seconds")
    return None

def updateGasoline(data):
    # Kroger Deconstruction Helper
    # cleaner function for Kroger trip data
    # Kroger Fuel Points (previously in price modifiers) now show up as duplicate entry of gasoline with a quantity of zero and a negative price paid to correspond to savings
    # Must be run before deconstructions.
    # Raises ZeroDivisionError on Calucations that use Quantity 

    for trip_index, trip in enumerate(data):
        for item_index, item in enumerate(trip.get('items')):
            if item.get('quantity')==0:
                if item_index==0:
                    data[trip_index]['items'][item_index+1]['pricePaid'] = round(data[trip_index]['items'][item_index]['pricePaid']+data[trip_index]['items'][item_index]['pricePaid'], 2)
                    data[trip_index]['items'][item_index+1]['totalSavings'] = round(data[trip_index]['items'][item_index]['totalSavings']+data[trip_index]['items'][item_index]['totalSavings'], 2)
                    data[trip_index]['items'][item_index+1]['priceModifiers'].extend(data[trip_index]['items'][item_index]['priceModifiers'])
                else:
                    data[trip_index]['items'][item_index-1]['pricePaid'] = round(data[trip_index]['items'][item_index]['pricePaid']+data[trip_index]['items'][item_index-1]['pricePaid'], 2)
                    data[trip_index]['items'][item_index-1]['totalSavings'] = round(data[trip_index]['items'][item_index]['totalSavings']+data[trip_index]['items'][item_index-1]['totalSavings'], 2)
                    data[trip_index]['items'][item_index-1]['priceModifiers'].extend(data[trip_index]['items'][item_index]['priceModifiers'])
                data[trip_index]['items'].pop(item_index)

    return data

def getKrogerTrips():
    iterations = requests.get("http://localhost:5000/i")["i"]
    iterations = ( iterations // 5 ) + 1
    for i in range(iterations):
        # Nav to End of Page
        pag.press(["pagedown"]*3)
        # Move to Arrow
        pag.moveTo(1192, 323)
        time.sleep(1)
        # click arrow
        p.click()
        # request with timeout after 5 seconds and not refire until page reload
        salt = random.randint(400, 1300)
        salt /= 100
        print(f"sleeping for {8+salt}")
        time.sleep(8+salt)
    # Proceed Func call with final Call to Eat this Page 
    return None


def getFamilyDollarItems():
    # example url : https://www.familydollar.com/categories?N=categories.1%3ADepartment%2Bcategories.2%3AHousehold&No=0&Nr=product.active:1
    # dependencies: scrollDown and getArrow
    # a function that retrieves all the items and prices from the local family dollars
    # CATEGORY = Larger Web Function
    # Site Specific Interaction for More Involved User Site
    
    # Dependices : Server Setting Iterations at Setup,
    # Graph: setupBrower >> getFamilyDollarItems >> eatThisPage
    tries=0
    results = requests.get('http://127.0.0.1:5000/i').json()
    while results.get('i')==None:
        time.sleep(2)
        print('slept for two, no i')
        results = requests.get('http://127.0.0.1:5000/i')
        tries+=1
        if tries>20:
            raise ValueError('i was not defined on server')
        
    results = results.get('i')
    results = results // 96
    startingSleep=10
    pag.moveTo(100, 645)
    pag.click()
    time.sleep(startingSleep)
    startTime = time.perf_counter()

    for i in range(results):
        scrollDown(startingSleep)
        getArrow()
        if i%34==0 and i>0:
            print(f"finished with {i}. {results-i} to go. Data Sent")
            startingSleep=60
        else:
            salt = random.randint(1, 25)
            startingSleep=10+salt

    print(f"finished in {time.perf_counter()-startTime} seconds. Obtainted {results} objects.")
    
    return None

def getScrollingData(chain: str):
    # Browser Scraping Function that Handles Pages with Simple Pagination (only need to scroll to execute further API calls) and Handles Url Changes
    # Performs keyboard actions / browser navigation by referencing the scroll bar's position
    # Handles Instacart Sites (publix, aldi, family dollar) and Food Depot Site
    # graph : setupBrowser >> getScrollingData >> eatThisPage
    scrollVars = [
    {'chain': 'fooddepot', 'base_url': 'https://shop.fooddepot.com/online/fooddepot40-douglasvillehwy5/shop/', 'urls': [
        "produce", "meatseafood", "bakery", "deli", "dairyeggs", "beverages",
        "breakfast","cannedgoods", "drygoodspasta", "frozen", "household", "international",
        "pantry", "personalcare", "pets", "snacks", "alcohol", "babies", "seasonal"
    ]
    },
    {'chain': 'aldi', 'base_url': 'https://shop.aldi.us/store/aldi/collections/', 'urls': [
        "d295-alcohol" ,"d282-produce", "d297-dairy-eggs", "d292-snacks",
        "d299-frozen", "d290-pantry", "d298-meat-seafood", "d294-bakery",
        "d289-canned-goods", "d17068-aldi-finds-limited-time", "d296-beverages",
        "d286-household", "d291-dry-goods-pasta", "d288-breakfast", "d283-deli",
        "d293-babies", "d285-personal-care", "d284-pets",
        "d12951-organic", "d6517-floral", "d287-international", "d18863-vegan",
        "d13031-gluten-free", "d26015-seasonal", "dynamic_collection-sales"]
    },
    {'chain': 'publix', 'base_url': 'https://delivery.publix.com/store/publix/collections/', 'urls': [
        'd1102-produce', 'd1090-dairy-eggs', 'd1106-frozen','d1089-beverages', 'd1099-snacks', 'd1095-pantry', 'dynamic_collection-sales',
        'd1094-meat-seafood', 'd1088-bakery', 'd1091-deli', 'd1092-household', 'd1104-canned-goods',
        'd1100-dry-goods-pasta', 'd1097-personal-care', 'd1103-breakfast', 'd1093-international', 'd1101-babies', 'd1098-pets', 'd5626-greeting-cards',
        'd21232-wine', 'd21231-beer', 'd3152-popular', 'd5625-floral', 'd5630-platters', 'd50450-ready-to-eat-ready-to-cook', 'd1105-new-and-interesting',
        'd41671-storm-prep','d41622-tailgating', 'd51523-deli-grab-and-go']
    },
    {'chain': 'family dollar', 'base_url': "https://sameday.familydollar.com/store/family-dollar/collections/", 'urls':[
        'd34605-grocery', 'd34606-household-essentials', 'd34603-personal-care', 'd34602-beauty', 'd34598-kitchen-dining',
        'd34604-pets', 'd34599-home', 'd36226-baby-care', 'd34596-bath', 'dynamic_collection-sales'
    ]
    }]
    base_url, urls = list(map(lambda x: (x.get('base_url'), x.get('urls')), list(filter(lambda x: x['chain']==chain, scrollVars))))[0]

    # CATEGORY = Larger Web Task
    # works for Aldi + Publix Instacart Sites as well as Food Depot's 1st Party Site
    pageEndColor = (205, 205, 205)
    continueColor = (240, 240, 240)
    noScrollColor = (255, 255, 255)
    noScrollColor2 = (248, 248, 248)
    startTime = time.perf_counter()
    # switch to first url
    for url in urls:
        switchUrl(url=base_url+url)
        scrollDown(sleep=5)
        scroll_color = pag.pixel(x=1911, y=1016)
        # checks to see if scroll bar has more room to go
        while scroll_color!=pageEndColor:
            if scroll_color==noScrollColor or scroll_color==noScrollColor2:
                break
            else:
                scrollDown(sleep=22.2)
                scroll_color=pag.pixel(x=1911, y=1016)
        print('Done with ', url)
    print(f"finished in {time.perf_counter()-startTime} seconds. Obtainted {len(urls)} pages.")
    return None

def getPublixCouponData(deals=673):
    # Category = Larger Web Task
    # TODO: Full coupon data can be receieve w/ right url in one step
    # Scrapes Publix 1st Party Coupon Data in Single Step
    loadMoreColor = (171, 205, 159)
    loadMorePosition = (1091, 344)
    iterations = 673 // 36
    pag.click()
    for i in range(iterations):
        time.sleep(2)
        pag.press('end')
        time.sleep(2)
        pag.scroll(400)
        time.sleep(2)
        pag.moveTo(*loadMorePosition)
        positionColor = pag.pixel(*loadMorePosition)
        if positionColor == loadMoreColor:
            time.sleep(2)
            pag.click()

    return None

# Amendment to Dollar General Items Procedure: 
def getDGItems():
    # make sure set up handles extensionLoading, urlLoading, and store handling
    # wait for iterations set by extension to happen
    # make sure browser navigates to sale items with store and extension handling complete
    pag.moveTo(1520, 426, duration=.1)
    pag.click()
    i = requests.get("http://localhost:5000/i").json()["i"]
    iterations = (i // 12) + 1
    badUrls = []
    print(iterations, " number of iterations")
    pag.press('end')
    time.sleep(3)
    sleeper = 1
    for n in range(iterations):
        time.sleep(sleeper)
        pag.press("end")
        time.sleep(1)
        pag.scroll(500)
        # two pronged approach to ensure it cursor provides access to next page 
        initialButtonPosition = (1036, 320)
        buttonActiveColor = (64, 64, 64)
        cursorIconCode = 65569
        pag.moveTo(*initialButtonPosition, duration=2)
        color = pag.pixel(*initialButtonPosition)
        cursorCode = win32gui.GetCursorInfo()[1]
        if color==buttonActiveColor and cursorCode==cursorIconCode:
            pag.click()
            sleeper = random.randint(10, 16)
            print(f"finished with {n}. {iterations-(n+1)} left. sleeping for {sleeper}...")
        else:
            print("logged an error at {} iteration".format(n))
            badUrls.append(f"https://www.dollargeneral.com/c/on-sale?page={n+1}")
            
    # tweaking blocked requests for this specific site has helped diminish request from returning 500, but still keep errors in mind if bug continues
    if badUrls:
        print("Loading Errors Occured At: ")
        pprint(badUrls)

        
        


    return None

def deconstructDollars(file='./requests/server/collections/familydollar/digital052122FD.json'):
    # Deconstructs Dollar General Items and Promotions into Items, Promotions, Prices, and Inventories
    # Deconstructs Family Dollar Promotions to Promotions with Normalized Features 
    # Applied to Successfully Generated Dollar Store Scrape Files 
    # Handles Insertion

    # retrieve store selection api for stores: DollarGeneral, FamilyDollar, Publix, Aldi, FoodDepot 
    # existing coupon schema:
        # uuid: id, krogerCouponNumber
        # qualifying products: productUPCs
        # qualifying products categories: brandName, categories
        # coupon categories: type, cashbackCashoutType, isSharable, forCampaign, specialSavings
        # web elems: imageUrl, title, requirementDescription
        # dates: startDate, expirationDate
        # values: redemptionsAllowed, requirementQuantity, value, 
    # dg coupon schema
        # uuid: OfferGS1, OfferID, OfferID=mainCouponId,  OfferCode,
        # values: RewardQuantity, RedemptionLimitQuantity, MinQuantity, RewardedOfferValue, 
        # coupon categories: isManufacturerCoupon, OfferType, RecemptionFrequency, BrandName, Companyname
            # OfferSummary = "Save $3.00", TargetType, RewardedCategoryName
        # web elems: Image1, Image2, OfferDescription, offerDisclaimer, 
        # dates: OfferActivationDate, OfferExpirationDate   
        # qualifying products = in parent element url
    # family dollar coupon schema
        # uuid: mid, 
        # qualifying products: nihil 
        # qualifying products categories: nihil 
        # coupon categories: brand, category{}, clipType, offerType, redemptionGating, redemptionChannels, group, groups, status, ?tags, ?badge
        # web elems: imageUrl, enhancedImageUrl, description{text}, shortDescription{text}, terms, type{text='mfg'}, 
        # dates: clipEndDate, clipStartDateTime, clipEndDateTime, clipStartDate, expirationDate, expirationDatetime, redemptionStartDatetime
        # coupon values: clippedCount, popularity,  minPurchase, offerSortValue, valueSort, valueText, redemptionsPerTransaction, isActive, ?value, 
    # Promotions.categories <List> -> {Condiments & Sauces, Beverages, Pasta Sauces Grain, International, Cleaning Products, Baby, Apparel, General, Beauty, Garden & Patio, Meat & Seafood,\
            # Home Decor, Deli, Health, Breakfast, Bakery, Sporting Goods, Pet Care, Hardware, Entertainment, Gift Cards, Dairy, Personal Care, Canned & Packaged, Candy, Tobacco,
            # Frozen, Produce, Snacks, Adult Beverages, Health & Beauty, Baking Goods, Kitchen, Natural & Organic, Electronics, Party}
        # Promotions.type <String> -> {CASH_BACK, STANDARD}
        # Promotions.cashbackCashoutType <String> -> {UNRESTRICTED, NON_RETAILER_ONLY}
        # Promotions.specialSavings <List[<Dicts>]>.name -> {HOTP5: Use up to 5 Times in a Single Transaction, 5X: <-ibid, 4XGCEVENT: GiftCard/Fuel Points, HOTP3:Use Up to Five Times in a Single Transaction, HOMECHEF:Private Label Ready Made Meals,\
            # BPCS:Beauty & Personal Care Savings, SFY:Personalized Savings, CL:Pickup&Delivery Only, NSK:<-ibid, WDD:Weekly Digital Deals}
        # Promotions.modalities <List> -> {DELIVERY, PICKUP, IN_STORE, SHIP}
        # Promotions.redemptionsAllowed -> {-1, 1, 2, 3, 4, 5} <- -1 often corresponds to multiple redemptions in a single trip, should change to reflect this

        # family dollar: mdid
            # all available :
                # XclippedCount => social amount coupon clipped <Int>
                # Xpopularity  => social amount coupon clipped <Int>
                # Xbrand => Company Promotions <String>
                # Xcategory => Code value, name and key for promotional items and promtion <HashMap> 
                # XclipEndDate => ISO Datetime String w/o Time for promotion clip end <HashMap>
                # XclipStartDate => ISO Datetime String w/o Time for promotion clip start <HashMap>
                # XclipType => clip type  <String> {'consumer clip'}
                # Xdescription => "Save ${valueSort} on any ONE ..."<String> ~= shortDescription w/ more exclusions/terms baked in short form
                # XexpirationDate => ISO Datetime String w/o Time for promotion redemption end <HashMap>
                # XimageUrl => href for Promotion Image <String>
                # XminPurchase => Amount Necessary for promotion to execute <Integer>
                # XofferSortValue => String Amount of valueSort of Promotion <String>
                # XofferType => Promotion Category <String> {bogo, cents off, order total, percent off}
                # XredemptionChannels => Promotion Redemption Category <List> {coupon}
                # XredemptionGating => Brand Gating Switch  <String> {NO_GATING}
                # XshortDescription =>  "Save ${valueSort} on any ONE ..."<String>
                # Xterms => Manufacture Legalese <String>
                # Xtype => Coupon Type <String> {mfg, store}
                # Xvalue => cents amount of offer or percentage off for offer <Integer>
                # XvalueSort => Best Value Best Proxy for Coupon (ie. better than value) <Integer>
                # XvalueText => "Save ${valueSort/100}" <String>
                # {{{Xmdid => uuid for promotion <Integer>}}}
                # Xgroup => <String> {'available'}
                # Xgroups => <List> {'available'}
                # Xstatus => <String> {'available'}
                # XenhancedImageUrl => Additional IMG Data for Promotion, Higher Resolution <String>
                # XredemptionsPerTransaction => Amount of Times Coupon Can Be Used in A Transaction <Integer>
                # Xclipped => User Has Clipped Coupon to Account/Wallet <Boolean>
                # XclipStartDateTime => ISO Datetime String w/ Time for promotion clip start <HashMap>
                # XclipEndDateTime => ISO Datetime String w/ Time for promotion clip end <HashMap>
                # XisActive => Coupon Can Still Be Used As of Time of Acquisition <Boolean>
                # XexpirationDateTime => ISO Datetime String w/ Time for promotion redemption end <HashMap>
                # XredemptionStartDateTime  => ISO Datetime String w/ Time for promotion redemption start <HashMap>
                # X?tags => Family Dollar's Product Categories / slugs <List>
                # X?badge => Visual Code for Web Widgets <String> {'', 'new', 'expiring'}
                # X?clippedDates => User Clip Dates for Specific Promotion <List>
                # X?redeemedDates => User Redemption Dates for Promtoion <List>
                # X?contextTypes =>  all empty <List>
                # X?clipRedemptionChannel => all empty <String>

        # dollar general:
            # all available;
                # XDiscountIndicator={0} <Int>,
                # XOfferID => UNIQUE KEY TO CONNECT TO ITEMS api request <HEX STRING>
                # XOfferCode => unique string id to link offer to offer's product page <String>
                # XImage1 => unique string
                # XImage2 => unique string
                # XOfferType => {'BuyXGetYFree', 'AmountOff', 'PercentOff'} <String>
                # XRecemptionFrequency => {'OnceTimeOffer'} <String>
                # XOfferActivationDate => Date When Coupon Can Be Applied <Date String w/ TZ>
                # XOfferExpirationDate => Date When Coupon Ends <Date String w/ TZ> 
                # XOfferDescription => 'Save {amt} on {product}' <String>
                # XBrandname => Brand of Products Which Coupon Applies, <String>
                # XCompanyname => Company That Owns Brand <String>
                # XOfferSummary => Short Representation of Deal, similar to Kroger's Title, "SAVE $1.00", "$1.50 OFF", "Buy 4, Get 1 Free" <String>
                # XIsAutoActivated => {0} <Int>
                # XTargetType => "recommended" <String>
                # XActivationDate => User DT when clippes <Date w/TZ>
                # XRedemptionLimitQuantity => {1} <Integer> 
                # XMinBasketValue => {0} <Integer>
                # XMinTripCount => {0} <Integer>
                # XTimesShopQuantity => {0} <Integer>
                # XMinQuantity => {1, 2, 3, 4, 5} <Integer>
                # XRewaredOfferValue => Specific Amount Saved with Coupon <Float/Int>
                # XRewaredCategoryName => <String> Product Category {'Baby & Toddler', 'Beverages', 'Personal Care & Beauty', 'Baby Care','Household & Paper Products', 'Foods', 'Pet Care', 'Household', 'Dollar General', 'Personal Care', 'Flowers & Gifts', 'Health Care'}
                # XRewardQuantity => Items rewarded by Coupon Redemption <Integer> {0, 1}
                # XIsClipped => Customer specific coupon action <Int> {0, 1}
                # XIsManufactureCoupon => Coupon Originator <Int> {0, 1}
                # X?OfferDisclaimer => Legalese for Coupon <String> 
                # X?OfferFinePrint => all empty <String>
                # X?OfferGS1 => Not all have gs1, OfferCodes Have X in them  <String>
                # X?UPCs => all empty <List>
                # X?OfferFeaturedText => all empty <String>
                # X?Visible => all empty <String>
                # X?AssociationCode => all empty
                # X?MinQuantityDescription => all empty

    # type summarys:
            # strings: krogerCouponNumber, brandName, type, ?cashbackCashoutType, shortDescription, requirementDescription, imageUrl, ?longDescription,
                # value[float as value]    
            # dates: startDate, expirationDate [as UtcTimestamps with timezones]
            # integers: id, requirementQuantity, redemptionsAllowed
            # lists: categories, modalities
            # list of dicts: ?specialSavings
            # booleans: ?isSharable, ?forCampaign,

            # integer: clippecCount, popularity, minPurchase, value, valueSort, mdid, group, status, redemptionsPerTransaction, 
            # string: brand, clipType, description, imageUrl, offerSortValue, offerType, redemptionChannels, redemptionGating, shortDescription, terms, type,
                # valueText, enhancedImageUrl, badge, 
            # dict: category, clipEndDate, clipStartDate, expirationDate, clipStartDateTime, clipEndDateTime, expirationDateTime, redemptionStartDateTime  
            # list: groups, tags, !!clippedDates, !!redeemedDates, !!contextTypes, !!clip Redemption Channels 
            # bool: clipped, isActive

            # integer: DiscountIndicator, IsAutoActivated, RedemptionLimitQuantity, MinBasketValue, MinTripCount, TimesShopQuantity, MinQuantity, RewardQuantity
                # IsClipped, IsManufactureCoupon,   
            # float: RewaredOFfferValue, 
            # string: OfferID, OfferCode, Image1, Image2, OfferType, RecemptionFrequency, OfferActivationDate, OfferExpirationDate, OfferDescription, Brandname,
                # Companyname, OfferSummary, TargetType, !!ActivationDate, RewardedCategoryName, ?OfferDisclaimer, ?OfferGS1, !!OfferFinePrint, !!OfferFeaturedText, !!Visible, !!AssociationCode,
                # !!MinQuantityDescription
            # list: !!UPC

        # items: Description, UPC, Image, IsGenericBrand, IsSellable, IsBopisEligible, Ratings {AverageRating, RatingReviewCount, }, Category(| separated string)
            # shipToHomeQuantity, isShipToHome
        # inventories: AvailableQty, AvailableStockStore, InventoryStatus,
        # prices: Price, OriginalPrice,
        # quasiPriceModifiers: DealsAvailable, DealStatus, SponsoredProductId, SponsoredAgreementId, SponsoredDisplayRow
        # <bool>: CartQuantity
    # REQUIRES : pytz, re, datetime, urllib, json
    # insertData(), insertFilteredData(); 
    mytz = pytz.timezone('America/New_York')
                             
    newProducts=[]
    newCoupons=[]
    newPrices = []
    newInventory = []
    storeCode = ''
    booleans = {'prices': {'IsSellable': 'IN_STORE', 'IsBopisEligible': 'PICKUP', 'isShipToHome': 'SHIP'}, 'items': {'IsGenericBrand', 'IsBopisEligible', 'isShipToHome'}}
    inventoryKeys= {'1': 'TEMPORARILY_OUT_OF_STOCK', '2': "LOW", "3": 'HIGH'}
    productsForCoupons = {}
    descriptionRegex = re.compile(r"^save", re.IGNORECASE)

    if 'dollargeneral' in file:
        # deconstructs into coupons (promotions), items, prices, and inventories 
        with open(file, 'r', encoding='utf-8') as fd:
            data = sorted(json.loads(fd.read()), key=lambda x: x.get('url'))
            products = filter(lambda p: 'eligibleProductsResult' in p.keys(), data)
            coupons = filter(lambda p: 'Coupons' in p.keys(), data)
        for item in products:
            # specific implementation for python's datetime module
            utcTimestamp = item["acquisition_timestamp"] / 1000
            utcTimestamp = dt.datetime.fromtimestamp(utcTimestamp)
            utcTimestamp = mytz.localize(utcTimestamp).astimezone(pytz.utc)
            url = item['url']
            params = urllib.parse.parse_qsl(url)
            if bool(storeCode)==False:
                storeCode = list(filter(lambda x: x[0]=='store', params))[0][1]
            couponId = list(filter(lambda x: x[0].endswith('couponId'), params))[0][1]
            itemList = item.get('eligibleProductsResult').get('Items')
            for i in itemList:
                i = {k:(v.strip() if type(v)==str else v) for k, v in i.items()}
                i['UPC']=str(i['UPC'])
                modalities = []
                for key, val in booleans.get('prices').items():
                    if i[key]:
                        modalities.append(val)
                if couponId not in productsForCoupons.keys():
                    productsForCoupons[couponId] = {i.get('UPC')}
                else:
                    productsForCoupons[couponId].add(i.get('UPC'))

                # deconconstuct to prices
                newPrices.append({'value': i.get('OriginalPrice'),\
                    'type': 'Regular', 'isPurchase': False,\
                         'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                    'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
                if i.get('OriginalPrice')!=i.get('Price'):
                    newPrices.append({'value': i.get('Price'),\
                        'type': 'Sale', 'isPurchase': False,\
                            'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                    'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
                # deconstruct to inventories
                itemStatus = inventoryKeys[str(i.get('InventoryStatus'))]
                newInventory.append({'stockLevel': itemStatus,\
                    'availableToSell': i.get('AvailableStockStore'),\
                        'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                            'upc': i.get('upc')})     
                # deconstuct into Items
                itemDoc = {'description': i.get('Description'),\
                    'upc': i.get('UPC'),\
                        'images': [{'url': i.get('Image'), 'perspective': 'front',\
                            'main': True, 'size': 'xlarge'}],\
                    'soldInStore': i.get('IsSellable'),"modalities": modalities}

                if i.get('RatingReviewCount')!=0:
                    itemDoc['ratings'] = {'avg': i.get('AverageRating'),\
                        'ct': i.get('RatingReviewCount')}
    
                if 'Category' in i:
                    itemDoc['categories'] = i.get('Category').split('|')
                
                for ky in booleans.get('items'):
                    if bool(i[ky]):
                        itemDoc[ky] = i[ky]
                    if ky=='isShipToHome' and bool(i[ky]):
                        itemDoc['maximumOrderQuantity'] = i.get('shipToHomeQuantity')
                
                
                wasProcessed = list(filter(lambda x: x.get('upc')==itemDoc.get('upc'), newProducts))
                if len(wasProcessed)==0:
                    newProducts.append(itemDoc)
        for coupon in coupons:
            utcTimestamp = coupon.pop('acquisition_timestamp')
            for coup in coupon.get('Coupons'):
                newC = {}
                # ids => OfferID=id, OfferCode=offerCode, bool(get OfferGS1)
                newC['id'] = coup.get('OfferID')
                newC['offerCode'] = coup.get('OfferCode')
                if bool(coup.get('OfferGS1')):
                    newC['offerGS1'] = coup.get('OfferGS1')
                # Brandname => brandName, CompanyName => companyName, offerType=> type
                # OfferSummary + OfferDescription => shortDescription
                # OfferDisclaimer => terms
                # RewaredCategoryName => categories[]
                startsWithSave = re.findall(descriptionRegex, coup.get('OfferDescription'))
                if startsWithSave:
                    newC['shortDescription'] = coup.get('OfferDescription')
                else:
                    newC['shortDescription'] = coup.get('OfferSummary') + coup.get('OfferDescription')

                newC['brandName'] = coup.get('BrandName') 
                newC['companyName'] = coup.get('Companyname') 
                newC['offerType'] = coup.get('OfferType')
                if bool(coup.get('OfferDisclaimer')):
                    newC['terms'] = coup.get('OfferDisclaimer') 
                newC['isManufacturerCoupon'] = coup.get('IsManufacturerCoupon') 
                newC['categories'] = [coup.get('RewaredCategoryName')] 
                # OfferActivationDate => startDate  %Y-%m-%dT%H:%M:%S
                # OfferExpirationDate => endDate %Y-%m-%dT%H:%M:%S
                startDate =  dt.datetime.strptime(coup.get('OfferActivationDate'), '%Y-%m-%dT%H:%M:%S')
                newC['startDate'] = mytz.localize(startDate).astimezone(pytz.utc)
                expirationDate =  dt.datetime.strptime(coup.get('OfferExpirationDate'), '%Y-%m-%dT%H:%M:%S')
                newC['expirationDate'] = mytz.localize(expirationDate).astimezone(pytz.utc)
                # RewaredOfferValue => value
                newC['value'] = coup.get('RewaredOfferValue')
                # MinQuantity => requirementQuantity 
                newC['requirementQuantity'] = coup.get('MinQuantity')
                # RedemptionLimitQuantity => redemptionsAllowed
                newC['redemptionsAllowed'] = coup.get('RedemptionLimitQuantity')
                # + MinTripCount, MinBasketValue, TimesShopQuantity, RecemptionFrequency
                newC['redemptionFreq'] = coup.get('RecemptionFrequency')
                # Image1 => imageUrl, +Image2
                newC['imageUrl'] = coup.get('Image1') 
                newC['imageUrl2'] = coup.get('Image2') 
                booleans2 = ['MinTripCount', 'MinBasketValue', 'TimesShopQuantity']
                for b in booleans2:
                    if bool(coup.get(b)):
                        newC[b] = coup.get(b)
                
                joinID = coup.get('OfferID')
                if joinID in productsForCoupons.keys():
                    newC['productUpcs'] = list(productsForCoupons.get(joinID))
                newCoupons.append(newC)
    # !!! Family Dollar -> currently deconstructs into promotions collections (promotions are separated from their assoicated items, though items are still catalogued)
    elif 'familydollar' in file:
        with open(file, 'r', encoding='utf-8') as fd:
            data = json.loads(fd.read())
            if type(data[0])==dict:
                coupons = data[0].get('data')
            else:
                coupons = data[0]
        for coup in coupons:
            newC = {}
            # mid => id
            newC['id'] = coup.get('mdid')
            # brand => brandName
            newC['brandName'] = coup.get('brand')
            # offerType => type
            newC['type'] = coup.get('offerType')
            # description => shortDescription
            newC['shortDescription'] = coup.get('description')
            # terms => terms
            newC['terms'] = coup.get('terms')
            # category.get('name') => categories
            newC['categories'] = [coup.get('category').get('name')]
            # [x.replace('fd-', '').strip().title() for x in tags] +=> categories
            newC['categories'].extend([x.replace('fd-', '').strip().title() for x in coup.get("tags")])
            # redemptionStartDateTime => startDate %Y-%m-%dT%H:%M:%S
            # redemptionEndDateTime => expirationDate %Y-%m-%dT%H:%M:%S
            startDate =  dt.datetime.strptime(coup.get('redemptionStartDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ')
            newC['startDate'] = mytz.localize(startDate).astimezone(pytz.utc)
            expirationDate =  dt.datetime.strptime(coup.get('expirationDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ')
            newC['expirationDate'] = mytz.localize(expirationDate).astimezone(pytz.utc)
            # clipStartDateTime %Y-%m-%dT%H:%M:%S
            # clipEndDateTime
            clipStartDate = dt.datetime.strptime(coup.get('clipStartDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ')
            newC['clipStartDate'] = mytz.localize(clipStartDate).astimezone(pytz.utc)
            clipEndDate = dt.datetime.strptime(coup.get('clipEndDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ')
            newC['clipEndDate'] = mytz.localize(clipEndDate).astimezone(pytz.utc)
            # offerSortValue => value
            newC['value'] = int(coup.get('offerSortValue'))
            # minPurchase => requirementQuantity
            newC['requirementQuantity'] = int(coup.get('minPurchase'))
            # redemptionsPerTransaction => redemptionsAllowed
            newC['redemptionsAllowed'] = coup.get('redemptionsPerTransaction')
            # imageUrl => imageUrl, + enchancedImageUrl
            newC['imageUrl'] = coup.get('imageUrl')
            newC['enhancedImageUrl'] = coup.get('enhancedImageUrl')
            if coup.get('type')=='mfg':
                newC['isManufacturerCoupon'] = True
            else:
                newC['isManufacturerCoupon'] = False
        
            # type => isManufacturerCoupon if type=mfg else False
            # +socials :: popularity, clippedCount
            newC['popularity'] = coup.get('popularity')
            newC['clippedCount'] = coup.get('clippedCount')

            newCoupons.append(newC)

    # newPrices, newCoupons, newInventory, newProducts
    if newPrices:
        insertData(newPrices, "prices")
    if newInventory:
        insertData(newInventory, "inventories")
    
    if newCoupons:
        insertFilteredData(newCoupons, "promotions", "new", "id")
    if newProducts:
        insertFilteredData(newProducts, "items", "new", "upc")

    print(f"Finished with {file}") 

    return None

def backupDatabase():
    # more raw to archive and compress,
    # dump database and compress
    # clean up files 
    # move and compressed extension files to separate archive 
    subprocess.Popen(['7z', "a", "../data/archive.7z", "../data/collections", f"-p{EXTENSION_ARCHIVE_KEY}", "-mhe", "-sdel"])
    # helper to dump bsons and zip files for archive
    if os.path.exists("../data/archive/"):
        os.remove('../data/archive/')
    process1 = subprocess.Popen(['mongodump', "-d", "new", "-o", "../data/data"])
    process1.wait(90)
    # 7zip archive mongodumps w/ password
    process2 = subprocess.Popen(['7z', "a", "../data/data.7z", "../data/data", f"-p{DB_ARCHIVE_KEY}", "-mhe", "-sdel"])
    process2.wait(30)
    if os.path.exists("../data/data"):
        shutil.rmtree('../data/data')
    return None


def deconstructExtensions(filename):
    # Deconstruct Extension Created Kroger Files into Final Collections
    # CATEGORY = Wash Data (file=> append to madeCollections to make fullCollections). Handles Kroger's promotions and trips
    # breaks down promotion jsons generated by the extension into the promotions, items and prices collections
    # 1.) Trips -> Prices, Items, Trips, Promotions
    # 2.) Coupons (digital/cashback) -> Promotions, Items, Prices
    # Add item UPCs that correspond to their appropiate promotion
    # Aggregate couponDetails separate calls into promotions collections
    # Break down item api calls into both price and item collections
    # REQ: datetime, re, pytz, 

    # Decomposing Product Calls into Separate Collections that Cover the Static and nonStatic properties of individual products:
            # (n.b.) calls to api w/ full projection filters gives several valuable properties regarding products:
            # in all calls thr response includes:
                #! item, ship, id, sourceLocations, itemsV1, laf
                    # constant item specific properties::
                        # item includes static information based on the individual product, interal groupings, size, labels and web elements for display on website
                        # itemv1 includes new classifications, ids and nutritional scores to apply additional information to product pages
                        # id is upc present in item object
                    # store/fulfillment properties based on the call to the api route (those close to me)
                    # constant store/fulfillment properties:
                        # the two most important nonstatic properties involved in this project are: price and inventory.
                        # due to different online shopping types (pickup, delivery, shipping, in-store) calls on a product in a specific area returns the prices/inventory
                        # of this product in the associated fulfillment networks.
                            # shipping hubs do not connect directly with stores and provide far less items currently. hence, why a ship attribute returns with each response
                            # pickup connects more hubs to a specific pickup store and provides with the most availability with items.
                            # inStore refers to a specific, selected store
                            # delivery is an extension of pickup+instore
                        # prices and inventory are constantly changing flows that provide important information on the value of deals/items/shopping at a specific moment of time.
                        # breaking apart these flows from static properties of individual objects will help see how promotions and prices change through time with the introduction of promotions
                        # inventory+price are location-specific
                        # the location variables generate many summary/aggregation properties in the api response that summarize properties of an item on the network
                        # moreover, there seems to be a lot of repeat information about the network given in each location object that summarizes more fleshed out location in laf, sourceLocations
                        # so they need to be cleaned up to purge repeat data. 
                        # calls to the product api will be decomposed into:
                            # Dynamic Properties:
                                # Price {prices collection}
                                # Inventory {inventories collection}
                            # General Static Properties:
                                # Product dimensions/size/nutrition {items collection}
                            # Location Static Properties:
                                # Item Location {items collection + stores collection}
                                # Network of fulfillment Centers {stores collection}
                                # General Store Information  {stores collection}          
    mytz=pytz.timezone('America/New_York')
    startingArray=[]
    upcsRegex = re.compile(r'https://www\.kroger\.com/cl/api/couponDetails/(\d+)/upcs')
    couponsDetailsRegex = re.compile(r'https://www\.kroger\.com/cl/api/coupons.+')
    productsRegex = re.compile(r'https://www\.kroger\.com/atlas/v1/product/v2/products\?.+')
    tripRegex = re.compile(r'https://www\.kroger\.com/mypurchases/api/v1/receipt.+')
    storeRegex = re.compile(r'https://www\.(.+)\.com.+')
    specialPromoRegex = re.compile(r'https://www\.kroger\.com/products/api/products/details-basic',)
    productErrorsRegex = re.compile(r'\.gtin13s=(\d+)')
    storeDict = filename.split('/')[-2]
    print(filename)
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            startingArray = json.loads(file.read())

        cDict={}
        try:
            if 'trips' in filename:
                startingArray = list(filter(lambda x: type(x)==dict and "data" in x, startingArray))
                startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=True)
            else:
                startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=False)
        except TypeError as err:
            print(err)
        except KeyError:
            print(list(map(lambda x: x.keys(), startingArray)))
        # static collections
        promotionsCollection = []
        itemCollection = []
        # # dynamic flows @ specific moment in time
        pricesCollection = []
        inventoryCollection = []
        # # dependent tables @ specific moment in time
        tripCollection = retrieveData("trips")
        priceModifierCollection = []
        # # identifying the users specific relation to and contact with these flows/objects to present data solutions based on past interactions with all these elements
        userCollection = []
        sellerCollection = []
        # # intermediaries
        forGeneralItems={}
        connectionErrors = []
        for apiCall in startingArray:
            url = apiCall.pop('url')
            acquistionTimestamp = mytz.localize(dt.datetime.fromtimestamp(apiCall.pop('acquisition_timestamp')/1000))
            data = apiCall.get('data')
            # match promotions to product upcs
            if re.match(upcsRegex, url):
                couponId = re.match(upcsRegex, url).group(1)
                cDict[couponId] = data
            # handle special case promotions
            elif re.match(specialPromoRegex, url):
                allUpcs = set()
                allOffers = set()
                qualifiers = apiCall.get('products')
                for q in qualifiers:
                    allUpcs.add(q.get('upc'))
                    for offer in q.get('offers'):
                        allOffers.add(str(offer).replace("'", "\""))

                if not allOffers:
                    reqAmt, savings = re.findall(re.compile(r"[^\d]+(\d+)[^\d]+(\d+)"), filename)[0]
                    reqAmt = int(reqAmt)
                    savings = int(savings)
                    upcsQual = list(filter(lambda x: 'products' in x, startingArray))
                    upcsQual = [u['upc'] for sublist in upcsQual for u in sublist['products']]
                    hasNewPromotion = list(filter(lambda x: x.get('id')==f"buy{reqAmt}save{savings}", promotionsCollection))
                    if not hasNewPromotion:
                        promotionsCollection.append({
                            "value": savings,
                            "type": "Amount off",
                            "requirementQuantity": reqAmt,
                            "shortDescription": f"Buy {reqAmt} or More, Save ${savings} Total",
                            "redemptionsAllowed": -1,
                            "productUpcs": upcsQual,
                            "id": f"buy{reqAmt}save{savings}",
                            "krogerCouponNumber": f"buy{reqAmt}save{savings}"
                        })  
                else: 
                    allOffers = json.loads(list(allOffers)[0])
                    # filterBoolean calculated
                    hasNewPromotion = list(filter(lambda x: x.get('krogerCouponNumber')==allOffers.get('couponNumber'), promotionsCollection))
                    
                
                if len(hasNewPromotion)==0 and type(allOffers)==dict:
                    newPromotion = {}
                    # couponAmount => value
                    newPromotion['value'] = allOffers.get('couponAmount')
                    # couponNumber => krogerCouponNumber # offerId => krogerCouponNumber
                    newPromotion['krogerCouponNumber'] = allOffers.get('couponNumber')
                    # effectiveDate => startDate + T00:00:00Z
                    startDate = allOffers.get('effectiveDate') + "T00:00:00"
                    startDate = mytz.localize(dt.datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    newPromotion['startDate'] = startDate
                    # expirationDate => expirationDate + T11:59:59Z
                    expirationDate = allOffers.get('expirationDate') + "T11:59:59"
                    expirationDate = mytz.localize(dt.datetime.strptime(expirationDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    newPromotion['expirationDate'] = expirationDate
                    # rewardTypeDescription => "Amount off"
                    newPromotion['type'] = allOffers.get('rewardTypeDescription')
                    # totalPurchaseQty => requirementQuantity
                    newPromotion['requirementQuantity'] = allOffers.get('totalPurchaseQty')
                    # webDescription => shortDescription
                    newPromotion['shortDescription'] = allOffers.get('webDescription')
                    # upcs => productUpcs[]
                    newPromotion['productUpcs'] = list(allUpcs)
                    newPromotion['redemptionsAllowed'] = -1
                    # special promotions "inserted" into massive array
                    promotionsCollection.append(newPromotion)
                elif len(hasNewPromotion)>0:
                    hasNewPromotion[0]['productUpcs'].extend(list(allUpcs))
            
            # handle regular coupons
            elif re.match(couponsDetailsRegex, url):
                if "couponData" in data:
                    data = data.get("couponData")
                coupons = data.get('coupons') 
                coupSchema = {'keep':{"id", "krogerCouponNumber", "brandName", "categories", "productUpcs", "type", "expirationDate",\
                     "redemptionsAllowed", "value", "requirementQuantity", "displayStartDate", "imageUrl", "shortDescription", "requirementDescription",
                     "modalities"},\
                     "bool": {"cashbackCashoutType", "isSharable", "forCampaign", "specialSavings",  "longDescription"}}
                for k,v in coupons.items():
                    promo = {}
                    if k in cDict:
                        v.update({'productUpcs': cDict[k]})
                    else:
                        v.update({'productUpcs': []})

                    for coupKey, coupVal in v.items():
                        if coupKey in coupSchema['bool']:
                            if bool(coupVal):
                                if coupKey=='longDescription':
                                    promo['terms'] = coupVal
                                else:
                                    promo[coupKey] = coupVal
                        elif coupKey in coupSchema['keep']:
                            if coupKey=='displayStartDate':
                                promo['startDate'] = pytz.utc.localize(dt.datetime.strptime(coupVal, "%Y-%m-%dT%H:%M:%SZ"))
                            elif coupKey=='expirationDate':
                                promo['expirationDate'] = pytz.utc.localize(dt.datetime.strptime(coupVal, "%Y-%m-%dT%H:%M:%SZ"))
                            elif coupKey=='shortDescription':
                                promo[coupKey] = coupVal.strip()
                            else:
                                promo[coupKey] = coupVal
                    # filterBoolean is Calculated
                    isProcessed = bool(list(filter(lambda x: x.get('krogerCouponNumber')==promo.get('krogerCouponNumber'), promotionsCollection)))
                    if isProcessed==False:
                        # promotions is appended to massiveArray
                        promotionsCollection.append(promo)
            elif re.match(tripRegex, url): # receipt?
                # trips => {attributes to add to overall item collection, prices, users, priceModifiers}
                # items:
                data = updateGasoline(data=data)
                removalTrip = ['address', 'returns', 'barcode', 'purchaseHistoryID', 'priceModifiers', 'coupon', 'source', 'version', 'transactionTime']
                removalAggregations = ['tipAmounts', 'totalSavings', 'tenderChanges', 'total', 'subtotal', 'totalTax', 'grossAmount', 'totalTender', 'totalLineItems', 'totalTenderChange']
                tripKeep = {'loyaltyId', 'assocaiteId', 'transactionTimeWithTimezone', 'fulfillmentType', 'tax', 'total', 'totalSavings', 'subtotal',\
                'tenders', 'items', 'receiptId'}
                # isContainerDeposit, isManagerOverride, isManagerOverrideIgnore
                itemKeep = {'isFuel', 'isGiftCard', 'isPharmacy', 'isWeighted', 'barCodes', 'monetizationId'}
                for trip in data:
                    # setup trip
                    tripDocument = {}
                    transactionId = trip.get('receiptId').get('transactionId')
                    # filterBoolean is calculated
                    isProcessed = bool(list(filter(lambda x: x.get('transactionId')==transactionId, tripCollection)))
                    if isProcessed==False and trip.get("transactionTimeWithTimezone"):
                        purchaseTimestamp = pytz.utc.localize(dt.datetime.strptime(trip.get("transactionTimeWithTimezone"), "%Y-%m-%dT%H:%M:%SZ"))
                        for key, value in trip.items():
                            if key in tripKeep:
                                if key=='tenders':
                                    tripDocument['tenderType'] = value[0].get('tenderType')
                                elif key=='receiptId':
                                    tripDocument['locationId'] = value.get('divisionNumber') + value.get('storeNumber')
                                    tripDocument['terminalNumber'] = value.get('terminalNumber')
                                    tripDocument['transactionId'] = transactionId
                                    if len(userCollection)==0:
                                        # user collection derived from trip
                                        userCollection.append({'userId': value.get('userId'), 'loyaltyId': trip.get('loyaltyId'), 'trips': [value.get('transactionId')]})
                                    else:
                                        try:
                                            user = list(filter(lambda u: u.get('loyaltyId')==trip.get('loyaltyId'), userCollection))[0]
                                        except IndexError:
                                            user = userCollection[0]
                                        if transactionId not in user.get('trips'):
                                            user['trips'].append(transactionId)
                                elif key=='items':
                                    # offshoots to new collections
                                    # needs to reference back to items (by baseUpc), trip (via trip Id), priceModifiers (pointers to priceModifier) and time (via acquistion timestamp)
                                    # priceModifierCollection set via trips
                                    currentPMs = set(map(lambda x: x.get('promotionId'), priceModifierCollection))
                                    for item in value:
                                        if item.get('itemType')!='STORE_COUPON':
                                            # setup priceModifiers collection
                                            if item.get('priceModifiers'):
                                                for pm in item.get('priceModifiers'):
                                                    if pm.get('promotionId') not in currentPMs and bool(pm.get('amount')):
                                                        pm.pop('action')
                                                        pm['redemptions'] = 1
                                                        pm.setdefault('redemptionKeys', [])
                                                        pm['redemptionKeys'].append({'upc': item.get('baseUpc'), 'transactionId': transactionId, 'amount': pm.get('amount'), 'redeemed': 1})
                                                        pm['total'] = pm.get('amount')
                                                        # priceModifiers insert
                                                        priceModifierCollection.append(pm)
                                                    elif pm.get('promotionId') in currentPMs and bool(pm.get('amount')):
                                                        existingPm = list(filter(lambda x: x.get('promotionId')==pm.get('promotionId'), priceModifierCollection))[0]
                                                        existingPm['total'] += pm.get('amount')
                                                        existingPm['redemptions'] += 1
                                                        matchingObjs = list(filter(lambda x: x.get('upc')==item.get('baseUpc'), existingPm.get('redemptionKeys')))
                                                        if bool(matchingObjs):
                                                            matchingObjs = matchingObjs[0]
                                                            if matchingObjs.get('transactionId')==transactionId:
                                                                matchingObjs['amount'] += pm.get('amount')
                                                                matchingObjs['redeemed'] += 1
                                                            else:
                                                                existingPm['redemptionKeys'].append({'upc': item.get('baseUpc'), 'transactionId': transactionId, 'amount': pm.get('amount'), 'redeemed': 1})
                                                        else:
                                                            existingPm['redemptionKeys'].append({'upc': item.get('baseUpc'), 'transactionId': transactionId, 'amount': pm.get('amount'), 'redeemed': 1})

                                            # setup prices collection
                                            if item.get('extendedPrice')==item.get('pricePaid'):
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                # pricesCollection appended to
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})
                                            else:
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                # pricesCollection appended to
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})
                                                value = round(item.get('pricePaid') / item.get('quantity'), 2)
                                                # pricesCollection appended to
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Sale', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber'),
                                                'offerIds': ','.join(list(map(lambda pm: pm.get('promotionId'), item.get('priceModifiers'))))})

                                            if item.get('isWeighted'):
                                                averageWgt = item.get('detail').get('averageWeight') or 1
                                                # pricesCollection appended to
                                                pricesCollection.append({'value': item.get('unitPrice'), 'quantity': averageWgt, 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': False, 'transactionId': transactionId,
                                                'type': 'Average', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})

                                            for booleanCategory in itemKeep:
                                                if bool(item.get(booleanCategory)):
                                                    forGeneralItems.setdefault(item.get('baseUpc'), {})
                                                    if type(item.get(booleanCategory))==bool:
                                                        forGeneralItems[item.get('baseUpc')] = {booleanCategory: item.get(booleanCategory)}
                                                    elif type(item.get(booleanCategory))==str: # internal site promotions
                                                        forGeneralItems[item.get('baseUpc')].setdefault(booleanCategory, [])
                                                        forGeneralItems[item.get('baseUpc')][booleanCategory].append({'id': item[booleanCategory], 'acquisition_timestamp': acquistionTimestamp})
                                                    else:
                                                        forGeneralItems[item.get('baseUpc')].setdefault('barCodes', [])
                                                        forGeneralItems[item.get('baseUpc')]['barCodes'].extend(item.get('barCodes'))
                                elif key == 'transactionTimeWithTimezone':
                                    tripDocument['utcTimestamp'] = pytz.utc.localize(dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
                                else:
                                    tripDocument[key] = value
                        # new trips is appended 
                        tripCollection.append(tripDocument)
                # dealing with the items aggregation
            elif re.match(productsRegex, url): # products?
                # products => {the final item collection, adds to prices collection, creates and adds to inventory collection, creates promotions}
                itemKeep = {"bool": {"alcoholFlag", "bounceFlag", "hazmatFlag", "heatSensitive", "prop65",\
                    "shipsWithColdPack"},
                    "keep": {"prop65Warning", "images", "romanceDescription", "categories", "dimensions",\
                        "familyTree", "taxonomies", "brand", "taxGroupCode","familyCode", "taxGroupCode", "snapEligible", "shipToHomeItem", "soldInStore", "homeDeliveryItem", \
                            "temperatureIndicator", "minimumOrderQuantity", "maximumOrderQuantity", "countriesOfOrigin", "customerFacingSize",\
                                "description", 'nutrition', "familyTreeV1", "idV1", "tareValue", "upc", "weight", "weightPerUnit", 'orderBy', 'sellBy'}}


                if data==None:
                    connectionErrors.extend([x for x in re.findall(productErrorsRegex, url)])
                else:
                    for p in data.get('products'):
                        # create item collection
                        itemDoc = p.get('item')
                        # add additional item factors

                        if 'nutrition' in p:
                            nutritionalDict =p.get('nutrition')
                            newNutrition = {}
                            for k,v in nutritionalDict.items():
                                if bool(v):
                                    newNutrition[k] = v
                                if k=="components":
                                    compList = []
                                    for component in v:
                                        newComp = {}
                                        for ck, cv in component.items():
                                            if bool(cv) and type(cv)!=list:
                                                newComp[ck] = cv
                                            elif bool(cv) and len(cv)==1:
                                                newComp[ck] = cv
                                            elif bool(cv):
                                                newComp[ck] = []
                                                for prepState in cv:
                                                    if prepState not in newComp[ck]:
                                                        newComp[ck].append(prepState)
                                        compList.append(newComp)
                                    newNutrition[k] = compList
             
                            itemDoc['nutrition'] = newNutrition
                        
                        if 'itemsV1' in p:
                            itemsV1 = p.pop('itemsV1')
                            itemDoc['familyTreeV1'] = itemsV1.get('product').get('familyTree')
                            itemDoc['idV1'] = itemsV1.get('product').get('id')
                            if 'nutritionalRating' in itemsV1:
                                itemDoc['nutrition']['nutritionalRating'] = itemsV1.get('nutritionalRatings') 

                        if bool(p.get('productRestrictions')):
                            itemDoc['productRestrictions']  = p.get('productRestrictions')
                        
                        sources = p.get('sourceLocations')
                        for source in sources:
                            priceData={}
                            if 'prices' in source:

                                prices = source.get('prices')[0]

                                sellers = list(filter(lambda x: x.get('sellerId')==prices.get('sellerId'), sellerCollection))

                                
                                if bool(prices.get('sale')):
                                    promo = float(prices.get('sale').get('nFor').get('price').replace('USD', ''))
                                    quantity = float(prices.get('sale').get('nFor').get('count'))
                                    priceData['value'] = round(promo / quantity, 2)
                                    priceData['quantity'] = quantity
                                    priceData['type'] = prices.get('displayTemplate')
                                    if 'linkedOfferCode' in prices.get('sale'):
                                        priceData['offerIds'] = prices.get('sale').get('linkedOfferCode')
                                    
    
                                if bool(prices.get('regular')):
                                    priceData['value'] = float(prices.get('regular').get('nFor').get('price').replace('USD', '')) / prices.get('regular').get('nFor').get('count')
                                    priceData['quantity'] = prices.get('regular').get('nFor').get('count')
                                    priceData['type'] =  prices.get('displayTemplate')
                                    if '.' in prices.get('effectiveDate').get('value'):
                                        priceData['effectiveDate'] = pytz.utc.localize(dt.datetime.strptime(prices.get('effectiveDate').get('value'), "%Y-%m-%dT%H:%M:%S.%fZ"))
                                    else:
                                        priceData['effectiveDate'] = pytz.utc.localize(dt.datetime.strptime(prices.get('effectiveDate').get('value'), "%Y-%m-%dT%H:%M:%SZ"))
                                    if '.' in prices.get('expirationDate').get('value'):
                                        priceData['expirationDate'] =  pytz.utc.localize(dt.datetime.strptime(prices.get('expirationDate').get('value'), "%Y-%m-%dT%H:%M:%S.%fZ"))
                                    else:
                                        priceData['expirationDate'] =  pytz.utc.localize(dt.datetime.strptime(prices.get('expirationDate').get('value'), "%Y-%m-%dT%H:%M:%SZ"))
                                    itemDoc['sellBy'] = prices.get('sellBy')
                                    itemDoc['orderBy'] = prices.get('orderBy')
                                    
                                    if len(sellers)==0:
                                        id = len(sellerCollection)
                                        # seller collection appended 
                                        sellerCollection.append({'sellerId': prices.get('sellerId'), 'sellerName': prices.get('sellerName'), "id": id})
                                        priceData['sellerKey'] = id 
                                    else:
                                        id = sellerCollection.index(sellers[0])
                                        priceData['sellerKey'] = id 
                                        

                                if 'modalityAvailabilities' in source:
                                    priceData.setdefault('modalities', [])
                                    for modal in source.get('modalityAvailabilities'):
                                        if modal.get('availability'):
                                            priceData['modalities'].append(modal.get('modalityType'))

                                priceData['upc']=itemDoc.get('upc')
                                priceData['locationId'] = source.get('id')
                                priceData['utcTimestamp']=acquistionTimestamp
                                priceData["isPurchase"] = False
                                # priceCollection appended 
                                pricesCollection.append(priceData)

                            if 'inventory' in source:
                                inventory = source.get('inventory')
                                # Inventory docs repeat in same source
                                i = inventory[0]
                                i['locationId'] = source.get('id')
                                i['utcTimestamp'] = acquistionTimestamp
                                i['upc'] = itemDoc.get('upc')
                                sellers = list(filter(lambda x: x.get('sellerId')==i.get('sellerId'), sellerCollection))
                                if len(sellers)==0:
                                    id = len(sellerCollection)
                                    sellerCollection.append({'sellerId': i.get('sellerId'), 'sellerName': i.get('sellerName'), "id": id})
                                    i['sellerKey'] = id 
                                else:
                                    id = sellerCollection.index(sellers[0])
                                    i['sellerKey'] = id 
                                i.pop('sellerId')
                                i.pop('sellerName')
                                if 'offerId' in i:
                                    i.pop('offerId')
                                # inventoryCollection Appended 
                                inventoryCollection.append(i)
                                
                        toPop = []
                        for key, value in itemDoc.items():
                            if key in itemKeep['bool']:
                                if key=='prop65':
                                    value = value.get('required')
                                if bool(value)==False:
                                    toPop.append(key)
                            elif key in itemKeep['keep']:
                                if key=='mainImagePerspective':
                                    imgs = list(filter(lambda x: x.get('perspective')==value, itemDoc.get('images')))
                                    imgs = sorted(imgs, key=lambda i: i.get('size'))
                                    imgs[0].setdefault('main', True)
                        
                        itemDoc = {k:v for k,v in itemDoc.items() if (k not in toPop and k in itemKeep['bool']) or  (k in itemKeep['keep'])}
                        if itemDoc.get('upc') in forGeneralItems.keys():
                            moreInfo = forGeneralItems[itemDoc.get('upc')]
                            itemDoc.update(moreInfo)
     

                        isProcessed = bool(list(filter(lambda x: x.get('upc')==itemDoc.get('upc'), itemCollection)))
                        if isProcessed==False:
                            itemCollection.append(itemDoc)
    # entries, collection_name, dbName, uuid
    if promotionsCollection:
        insertFilteredData(promotionsCollection, "promotions", "new", "krogerCouponNumber")
    if itemCollection:
        insertFilteredData(itemCollection, "items", "new", "upc")
    if tripCollection:
        insertFilteredData(tripCollection, "trips", "new", "transactionId")  
    if priceModifierCollection:
        insertFilteredData(priceModifierCollection, "priceModifiers", "new", "promotionId")
    if userCollection:
        insertFilteredData(userCollection, "users", "new", "loyaltyId") 
    if sellerCollection:
        insertFilteredData(sellerCollection, "sellers", "new", "sellerId")

    if pricesCollection:
        insertData(pricesCollection, "prices", "new")
    if inventoryCollection:
        insertData(inventoryCollection, "inventories", "new")
    
    print("decomposed {}".format(filename))
    return None
        

def normalizeStoreData():
    # create normalized stores and insert them into collection
    # REQ : datetime, os, 
    storeDirectories = ['/aldi/stores/', '/dollargeneral/stores/', '/familydollar/stores/', '/fooddepot/stores/', '/publix/stores/'] 
    head= './requests/server/collections/'
    newStores = []
    storeFiles = []
    instacartFiles = []
    for folder, subfolders, files in os.walk(head):
        for file in files:
            if 'stores' in folder:
                if 'IC' not in file:
                    storeFiles.append(folder.replace('\\', '/')+'/'+file)
                else:
                    instacartFiles.append(folder.replace('\\', '/')+'/'+file)

    # --- Kroger's ---
    # address { 
    #   {addressLine1, city, county, state, zipCode} <String>
    #  }
    # chain : <String> UPPER,
    # departments: [{'departmentId': <String>, 'name': <String> +
    #   ?hours: {weekday: {close, open, open24}, open24, name, ?phone} <String> + <Bool::open24>
    # }]
    # geolocation: {latLng: <String>, latitude: <Float>, longitude: <Float>}
    # hours: {gmtOffset: <String>, open24: <Bool>, timezone:<String>, <:weekdays:>: {open24, open, close}}
    # locationId: <String> <- Connector to Items, Inventory, et all.
    # name: <String> - chain + real estate name
    # phone: <String> 


    # --- Aldi ---
    ## response.entities <- list of objects 
        # alt ids: distance.id 
        # main ids : .profile = x
            # address = {addressLine1: x.address.line1, zipCode: x.address.postalCode, city: x.address.city, county: n/a, state: x.address.region, }
                # c_facebookDescriptor = additional address
            # chain, name = "ALDI", chain.title() = x.name
            # geolocation = {latitude: x.geocodedCoordinates.lat, longitude: x.geoCodedCoordinates.long}
            # hours: {sunday...monday} = x.hours.map(lambda y: y.day.lower(): {open: y.intervals[0].start, close: y.intervals.end, open24: false})
            # locationId <- derived with geolocation
            # name : chain.title() = x.name
            # additionalIds: {path: , id: } = {'c_internalALDIID', facebookStoreId, c_corpId, c_dIV, c_corpIdExpandedName}

            # add to stores = > pickupAndDeliveryServices, paymentOptions, mainPhone.display, 



    with open(storeFiles[0], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        maxRadius = 0
        data = list(filter(lambda x: 'r=' in x['url'], data))
        for d in data:
            urlVars = urllib.parse.parse_qsl(d.get('url'))
            radius = filter(lambda x: x[0]=='r', urlVars)
            radius = float(list(radius)[0][1])
            if radius>maxRadius:
                maxRadius = radius
        maxRadius = math.floor(maxRadius)
        data = list(filter(lambda x: f'r={maxRadius}' in x['url'] , data))
        data = [item.get('profile') for sublist in data for item in sublist.get('response').get('entities') if 'closed' not in item.get('profile')]
         ## response.entities <- list of objects 
        # alt ids: distance.id 
        # main ids : .profile = x
            # XX address = {addressLine1: x.address.line1, zipCode: x.address.postalCode, city: x.address.city, county: n/a, state: x.address.region, }
                # c_facebookDescriptor = additional address

            # XX chain, name = "ALDI", chain.title() = x.name
            # XX geolocation = {latitude: x.geocodedCoordinates.lat, longitude: x.geoCodedCoordinates.long}
            # XX hours: {sunday...monday} = x.hours.map(lambda y: y.day.lower(): {open: y.intervals[0].start, close: y.intervals.end, open24: false})
            # locationId <- derived with geolocation
            # XX name : chain.title() = x.name
            # additionalIds: {path: , id: } = {}

            # add to stores = > pickupAndDeliveryServices, paymentOptions, mainPhone.display, 

        # all stores
        # address {addressLine1, city, county, state, zipCode}, departments [{id, name, hours{close, open, open24}, open24}]
        # geolocation {latLng, latitude, longitude},
        # hours {timezone, gmtOffset, open24, <weekdays:{close, open, open24}>}, locationId, name, phone

        additionalIds = {'c_internalALDIID', 'facebookStoreId', 'c_corpId', 'c_dIV', 'c_corpIdExpandedName'}
        for storeData in data:
            oldAddress = storeData.pop('address')
            newDoc = {}
            newDoc['address'] = {
                "addressLine1": oldAddress.get('line1'),
                "zipCode": oldAddress.get('postalCode'),
                "city": oldAddress.get('city'),
                "state": oldAddress.get('region')
            }
            newDoc['chain'] = storeData.get('name')
            newDoc['name'] = newDoc.get('chain').title()
            # newDoc['locationId'] = d.get('id') <- to be set by join down below
            newDoc['altAddress'] = storeData['facebookDescriptor']
            newDoc['geolocation'] = {}
            newDoc['geolocation']['latitude'] = storeData.get('geocodedCoordinate').get('lat')
            newDoc['geolocation']['longitude'] = storeData.get('geocodedCoordinate').get('long')
            # parse hours in to hours 
            oldHours = storeData.pop('hours')
            oldHours = oldHours['normalHours']
            newDoc.setdefault('hours', {})
            for hour in oldHours:
                day = hour['day'].lower()
                newDoc['hours'][day] = {'open':  hour['intervals'][0]['start'],'close': hour['intervals'][0]['end']}
                newDoc['hours'][day]['open24'] = newDoc['hours'][day]['open']==newDoc['hours'][day]['close']


            if storeData.get('mainPhone').get('display'):
                newDoc['phone'] = storeData['mainPhone']['display']

            newDoc['modalities'] = storeData['pickupAndDeliveryServices']
            newDoc['payments'] = storeData['paymentOptions']

            for addId in additionalIds:
                if addId in storeData:
                    newDoc.setdefault('additionalIds', [])
                    newDoc['additionalIds'].append({f"{addId}": storeData[addId]})

            if 'Curbside Pickup' in newDoc.get('modalities'):
                newStores.append(newDoc) 
    # ---DollarGeneral---
        # ad=address, cc<Int>, ct=city, di='U', dm=<datetime>, ef<Int>, hf<hours friday>, hh<hours thursday>, hm<hours monday>,
        # hs<hours sat>, ht, hu, hw, la=latitude, lo=longitude, pn='4708932140', se=1, sg=0, si=2, sn=id<13141>, ss=123054, 
        # st=state, um=3793, uu='hex-code', zp=zipCode full 
    

    with open(storeFiles[1], 'r', encoding='utf-8') as file:
        data=json.loads(file.read())
        storeLimited = list(map(lambda x: x.get('data').get('storeDetails'), data))
        storeFull = list(map(lambda x: x.get('data').get('stores'), data))
        storeFull = list(filter(None, storeFull))[0]
        storeLimited = filter(None, storeLimited)
        
        for d in storeLimited:
            newDoc={}
            newDoc['address'] = {'addressLine1': d.get('ad'), 'city': d.get('ct'), 'state': d.get('st'), 'zipCode': d.get('zp')}
            newDoc['locationId'] = d.get('sn')
            newDoc['geolocation'] = {'latitude': d.get('la'), 'longitude': d.get('lo')}
            newDoc['chain'] = 'Dollar General'
            newDoc['name'] = 'Dollar General'

            newDoc['hours'] = {
                'monday' : {'open':d.get('hm').split(':')[0], 'close':d.get('hm').split(':')[-1], 'open24': False},
                'tuesday' : {'open':d.get('ht').split(':')[0], 'close':d.get('ht').split(':')[-1], 'open24': False},
                'wednesday': {'open':d.get('hw').split(':')[0], 'close':d.get('hw').split(':')[-1], 'open24': False},
                'thursday':{'open':d.get('hh').split(':')[0], 'close':d.get('hh').split(':')[-1], 'open24': False},
                'friday':{'open':d.get('hf').split(':')[0], 'close':d.get('hf').split(':')[-1], 'open24': False},
                'saturday':{'open':d.get('hs').split(':')[0], 'close':d.get('hs').split(':')[-1], 'open24': False},
                'sunday':{'open':d.get('hu').split(':')[0], 'close':d.get('hu').split(':')[-1], 'open24': False}
            }
            newStores.append(newDoc)

        for d in storeFull:
            # address {addressLine1, city, county, state, zipCode}, departments [{id, name, hours{close, open, open24}, open24}]
            # geolocation {latLng, latitude, longitude},
            # hours {timezone, gmtOffset, open24, <weekdays:{close, open, open24}>}, locationId, name, phone
            if d.get('storenumber') in set(map(lambda x: x.get('id'), newStores)):
                newDoc = list(filter(lambda x: x.get('id')==d.get('storeNumber'), newStores))[0]
                newDoc['phone'] = d.get('phoneNumber')
                newDoc['clickandcollect'] = d.get('clickandcollect')
                newDoc['scanandgoactive'] = d.get('scanandgoactive')
                newDoc['departments'] = d.get('storeServices')
            else:
                newDoc = {}
                newDoc['address'] = {'addressLine1': d.get('address'), 'city': d.get('city'), 'state': d.get('state'), 'zipCode': d.get('zip')}
                newDoc['locationId'] = d.get('storenumber')
                newDoc['geolocation'] = {'latitude': d.get('latitude'), 'longitude': d.get('longitude')}
                newDoc['chain'] = 'Dollar General'
                newDoc['name'] = 'Dollar General'
                newDoc['phone'] = d.get('phoneNumber')
                newDoc['clickandcollect'] = d.get('clickandcollect')
                newDoc['scanandgoactive'] = d.get('scanandgoactive')
                newDoc['departments'] = d.get('storeServices')
                newStores.append(newDoc)

    # ---FamilyDollar--- {features, web, times, address}
        # _distance, _distanceuom, address1<street>, address2<place>, adult_beverages, adwordlabels, atm, bho, billpay, bopis, city, clientkey, coming_soon
        # country, dc_localpage_address, distributioncenter, ebt, end_date, fax, friclose, friopen, frozen_meat, geofence_radius, gt_radius, h1_text, h2_text, helium,
        # hiring_banner_url, holidayhours, hybrid_stores, ice, icon, job_search_url, latitude, localpage_banner, longitude, main_paragraph, monclose, monopen, name<-with #ID, 
        # now_open, phone, postalcode, propane, province, red_box, refrigerated_frozen, reopen_date, sameday_delivery, satclose, satopen, second_paragraph, start_date, state, store<-ID,
        # store_open_date, sunclose, sunopen, temp_closed, thuclose, thuopen, timezone, tobacco, tueclose, tueopen, uid, water_machine, wedclose, wedopen, wic
    with open(storeFiles[2], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        data = data.get('data').get('response').get('collection')

        servicesSet = {'atm', 'bho', 'billpay', 'bopis', 'ebt', 'helium', 'ice', 'propane', 'red_box', 'refrigerated_frozen', 'sameday_delivery', 'tobacco',
            'water_machine', 'wic', 'fronzen_meat'}
        toBool = {'Y': True, 'N': False, '1': True}
        for d in data:
            newDoc = {}
            newDoc['address'] = {'addressLine1': d.get('address1'), 'city': d.get('city'), 'zipCode': d.get('postalcode')}

            newDoc['departments'] = {k:toBool[v] for k in d.items() if k in servicesSet}
            newDoc['geolocation'] = {'latitude': d.get('latitude'), 'longitude': d.get('longitude'), 'distance': f"{d.get('_distance')} {d.get('_distanceuom')}"}
            newDoc['hours'] = {'timezone': d.get('timezone'),
                'sunday': {'open': dt.datetime.strptime(d.get('sunopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('sunclose'), "%I:%M %p").strftime('%H:%M')},
                'monday': {'open': dt.datetime.strptime(d.get('monopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('monclose'), "%I:%M %p").strftime('%H:%M')},
                'tuesday': {'open': dt.datetime.strptime(d.get('tueopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('tueclose'), "%I:%M %p").strftime('%H:%M')},
                'wednesday': {'open': dt.datetime.strptime(d.get('wedopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('wedclose'), "%I:%M %p").strftime('%H:%M')},
                'thursday': {'open': dt.datetime.strptime(d.get('thuopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('thuclose'), "%I:%M %p").strftime('%H:%M')},
                'friday': {'open': dt.datetime.strptime(d.get('friopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('friclose'), "%I:%M %p").strftime('%H:%M')},
                'saturday': {'open': dt.datetime.strptime(d.get('satopen'), "%I:%M %p").strftime('%H:%M'), 'close': dt.datetime.strptime(d.get('satclose'), "%I:%M %p").strftime('%H:%M')},
            
            }
            newDoc['locationId'] = d.get('store')
            newDoc['chain'] = 'Family Dollar'
            newDoc['phone'] = d.get('phone')
            newDoc['additionalIds'] = [{
                'path': 'clientkey',
                'id': d.get('clientkey'), 
            }]
            newStores.append(newDoc)



    # ---Food Depot---
        # data[0] = franchises 
            # KEEP Id, DeliveryServiceName, FavIconImageUrl, IconImageUrl, LogoImageUrl, LoyaltyType, MaximumOrderSpend, Name, PaymentProvider, PickingVariationPercentage, PickupServiceName
                # StoreTypeLabels, Stores = {
                #   Address {Country, Postcode:zipCode, State, StreetAddress:addressLine1, Suburb:city},
                #   HasDelivery, HasPickup, Id, LogoImageUrl, Name, StoreType, TimeZoneName, 
                # }
        # data[1] = stores
            # ['Id', 'Address', 'Categories', 'ContactPhone', 'CostPlusLabel', 'Currency', 'CurrentStoreTime', 'CustomersCanCancelOrders', 'CustomPages', 'DefaultDeliveryTip', 'DefaultPickupTip', 'DefaultProductSortForCategories', 'DefaultProductSortForSpecials', 'DeliveryInstructionsPrompt', 'DeliveryZones', 'FavIconImageUrl', 'HasDelivery', 'HasPickup', 'HasPromotions', 'HasShipping', 'HeaderLinks', 'HideTobaccoImages', 'HomePageTiles',
            # 'HomePageWelcomeContent', 'IconImageUrl', 'ImagePromotions', 'IsCostPlus', 'IsCouponsEnabled', 'IsDeliveryTipAllowed', 'IsFirstDeliveryFeeFree', 'IsFirstPickupFeeFree', 'IsLoyaltyEnabled',
            # 'IsOnline', 'IsPickerMessagingEnabled', 'IsPickupTipAllowed', 'Locales', 'LogoImageUrl', 'MinimumDeliveryPreparationTime', 'MinimumDeliverySpend', 'MinimumPickupPreparationTime', 'MinimumPickupSpend', 'Name', 'OfflinePaymentTypes', 'OrderMessageAlcoholDelivery', 'OrderMessageAlcoholPickup', 'OrderMessageTobaccoDelivery', 'OrderMessageTobaccoPickup', 'PickupInstructionsPrompt', 'PickupLocations', 'ProductCountOnSpecial', 'ProductOptions', 'ProductRankDisplayName', 'ProductRankSortDescending', 'ShippingOptions', 'ShowLogoOnHomePage', 'SnapLabel', 'StoreType', 'SupportedCreditCards', 'SupportEmail', 'SupportPhone', 'SupportsEbtPayments',
            # 'TagDefinitions', 'TimeZoneName', 'TobaccoMinAge', 'TobaccoRestriction', 'TobaccoWarningImageUrl', 'TradingHours', 'UnitConversion', 'UrlSlug', 'ValidatePhoneNumber']
            # 
            # KEEP Id, Address, Categories => {Name, Id, if ParentCategoryId=>append to parent by id} for departments,
            # ContactPhone, CostPlusLabel, CurrentStoreTime, HasDelivery, HasPickup, HasPromotions, HasShipping,
            # IconImageUrl, LogoImageUrl, MinimumDeliverySpend, MinimumPickupSpend, Name="Food Depot 40 - Douglassville Hwy 5",
            # minimumPickupWait = pickuplocations[0][TimeSlots][0]['Start']-pickuplocations[0][TimeSlots][0]['Cutoff'],
            # PickupFee = pickuplocations[0][TimeSlots][0]['defaultFee']
            # ProductCountOnSpecial, ?ShippingOptions, SupportedCreditCards,
            # SupportPhone, TimeZoneName  
    with open(storeFiles[3], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        data = list(map(lambda x: x.get('Result'), data[:2]))
        # address {addressLine1, city, county, state, zipCode}, departments [{id, name, hours{close, open, open24}, open24}]
        # geolocation {latLng, latitude, longitude},
        # hours {timezone, gmtOffset, open24, <weekdays:{close, open, open24}>}, locationId, name, phone
        franchiseCols = {'Id', 'DeliveryServiceName', 'FavIconImageUrl', 'IconImageUrl', 'LogoImageUrl', 'LoyaltyType', 'MaximumOrderSpend', 'Name',
        'PaymentProvider', 'PickingVariationPercentage', 'PickupServiceName', 'Stores'}
        storeCols = {'Id', 'Address', 'Categories', 'ContactPhone', 'CostPlusLabel', 'HasDelivery', 'HasPickup', 'HasPromotions', 'HasShipping', 'IconImageUrl', 'LogoImageUrl', 'MinimumDeliverySpend',
        'Name', 'minimumPickupWait', 'ProductCountOnSpecial', 'ShippingOptions', 'SupportedCreditCards', 'SupportPhone', 'TimeZoneName'}
        for d in data[0:1]:
            d = {k:v for k, v in d.items() if k in franchiseCols}
            for store in d.get('Stores'):
                newDoc={}
                oldAddress = store.get('Address')
                newDoc['address'] = {'addressLine1': oldAddress.get('StreetAddress'), 'city': oldAddress.get('Suburb'), 'state': oldAddress.get('State'), 'zipCode': oldAddress.get('Postcode')}
                newDoc['locationId'] = store.get('Id')
                newDoc['chain'] = 'Food Depot'
                newDoc['name'] = store.get('PickupLocations')[0].get('Name')

                newDoc['images'] = {'Icon' : d.get('IconImageUrl'), 'Logo': d.get('LogoImageUrl')}
                newDoc['restraints'] = {'max_spend': d.get('MaximumOrderSpend'), 'additionalFees': d.get('PickingVariationPercentag')}
                # newDoc['departments'] = []
                # newDoc['geolocation'] = {}
                # newDoc['hours'] = {}
                # newDoc['phone'] = ''
                moreStoreInfo = list(filter(lambda x: x.get('Id')==newDoc.get('locationId'), data[1:]))
                if moreStoreInfo:
                    for msi in moreStoreInfo:
                        newDoc['phone'] = msi.get('ContactPhone')
                        if msi.get('HasShipping'):
                            newDoc.setdefault('modalities', [])
                            newDoc['modalities'].append('SHIP')
                        if msi.get('HasDelivery'):
                            newDoc.setdefault('modalities', [])
                            newDoc['modalities'].append('DELIVERY')
                        if msi.get('HasPickup'):
                            newDoc.setdefault('modalities', [])
                            newDoc['modalities'].append('PICKUP')
                        if msi.get('Categories'):
                            departments = []
                            for cat in msi.get('Categories'):
                                if cat.get('ParentCategoryId'):
                                    departments.append({'departmentId': cat.get('Id'), 'name': cat.get('Name'), 'parentId': cat.get('ParentCategoryId')})
                                else:
                                    departments.append({'departmentId': cat.get('Id'), 'name': cat.get('Name')})
                            newDoc['departments'] = departments
                newStores.append(newDoc)

    # ---Publix---
  
    # Stores : [15] {ADDR, CITY, CLAT, CLON, DISTANCE, EPPH, IMAGE{}, ISENABLED, KEY, NAME, OPTION, PHMPHONE, PHONE, SHORTNAME, STATE, STOREDATETIME, STOREMAPSID,
                # STORETIMEZONE, STRHOURS format "%a %-h:%M %p,", TYPE, WABREAK, ZIP}
            # NULL {CLOSINGDATE, CSPH, DEPTS, EMPTY, FAX, LQHOURS, LQRPHONE, MAPH, OPENINGDATE, PHMHOURS, PXFHOURS, PXFPHONE, SERVICES, STATUS, STOREMAPTOGGLE, 
            #  StoreAdjustedHoursMobileApp, StoreAdjustedHoursWebsite, UNIQUE, WASTORENUMBER}
        
        # address {addressLine1, city, county, state, zipCode } <String> => {ADDR, CITY, _, STATE, ZIP}
        # chain => 'Publix'

        # departments: [{'departmentId': <String>, 'name': <String> +
        #   ?hours: {weekday: {close, open, open24}, open24, name, ?phone} <String> + <Bool::open24>
        # }]

        # geolocation: {latLng: <String>, latitude: <Float>, longitude: <Float>} => {f'{CLAT} {CLON}', latitude:LAT, longitude:CLON, ~DISTANCE}
        # hours: {gmtOffset: <String>, open24: <Bool>, timezone:<String>, <:weekdays:>: {open24, open, close}} => {timezone:STORETIMEZONE, STRHOURS "%a %-h:%M %p,",}
        # locationId: <String> <- Connector to Items, Inventory, et all. => {KEY}
        # name: <String> - chain + real estate name => {SHORTNAME, NAME}
        # phone: <String>  => {PHMPHONE, PHONE, EPPH, }
        # !image: {hero:IMAGE.Hero, thumbnail:IMAGE.Thumbnail}
        # !others = {OPTION=<varchar>, TYPE='R', OPENINGDATE=<datetime>, STATUS=''|'Coming Soon', WABREAK='4|None'}

    with open(storeFiles[4], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        data = data[0].get('Stores')
        
        for d in data:
            d = {k:v for k, v in d.items() if v!='-' and v!=''}
            newDoc = {}
            newDoc['address'] = {'addressLine1': d.get('ADDR'), 'city': d.get('CITY'), 'zipCode': d.get('ZIP'), 'state': d.get('STATE')}      
            newDoc['geolocation'] = {'latitude': float(d.get('CLAT')), 'longitude': float(d.get('CLON'))}
            if 'STRHOURS' in d:
                oldHours = d.get('STRHOURS').split(',')
                oldHours = list(filter(None, oldHours))
                dateRe = r'(\w+)\s([0-9\:]+\sAM)\s-\s([0-9\:]+\sPM)'
                newDoc['hours'] = {}
                for hour in oldHours:
                    day, openH, closeH = re.findall(dateRe, hour)[0]
                    day = normalizeDay(day)
                    newDoc['hours'][day] = {'open': dt.datetime.strptime(openH , '%I:%M %p').strftime('%H:%M'),'close': dt.datetime.strptime(closeH, '%I:%M %p').strftime('%H:%M')}
                    newDoc['hours'][day]['open24'] = newDoc['hours'][day]['open']==newDoc['hours'][day]['close']
                newDoc['hours']['timezone'] = d.get('STORETIMEZONE')
            newDoc['locationId'] =d.get('KEY')
            newDoc['images'] = d.get('IMAGE')
            newDoc['name'] = f"Publix - {d.get('SHORTNAME')}"
            newDoc['chain'] = 'Publix'
            newDoc['phone'] = d.get('PHONE')
            newDoc['additionalIds'] = [
                {'path': 'OPTION', 'id': d.get('OPTION')},
            ]
            newStores.append(newDoc)
            
    addressRegex = re.compile(r'^(\d+)')
    for icFile in instacartFiles:
        with open(icFile, 'r', encoding='utf-8') as file:
            additionalStoreData = json.loads(file.read())[0]
            stores = additionalStoreData['data']['availablePickupRetailerServices']['pickupRetailers'][0]['locations']
            # retailerLocationId + streetAddress 
            if 'aldi' in icFile:
                possibleStores = filter(lambda x: x.get('chain')=='ALDI', newStores)
            elif 'publix' in icFile:
                possibleStores = filter(lambda x: x.get('chain')=='Publix', newStores)
            
            
            for x in possibleStores:
                sums = [abs((x['geolocation']['latitude']-y['coordinates']['latitude'])+(x['geolocation']['longitude']-y['coordinates']['longitude'])) for y in stores]
                guessIndex = sums.index(min(sums))
                addressNumbersGuess = re.findall(addressRegex , stores[guessIndex]['streetAddress'])[0]
                addressNumbers = re.findall(addressRegex, x['address']['addressLine1'])[0]
                if addressNumbersGuess==addressNumbers:
                    finalGuess = stores[guessIndex]
                else:
                    if 'altAddress' in x:
                        altAddressNumbers = re.findall(addressRegex , x['altAddress'])[0]
                        if altAddressNumbers == addressNumbers:
                            finalGuess = stores[guessIndex]
                        elif altAddressNumbers == addressNumbersGuess:
                            finalGuess = stores[guessIndex]  
                    else:
                        moreGuesses = [i for i, x in enumerate(sums) if x<.01]
                        finalGuess = [stores[i] for i in moreGuesses if re.findall(addressRegex, stores[i]['streetAddress'])[0]==addressNumbers][0]
                x['locationId'] = finalGuess['retailerLocationId']
                
    insertData(newStores, 'stores', 'new')
    storeFiles.extend(instacartFiles)
    for storeFile in storeFiles:
        os.makedirs('../data/'+'/'.join(storeFile.split('/')[3:-1]), exist_ok=True)
        os.rename(storeFile , "../data/"+'/'.join(storeFile.split('/')[3:]))

    return None


def createDecompositions(dataRepoPath: str, wantedPaths: list, additionalPaths: dict = None, setStores: bool = False):
    # CATEGORY - Combine legacy files w/ current files to create full collections
    # calls decompose functions that handle database entry for different file types
    # pytz, os, backUpDatabase(), createDBSummaries()
    walkResults = sorted([x for x in os.walk(dataRepoPath)], key=lambda x: x[0], reverse=True)
    # initial setup if data folders do not exist in repo
    if os.path.exists('./requests/server/collections/kroger/API/myStores.json'):
        mytz = pytz.timezone('America/New_York')
        # setup archive for preprocessed data
        with open('./requests/server/collections/kroger/API/myStores.json', 'r', encoding='utf-8') as storeFile:
            stores = json.loads(storeFile.read())
            insertFilteredData(stores, 'stores', "new", "locationId")

        with open('./requests/server/collections/kroger/API/combinedPrices.json', 'r', encoding='utf-8') as priceFile:
            oldPrices = json.loads(priceFile.read())
            oldPrices = list(filter(lambda y: y.get('isPurchase')==False, oldPrices)) # trip price data will already have been recorded
        
        newFromOldPrices = []
        for oldPrice in oldPrices:
            # turn promo and regular to value
            oldTimestamp = mytz.localize(dt.datetime.fromtimestamp(oldPrice.get('acquistion_timestamp'))).astimezone(pytz.utc)
            if oldPrice.get('promo') == oldPrice.get('regular'):
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Regular'})
            else:
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Regular'})
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('promo'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Sale'})
        
        insertData(newFromOldPrices, 'prices', "new")
        
        os.makedirs('../data/collections/kroger/API', exist_ok=True)
        os.rename("./requests/server/collections/kroger/API/myStores.json", "../data/collections/kroger/API/myStores.json")
        os.rename('./requests/server/collections/kroger/API/combinedPrices.json', "../data/collections/kroger/API/combinedPrices.json")
    # file does not exist (clean up has happened therefore read from ../)
        # promotions (nonTime bound in db; no duplicates preferrable, filter check)
        # items (nonTime bound in db; no duplicates preferrable, filter check)
        # prices (time bound, no duplicates possible)
        # inventories (time bound, no duplicates possible)
        # trips (past transactions; not time bound; no duplicates preferrable, filter check)
            # priceModifierCollection (coupons applied a @ purchase. tied with trips. )
        # userCollection (nonTime bound in db, no duplicates preferrable, filter check)
        # sellerCollection (nonTime bound in db, no duplicates preferrable, filter check)
    if wantedPaths: 
        for head, subfolders, files in walkResults:         
            if head.split('\\')[-1] in wantedPaths:
                folder = head.split('\\')[-1]
                os.makedirs(f'../data/collections/kroger/{folder}/', exist_ok=True)
                for file in files:
                    deconstructExtensions(head+"\\"+file)
                    print(f'processed {file}.')

    if additionalPaths:
        for repo in additionalPaths:
            pathName = dataRepoPath.replace('kroger', repo)
            couponFiles = list(os.walk(pathName))
            couponFiles = couponFiles[0][2]
            for ofile in couponFiles:
                # handles insertion
                deconstructDollars(pathName+'/'+ofile)
                os.makedirs(f'../data/collections/{repo}', exist_ok=True)
                os.rename(pathName+'\\'+ofile, f'../data/collections/{repo}/{ofile}')  
                print(f'processed {ofile}.')

    for head, subfolders, files in os.walk(dataRepoPath):         
        if head.split('\\')[-1] in wantedPaths:
            folder = head.split('\\')[-1]
            for file in files:
                os.rename(head+'\\'+file, f'../data/collections/kroger/{folder}/{file}')

    if setStores:
        normalizeStoreData()
    backupDatabase()
    createDBSummaries('new')

    return None

def queryDB(db="new", collection="prices", pipeline=None, filterObject=None, stop=0):
    # wrapper for db aggregation and filter calls
    # REQ : os, pprint, pymongo

    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client[db]
    if pipeline:
        res = cursor[collection].aggregate(pipeline=pipeline)
    elif filterObject:
        res = cursor[collection].find(filterObject)
    else:
        res = cursor[collection].find({}).limit(1)
  
    res = [x for x in res]
    if not stop:
        pprint(res[:stop])
    else:
        pprint(res)

    client.close()

    return None

def getCollectionFeatureCounts(db='new', collection='prices'):
    # Helper for Counting Features in Documetn Collection
    # REQ : os, pprint, pymongo
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client[db]
    res = cursor[collection].aggregate(pipeline=[
        {'$project': {'features': {"$objectToArray": "$$ROOT"}}},
        {'$unwind': {'path': '$features', 'preserveNullAndEmptyArrays': False}},
        {'$project': {'keys': '$features.k'}},
        {'$group': {'_id': "$keys", 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ])
    res = [x for x in res]
    pprint(res)
    client.close()
    return None

def getCollectionFeatureTypes(db='new', collection='items', feature='upc'):
    # DB helper for getting feature types from command line
    # REQ : os, pprint, pymongo
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client[db]
    res = cursor[collection].aggregate(pipeline=[
        {'$project': {'upc': f'${feature}', 'type': {'$type' : f'${feature}'}}},
        {'$group': {'_id': '$type', 'count': {'$sum': 1}}},
        {'$sort': {'_id': -1}}
    ])
    res = [x for x in res]
    client.close()
    pprint(res)
    return None

def getStores():
    # REQ : os, pprint, pymongo
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client['new']
    res = cursor['stores'].find({})
    res = [r for r in res]
    pprint(res[0])
    client.close()
    return None

def findAndInsertExtraPromotions(head):
    # To Extract Coupons Left in Archive Files (those with unclipped in url) 
    upcsRegex = re.compile(r'https://www\.kroger\.com/cl/api/couponDetails/(\d+)/upcs')
    promotionsCollection = []
    for folder, _, files in os.walk(head):
        for fd in files:
            file_handle = open(folder+fd, "r", encoding="utf-8") 
            jsonData = json.loads(file_handle.read())
            file_handle.close()
            missedResults = list(filter(lambda x: re.findall(r"unclipped|upcs$", x["url"]), jsonData))
            cDict = {}
            if missedResults:
                for mr in missedResults:
                    url = mr.pop('url')
                    data = mr.pop("data")
                    if "upcs" in url:
                        couponId = re.match(upcsRegex, url).group(1)
                        cDict[couponId] = data
                    else: 
                        coupons = data.get("couponData").get('coupons') 

                        coupSchema = {'keep':{"id", "krogerCouponNumber", "brandName", "categories", "productUpcs", "type", "expirationDate",\
                                "redemptionsAllowed", "value", "requirementQuantity", "displayStartDate", "imageUrl", "shortDescription", "requirementDescription",
                                "modalities"},\
                                "bool": {"cashbackCashoutType", "isSharable", "forCampaign", "specialSavings",  "longDescription"}}
                        for k,v in coupons.items():
                            promo = {}
                            if k in cDict:
                                v.update({'productUpcs': cDict[k]})
                            else:
                                v.update({'productUpcs': []})

                            for coupKey, coupVal in v.items():
                                if coupKey in coupSchema['bool']:
                                    if bool(coupVal):
                                        if coupKey=='longDescription':
                                            promo['terms'] = coupVal
                                        else:
                                            promo[coupKey] = coupVal
                                elif coupKey in coupSchema['keep']:
                                    if coupKey=='displayStartDate':
                                        promo['startDate'] = pytz.utc.localize(dt.datetime.strptime(coupVal, "%Y-%m-%dT%H:%M:%SZ"))
                                    elif coupKey=='expirationDate':
                                        promo['expirationDate'] = pytz.utc.localize(dt.datetime.strptime(coupVal, "%Y-%m-%dT%H:%M:%SZ"))
                                    elif coupKey=='shortDescription':
                                        promo[coupKey] = coupVal.strip()
                                    else:
                                        promo[coupKey] = coupVal
                            # filterBoolean is Calculated
                            isProcessed = bool(list(filter(lambda x: x.get('krogerCouponNumber')==promo.get('krogerCouponNumber'), promotionsCollection)))
                            if isProcessed==False:
                                # promotions is appended to massiveArray
                                promotionsCollection.append(promo)
            print(f"finished {folder+fd}")
    insertFilteredData(promotionsCollection, "promotions", "new", "krogerCouponNumber")
    
    return None


# findAndInsertExtraPromotions("./requests/server/collections/kroger/digital/")
# findAndInsertExtraPromotions("./requests/server/collections/kroger/cashback/")
createDecompositions('./requests/server/collections/kroger', wantedPaths=[], additionalPaths=["dollargeneral/promotions"])
# backupDatabase()
# createDBSummaries('new')