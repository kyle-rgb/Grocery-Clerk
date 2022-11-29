
from enum import unique
import re, requests, datetime, time, json, pprint, random, math, os
from urllib.parse import quote
import numpy as np
from base64 import b64encode
from bson.json_util import dumps
from pymongo import MongoClient

from api_keys import CLIENT_ID, CLIENT_SECRET, RECIPE_KEY, recipe_base_url


# helper for Kroger API. 3600 second token
def getToken():
#     curl -X POST \
#   'https://api.kroger.com/v1/connect/oauth2/token' \
#   -H 'Content-Type: application/x-www-form-urlencoded' \
#   -H 'Authorization: Basic {{base64(“CLIENT_ID:CLIENT_SECRET”)}}' \
#   -d 'grant_type=client_credentials&scope={{SCOPE}}'
    authStr = b64encode(bytes(f"{CLIENT_ID}:{CLIENT_SECRET}", 'utf-8'))
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f"Basic {authStr.decode('utf-8')}"}
    data = {'grant_type': 'client_credentials', 'scope': 'product.compact'}
    res = requests.post('https://api.kroger.com/v1/connect/oauth2/token', data=data, headers=headers)
    acquistion_time = datetime.datetime.now()
    if res.status_code == 200:
        obj= json.loads(res.text)
        print('ACQUIRED: ', acquistion_time)
        print('EXPIRES: ', acquistion_time + datetime.timedelta(seconds=obj.get('expires_in')))
        pprint.pprint(obj)
        return obj.get('access_token')
    else:
        raise ValueError('The POST request failed')


# Queries Location Endpoint of Kroger API. Adds acquisition_timestamp
def getStoreLocation(ids):    
    # TODO: Add Location Id to the trip collection via the address attribute
    # /locations/<LOCATION_ID> :: address<Object>, chain<String>, phone<String>, departments<Array of Objects w/[departmentId, name, phone, hours<Object w/ weekdays<Objects w/ Hours>>]>, geolocation<Object>, hours<Object>, locationId<String>, name<String>
    # Web App can provide general information about the store chain, hours, departments, etc. 
    # IDEA: Store information can be combined with /cart route to quickly compare prices across close stores, submit cart reorders across stores and see if an order is possible given the time the client app is accessed.
    # This will give me general cart information and allow me to accurately query products via the correct store.
    token = getToken()
    #current_locations = {'01100482', '01100685', '01100438'} <- '01100479' refers to the pre-remodel '01100685' location : thus, id need to map '01100685':'01100479'
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    # endpoint
    endpoint = 'https://api.kroger.com/v1/locations'
    # params = f"?filter.zipCode.near={zipCode}"
    # will be a list of 10 closest stores to zip
    array = []
    for id in ids:
        response = requests.get(endpoint+f"/{id}", headers=headers)
        if response.ok:
            array.append(json.loads(response.text)['data'])

    array.append({'meta': {'acquistion_timestamp': (datetime.datetime.now()).timestamp()}})

    with open('./data/API/myStoresAPI.json', 'w') as file:
        file.write(json.dumps(array))

    print(f'{len(array)-1} locations written to disk')

    return None

