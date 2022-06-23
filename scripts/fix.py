from functools import reduce
import json, re, os, unicodedata, itertools, sys, time, pytz, datetime as dt
from pprint import pprint
from make_dataset import deconstructDollars

startTime = time.perf_counter()
# find position where streaming data overlaps in early collected data 
def fixData():
    with open('./requests/server/collections/toFix/aprilTrips.txt', 'r', encoding="utf-8") as file:
        myString = file.read()

    for j in range(100_000):
        try:
            json.loads(myString)
            break
        except json.decoder.JSONDecodeError as jError:
            print(jError.colno)
            newString = myString[:jError.colno-2] + myString[jError.colno-1:]
            myString = newString


    with open("./requests/server/collections/toFix/aprilTrips.json", "w", encoding="utf-8") as z:
        z.write(json.dumps(myString))

# remove customer data 
def destroyIDs(dataFile):
    with open(dataFile, 'r', encoding="utf-8") as file:
        myString = file.read()
        jj = json.loads(myString)
        for entry in jj:
            if 'data' in entry:
                data = entry['data']
                if isinstance(data, list):
                    data = data[-1]
                    if 'tenders' in data:
                        data['tenders'][0]['emv'] = {}
                        data['tenders'][0]['referenceCode'] = ""
                    if 'purchaseHistoryID' in data:
                        data['purchaseHistoryID'] = ''
                    if 'loyaltyId' in data:
                        data['loyaltyId'] = ''

    filename = 'parsed' + dataFile.split('/')[-1]
    filename = "/".join(dataFile.split('/')[:-1] + [filename])
    with open(filename, 'w', encoding="utf-8") as file:
        file.write(json.dumps(jj))
        

    return None

# fix attempt for crossed streaming data
def partitionString(string, openChar, closeChar, index=0):
    CHAR_IDs = {"{": {"close": "}", "type": "object"}, "[": {"close":"]", "type": "array"}, "\"": {"type": "string", "close":"\""}}
    arr = []
    string = string[index:]
    for i, signifier in enumerate(string):
        startingIndex = i + index
        nextSign = string[i+1]
        if signifier==openChar:
            arr.append([signifier, i+index, len(string)])
            nextIndex = i + 1
            while nextSign != closeChar:
                print(nextIndex, len(string)-1)
                nextSign = string[nextIndex]
                if nextSign in CHAR_IDs.keys():
                    return partitionString(string, nextSign, CHAR_IDs[nextSign]['close'], index=nextIndex)
                nextIndex+=1
        else:
            next
                
    print(arr)

