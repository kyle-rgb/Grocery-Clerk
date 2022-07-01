
from pprint import pprint
import time, re, random, datetime as dt, os, json, urllib, pytz
import pyautogui as pag

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid
import pyperclip as clip

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

def insertData(entries, collection_name, db='new'):
    # Going to add Entries to Locally running DB w/ same structure as Container application
    # Then migrate them over to Container DB
    # Wrapper to always use insert many
    if type(entries) != list:
        entries = [entries]
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]

    if collection_name not in db.list_collection_names():
        e = sys.exec_info()[0]
        d = ', '.join(db.list_collection_names())
        raise CollectionInvalid(f'Collection {collection_name} does not exist. Valid Names in {db} are {d}')
    else:
        res = db[collection_name].insert_many(entries)
        res = len(res.inserted_ids)
        print(f"Inserted {res} documents in {collection_name}")
    client.close()

    return None


# document scraping functions via a description and function calls
# Place into Runs Collections
# Admin DB to Track and Monitor the Execution of Scraping Functions that Work on Different Schedules BAased on Store's Internal Promotion Schedule
# TODO: Add CPU/resource usage for processes related to the functions (browser/Python Application, Mongo Create Operations) 
def runAndDocument(funcs:list, callNames:list, **kwargs):
    data = []
    for name, func in zip(callNames, funcs):
        if callable(func):
            start = time.perf_counter()
            func(**kwargs)
            end = round(time.perf_counter() - start, 4)
            funcName = [k for k, v in globals().items() if v==func]
            data.append({'function': funcName, 'time': end, 'description': name})

    insertData(data, 'runs')
    return None

# Trip Level Data : Collection<Items> https://www.kroger.com/mypurchases/api/v1/receipt/details https://www.kroger.com/atlas/v1/purchase-history/details
# Trip and Account Metadata and More Precise Data on the Sales  
# More Precise Item information (UPC to join to receipt), ingredients, ratings, health_info, etc. 

def simulateUser(link):
    neededLinks = {'cashback': {"no": 202, "button": "./requests/server/cashback.png", "confidenceInterval": .66, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -2008, 'initalScroll': -700},\
        'digital': {"no":354, "button": "./requests/server/signIn.png", "confidenceInterval": .6, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -2000, 'initalScroll': -800},\
            'dollarGeneral': {'no': 133, "button": "./requests/server/addToWallet.png", "confidenceInterval": .7, 'maxCarousel': 3, 'buttonColor': (0, 0, 0), 'scrollAmount': -1700 ,"moreContent": "./requests/server/loadMore.png",\
                 'initalScroll': -1650}}
    # browser up start will be setting user location, navigating to the page, and placing mouse on first object
    # from here: the code will commence
    # start at top of the screen 
    # align all items https://www.kroger.com/savings/cl/coupons/
    iterations = neededLinks[link]["no"] // 12
    iterations = iterations + 1
    if link!='dollarGeneral':
        time.sleep(3)
        pag.scroll(neededLinks[link]['initalScroll'])
        time.sleep(2)

    # find all buttons
    for i in range(iterations):
        buttons = list(pag.locateAllOnScreen(neededLinks[link]['button'], confidence=neededLinks[link]['confidenceInterval'], grayscale=False))
        buttons = [pag.center(y) for i, y in enumerate(buttons) if (abs(buttons[i].left-buttons[i-1].left) > 100) or (abs(buttons[i].top-buttons[i-1].top)>100)] # > 2
        if link=='dollarGeneral':
            buttons = list(filter(lambda x: x.x<1600, buttons))
        print(f"Located {len(buttons)} Items")
        if len(buttons)>12:
            yaxis = list(map(lambda b: b.y, buttons))
            buttons = [x for x in buttons if yaxis.count(x.y) >= neededLinks[link]['maxCarousel']  and (x.y+1 not in yaxis)]
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
                # switch to tab
                # pag.keyDown('shiftleft')
                # pag.keyDown('tab')

                pag.keyUp('ctrlleft')
                # pag.keyUp('shiftleft')
                # pag.keyUp('tab')
                time.sleep(6)
                pag.press('pagedown', 3, interval=0.5)
                # escape out of portal
                moreItems = loadMoreAppears()
                while bool(moreItems):
                    button = moreItems
                    pag.moveTo(button.x, button.y, duration=0.5)
                    pag.click()
                    time.sleep(3)
                    pag.press('pagedown', 3, interval=0.5)
                    moreItems = loadMoreAppears()
                pag.keyDown('ctrlleft')
                pag.keyDown('w')
                pag.keyUp('ctrlleft')
                pag.keyUp('w')
                time.sleep(2.5)

        if i==0 and link=='dollarGeneral':
            pag.scroll(neededLinks[link]['initalScroll'])
        else:
            pag.scroll(neededLinks[link]['scrollAmount'])
        print('finished row {}; {} to go; mouse currently @ {} :: {} seconds left'.format(i, iterations-i, pag.position(), (time.perf_counter()/(i+1))*(iterations-i)))
        time.sleep(2)

    print(f"Processed {neededLinks[link]['no']} in {time.perf_counter()} seconds")
    return None