# Queries Product Endpoint of KrogerAPI with Working Location Id 
# Combines Prices of Customer Trips and Prices Obtained At Previous API calls and Adds New Prices of Objects to Collection
def getItemInfo(itemLocationPairs): 
    # DOCS: https://developer.kroger.com/reference/#section/Refresh-Token-Grant
    ### HEADERS ####
    # Authorization: Basic {base64(client_id:client_secret)}
    ### ROUTE ####
    # for cilent id based operation (im guessing mostly cart and data about client)
    # f"https://api.kroger.com/v1/connect/oauth2/authorize?scope={SCOPES}&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    # for more basic information: 
    # f"https://api.kroger.com/v1/connect/oauth2/token?scope=product.compact&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

    # When making an access token request, the authorization header must be in the following form, where your client_id and client_secret are joined by a single colon and base64 encoded.

    # bring in Bearer token in headers and Accept application/json
    # critical item features require a LocationId filter such as, {aisleLocations, items, itemInformation, fulfillment, price, nationalPrice, size, soldBy}
        # :: w/o it I am only getting a few of these features, most importantly not price
    # The product will return if the queried store currently sells the product (but this does not mean it is currently stocked at the store),
    # I will have to handle the control flow to call the generalized item id route if this certain one fails.
        # API product calls did not end up failing, so will need to check these individual features associated with location to actually check if API call was successful
        # such as fulfillment type or say aislelocation.
        # 
    # {}

    # make upcSet come with location data from cart_number column that is never shown but is used for calling

    # change upcSet to container with both upc and location id

    # I want to keep locationId to be cart specific

    # the price that i do get with API will always be bound to location and acquistion time.
    # since 30 items of the 595, did not have price associated with them I still have some semblanance of price based on my concrete purchases

    # return item object:
        # query API for appropiate item @ store associated with the trip:
        # probably  static properties of item (not location bound thus can be added to the current item object in items collection)
            # location-bound: aisleLocations<Array>, items<Array> {favorite, fulfillment, price{promo, regular}, size, soldBy}, itemInformation<Object> {'depth', 'height', 'width'} <= spacial information, 
            # static: brand<String>, categories<Array>, countryOrigin<String>, description<String>, images<Array>, productId<String>, temperature<Object>, upc<String>, productId<String>

    # product_description = description, upc=UPC/productId

    # API items currently all have: 'productId', 'upc', 'aisleLocations', 'categories', 'description', 'items' {price and soldBy can be missing}, 'itemInformation', 'temperature'
        # 591 have 'images'
        # 576 have 'brand'
        # 572 have 'countryOrigin'
        

    # items currently all have: _id, cart_number, item_index, image, product_name, item_link, UPC, price_equation, product_size, product_promotional_price, product_original_price
        # 1043 have health_info and ingredients
        # 363 have avg_ratings, reviews and ratings_distribution
    
    token = getToken()
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    # endpoint
    endpoint = 'https://api.kroger.com/v1/products'
    data = []

    for i, pair in enumerate(itemLocationPairs):
        pairs = pair.split(";")
        upc = pairs[0]
        location = pairs[1]
        if location == '01100479':
            location = '01100685'

        params = f'/{upc}' # ?filter.locationId={LOCATION_ID}
        req = endpoint+params+"?filter.locationId={}".format(location)
        response = requests.get(req, headers=headers)
        try:
            obj = json.loads(response.text)
            obj = obj.get('data')
            obj = obj.get('items')[0] 
            # add the implicit queried location id to response
            if 'price' in obj:
                price = obj.get('price')
                if price.get('promo')==0:
                    price['promo'] = price['regular']
                data.append({'locationId': location, 'acquistion_timestamp': datetime.datetime.now().timestamp(), "isPurchase": False, "cart_number": None, "upc": upc,
                "quantity": 1, "promo": price.get('promo'), "regular": price.get('regular')
                })
            # add timestamp of scrape for future data analysis
            time.sleep(1)
        except json.decoder.JSONDecodeError:
            print(i)
            print(f"{upc};{location}")
            print(response)
            time.sleep(12)
        if i % 10 == 0:
            print(f"DONE WITH {i}. {len(itemLocationPairs)-i} TO GO @ {datetime.datetime.now()}. LEN: {len(data)}")

            
    if os.path.exists('./data/collections/combinedPrices.json'):
        with open('./data/collections/combinedPrices.json', 'r') as file:
            prev_object_list = json.loads(file.read())
            prev_object_list.extend(data)
        with open('./data/collections/combinedPrices.json', 'w') as file:
            file.write(json.dumps(prev_object_list))
    else:
        with open('./data/API/prices.json', 'w') as file:
            file.write(json.dumps(data))
    

    print(f'{len(data)} items written to disk')

    return None

