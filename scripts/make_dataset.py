
from pprint import pprint
import time, re, random, datetime as dt, os, json, urllib, pytz, sys
import pyautogui as pag
import subprocess, shutil, requests


from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import pyperclip as clip, inspect
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
startTime = time.perf_counter()

def normalizeDay(string):
    string = string
    today= dt.datetime.now()
    abbv = today.strftime('%a')
    if len(string)>3:
        string = string[:3]
    while abbv!=string:
        today -= dt.timedelta(days=1)
        abbv = today.strftime('%a')
    return today.strftime('%A').lower()



def switchUrl(x=468, y=63, url="https://www.dollargeneral.com/dgpickup/deals/coupons?"):
    # CATEGORY = HELPER Web Interaction Function
    # automate browser request change in switching relevant pages or to new collections  
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

def eatThisPage(reset=False):
    # flush remaining results after main data call to server using browser context menu
    pag.moveTo(1410, 1004)
    time.sleep(2)
    pag.click(button='right')
    time.sleep(1)
    pag.moveRel(50, -25, duration=3)
    pag.click()
    time.sleep(15)
    if reset:
        subprocess.Popen(['taskkill', '/IM', 'firefox.exe', '/F'])
    return None

def loadExtension(fromTab=True):
    # load extension via tab
    pag.keyDown('ctrlleft')
    pag.keyDown('t')
    pag.keyUp('ctrlleft')
    pag.keyUp('t')
    time.sleep(3)
    switchUrl(url='about:debugging#/runtime/this-firefox')
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


def setUpBrowser(n=0, initialSetup=True, url=None):
    # create setup for Kroger coupons (digital and cashback)
    if initialSetup:
        p1 = subprocess.Popen(['C:\Program Files\Mozilla Firefox\\firefox.exe'])
        p1.wait(2)
    if n=='kroger-trips':
        # for trips
        switchUrl(url="https://www.kroger.com/")
        time.sleep(3)
        # Click SignIN Select
        pag.moveTo(1705, 465)
        pag.click()
        time.sleep(2)
        # Click SignIn Button
        pag.moveTo(1797, 169)
        time.sleep(2)
        pag.moveRel(0, 50)
        pag.click()
        time.sleep(2)
        # Unselect SignIn 
        pag.moveTo(736, 625, duration=1)
        pag.click()
        time.sleep(2)
        pag.moveRel(50, 50)
        pag.click()
        time.sleep(2)
        # Load Extension 
        loadExtension()
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
            time.sleep(2)
            # reset filter to get amount of available coupons
            pag.moveTo(1768, 499, duration=2)
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
        pag.moveTo(1307, 194, duration=3)
        time.sleep(2)
        pag.click()
        time.sleep(6.5)
        pag.moveTo(93, 286, duration=3)
        pag.click()
        time.sleep(5)
        pag.moveRel(0, 50, duration=2)
        pag.click()
        time.sleep(5)
        pag.moveTo(371, 397, duration=3)
        pag.click()
        time.sleep(6.5)
        loadExtension()
        time.sleep(2)
    elif n=="publix-coupons": # publix Coupons
        # nav to https://www.publix.com/savings/all-deals
        switchUrl(url="https://www.publix.com/savings/all-deals")
        # load extension
        time.sleep(3)
        loadExtension()
        time.sleep(3)
        # allow to access location
        pag.moveTo(570, 191, duration=3)
        pag.click()
        time.sleep(7)
        # eat page
        eatThisPage()
    elif n=='publix-items': # publix / instacart site
        switchUrl(url="https://delivery.publix.com/store/publix/collections/")
        time.sleep(7)
        pag.moveTo(858, 653, duration=2)
        pag.click()
        pag.typewrite(list(f"{ZIPCODE}"), interval=.35)
        pag.press('enter')
        time.sleep(1)
        pag.moveTo(969, 863, duration=2)
        pag.click()
        pag.moveTo(773, 515, duration=2)
        pag.click()
        time.sleep(1)
        pag.moveTo(791, 512, duration=2)
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
        # time.sleep(2)
        # pag.keyDown('ctrlleft')
        # pag.keyDown('-')
        # time.sleep(2)
        # pag.keyUp('ctrlleft')
        # pag.keyUp('-')
        time.sleep(2)
        # create setup for dollar general
        switchUrl(url="https://www.dollargeneral.com/dgpickup/deals/coupons")
        # change store
        loadExtension()
        pag.moveTo(73, 222, duration=2)
        pag.click()
        time.sleep(2)
        pag.moveTo(32, 302, duration=2)
        pag.click()
        time.sleep(3)
        pag.moveTo(82, 410, duration=2)
        pag.click()
        time.sleep(3)
        pag.moveTo(239, 574, duration=2)
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
    elif n=='family-dollar-coupons': # family-dollar smart coupons
    # create setup for family dollar coupons
        loadExtension()
        time.sleep(1)
        switchUrl(url="https://www.familydollar.com/smart-coupons")
        time.sleep(5)
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

    else:
        print('skipping setup')

    return None


def getStoreData(chain):
    # TODO: a function that automates processes to gather store data from the following sites API:
    # aldi, publix
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