# force close dirty JSONs 
def forceClose(dataFile, streams=True):
    # identifys loose objects involuntarily inserted into streams via early pulls
    with open(dataFile, 'r', encoding="utf-8") as file:
        myString = file.read()
        myString = myString.replace("\x18", "")
        myString = myString.replace("\x19", "")
        myString = myString.replace("\x13", "")
        myString = myString.replace("\x14", "")
        myString = myString.replace("\x02", "")
        myString = myString.replace("\x10", "")
        myString = myString.replace("\x11", "")
        myString = myString.replace("\x1c", "")
        myString = myString.replace("\x1e", "")
        myString = myString.replace("\x1d", "")
        myString = myString.replace("\x0b", "")
        myString = myString.replace("\x0f", "")
        myString = myString.replace("\xae", "")

    regFive = re.compile(r"(?=:\{?\[?\")(:\")(.*?)(?=\"[\}\],\{\[]+\"[A-z])")
    regxFour = re.compile(r"(?=\:\")(\:\")([^\\\"]+)(\")(?!\"[\}\]\s\,])([^\:\}\]]+\,)") # (?=:")(:")([^\\"]+)(")(?!"[\}\]\s,])([^:\}\]]+,)
    regTwo = re.compile(r"((\{\s*|\"success\"\s*:\s*true,)\s*\"data\")")
    regURL = re.compile(r'(\|[^\s\|:]+:)+') # make sure resulting object is not encased in a string, no spaces perhaps?
    regxFourImp = re.compile(r"(?=:\")(:\")([^\\\"]+)(\")(?!\"[\}\]\s,])([^:\}\]]+(,|\}|\]))")
    regThree = re.compile(r"(\"\w+\":)")

    urlsAndObjects = re.split(regURL, myString)
    urls = list(filter(lambda x: re.match(regURL, x), urlsAndObjects))
    objects = list(filter(lambda x: ((x!='')and(re.match(regURL, x))==None), urlsAndObjects))
    filteredObjects = []

    print("URLS:", len(urls), "OBJECTS:", len(objects))
    if streams:
        for i, o in enumerate(objects):
            completeObjectRegex = re.compile(r"(,\s)(?=\{\"(data|success)\")") # check to see if object is complete and duplicated
            brokenObjectRegex = re.compile(r"(?<!,\s)(\{\"(data|success)\")")
            completeObjects = re.split(completeObjectRegex, o)

            if len(completeObjects)==1:
                # object broken by stream, we know that the stream breakpoint is the start of the original string
                # search nonsplit string for its beginning, get both the span to find break location
                # object is closed successfully, so get ending and search the stream breaker for the ending location
                # append broken first half with broken second helf compare objects equality and add single object
                startOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', o[:500])
                endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', o[-500:])
                starts = [x.span() for x in re.finditer(startOfStream, o)]
                ends = [x.span() for x in re.finditer(endOfStream, o)]
                #print(o[ends[0][1]:ends[0][1]+100])
                if len(starts)!=2 or len(ends)!=2:
                    print(starts, ends)
                    raise re.error('indicators contain an unescaped general character')
                
                cutoff = o[:starts[1][0]]
                s1 = o[starts[0][0]:starts[1][0]] + o[ends[0][1]+1:] 
                s2 = o[starts[1][0]:ends[0][1]]
                a = max([s1, s2], key=len)
                b = o[starts[0][0]:starts[1][0]]#min([s1, s2], key=len)
                
                newString = ''
                lastStart = 0
                for group in re.finditer(regFive, a):
                    groupMatches = group.groups()
                    if '"' in groupMatches[1]:
                        start, stop = group.span()
                        data = re.sub(r'(?<![\\])"', " ",groupMatches[1])
                        newString = newString + a[lastStart:start] + groupMatches[0] + data
                        lastStart = stop
                    else:
                        start, stop = group.span()
                        newString = newString + a[lastStart:stop] 
                        lastStart = stop
                newString = newString + a[lastStart:]
                try:
                    filteredObjects.append(json.loads(newString))
                    
                except json.decoder.JSONDecodeError as e:

                    if e.pos == len(newString)-1:
                        try:
                            print(e)
                            print(newString[-200:])
                            print(newString[:200])
                            json.loads(newString)

                        except json.decoder.JSONDecodeError as je:
                            print(je)
                            with open('g.json', 'w', encoding='utf-8') as h:
                                h.write(newString)
                            
                    else:
                        msg = e.args[0]
                        charAt = e.pos
                        
                        endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', newString[e.pos:e.pos+1000])
                        mat = [x.span() for x in re.finditer(endOfStream, newString[:e.pos])]
                        eos = newString[e.pos:e.pos+1000] 
                        eos = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', eos)
                        mat = [x.span() for x in re.finditer(eos, newString)]
                        returnal = b[-100:] + newString[mat[0][0]:mat[0][1]]
                        unstreamed = newString[mat[1][0]-100:mat[1][1]]
                        n=1
                        while returnal not in unstreamed:
                            returnal = b[-100+n:] + newString[charAt-n:][:100]
                            n +=1
                            if n > 50:
                                break
                        
                        if n == 51:
                            file = dataFile.replace('.txt', '')
                            file = file.replace('./requests/server/collections/toFix/', '')
                            with open(f'./requests/server/collections/toFix/fixes/{file}ToFix.txt', 'w', encoding='utf-8') as f:
                                f.write(f"<NEWSTRING{i}>")
                                f.write(newString[:charAt])
                                f.write(f"<ORIG_OBJECT{i}>")
                                f.write(cutoff)
                                f.write(f"<S1{i}>")
                                f.write(s1)
                                f.write(f"<S2{i}>")
                                f.write(s2)
                                f.write('<END_OF_STRING>')
                        else:
                            try:
                                n-=1
                                secondTry = b + newString[charAt-n:]
                                json.loads(secondTry)
                                print('passed 2')
                            except json.decoder.JSONDecodeError as e2:
                                print(e2)
                                print(f"{secondTry[e2.pos-500:e2.pos]}" + f"<<<<<{secondTry[e2.pos]}>>>>>",  f"{secondTry[e2.pos+1:e2.pos+500]}" )
                                
                        
                        
                        
                        #print([(newString[x[0]-100:x[0]], f"<<{newString[x[0]:x[1]]}>>", newString[x[1]:x[1]+100]) for x in mat])
                    
                        # while mat == []:
                        #     charAt-= 1
                        #     eos = b[-100:] + newString[charAt:charAt+100]
                        #     print(eos)
                        #     eos = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', eos)
                        #     mat = [x.span() for x in re.finditer(eos, newString[:e.pos])]
                            
                        # print(mat)
                        # returningString = newString[e.pos+1:e.pos+500]
                        # startOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', returningString)
                        # # print([x.span() for x in re.finditer(startOfStream, newString[charAt:])])
                        # endOfStream = re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1', b[-500:])
                        # matches = [x.span() for x in re.finditer(endOfStream, newString)]
                        # matches = [re.sub(r'([\"\{\}\[\]\(\).$])', r'\\\1',newString[x[1]:x[1]+500])for x in matches]
                        # matches = [x.span() for x in re.finditer(matches[0], newString)]
                        #print("\n", matches)
                print('#'*50, f'object {i}', f'length: {len(o)}', '#'*50)
                print('\n')

            else:
                try:
                    filteredObjects.append(json.loads(completeObjects[0]))
                except json.decoder.JSONDecodeError as e2:
                    secondTry = completeObjects[0]
                    lastStart = 0
                    newString = ''
                    for group in re.finditer(regFive, secondTry):
                        groupMatches = group.groups()
                        if '"' in groupMatches[1]:
                            start, stop = group.span()
                            data = re.sub(r'(?<![\\])"', " ",groupMatches[1])
                            newString = newString + secondTry[lastStart:start] + groupMatches[0] + data
                            lastStart = stop
                        else:
                            start, stop = group.span()
                            newString = newString + secondTry[lastStart:stop] 
                            lastStart = stop
                    newString = newString + secondTry[lastStart:]
                    try:
                        filteredObjects.append(json.loads(newString))
                    except json.decoder.JSONDecodeError as e3:
                        print(i, e3)
    else:
        a = objects[0]
        print(a[3069842-50:3069842])
        newString = ''
        lastStart = 0
        for group in re.finditer(regFive, a):
            groupMatches = group.groups()
            if '"' in groupMatches[1]:
                print(groupMatches[1])
                start, stop = group.span()
                data = re.sub(r'(?<![\\])"', " ",groupMatches[1])
                newString = newString + a[lastStart:start] + groupMatches[0] + data
                lastStart = stop
            else:
                start, stop = group.span()
                newString = newString + a[lastStart:stop] 
                lastStart = stop
        newString = newString + a[lastStart:]
        try:
            filteredObjects = json.loads(newString)
        except json.decoder.JSONDecodeError as e:
            with open('./d.txt', 'w', encoding='unicode_escape') as d:
                d.write(newString)
            print(newString[e.colno-10:e.colno+10])


    newFile = dataFile.split("/")
    fileName = newFile[-1].replace('.txt', '.json')
    newFile = "/".join(newFile[:-1]+[fileName])
    with open(newFile, 'w', encoding='utf-8') as final:
        final.write(json.dumps(filteredObjects))

        # else: 
        #     # print(completeObjects[0]==completeObjects[-1])
    # for i, o in enumerate(objects):
    #     # Stream writes in 3 ways:
    #         # writing of object attributes are cut off by a repeat call
    #         # An Object's stream exhausts mid-parameter, causing parms to be cut off.
    #         # the intercepting object can also be cut off mid paramter by the starting streams return.   
    #     try:
    #         # 1st: see if the stream was written in one buffer
    #         filteredObjects.append(json.loads(o))
        
    #     except json.decoder.JSONDecodeError as error:
    #         print(error)
    #         msg = error.args[0]
    #         charAt = int(re.findall(r'char (\d+)', msg)[0])
    #         looseObjs = []
    #         looseObjs.append(o[:charAt])
    #         if msg.startswith("Extra"):
    #             try:
    #                 firstData = json.loads(o[:charAt])
    #                 secondData = json.loads(o[charAt+2:])
    #                 if firstData==secondData:
    #                     firstData['url'] = urls[i]
    #                     filteredObjects.append(firstData)
    #             except json.decoder.JSONDecodeError as error2:
    #                 msg = error2.args[0]
    #                 charAt = int(re.findall(r'char (\d+)', msg)[0])
    #         elif 'Invalid control' in msg:
    #             print(msg, charAt)
    #             try:
    #                 controlObject = o[:charAt] + o[charAt+1:]
    #                 filteredObjects.append(json.loads(controlObject))

    #             except json.decoder.JSONDecodeError as errorControl:
                    
    #                 msg = errorControl.args[0]
    #                 charAt = int(re.findall(r'char (\d+)', msg)[0])
    #                 print(errorControl, charAt)
    #                 print(controlObject[charAt-10:charAt] + f"<<<{controlObject[charAt]}>>>" + controlObject[charAt+1:charAt+10])

            
    #         else:
    #             # expecting ',' delimiter: line 1 column n+1 (char n)
    #             # case: stream interupts object with url indicator with the entire combined string from the api
    #             # solution: get the object with the greater length and check to see if it has the call url parameter inside, if not pop it from interupted object and place in full object
    #             print(msg)
    #             print(o[charAt-15:charAt], f"<<<<{o[charAt]}>>>>", o[charAt+1:charAt+15])
    #             while o[charAt]!="\"": # use "{" for broken streams and "\""
    #                 if o[charAt]=='{':
    #                     break
    #                 charAt-=1
    #             try:
    #                 print(o[charAt-15:charAt], f"<<<<{o[charAt]}>>>>", o[charAt+1:charAt+15])
    #                 stringObj = o[charAt:]
    #                 fullObject = json.loads(stringObj)
    #             except json.decoder.JSONDecodeError as er:
    #                 msg = er.args[0]
    #                 charStreamReturn = int(re.findall(r'char (\d+)', msg)[0])
    #                 print(msg)
    #                 print(o[charAt:][charStreamReturn-15:charStreamReturn], f"<<<<{o[charAt:][charStreamReturn]}>>>>", o[charAt:][charStreamReturn+1:charStreamReturn+15])
    #                 try:
    #                     nextObject = json.loads(stringObj[:charStreamReturn])
    #                     nextObject['url'] = urls[i]
    #                     filteredObjects.append(nextObject)

    #                 except json.decoder.JSONDecodeError as er2:
    #                     try:
    #                         print(msg2)   
    #                         msg2 = er2.args[0]
    #                         offendingString = int(re.findall(r'char (\d+)', msg)[0])
    #                         endOfObject = o[-100:]
    #                         closer = stringObj[offendingString:].index(endOfObject)
    #                         secondHalf = stringObj[offendingString-2:][:closer+len(endOfObject)+2]
    #                         fullObject = looseObjs[-1] + secondHalf
    #                         finalForm = json.loads(fullObject)
    #                         finalForm['url'] = urls[i]
    #                         filteredObjects.append(finalForm)
    #                     except:
    #                         msg = er2.args[0]
    #                         offendingString = int(re.findall(r'char (\d+)', msg)[0])
    #                         print(fullObject[offendingString], repr(fullObject[offendingString]), ord(fullObject[offendingString]))
    #                         raise ValueError

    #     print(f'@{i}. FilteredObjects = {len(filteredObjects)} . {type(filteredObjects[-1])}')


    # with open(dataFile.replace("txt", "json"), "w") as jfile:
    #     jfile.write(json.dumps(filteredObjects))
    
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

