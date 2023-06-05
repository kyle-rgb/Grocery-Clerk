import json, re, os, datetime as dt, time
from pprint import pprint
from pymongo import MongoClient
import pytz

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

def deconstructKrogerFile(filename):
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
        
        if 'trips' in filename:
            startingArray = list(filter(lambda x: type(x)==dict and "data" in x, startingArray))
            startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=True)
        else:
            startingArray = sorted(startingArray, key=lambda x: x['url'], reverse=False)
        couponDict={}
        promotionsCollection = []
        itemCollection = []
        pricesCollection = []
        inventoryCollection = []
        tripCollection = []
        priceModifierCollection = []
        userCollection = []
        sellerCollection = []
        forGeneralItems={}
        connectionErrors = []
        print("MAXTZ:", max(list(map(lambda x: x["acquisition_timestamp"], startingArray))))
        print("MINTZ:", min(list(map(lambda x: x["acquisition_timestamp"], startingArray))))
        for apiCall in startingArray:
            url = apiCall.pop('url')
            acquistionTimestamp = mytz.localize(dt.datetime.fromtimestamp(apiCall.pop('acquisition_timestamp')/1000))
            data = apiCall.get('data')
            if re.match(upcsRegex, url):
                couponId = re.match(upcsRegex, url).group(1)
                couponDict[couponId] = data
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
                    hasNewPromotion = list(filter(lambda x: x.get('krogerCouponNumber')==allOffers.get('couponNumber'), promotionsCollection))
                if len(hasNewPromotion)==0 and type(allOffers)==dict:
                    newPromotion = {}
                    newPromotion['value'] = allOffers.get('couponAmount')
                    newPromotion['krogerCouponNumber'] = allOffers.get('couponNumber')
                    startDate = allOffers.get('effectiveDate') + "T00:00:00"
                    startDate = mytz.localize(dt.datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    newPromotion['startDate'] = startDate
                    expirationDate = allOffers.get('expirationDate') + "T11:59:59"
                    expirationDate = mytz.localize(dt.datetime.strptime(expirationDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    newPromotion['expirationDate'] = expirationDate
                    newPromotion['type'] = allOffers.get('rewardTypeDescription')
                    newPromotion['requirementQuantity'] = allOffers.get('totalPurchaseQty')
                    newPromotion['shortDescription'] = allOffers.get('webDescription')
                    newPromotion['productUpcs'] = list(allUpcs)
                    newPromotion['redemptionsAllowed'] = -1
                    promotionsCollection.append(newPromotion)
                elif len(hasNewPromotion)>0:
                    hasNewPromotion[0]['productUpcs'].extend(list(allUpcs))
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
                    if k in couponDict:
                        v.update({'productUpcs': couponDict[k]})
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
            elif re.match(tripRegex, url):
                data = updateGasoline(data=data)
                removalTrip = ['address', 'returns', 'barcode', 'purchaseHistoryID', 'priceModifiers', 'coupon', 'source', 'version', 'transactionTime']
                removalAggregations = ['tipAmounts', 'totalSavings', 'tenderChanges', 'total', 'subtotal', 'totalTax', 'grossAmount', 'totalTender', 'totalLineItems', 'totalTenderChange']
                tripKeep = {'loyaltyId', 'assocaiteId', 'transactionTimeWithTimezone', 'fulfillmentType', 'tax', 'total', 'totalSavings', 'subtotal',\
                'tenders', 'items', 'receiptId'}
                itemKeep = {'isFuel', 'isGiftCard', 'isPharmacy', 'isWeighted', 'barCodes', 'monetizationId'}
                for trip in data:
                    tripDocument = {}
                    transactionId = trip.get('receiptId').get('transactionId')
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
                                        
                                        userCollection.append({'userId': value.get('userId'), 'loyaltyId': trip.get('loyaltyId'), 'trips': [value.get('transactionId')]})
                                    else:
                                        try:
                                            user = list(filter(lambda u: u.get('loyaltyId')==trip.get('loyaltyId'), userCollection))[0]
                                        except IndexError:
                                            user = userCollection[0]
                                        if transactionId not in user.get('trips'):
                                            user['trips'].append(transactionId)
                                elif key=='items':
                                    currentPMs = set(map(lambda x: x.get('promotionId'), priceModifierCollection))
                                    for item in value:
                                        if item.get('itemType')!='STORE_COUPON':
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
                                            if item.get('extendedPrice')==item.get('pricePaid'):
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})
                                            else:
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})
                                                value = round(item.get('pricePaid') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': purchaseTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Sale', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber'),
                                                'offerIds': ','.join(list(map(lambda pm: pm.get('promotionId'), item.get('priceModifiers'))))})
                                            if item.get('isWeighted'):
                                                averageWgt = item.get('detail').get('averageWeight') or 1
                                                pricesCollection.append({'value': item.get('unitPrice'), 'quantity': averageWgt, 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': False, 'transactionId': transactionId,
                                                'type': 'Average', 'locationId': trip.get('receiptId').get('divisionNumber')+trip.get('receiptId').get('storeNumber')})
                                            for booleanCategory in itemKeep:
                                                if bool(item.get(booleanCategory)):
                                                    forGeneralItems.setdefault(item.get('baseUpc'), {})
                                                    if type(item.get(booleanCategory))==bool:
                                                        forGeneralItems[item.get('baseUpc')] = {booleanCategory: item.get(booleanCategory)}
                                                    elif type(item.get(booleanCategory))==str: 
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
            elif re.match(productsRegex, url): 
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
                        itemDoc = p.get('item')
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
                        if sources!=None:
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
    print(os.environ)
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client[db]
    res = db[collection_name].insert_many(entries)
    res = len(res.inserted_ids)
    print(f"Inserted {res} documents in {collection_name}")
    client.close()

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
    entriesForDb = filter(lambda x: x[uuid] not in currentIds, entries)
    entriesForDb = [x for x in entriesForDb]
    if len(entriesForDb)==0:
        print("no values to place into {}".format(collection_name))
    else:
        res = db[collection_name].insert_many(entriesForDb).inserted_ids
        print(f"Inserted {len(res)} documents in {collection_name}")
     
    print(f"ended in {time.perf_counter()-start} seconds")