def loadMoreAppears(png='./requests/server/images/moreContent.png'):
    # Evaluate if Dollar General's Promotional Page of Associated Items Has More Items
    # Returns location of button in y [419, 559] band of standard 1920 by 1080 screen 
    locations = list(pag.locateAllOnScreen(png, confidence=.6, grayscale=False))
    locations = list(map(lambda x: pag.center(x), locations))
    i = 0
    locations = list(filter(lambda x: x.y>318 and x.y<400, locations))
    if locations:
        loc = locations[i]
        x, y = loc
        color = pag.pixel(int(x), int(y))
        if color==(0, 0, 0):
            return loc
        else:
            i+=1

    return None

def getArrow(sleep=2):
    # CATEGORY = Helper Web Interaction Function
    # Pagination Helper For Family Dollar Items / Prices Collection
    time.sleep(sleep)
    pag.moveTo(1559, 346)
    time.sleep(sleep)
    pag.click() 
    return None

def scrollDown(sleep=10):
    # CATEGORY = Helper Web Interaction Function
    # Helper for scrolling data with api calls linked to pagination (food depot, aldi, publix)
    time.sleep(sleep)
    pag.press('end')
    return None

def insertData(entries, collection_name, db='new'):
    # Going to add Entries to Locally running DB w/ same structure as Container application
    # Then migrate them over to Container DB
    # Wrapper to always use insert many
    if type(entries) != list:
        entries = [entries]
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    res = db[collection_name].insert_many(entries)
    res = len(res.inserted_ids)
    print(f"Inserted {res} documents in {collection_name}")
    client.close()

    return None

def retrieveData(collection_name, db='new'):
    # Going to add Entries to Locally running DB w/ same structure as Container application
    # Then migrate them over to Container DB
    # Wrapper to always use insert many
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    res = db[collection_name].find({})
    data = []
    for r in res:
        r.pop('_id')
        data.append(r)
    print(f"Found {len(data)} documents in {collection_name}")
    client.close()

    return data

def createDBSummaries(db='new'):
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

    return None



# document scraping functions via a description and function calls
# Place into Runs Collections
# Admin DB to Track and Monitor the Execution of Scraping Functions that Work on Different Schedules BAased on Store's Internal Promotion Schedule
# TODO: Add CPU/resource usage for processes related to the functions (browser/Python Application, Mongo Create Operations) 
def runAndDocument(funcs:list, callNames:list, kwargs: list, callback=None):
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
    neededLinks = {'cashback': {"no": 12, "button": "./requests/server/images/cashback.png", "confidenceInterval": .66, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -1640, 'initialScroll': -800},\
        'digital': {"no":12, "button": "./requests/server/images/signIn.png", "confidenceInterval": .6, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -1640, 'initialScroll': -740},\
            'dollarGeneral': {'no': 12, "button": "./requests/server/images/addToWallet.png", "confidenceInterval": .7, 'maxCarousel': 3, 'buttonColor': (0, 0, 0), 'scrollAmount': -1750 ,"moreContent": "./requests/server/images/loadMore.png",\
                 'initialScroll': -1750}}
    # browser up start will be setting user location, navigating to the page, and placing mouse on first object
    # from here: the code will commence
    # start at top of the screen 
    # align all items https://www.kroger.com/savings/cl/coupons/
    #iterations = neededLinks[link]["no"] // 12
    #iterations = iterations + 1
    response = requests.get("http://127.0.0.1:5000/i").json()
    j = 0
    while response.get('i')==None:
        print(f"waiting for i from server for {j} seconds")
        j+=1
        time.sleep(1)
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
            if iterations-i<=2: 
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
                pag.moveRel(-70, 0, duration=1.5)
                pag.moveRel(0, -125, duration=1.5)
                # expand items
                pag.keyDown('ctrlleft')
                pag.click()
                time.sleep(3)
                pag.keyUp('ctrlleft')
                time.sleep(6)
                pag.press('end')
                time.sleep(3)
                # check for load more button (indicating more loadable items) 
                moreItems = loadMoreAppears()
                while bool(moreItems):
                    button = moreItems
                    pag.moveTo(button.x, button.y, duration=0.5)
                    pag.click()
                    time.sleep(7)
                    pag.press('pagedown', 3, interval=1)
                    moreItems = loadMoreAppears()
                pag.keyDown('ctrlleft')
                pag.keyDown('w')
                pag.keyUp('ctrlleft')
                pag.keyUp('w')
                time.sleep(2.5)
                    

        if i<=1 and link=='dollarGeneral':
            pag.scroll(neededLinks[link]['initialScroll'])
        elif link=='dollarGeneral':
            pag.scroll(neededLinks[link]['scrollAmount'])
            pag.scroll(-20)
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
    # cleaner function for Kroger trip data
    # Kroger Fuel Points (previously in price modifiers) now show up as duplicate entry of gasoline with a quantity of zero and a negative price paid to correspond to savings
    # Must be run before deconstructions.
    # Raises ZeroDivisionError on Calucations that use Quantity 
    indices = ''
    for trip_index, trip in enumerate(data):
        for item_index, item in enumerate(trip.get('items')):
            if item.get('quantity')==0:
                indices = trip_index, item_index
    if indices:
        data[indices[0]]['items'][indices[1]-1]['pricePaid'] = round(data[indices[0]]['items'][indices[1]-1]['pricePaid']+data[indices[0]]['items'][indices[1]]['pricePaid'], 2)
        data[indices[0]]['items'][indices[1]-1]['totalSavings'] = round(data[indices[0]]['items'][indices[1]-1]['totalSavings']+data[indices[0]]['items'][indices[1]]['totalSavings'], 2)
        data[indices[0]]['items'][indices[1]-1]['priceModifiers'].extend(data[indices[0]]['items'][indices[1]]['priceModifiers'])
        data[indices[0]]['items'].pop(indices[1])
    return data