# Deconstruct Extension Created Files into Final Collections
def deconstructExtensions(filename, **madeCollections):
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
            # static: 

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
        except TypeError:
            print(start)
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
            acquistionTimestamp = apiCall.pop('acquisition_timestamp')
            data = apiCall.get('data')
            # match promotions to product upcs
            if re.match(upcsRegex, url):
                couponId = re.match(upcsRegex, url).group(1)
                cDict[couponId] = data
            elif re.match(specialPromoRegex, url):
                allUpcs = set()
                allOffers = set()
                qualifiers = api.get('products')
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
                    startDate = pytz.timezone('America/New_York').localize(dt.datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    startDate = dt.datetime.strftime(startDate, "%Y-%m-%dT%H:%M:%S")
                    newPromotion['startDate'] = startDate
                    # expirationDate => expirationDate + T11:59:59Z
                    expirationDate = allOffers.get('expirationDate') + "T11:59:59"
                    expirationDate = pytz.timezone('America/New_York').localize(dt.datetime.strptime(startDate, "%Y-%m-%dT%H:%M:%S")).astimezone(pytz.timezone('UTC'))
                    expirationDate = dt.datetime.strftime(expirationDate, "%Y-%m-%dT%H:%M:%S")
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
                                promo['startDate'] = coupVal
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
                                                        matchingObjs = list(filter(lambda x: x.get('upc')==item.get('upc'), existingPm.get('redemptionKeys')))
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
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular'})
                                            else:
                                                value = round(item.get('extendedPrice') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Regular'})
                                                value = round(item.get('pricePaid') / item.get('quantity'), 2)
                                                pricesCollection.append({'value': value, 'quantity': item.get('quantity'), 'utcTimestamp': acquistionTimestamp, 'upc': item.get('baseUpc'), 'isPurchase': True, 'transactionId': transactionId, 'type': 'Sale',
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
                                    tripDocument['utcTimestamp'] = value
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
                                    priceData['effectiveDate'] = prices.get('effectiveDate').get('value')
                                    priceData['expirationDate'] = prices.get('expirationDate').get('value')
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
        

def createDecompositions(dataRepoPath: str, wantedPaths: list, additionalPaths: dict):
    # add stores via api and previously scraped prices to new price collection schema

    with open('data/API/myStoresAPI.json', 'r', encoding='utf-8') as storeFile:
        stores = json.loads(storeFile.read())

    if not os.path.exists('../data/stores/collection.json'):
        os.mkdir("../data/stores/")
        with open('../data/stores/collection.json', 'w', encoding='utf-8') as storeFile:
            storeFile.write(json.dumps(stores))

    with open('data/collections/combinedPrices.json', 'r', encoding='utf-8') as priceFile:
        oldPrices = json.loads(priceFile.read())
        oldPrices = list(filter(lambda y: y.get('isPurchase')==False, oldPrices)) # trip price data will already have been recorded


    newFromOldPrices = []
    for oldPrice in oldPrices:
        # turn promo and regular to value
        if oldPrice.get('promo') == oldPrice.get('regular'):
            newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                'upc': oldPrice.get('upc'), 'utcTimestamp': oldPrice.get('acquistion_timestamp'), "type": 'Regular'})
        else:
            newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('regular'), 'quantity': oldPrice.get('quantity'),\
                'upc': oldPrice.get('upc'), 'utcTimestamp': oldPrice.get('acquistion_timestamp'), "type": 'Regular'})
            newFromOldPrices.append({'locationId': oldPrice.get('locationId'), 'isPurchase': oldPrice.get('isPurchase'), 'value': oldPrice.get('promo'), 'quantity': oldPrice.get('quantity'),\
                'upc': oldPrice.get('upc'), 'utcTimestamp': oldPrice.get('acquistion_timestamp'), "type": 'Sale'})

    iteration=0
    for head, subfolders, files in os.walk(dataRepoPath):
        if head.split('\\')[-1] in wantedPaths:
            for file in files:
                if iteration == 0 :                    
                    returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=[], itemCollection=[], pricesCollection=[], inventoryCollection=[], tripCollection=[], priceModifierCollection=[], userCollection=[], sellerCollection=[])
                    iteration+=1
                else:
                    returnTuple = deconstructExtensions(head+"\\"+file, promotionsCollection=returnTuple[0], itemCollection=returnTuple[1], pricesCollection=returnTuple[2], inventoryCollection=returnTuple[3], tripCollection=returnTuple[4], priceModifierCollection=returnTuple[5], userCollection=returnTuple[6], sellerCollection=returnTuple[7])
                print(f'processed {file}.')
    
    listTranslater={"0": "promotions", "1": "items", "2": "prices", "3": "inventories", "4":"trips", "5":"priceModifiers", "6":"users", "7":"sellers"}
    for i, finalCollection in enumerate(returnTuple):
        if not os.path.exists('../data/'):
            os.mkdir("../data/")
    
        if not os.path.exists(os.path.join("..", "data", listTranslater[str(i)])):
            os.mkdir(os.path.join("..", "data", listTranslater[str(i)]))
        else:
            with open(os.path.join("..", "data", listTranslater[str(i)], "collection.json"), "r", encoding='utf-8') as prevFile:
                oldCollection = json.loads(prevFile.read())
                finalCollection.extend(oldCollection)
        

        with open(os.path.join("..", "data", listTranslater[str(i)], "collection.json"), "w", encoding="utf-8") as file:
            if i==2:
                finalCollection.extend(newFromOldPrices)
            size = sys.getsizeof(finalCollection)
            file.write(json.dumps(finalCollection))
            print(f"Wrote {size} to Disk. {len(finalCollection)} items in {listTranslater[str(i)]}")

    for repo in additionalPaths:
        pathName = dataRepoPath.replace('kroger', repo)
        couponFiles = list(os.walk(pathName))
        couponFiles = couponFiles[0][2]
        for ofile in couponFiles:
            deconstructDollars(pathName+'/'+ofile)
    
    return None

# provideSummary('./requests/server/collections/trips/trips052822.json')
createDecompositions('./requests/server/collections/kroger', wantedPaths=['trips', 'digital', 'cashback'], additionalPaths=['familydollar', 'dollargeneral'])
#deconstructExtensions('./requests/server/collections/digital/digital050322.json', sample)
# summarizeCollection('./requests/server/collections/recipes/recipes.json')
# forceClose("./requests/server/collections/digital/digital42822.txt", streams=False)
# destroyIDs("./requests/server/collections/trips/trips052122.json")
#partitionString('{"type": "boose", "cost": 129.99, "tax": 23.22, "devices": ["soundbar", "voice remote", "smart alexa"], "customerInfo": {"address": "4501 Brekley Ridge", "zipCode": "75921", "repeat": true, "_id": {"oid": 2391312084123, "REF": 129031923}}}',
#openChar="{", closeChar="}")


print(f"Finsihed in {time.perf_counter()-startTime} seconds")