# Combine Selenium Scraped Data w/ API calls to Filled Out Item Collection
# To Create Combined Prices and Combined Items 
def combineItems(api, scraped):
    # Keys on all Objects
    # productId<String>, upc<String>, description<String>, acquisition_timestamp<Float>, locationId<String>, 
    # temperature<Object {'heatSensitive'<Bool>, 'indicator'<String>}>, categories<Array>,
    # items<Array with Single Object  {'itemId'<String>, 'favorite'<Bool>, 'fulfillment'<{'curbside'<Bool>, 'delivery'<Bool>, 'inStore'<Bool>, 'shipToHome'<Bool>}>, 'size', '?price{'regular', 'promo'}', '?soldBy'}>
        # -> for items w/o price or Sold fulfillment and size still matter
        # favorite more corresponds to a customer auth api route {'upc': false}
    
    # Reversed so that single items that have only a few meaningful nonstatic/variable, time-based attributes are updated while the bulk of the object stay the same 
    # set to determine presence of updating collection
    parsedItemsSet = set()
    final_product_array = []
    prices_array = []
    if os.path.exists('./data/collections/combinedItems.json') and os.path.exists('./data/collections/combinedPrices.json'):
        # load each file
        with open('./data/collections/combinedItems.json', 'r') as file:
            final_product_array = json.loads(file.read())
            _upcs = list(map(lambda x: parsedItemsSet.add(x.get('upc')), final_product_array))
            
        with open('./data/collections/combinedPrices.json', 'r') as file:
            prices_array = json.loads(file.read())

        # write upcs to parsedItemSet
    for product in api:
        upc = product.get('upc')
        if upc in parsedItemsSet:
            # get location specific data: aisleLocations, fullfillment and connect it back to existing object
            # find matching object
            locationId = product.get('locationId')
            apiMatch = filter(lambda x: x.get('upc') == upc, final_product_array)
            for a in apiMatch:
                item_data = product.get('items')[0]
                if 'aisleLocations' in product: 
                    a['locationsData'].append({locationId: {"located": product.get('aisleLocations'), 'fulfillment': item_data.get('fulfillment'), "acquistion_timestamp": product.get('acquistion_timestamp')}})
                else:
                    a['locationsData'].append({locationId: {"located": None, 'fulfillment': item_data.get('fulfillment'), "acquistion_timestamp": product.get('acquistion_timestamp')}})
                
                if 'price' in item_data:
                    prices = item_data.get('price')
                    if prices.get('promo')==0:
                        prices['promo'] = prices['regular']
                    prices_array.append({
                        "promo": prices.get('promo'), "regular": prices.get('regular'), "upc": upc,\
                            'locationId': locationId, "acquistion_timestamp": product.get('acquistion_timestamp'),'isPurchase': False, "quantity": 1, "cart_number": None,
                    })
                else:
                    prices_array.append({
                        "promo": None, "regular": None, "upc": upc,\
                        'locationId': locationId, "acquistion_timestamp": product.get('acquistion_timestamp'),'isPurchase': False, "quantity": 0, "cart_number": None,
                    })
        else:
            final_item_object = {}
            locationId = product.get('locationId')
            final_item_object["upc"] = upc
            final_item_object["categories"] = product.get('categories')
            final_item_object["names"] = [product.get('description')]
            final_item_object["temperatureClass"] = product.get('temperature').get('indicator')
            final_item_object["heatSensitive"] = product.get('temperature').get('heatSensitive')
            item_data = product.get("items")[0]
            final_item_object['sizes'] = [item_data.get('size')]

            if 'brand' in product:
                final_item_object['brands'] = product.get('brand')
            if 'countryOrigin' in product:
                final_item_object['countryOrigin'] = product.get('countryOrigin').split(';')
            if 'images' in product:
                final_item_object["images"] = product.get('images')
            if 'itemInformation' in product: 
                final_item_object["dimensions"] = product.get("itemInformation")

            if 'soldBy' in item_data:
                final_item_object['priceUnits'] = item_data.get('soldBy')

            if 'aisleLocations' in product: 
                final_item_object['locationsData'] = [{locationId: {"located": product.get('aisleLocations'), 'fulfillment': item_data.get('fulfillment'), "acquistion_timestamp": product.get('acquistion_timestamp')}}]
            else:
                final_item_object['locationsData'] = [{locationId: {"located": None, 'fulfillment': item_data.get('fulfillment'), "acquistion_timestamp": product.get('acquistion_timestamp')}}]

            if 'price' in item_data:
                prices = item_data.get('price')
                if prices.get('promo')==0:
                    prices['promo'] = prices['regular']
                prices_array.append({
                    "promo": prices.get('promo'), "regular": prices.get('regular'), "upc": upc,\
                        'locationId': locationId, "acquistion_timestamp": product.get('acquistion_timestamp'),'isPurchase': False, "quantity": 1, "cart_number": None,
                })
            else:
                prices_array.append({
                    "promo": None, "regular": None, "upc": upc,\
                    'locationId': locationId, "acquistion_timestamp": product.get('acquistion_timestamp'),'isPurchase': False, "quantity": 1, "cart_number": None,
                })

            matches = filter(lambda x: x.get('upc')==upc, scraped)
            final_item_object.setdefault('carts', [])
            for match in matches:
                final_item_object['carts'].append(match.get('cart_number'))
                final_item_object['health_info'] = match.get('health_info')
                
                nameAlias = match.get('product_name')
                sizeAlias = match.get('product_size')
                if nameAlias not in final_item_object.get('names'):
                    final_item_object['names'].append(nameAlias)
                if sizeAlias not in final_item_object.get('sizes'):
                    final_item_object['sizes'].append(sizeAlias)
                matchId = match.get('locationId')
                matchUPC = match.get('upc')
                quantity = match.get('price_equation').get('quantity')
                prices_array.append({
                    "promo": round(match.get('product_promotional_price')/quantity, 3), "regular": round(match.get('product_original_price')/quantity, 3), "upc": matchUPC,\
                        'locationId': matchId, "acquistion_timestamp": match.get('acquistion_timestamp'),'isPurchase': True, "quantity": match.get('price_equation').get('quantity'),\
                            'cart_number':match.get('cart_number')
                })


            final_product_array.append(final_item_object)
            parsedItemsSet.add(upc)
        # search API list for matching items:

            # remove api upc, productId, description,

            # keep calc vars on api: acquistion_timestamp, locationId
        # destructure temperature, keep heatSensitive and indicator->Temperature

        # destructure items
            # remove itemId, favorite
            # keep 1 of size or product_size
            # if soldBy exist keep it
            # if price exists: correspond "regular" and "promo" together w/ acquistion timestamp


        # Nearly-All:
        # images<Array of Objects {'perspective'<String>, 'featured'<Bool>, 'sizes'<Array of Objects {'size', 'url'}>}>,
            # if images exist: replace product image w/ image Array

        # brand<String>,
            # if brand exists: include brand in object
        # countryOrigin<String (with ; seperator) >
            # if countryOrigin exists: include brand in object

        # Fewer:
            # aisleLocations<Array of Objects {bayNumber, description, number, numberOfFacings, shelfNumber, shelfPositionInBay, side}> :: all strings
            # if aisleLocations not empty: include in object w/ refernce to locationID

            # itemInformation<Object {depth, height, width}> :: all string 

                # if itemInformation not empty: include in object as dimensions

    sparseItemSet = {s.get('upc') for s in scraped}.difference(parsedItemsSet)
    remainingItems = filter(lambda s: s.get('upc') in sparseItemSet, scraped)

    for item in remainingItems:
        item_obj = {}
        if item.get('upc') not in parsedItemsSet:
            # adds available data of nonimage/non-upc purchases to combinedItems collection 
            item_obj['names'] = [item.get('product_name')]
            item_obj['sizes'] = [item.get('product_size')]
            item_obj['priceUnits'] = 'UNIT'
            item_obj['carts'] = [item.get('cart_number')]
            item_obj['brands'] = 'Kroger'
            item_obj['upc'] = item.get('upc')
            # adds item initial price entry into prices collections
            quantity = item.get('price_equation').get('quantity')
            prices_array.append({
                    "promo": round(item.get('product_promotional_price')/quantity, 3), "regular": round(item.get('product_original_price')/quantity, 3), "upc": item.get('upc'),\
                        'locationId': item.get('locationId'), "acquistion_timestamp": item.get('acquistion_timestamp'),'isPurchase': True, "quantity": quantity,\
                            'cart_number':item.get('cart_number')
                })
            final_product_array.append(item_obj)
        else:
            # get parsed item
            parsedItem = filter(lambda x: item.get('upc'), final_product_array)
            for pi in parsedItem:
                pi.get('carts').append(item.get('cart_number'))
            quantity = item.get('price_equation').get('quantity')
            prices_array.append({
                    "promo": round(item.get('product_promotional_price')/quantity, 3), "regular": round(item.get('product_original_price')/quantity, 3), "upc": item.get('upc'),\
                        'locationId': item.get('locationId'), "acquistion_timestamp": item.get('acquistion_timestamp'),'isPurchase': True, "quantity": quantity,\
                            'cart_number':item.get('cart_number')
                })




    with open('./data/collections/combinedItems.json', 'w') as file:
        file.write(dumps(final_product_array))

    with open('./data/collections/combinedPrices.json', 'w') as file:
        file.write(dumps(prices_array))



    return final_product_array