def getFamilyDollarItems():
    # example url : https://www.familydollar.com/categories?N=categories.1%3ADepartment%2Bcategories.2%3AHousehold&No=0&Nr=product.active:1
    # dependencies: scrollDown and getArrow
    # a function that retrieves all the items and prices from the local family dollars
    # CATEGORY = Larger Web Function
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
        'd1102-produce', 'd1090-dairy-eggs', 'd1106-frozen','d1089-beverages', 'd1099-snacks', 'd1095-pantry', 'dynamic_collection-sales','d1094-meat-seafood', 'd1088-bakery', 'd1091-deli', 'd1092-household', 'd1104-canned-goods',
        'd1100-dry-goods-pasta', 'd1097-personal-care', 'd1103-breakfast', 'd1093-international', 'd1101-babies', 'd1098-pets', 'd5626-greeting-cards',
        'd21232-wine', 'd21231-beer', 'd3152-popular', 'd5625-floral', 'd5630-platters', 'd50450-ready-to-eat-ready-to-cook', 'd1105-new-and-interesting',
        'd41671-storm-prep','d41622-tailgating', 'd51523-deli-grab-and-go']
    }]
    base_url, urls = list(map(lambda x: (x.get('base_url'), x.get('urls')), list(filter(lambda x: x['chain']==chain, scrollVars))))[0]

    # CATEGORY = Larger Web Task
    # works for Aldi + Publix Instacart Sites as well as Food Depot's 1st Party Site
    pageEndColor = (205, 205, 205)
    continueColor = (240, 240, 240)
    noScrollColor = (255, 255, 255)
    noScrollColor2 = (248, 248, 248)
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


# Summarize Collections
def extract_nested_values(it):
    if isinstance(it, list):
        for sub_it in it:
            yield from extract_nested_values(sub_it)
    elif isinstance(it, dict):
        for key, value in it.items():
            if isinstance(value, list) and bool(value)==True:
                yield {"keyName":key, "values": list(extract_nested_values(value)), "count":1, 'type': type(value)}
            elif isinstance(value, list) and bool(value)==False:
                yield {"keyName":key, "count":0, 'type': type(value)}
            else:
                yield {"keyName": key, "count":1, 'type': type(value)}
    else:
        yield {'count':1, 'type': type(it)}