def loadMoreAppears(png='./requests/server/moreContent.png'):
    # Evaluate if Dollar General's Promotional Page of Associated Items Has More Items
    # Returns location of button in y [419, 559] band of standard 1920 by 1080 screen 
    locations = list(pag.locateAllOnScreen(png, confidence=.6, grayscale=False))
    locations = list(map(lambda x: pag.center(x), locations))
    i = 0
    locations = list(filter(lambda x: x.y>418 and x.y<560, locations))
    if locations:
        loc = locations[i]
        x, y = loc
        color = pag.pixel(int(x), int(y))
        if color==(0, 0, 0):
            return loc
        else:
            i+=1

    return None

def deconstructDollars(file='./requests/server/collections/familydollar/digital052122FD.json'):
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

        # family dollar:
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
                # Xmdid => uuid for promotion <Integer>
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
        # <bool>: CartQuantity,                         
    storeID = file.split('/')[-2]
    newProducts=[]
    newCoupons=[]
    newPrices = []
    newInventory = []
    storeCode = ''
    booleans = {'prices': {'IsSellable': 'IN_STORE', 'IsBopisEligible': 'PICKUP', 'isShipToHome': 'SHIP'}, 'items': {'IsGenericBrand', 'IsBopisEligible', 'isShipToHome'}}
    inventoryKeys= {'1': 'TEMPORARILY_OUT_OF_STOCK', '2': "LOW", "3": 'HIGH'}
    productsForCoupons = {}

    if storeID=='dollargeneral':
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
                itemDoc = {'description': i.get('Description'), 'upc': i.get('UPC'), 'images': [{'url': i.get('image'), 'perspective': 'front', 'main': True, 'size': 'xlarge'}],\
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
                    newC['startDate'] = dt.datetime.strptime(coup.get('OfferActivationDate'), '%Y-%m-%dT%H:%M:%S').timestamp()
                    newC['expirationDate'] = dt.datetime.strptime(coup.get('OfferExpirationDate'), '%Y-%m-%dT%H:%M:%S').timestamp()
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
                    
                    joinID = coup.get('CouponID')
                    if joinID in productsForCoupons.keys():
                        newC['productUpcs'] = list(productsForCoupons.get(joinID))
                    
                    newCoupons.append(newC)
                
    # !!! Family Dollar -> currently deconstructs into promotions collections (promotions are separated from their assoicated items, though items are still catalogued)
    elif storeID == 'familydollar':
        with open(file, 'r', encoding='utf-8') as fd:
            data = json.loads(fd.read())
            if type(data[0])==dict:
                coupons = data[0].get('data')
            else:
                coupons = data[0]
        for coup in coupons:
            newC = {}
            # mid => id
            newC['id'] = coup.get('mid')
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
            newC['startDate'] = dt.datetime.strptime(coup.get('redemptionStartDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
            newC['expirationDate'] = dt.datetime.strptime(coup.get('expirationDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
            # clipStartDateTime %Y-%m-%dT%H:%M:%S
            # clipEndDateTime
            newC['clipStartDate'] = dt.datetime.strptime(coup.get('clipStartDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
            newC['clipEndDate'] = dt.datetime.strptime(coup.get('clipEndDateTime').get('iso'), '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
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

def switchUrl(x=468, y=63, url="https://www.dollargeneral.com/dgpickup/deals/coupons?"):
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

def updateGasoline(files=['062222.json']):
    # cleaner function for Kroger trip data
    # Kroger Fuel Points (previously in price modifiers) now show up as duplicate entry of gasoline with a quantity of zero and a negative price paid to correspond to savings
    # Must be run before deconstructions.  
    for file in files:
        with open(f'./requests/server/collections/kroger/trips/{file}', mode='r', encoding='utf-8') as f:
            j = json.loads(f.read())
            tripsData = []
            indices = '' 
            for gi, t in enumerate(j):
                if 'mypurchases' in t.get('url'):
                    for trip_index, trip in enumerate(t.get('data')):
                        for item_index, item in enumerate(trip.get('items')):
                            if item.get('quantity')==0:
                                indices = gi, trip_index, item_index

           
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['pricePaid'] = round(j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['pricePaid']+j[indices[0]]['data'][indices[1]]['items'][indices[2]]['pricePaid'], 2)
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['totalSavings'] = round(j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['totalSavings']+j[indices[0]]['data'][indices[1]]['items'][indices[2]]['totalSavings'], 2)
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['priceModifiers'].extend(j[indices[0]]['data'][indices[1]]['items'][indices[2]]['priceModifiers'])
            j[indices[0]]['data'][indices[1]]['items'].pop(indices[2])
        with open(f'./requests/server/collections/kroger/trips/{file}', mode='w', encoding='utf-8') as f:
            f.write(json.dumps(j))

    return None

def getArrow(sleep=2):
    # Pagination Helper For Family Dollar Items / Prices Collection
    time.sleep(sleep)
    pag.moveTo(1559, 302)
    time.sleep(sleep)
    pag.click() 
    return None

def scrollDown(sleep=10):
    # Helper for scrolling data with api calls linked to pagination (food depot, aldi, publix)
    time.sleep(sleep)
    pag.press('end')
    return None


def getFamilyDollarItems(results):
    # example url : https://www.familydollar.com/categories?N=categories.1%3ADepartment%2Bcategories.2%3AHousehold&No=0&Nr=product.active:1
    # dependencies: scrollDown and getArrow
    # a function that retrieves all the items and prices from the local family dollars
    results = results // 96
    startingSleep=10
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

def getScrollingData(base_url, urls):
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

#summarizeIt()
#  publix
# runAndDocument([getScrollingData], ['getPublixInstacartData'], base_url='https://delivery.publix.com/store/publix/collections/', urls=['d1102-produce', 'd1090-dairy-eggs', 'd1106-frozen',
# 'd1089-beverages', 'd1099-snacks', 'd1095-pantry', 'd1094-meat-seafood', 'd1088-bakery', 'd1091-deli', 'd1092-household', 'd1104-canned-goods',
# 'd1100-dry-goods-pasta', 'd1097-personal-care', 'd1103-breakfast', 'd1093-international', 'd1101-babies', 'd1098-pets', 'd5626-greeting-cards',
# 'd21232-wine', 'd21231-beer', 'd3152-popular', 'd5625-floral', 'd5630-platters', 'd50450-ready-to-eat-ready-to-cook', 'd1105-new-and-interesting',
# 'd41671-storm-prep','d41622-tailgating', 'd51523-deli-grab-and-go', 'dynamic_collection-sales'])
# getPublixCouponData()
# runAndDocument([getPublixCouponData], ['getPublixCouponData'], deals=998)

# aldi
# getScrollingData(base_url="https://shop.aldi.us/store/aldi/collections/", urls = ["d295-alcohol" ,"d282-produce", "d297-dairy-eggs", "d292-snacks",
#     "d299-frozen", "d290-pantry", "d298-meat-seafood", "d294-bakery",
#     "d289-canned-goods", "d17068-aldi-finds-limited-time", "d296-beverages",
#     "d286-household", "d291-dry-goods-pasta", "d288-breakfast", "d283-deli",
#     "d293-babies", "d285-personal-care", "d284-pets",
#     "d12951-organic", "d6517-floral", "d287-international", "d18863-vegan",
#     "d13031-gluten-free", "d26015-seasonal", "dynamic_collection-sales"])

# runAndDocument([getScrollingData], ['getAldiInstacartData'], base_url="https://shop.aldi.us/store/aldi/collections/", urls = ["d295-alcohol" ,"d282-produce", "d297-dairy-eggs", "d292-snacks",
#     "d299-frozen", "d290-pantry", "d298-meat-seafood", "d294-bakery",
#     "d289-canned-goods", "d17068-aldi-finds-limited-time", "d296-beverages",
#     "d286-household", "d291-dry-goods-pasta", "d288-breakfast", "d283-deli",
#     "d293-babies", "d285-personal-care", "d284-pets",
#     "d12951-organic", "d6517-floral", "d287-international", "d18863-vegan",
#     "d13031-gluten-free", "d26015-seasonal", "dynamic_collection-sales"])

# family dollar Items
# getFamilyDollarItems(5184) 
# runAndDocument([getFamilyDollarItems], ['getFamilyDollarItems'], results=5194)

# food depot
# getScrollingData(base_url="https://shop.fooddepot.com/online/fooddepot40-douglasvillehwy5/shop/", urls = ["produce", "meatseafood", "bakery", "deli", "dairyeggs",
#     "beverages", "breakfast","cannedgoods", "drygoodspasta", "frozen",
#     "household", "international", "pantry", "personalcare", "pets", "snacks", "alcohol", "babies", "seasonal"])

# runAndDocument([getScrollingData], ['getFoodDepotItems'], base_url='https://shop.fooddepot.com/online/fooddepot40-douglasvillehwy5/shop/',
# urls=['produce', 'meatseafood','bakery', 'deli', 'beverages', 'dairyeggs', 'beverages', 'breakfast',
# 'cannedgoods', 'drygoodspasta', 'frozen', 'household', 'international', 'pantry', 'personalcare', 'pets', 'snacks', 'alcohol', 'babies', 'seasonal'])




# dollar general 
# simulateUser('dollarGeneral')
# runAndDocument([simulateUser], ['getKrogerCashbackCouponsAndItems'], link='cashback')
#addSpecialPromotion()
updateGasoline(["062922.json", "063022.json"])
#deconstructDollars()
#newOperation('./requests/server/collections/digital/dollars')
######## SCRAPING OPERATIONS # # # # # ## #  # ## # # # # # # # # #  ## # # 
# getMyData() 
# getDigitalPromotions()
# runAndDocument([simulateUser], ['getKrogerCashbackCouponsAndItems'], link='cashback')
# newOperation()
# switchUrl()