# Generator to Summarize Types & Counts for Nested Dicts/Lists  
def extract_nested_values(it):
    if isinstance(it, list):
        for sub_it in it:
            yield from extract_nested_values(sub_it)
    elif isinstance(it, dict):
        for key, value in it.items():
            yield {key: list(extract_nested_values(value)), "count":1, 'type': type(value)}
    else:
        yield {'count':1, 'type': type(it)}

# decompose API prices into prices collection 
def getPrices(api):
    more_prices = []
    for a in api:
        price_data = a.get('items')[0]
        if 'price' in price_data:
            more_prices.append({"promo": price_data['price'].get('promo'),\
            "regular": price_data['price'].get('regular'),\
                "upc": a.get('upc'),\
                    'locationId': a.get('locationId'),\
                    "acquistion_timestamp": a.get('acquistion_timestamp'),\
                        'isPurchase': False,
                        "quantity": price_data.get('size'),\
                            "cart_number": None,
            })      
    current_prices = json.loads(open('./data/collections/prices.json', 'r').read())
    current_prices.extend(more_prices)
    with open('./data/collections/prices.json', 'w') as f:
        f.write(json.dumps(current_prices))
    
    return None

# Work Within the Points-Based Confines of API to Gather Receipes by Meal Type and Ingredients
def getRecipes(ingredients=None, route="recipes/findByIngredients", limit=10, generalInfo=True):
    # pork, beef, chicken, salmon, eggs, lettuce, jalapenos, flour, sugar, 
    # types = ["main course", "side dish", "dessert", "appetizer", "salad", "bread", "breakfast", "soup", "beverage", "sauce", "marinade", "fingerfood", "snack", "drink"]
    # types = {'main course': {"max": 1516, "offset": 100}}
    types = {'main course': {"max": 1516, "offset": 1350} ,'side dish': {"offset": 1115, "max":1814}, 'dessert':{"offset": 305, "max": 299}, 'appetizer': {"offset": 272, "max":598}, 'salad': {"offset": 177, "max":266}, 'bread':{"offset": 39, "max": 38}, 'breakfast':{"offset": 138, "max": 224}, 'soup':{"offset": 169, "max": 320}, 'beverage':{"offset": 86, "max": 86}, 'sauce':{"offset": 74, "max": 74}, 'marinade':{"offset": 100, "max": 3}, 'fingerfood':{"offset": 100, "max": 31}, 'snack':{"offset": 272, "max": 598}, 'drink':{"offset": 100, "max": 86}}
    recipes = []
    amountLeft = 45.5 
    amountUsed = 150.0-amountLeft

    if not route:
        raise ValueError("You must enter a route")

    
    if os.path.exists("./requests/server/collections/recipes/recipes.json"):
        with open("./requests/server/collections/recipes/recipes.json", "r", encoding="utf-8") as file:
            recipes.extend(json.loads(file.read()))

    if generalInfo:
        if isinstance(ingredients, list):
            for ingredient in ingredients:
                req_url = recipe_base_url + route + "?" + f"ingredients={ingredient}" + f"&number={limit}&apiKey={RECIPE_KEY}"
                print(req_url)
                req = requests.get(req_url)
                headers = req.headers
                try:
                    headers_response = json.loads(str(headers))
                    pprint.pprint(headers_response)
                except:
                    pprint.pprint(headers)
                text = req.text
                recipes.extend(json.loads(text))
                time.sleep(1.5)
        elif isinstance(ingredients, dict):
            recSet = set([x.get('id') for x in recipes])
            for type in types.keys():
                offset = types[type]["offset"]
                max = types[type]["max"]
                if max == 0:
                    req_url = recipe_base_url + route + "?" + f"offset={offset}&type={type}&number={limit}&apiKey={RECIPE_KEY}"
                    print(req_url)
                    print("\n")
                    req = requests.get(req_url)
                    headers = req.headers

                    text = req.text
                    data = json.loads(text)
                    if isinstance(data, dict):
                        offset = data.get("number") + data.get("offset")
                        entries = data.get("totalResults")
                        recipes.extend(data["results"])
                        types[type]["max"] = entries
                    else:
                        recipes.extend(data)
                    amountUsed = float(headers.get('X-API-Quota-Request'))
                    amountLeft = float(headers.get('X-API-Quota-Left'))
                    print("AMT LEFT : ", amountLeft)
                    print("\nAMT USED : ", amountUsed)
                    print("\nTOTALS : ", entries)
                    if amountUsed>amountLeft:
                        break
                while (2<amountLeft) and (offset<max):
                    req_url = recipe_base_url + route + "?" + f"offset={offset}&type={type}&number={limit}&apiKey={RECIPE_KEY}"
                    print(req_url)
                    req = requests.get(req_url)
                    headers = req.headers
                    print(headers)
                    print("\n")
                    text = req.text
                    data = json.loads(text)
                    if isinstance(data, dict):
                        offset = offset + len(data["results"])
                        entries = data.get("totalResults")
                        recipes.extend([x for x in data["results"] if x.get('id') not in recSet])
                    else:
                        offset = max+limit
                        recipes.extend([x for x in data if x.get('id') not in recSet])
                    amountUsed = float(headers.get('X-API-Quota-Request'))
                    amountLeft = float(headers.get('X-API-Quota-Left'))
                    try:
                        with open("./requests/server/collections/recipes/recipes.json", "w", encoding="utf-8") as file:
                            file.write(json.dumps(recipes))
                    except:
                        with open("./requests/server/collections/recipes/recipesErr.txt", "w", encoding="utf-8") as file:
                            file.write(str(recipes))
                    print("AMT LEFT : ", amountLeft)
                    print("\nAMT USED : ", amountUsed)
                    print("\nTOTALS : ", entries)
                    time.sleep(5)
                print(f"++++++++++++FINISHED {type}++++++++++")
    else:
        recSet = set([x.get('id') for x in recipes])
        # has all ids of recipes based on the calls to the above route
        recArray = list(recSet)
        lastQuery = False

        if os.path.exists("./requests/server/collections/recipes/recipesInvolved.json"):
            with open("./requests/server/collections/recipes/recipesInvolved.json", "r", encoding="utf-8") as file:
                oldrecipes = json.loads(file.read())
                recipes = []
                alreadyScraped = set([x.get("id") for x in oldrecipes])
                recipes.extend(oldrecipes)
                recArray = list(recSet.difference(alreadyScraped))
                print(f"CURRENT RECIPES LEFT TO ACQUIRE {len(recArray)}.") 
                if len(recArray)==0:
                    raise ValueError("all current information has been collected. Re-run General Info w/ new params to access this endpoint.")
                elif limit > len(recArray):
                    limit = len(recArray)
                    lastQuery= True


        for j in range(0, len(recArray), limit):
            if amountLeft < ((limit+1)*.5):
                remainder = amountLeft // .5
                remainder -= 2
                limit = math.floor(remainder)
                lastQuery = True
            params = [str(x) for x in recArray[j:j+limit]]
            params = ",".join(params)
            req_url = recipe_base_url + route + "?" + f"ids={params}&apiKey={RECIPE_KEY}"
            print("Calling ", req_url)
            req = requests.get(req_url)
            headers = req.headers
            pprint.pprint(headers)
            text = req.text
            recipes.extend(json.loads(text)) # will be a list
            try:
                amountUsed = float(headers.get('X-API-Quota-Request'))
                amountLeft = 150 - float(headers.get('X-API-Quota-Used'))
                print("HEADERS RECEIVED")
            except:
                amountUsed = (limit+1)*.5
                amountLeft -= amountUsed
            print("\nAMT USED : ", amountUsed)
            print("AMT-LEFT : ", amountLeft)
            print("LIMIT: ", limit, "\n")
            print("RECIPE LN: ", len(recipes), "\n")
            try:
                with open("./requests/server/collections/recipes/recipesInvolved.json", "w", encoding="utf-8") as file:
                    file.write(json.dumps(recipes))
            except:
                with open('./recipesInvolved.txt', 'w', encoding='utf-8') as file:
                    file.write(str(recipes))
            if lastQuery:
                break
            time.sleep(65.5)

    return None

# # # # # # API CALLS # # # # # # 
# getItemInfo(upcSET)
# getStoreLocation({'01100482', '01100685', '01100438'})
# getRecipes(ingredients=['pork', 'beef', 'chicken', 'salmon', 'shrimp', 'eggs', 'flour', 'lettuce', 'sugar', 'butter'], limit=100)
# getRecipes(route="recipes/informationBulk", limit=50, generalInfo=False)
# getRecipes(route="recipes/complexSearch", limit=100, ingredients=dict(), generalInfo=True)