def deconstructDollars(file='./requests/server/collections/familydollar/digital052122FD.json'):
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
    mytz = pytz.timezone('America/New_York')
                             
    newProducts=[]
    newCoupons=[]
    newPrices = []
    newInventory = []
    storeCode = ''
    booleans = {'prices': {'IsSellable': 'IN_STORE', 'IsBopisEligible': 'PICKUP', 'isShipToHome': 'SHIP'}, 'items': {'IsGenericBrand', 'IsBopisEligible', 'isShipToHome'}}
    inventoryKeys= {'1': 'TEMPORARILY_OUT_OF_STOCK', '2': "LOW", "3": 'HIGH'}
    productsForCoupons = {}

    if 'dollargeneral' in file:
        # deconstructs into coupons (promotions), items, prices, and inventories 
        with open(file, 'r', encoding='utf-8') as fd:
            data = sorted(json.loads(fd.read()), key=lambda x: x.get('url'))
            products = filter(lambda p: 'eligibleProductsResult' in p.keys(), data)
            coupons = filter(lambda p: 'Coupons' in p.keys(), data)
        for item in products:
            utcTimestamp = item["acquisition_timestamp"]
            url = item['url']
            params = urllib.parse.parse_qsl(url)
            if bool(storeCode)==False:
                storeCode = list(filter(lambda x: x[0]=='store', params))[0][1]
            couponId = list(filter(lambda x: x[0].endswith('couponId'), params))[0][1]
            itemList = item.get('eligibleProductsResult').get('Items')
            for i in itemList:
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
                newPrices.append({'value': i.get('OriginalPrice'), 'type': 'Regular', 'isPurchase': False, 'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                    'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
                if i.get('OriginalPrice')!=i.get('Price'):
                    newPrices.append({'value': i.get('Price'), 'type': 'Sale', 'isPurchase': False, 'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                    'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
                # deconstruct to inventories
                itemStatus = inventoryKeys[str(i.get('InventoryStatus'))]
                newInventory.append({'stockLevel': itemStatus, 'availableToSell': i.get('AvailableStockStore'), 'locationId': storeCode, 'utcTimestamp': utcTimestamp, 'upc': i.get('upc')})     
                # deconstuct into Items
                itemDoc = {'description': i.get('Description'), 'upc': i.get('UPC'), 'images': [{'url': i.get('Image'), 'perspective': 'front', 'main': True, 'size': 'xlarge'}],\
                    'soldInStore': i.get('IsSellable'),"modalities": modalities}

                if i.get('RatingReviewCount')!=0:
                    itemDoc['ratings'] = {'avg': i.get('AverageRating'), 'ct': i.get('RatingReviewCount')}
    
                if 'Category' in i:
                    itemDoc['categories'] = i.get('Category').split('|')
                
                for ky in booleans.get('items'):
                    if bool(i[ky]):
                        itemDoc[ky] = i[ky]
                    if ky=='isShipToHome' and bool(i[ky]):
                        print(i)
                        itemDoc['maximumOrderQuantity'] = i.get('shipToHomeQuantity')
                
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
                newC['brandName'] = coup.get('Brandname') 
                newC['companyName'] = coup.get('Companyname') 
                newC['offerType'] = coup.get('OfferType')
                if bool(coup.get('OfferDisclaimer')):
                    newC['terms'] = coup.get('OffeDisclaimer') 
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
            newC['value'] = coup.get('offerSortValue')
            # minPurchase => requirementQuantity
            newC['requirementQuantity'] = coup.get('minPurchase')
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
    dollarCollections = {'prices': newPrices, 'promotions': newCoupons, 'inventories': newInventory, 'items': newProducts}
    [insertData(v, k) for k,v in dollarCollections.items() if v]
    print(f"Finished with {file}")

    return None

def backupDatabase():
    # move and compressed extension files to separate archive 
    subprocess.Popen(['7z', "a", "../data/archive.7z", "../data/raw", f"-p{EXTENSION_ARCHIVE_KEY}", "-mhe", "-sdel"])
    # helper to dump bsons and zip files for archive
    if os.path.exists("../data/archive/"):
        os.remove('../data/archive/')
    process1 = subprocess.Popen(['mongodump', "-d", "new", "-o", "../data/data"])
    process1.wait(30)
    # 7zip archive mongodumps w/ password
    process2 = subprocess.Popen(['7z', "a", "../data/data.7z", "../data/data", f"-p{DB_ARCHIVE_KEY}", "-mhe", "-sdel"])
    process2.wait(30)
    if os.path.exists("../data/data"):
        shutil.rmtree('../data/data')
    return None

# Deconstruct Extension Created Files into Final Collections
def deconstructExtensions(filename, **madeCollections):
    # CATEGORY = Wash Data (file=> append to madeCollections to make fullCollections). Handles Kroger's promotions and trips
    # breaks down promotion jsons generated by the extension into the promotions, items and prices collections
    # 1.) Trips -> Prices, Items, Stores?/Trips?, Promotions
    # 2.) Coupons (digital/cashback) -> Promotions, Items, Prices
    # Add item UPCs that correspond to their appropiate promotion
    # Aggregate couponDetails separate calls into promotions collections
    # Break down item api calls into both price and item collections

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
    couponsDetailsRegex = re.compile(r'https://www\.kroger\.com/cl/api/coupons\?.+')
    productsRegex = re.compile(r'https://www\.kroger\.com/atlas/v1/product/v2/products\?.+')
    tripRegex = re.compile(r'https://www\.kroger\.com/mypurchases/api/v1/receipt.+')
    storeRegex = re.compile(r'https://www\.(.+)\.com.+')
    specialPromoRegex = re.compile(r'https://www\.kroger\.com/products/api/products/details-basic',)
    productErrorsRegex = re.compile(r'\.gtin13s=(\d+)')
    storeDict = filename.split('/')[-2]
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            startingArray = json.loads(file.read())

        cDict={}
        try:
            if 'trips' in filename:
                startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=True)
            else:
                startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=False)
        except TypeError as err:
            print(err)
        except KeyError:
            print(list(map(lambda x: x.keys(), startingArray)))
        # static collections
        promotionsCollection = madeCollections['promotionsCollection']
        itemCollection = madeCollections['itemCollection']
        # # dynamic flows @ specific moment in time
        pricesCollection = madeCollections['pricesCollection']
        inventoryCollection = madeCollections['inventoryCollection']
        # # dependent tables @ specific moment in time
        tripCollection = madeCollections['tripCollection']
        priceModifierCollection = madeCollections['priceModifierCollection']
        # # identifying the users specific relation to and contact with these flows/objects to present data solutions based on past interactions with all these elements
        userCollection = madeCollections['userCollection']
        sellerCollection = madeCollections['sellerCollection']
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
            elif re.match(specialPromoRegex, url):
                allUpcs = set()
                allOffers = set()
                qualifiers = apiCall.get('products')
                for q in qualifiers:
                    allUpcs.add(q.get('upc'))
                    for offer in q.get('offers'):
                        allOffers.add(str(offer).replace("'", "\""))
                allOffers = json.loads(list(allOffers)[0])
                hasNewPromotion = list(filter(lambda x: x.get('krogerCouponNumber')==allOffers.get('couponNumber'), promotionsCollection))
                if len(hasNewPromotion)==0:
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
                    promotionsCollection.append(newPromotion)
                else:
                    hasNewPromotion[0]['productUpcs'].extend(list(allUpcs))
            elif re.match(couponsDetailsRegex, url):
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
                    isProcessed = bool(list(filter(lambda x: x.get('krogerCouponNumber')==promo.get('krogerCouponNumber'), promotionsCollection)))
                    if isProcessed==False:
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
                    isProcessed = bool(list(filter(lambda x: x.get('transactionId')==transactionId, tripCollection)))
                    if isProcessed==False:
                        for key, value in trip.items():
                            if key in tripKeep:
                                if key=='tenders':
                                    tripDocument['tenderType'] = value[0].get('tenderType')
                                elif key=='receiptId':
                                    tripDocument['locationId'] = value.get('divisionNumber') + value.get('storeNumber')
                                    tripDocument['terminalNumber'] = value.get('terminalNumber')
                                    tripDocument['transactionId'] = transactionId
                                    if len(userCollection)==0:
                                        #setup Users
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
                                    # needs to reference back to items (by baseUpc), trip (via trip Id), priceModifiers (pointes to priceModifier) and time (via acquistion timestamp)
                                    
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
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': tripDocument['locationId']})
                                            else:
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': tripDocument['locationId']})
                                                value = round(item.get('pricePaid') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Sale', 'locationId': tripDocument['locationId'],
                                                'offerIds': ','.join(list(map(lambda pm: pm.get('promotionId'), item.get('priceModifiers'))))})

                                            if item.get('isWeighted'):
                                                averageWgt = item.get('detail').get('averageWeight')
                                                pricesCollection.append({'value': item.get('unitPrice'), 'quantity': averageWgt, 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': False, 'transactionId': transactionId, 'type': 'Average'})

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
                        

        

    return promotionsCollection, itemCollection, pricesCollection, inventoryCollection, tripCollection, priceModifierCollection, userCollection, sellerCollection
        

def normalizeStoreData():
    storeFiles = ['/aldi/stores/071822.json', '/dollargeneral/stores/stores.json', '/familydollar/stores/stores.json', '/fooddepot/stores/071822.json', '/publix/stores/071822.json'] 
    head= './requests/server/collections'
    newStores = []

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
    # data[0] = store <- the single store
    # data[1] = gmap api with my lat/long / gmapsigner => just url
    # data[2] = specialevents => []
    # data[3] = listing => __typename and so on {}
    # data[4] = promotions => {} of promos w/ keys {promos, dpv2api, __typename} Query parms and user data
    # data[5] = promotion => {} the actual promotions
    # data[6] = 4 closest stores <- storeList

    # {address: {city:actual city, dmaName:City,ST, line1:street address, line2: None, postalCode: 30084, state} <string>
    # } ==> { city, addressLine1 : line1, bool(line2), zipCode: postalCode, state:  dmaName.split(',')[-1] }
    # currentPromotions: <Int> / previewPromotions / previewPromotions: <Int> / napi / listingCount
    # chain: name, 
    # locationId: id, # id: <String> <- storeId
    # hours: parse format <String> of "(%a): (%-H:%M %p)-(%-H:%M %p);" => {\1 : {open: \2, close: \3}, gmtOffset, timezone, open24}
    # geolocation: {latLng: f"{location.lat} {location.lng}", ~location.distance}
    # phone: bool(phone+areaCode, phone.phoneNumber)

    # logo: logos.logURL
    # additional_ids = {
    #   pretailer.id, pretailer.name,
    #   referenceNumber, retailer.id, retailer.name==pretailer.name : null : retailer.name; 
    # }

    with open(head+storeFiles[0], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        data = map(lambda x: x.get('data'), data)
        stores = filter(lambda x:'store' in x.keys() or 'storeList' in x.keys(), data)
        data = []
        for s in stores:
            if 'store' in s.keys():
                data.append(s['store'])
            else:
                data.extend(s['storeList'])
        # all stores
        # address {addressLine1, city, county, state, zipCode}, departments [{id, name, hours{close, open, open24}, open24}]
        # geolocation {latLng, latitude, longitude},
        # hours {timezone, gmtOffset, open24, <weekdays:{close, open, open24}>}, locationId, name, phone
        ###tzWhere = tzwhere.tzwhere()
        for d in data:
            newDoc = {}
            oldAddress = d.pop('address')
            oldAddress['addressLine1'] = oldAddress.pop("line1")
            oldAddress['zipCode'] = oldAddress.pop('postalCode')
            newDoc['address'] = {k:v for k,v in oldAddress.items() if k in {'addressLine1', 'zipCode', 'city', 'county', 'state'}}
            newDoc['chain'] = d.pop('name')
            newDoc['geolocation'] = {}
            newDoc['geolocation']['latitude'] = d['location']['coordinates'][1]
            newDoc['geolocation']['longitude'] = d['location']['coordinates'][0]
            # parse hours in to hours 
            oldHours = d.pop('hours').split(';')
            dateRe = r'(\w+)\:\s([0-9\:]+\sAM)-([0-9\:]+\sPM)'
            newDoc['hours'] = {}
            for hour in oldHours:
                day, openH, closeH = re.findall(dateRe, hour)[0]
                day = normalizeDay(day)
                newDoc['hours'][day] = {'open': dt.datetime.strptime(openH , '%I:%M %p').strftime('%H:%M'),'close': dt.datetime.strptime(closeH, '%I:%M %p').strftime('%H:%M')}
                newDoc['hours'][day]['open24'] = newDoc['hours'][day]['open']==newDoc['hours'][day]['close']
            ###newDoc['hours']['timezone'] = tzWhere.tzNameAt(newDoc['geoLocation']['latitude'], newDoc['geoLocation']['longitude'])
            newDoc['locationId'] = d.get('id')
            newDoc['name'] = newDoc.get('chain').title()

            if d.get('phone').get('phoneNumber'):
                newDoc['phone'] = d.get('phone').get('areaCode') + d.get('phone').get('phoneNumber')
            
            newDoc['additionalIds'] = [
                {'path': 'pretailer.id', 'id': d.get('pretailer').get('id')},
                {'path': 'retailer.id', 'id': d.get('retailer').get('id')},
                {'path': 'referenceNumber', 'id': d.get('referenceNumber')},
            ]
            newStores.append(newDoc)
    
    # ---DollarGeneral---
        # ad=address, cc<Int>, ct=city, di='U', dm=<datetime>, ef<Int>, hf<hours friday>, hh<hours thursday>, hm<hours monday>,
        # hs<hours sat>, ht, hu, hw, la=latitude, lo=longitude, pn='4708932140', se=1, sg=0, si=2, sn=id<13141>, ss=123054, 
        # st=state, um=3793, uu='hex-code', zp=zipCode full 
    

    with open(head+storeFiles[1], 'r', encoding='utf-8') as file:
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
                newDoc['id'] = d.get('storenumber')
                newDoc['geolocation'] = {'latitude': d.get('latitude'), 'longitude': d.get('longitude')}
                newDoc['chain'] = 'Dollar General'
                newDoc['name'] = 'Dollar General'
                newDoc['phone'] = d.get('phoneNumber')
                newDoc['clickandcollect'] = d.get('clickandcollect')
                newDoc['scanandgoactive'] = d.get('scanandgoactive')
                newDoc['departments'] = d.get('storeServices')
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

    with open(head+storeFiles[4], 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        data = data[0].get('Stores')
        
        for d in data:
            d = {k:v for k, v in d.items() if v!='-' and v!=''}
            newDoc = {}
            newDoc['address'] = {'addressLine1': d.get('ADDR'), 'city': d.get('CITY'), 'zipCode': d.get('ZIP'), 'state': d.get('STATE')}      
            newDoc['geolocation'] = {'latitude': d.get('CLAT'), 'longitude': d.get('CLON')}
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
            
    # ---FamilyDollar--- {features, web, times, address}
        # _distance, _distanceuom, address1<street>, address2<place>, adult_beverages, adwordlabels, atm, bho, billpay, bopis, city, clientkey, coming_soon
        # country, dc_localpage_address, distributioncenter, ebt, end_date, fax, friclose, friopen, frozen_meat, geofence_radius, gt_radius, h1_text, h2_text, helium,
        # hiring_banner_url, holidayhours, hybrid_stores, ice, icon, job_search_url, latitude, localpage_banner, longitude, main_paragraph, monclose, monopen, name<-with #ID, 
        # now_open, phone, postalcode, propane, province, red_box, refrigerated_frozen, reopen_date, sameday_delivery, satclose, satopen, second_paragraph, start_date, state, store<-ID,
        # store_open_date, sunclose, sunopen, temp_closed, thuclose, thuopen, timezone, tobacco, tueclose, tueopen, uid, water_machine, wedclose, wedopen, wic
    with open(head+storeFiles[2], 'r', encoding='utf-8') as file:
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
    with open(head+storeFiles[3], 'r', encoding='utf-8') as file:
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
                print(newDoc.get('locationId'))
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

        
    insertData(newStores, 'stores', 'new')
    for storeFile in storeFiles:
        os.makedirs('../data/raw'+'/'.join(storeFile.split('/')[:-1]), exist_ok=True)
        os.rename(head+storeFile, "../data/raw/"+storeFile)
        

    return None


def createDecompositions(dataRepoPath: str, wantedPaths: list, additionalPaths: dict):
    # CATEGORY - Combine legacy files w/ current files to create full collections
    # calls decompose functions that handle database entry

    # TODO: Currently only handles decomposition for legacy files and process would try to entered in all the data at once.
    # Want to have a legacy version for files (run once, then garabage collect files), then handle newly created cleaned data w/ care to only enter in new information to the database.
    # Where Best in the cleaning/processsing/insertion chain to apply that is most efficent will be key.    
    # add stores via api and previously scraped prices to new price collection schema
    iteration=0
    listTranslator={"0": "promotions", "1": "items", "2": "prices", "3": "inventories", "4":"trips", "5":"priceModifiers", "6":"users", "7":"sellers"}
    mytz = pytz.timezone('America/New_York')
    walkResults = sorted([x for x in os.walk(dataRepoPath)], key=lambda x: x[0], reverse=True)
    # initial setup if data folders do not exist in repo
    if os.path.exists('./requests/server/collections/kroger/API/myStores.json'):
        # setup archive for preprocessed data
        with open('./requests/server/collections/kroger/API/myStores.json', 'r', encoding='utf-8') as storeFile:
            stores = json.loads(storeFile.read())
            insertData(stores, 'stores')
        os.makedirs('../data/raw/kroger/API', exist_ok=True)

        with open('./requests/server/collections/kroger/API/combinedPrices.json', 'r', encoding='utf-8') as priceFile:
            oldPrices = json.loads(priceFile.read())
            oldPrices = list(filter(lambda y: y.get('isPurchase')==False, oldPrices)) # trip price data will already have been recorded
        
        newFromOldPrices = []
        for oldPrice in oldPrices:
            # turn promo and regular to value
            oldTimestamp = mytz.localize(dt.datetime.fromtimestamp(oldPrice.get('acquistion_timestamp')/1000)).astimezone(pytz.utc)
            if oldPrice.get('promo') == oldPrice.get('regular'):
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Regular'})
            else:
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Regular'})
                newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('promo'), 'quantity': oldPrice.get('quantity'),\
                    'upc': oldPrice.get('upc'), 'utcTimestamp': oldTimestamp, "type": 'Sale'})
    

        for head, subfolders, files in walkResults:
            folder = head.split('\\')[-1]
            if folder in wantedPaths:
                for file in files:
                    if iteration == 0 :                
                        returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=[], itemCollection=[], pricesCollection=[], inventoryCollection=[], tripCollection=[], priceModifierCollection=[], userCollection=[], sellerCollection=[])
                        iteration+=1
                    else:
                        returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=returnTuple[0], itemCollection=returnTuple[1], pricesCollection=returnTuple[2], inventoryCollection=returnTuple[3], tripCollection=returnTuple[4], priceModifierCollection=returnTuple[5], userCollection=returnTuple[6], sellerCollection=returnTuple[7])
                    os.makedirs(f'../data/raw/kroger/{folder}/', exist_ok=True)
                    print(f'processed {file}.')
        
        
        for i, finalCollection in enumerate(returnTuple):
            if i==2:
                finalCollection.extend(newFromOldPrices)
            insertData(finalCollection, listTranslator[str(i)])
    
        os.rename("./requests/server/collections/kroger/API/myStores.json", "../data/raw/kroger/API/myStores.json")
        os.rename('./requests/server/collections/kroger/API/combinedPrices.json', "../data/raw/kroger/API/combinedPrices.json")
    # file does not exist (clean up has happened therefore read from ../)
    else:
        # promotions (nonTime bound in db; no duplicates preferrable, filter check)
        # items (nonTime bound in db; no duplicates preferrable, filter check)
        # prices (time bound, no duplicates possible)
        # inventories (time bound, no duplicates possible)
        # trips (past transactions; not time bound; no duplicates preferrable, filter check)
            # priceModifierCollection (coupons applied a @ purchase. tied with trips. )
        # userCollection (nonTime bound in db, no duplicates preferrable, filter check)
        # sellerCollection (nonTime bound in db, no duplicates preferrable, filter check)
        promotionsCollection = retrieveData('promotions')
        itemCollection = retrieveData('items') 
        tripCollection = retrieveData('trips')
        priceModifierCollection = retrieveData('priceModifiers')
        userCollection = retrieveData('users')
        sellerCollection = retrieveData('sellers') 

        for head, subfolders, files in walkResults:         
            if head.split('\\')[-1] in wantedPaths:
                folder = head.split('\\')[-1]
                for file in files:
                    if iteration == 0:
                        returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=promotionsCollection, itemCollection=itemCollection, pricesCollection=[], inventoryCollection=[], tripCollection=tripCollection, priceModifierCollection=priceModifierCollection, userCollection=userCollection, sellerCollection=sellerCollection)
                        iteration+=1
                    else:
                        returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=returnTuple[0], itemCollection=returnTuple[1], pricesCollection=returnTuple[2], inventoryCollection=returnTuple[3], tripCollection=returnTuple[4], priceModifierCollection=returnTuple[5], userCollection=returnTuple[6], sellerCollection=returnTuple[7])
                    os.makedirs(f'../data/raw/kroger/{folder}/', exist_ok=True)
                    print(f'processed {file}.')

        for i, finalCollection in enumerate(returnTuple):
            if i!=2 and i!=3:
                currentCol = retrieveData(listTranslator[str(i)])
                if currentCol!=finalCollection:
                    insertData(finalCollection[len(currentCol):], collection_name=listTranslator[str(i)])
            else:
                insertData(finalCollection, collection_name=listTranslator[str(i)])

    if additionalPaths:
        for repo in additionalPaths:
            pathName = dataRepoPath.replace('kroger', repo)
            couponFiles = list(os.walk(pathName))
            couponFiles = couponFiles[0][2]
            for ofile in couponFiles:
                # handles insertion
                deconstructDollars(pathName+'/'+ofile)
                os.makedirs(f'../data/raw/{repo}', exist_ok=True)
                os.rename(pathName+'\\'+ofile, f'../data/raw/{repo}/{ofile}')  
                print(f'processed {ofile}.')
    
    for head, subfolders, files in os.walk(dataRepoPath):         
        if head.split('\\')[-1] in wantedPaths:
            folder = head.split('\\')[-1]
            for file in files:
                os.rename(head+'\\'+file, f'../data/raw/kroger/{folder}/{file}')
    normalizeStoreData()
    backupDatabase()
    createDBSummaries('new')

    return None

def queryDB(db="new"):
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client[db]
    #res = cursor['promotions'].aggregate(pipeline=[{"$sort": {"redemptions": -1}}, {"$unwind": "$redemptionKeys"}, {"$group": {"_id": {"x": "$redemptionKeys.upc" }, "count": {"$sum": 1}}}])
    #res = cursor['promotions'].aggregate(pipeline=[{'$match': {'popularity': {'$exists': True}}}, {'$project':  {"socials": {'clips': '$clippedCount', 'popInt': {'$divide': ['$popularity', 1000]}}, 'newValue': {'$convert': {'input': '$value', 'to':'int'}}}}, {'$sort': {'newValue': 1}}])
    #res = cursor['promotions'].aggregate(pipeline=[{'$match': {'popularity': {'$exists': False}, 'krogerCouponNumber': {'$exists':False}, 'productUpcs': {'$exists': True}}}])
    #res = cursor['promotions'].find_all({'shortDescription': {'$regex': '/^Buy 5.+/'}})
    res = cursor['inventories'].find({'stockLevel': 'out_of_stock'})
    #res = cursor['inventories'].aggregate(pipeline=[{'$group': {'_id': '$stockLevel', 'count': {'$sum': 1}}}])
    res = [x for x in res]
    pprint(res)

    return None

def getCollectionFeatureCounts(db='new', collection='prices'):
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

    return None

def getCollectionFeatureTypes(db='new', collection='items', feature='upc'):
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient()
    cursor = client[db]
    res = cursor[collection].aggregate(pipeline=[
        {'$project': {'upc': f'${feature}', 'type': {'$type' : f'${feature}'}}},
        {'$group': {'_id': '$type', 'count': {'$sum': 1}}},
        {'$sort': {'_id': -1}}
    ])
    res = [x for x in res]
    
    pprint(res[:55])
    # print(set(map(lambda x: x['_id'], res)))

    return None


def getStores():
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    cursor = client['new']
    res = cursor['stores'].find({})
    res = [r for r in res]
    pprint(res[0])
    return None

# queryDB()

# getCollectionFeatureCounts(collection='prices')
# getCollectionFeatureCounts(collection='inventories')
# getCollectionFeatureCounts(collection='items')


# getCollectionFeatureTypes(collection='inventories', feature='availableToSell')
# setUpBrowser()
# runAndDocument([getScrollingData], ['getFoodDepotItems'], chain='fooddepot')
# retrieveData('runs')

# runAndDocument([setUpBrowser, getScrollingData, eatThisPage], ["setUpBrowserForAldi", 'getAldiItems', 'flushData'],
# kwargs=[{"n": 'aldi-items', 'initialSetup': True}, {"chain": "aldi"}, {'reset': False}])

# runAndDocument([setUpBrowser, simulateUser, eatThisPage], ["setUpBrowserForKroger", 'getKrogerDigitalCouponsAndItems', 'flushData'],
# kwargs=[{"url": "https://www.kroger.com/savings/cl/coupons", "n": 'kroger-coupons', 'initialSetup': True}, {"link": "digital"}, {'reset': False}])

# runAndDocument([setUpBrowser, simulateUser, eatThisPage], ["setUpBrowserForKroger", 'getKrogerCashbackCouponsAndItems', 'flushData'],
# kwargs=[{"url": "https://www.kroger.com/savings/cbk/cashback/", "n": 'kroger-coupons', 'initialSetup': True}, {"link": "cashback"}, {'reset': False}])

# runAndDocument([setUpBrowser, simulateUser, eatThisPage], ['setUpBrowser', 'getDollarGeneralCouponsAndItems', 'flushData'],
# kwargs=[{"n": 'dollar-general-coupons', 'initialSetup': True},{"link": "dollarGeneral"}, {'reset': False}])


# runAndDocument([simulateUser, eatThisPage], ['getDollarGeneralCouponsAndItems', 'flushData'],
# kwargs=[{"link": "dollarGeneral"}, {'reset': False}])

# runAndDocument([setUpBrowser, getFamilyDollarItems, eatThisPage],
# ['setup', 'getFamilyDollarItems', 'flushData'] ,[{'n': 'family-dollar-items', 'initialSetup': True}, {}, {'reset': False}])

# runAndDocument([setUpBrowser, eatThisPage], ['setup', 'getFamilyDollarCoupons'], [{'n': 'family-dollar-coupons', 'initialSetup': True}, {'reset': False}])

# deconstructExtensions('./requests/server/collections/digital/digital050322.json', sample)
# runAndDocument([setUpBrowser, getScrollingData, eatThisPage], ['setup', 'getFoodDepotItems', 'flushData'], [{'n': 'food-depot-items', 'initialSetup': True}, {'chain': 'fooddepot'}, {'reset': False}])
# runAndDocument([setUpBrowser, getStoreData, eatThisPage], ['setup', 'getStores', 'flushData'], [{'n': None, 'initialSetup': True}, {'chain': 'aldi'}, {'reset':False}])
# createDecompositions('./requests/server/collections/kroger', wantedPaths=['digital', 'trips', 'cashback', 'buy5save1'], additionalPaths=['dollargeneral', 'familydollar/coupons'])
    
# normalizeStoreData()
backupDatabase()
createDBSummaries('new')