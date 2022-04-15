import re, requests, datetime, time, json, pprint, random, math
import numpy as np
from django.forms import ValidationError
from fuzzywuzzy import fuzz, process

from base64 import b64encode
# from requests_oauthlib import OAuth2Session
from bson.json_util import dumps
from pymongo import MongoClient

from api_keys import CLIENT_ID, CLIENT_SECRET


### Kroger API :: User Story <Shopping Trip 10-14 Days per Week>
''' Kroger API :: User Story <Shopping Trip 10-14 Days per Week>
- 5000 Calls Per Day
- Available Routes:
    - /Id for ID of customer (5000 Calls Per Day)
    - /Cart allows you to Add an Item to an authenticated customer's cart (5000 Calls Per Day)
    - /Products allows you to search the Kroger product catalog
        - default value returns 10 in a fuzzy search (can change on each request)
        - filter.limit increases products returned
        - filter.start (aka OFFSET) set number of results to skip in the response
        - Additional Valuable Data: Price (both regular and promo); nationalPrice (both regular and promo) for national price of the item;
        Fulfillment Type (Boolean object of {instore, shiptohome, delivery, curbside}); Aisle Locations;
        - You may also search the API via term (for fuzzy match, max 8 words / 7 spaces) or previously looked up productID.
            -filters: term (String>=3); locationId (VarChar 8); productId (Char 13-50); brand (String, case-sensitive, pipe-separated); fulfillment (Char 3)
            start (Int 1-1000); limit (Int 1-50);
    - /Locations allow you to search the departments, chains and details in the Kroger Family
        - Use Location Data to Find Closest Available Chain.'''

# Going to have to clean current item data to get UPC which will feed into API
    # Since on the scrape the web element stopped working
    # update cart link as well with a certain hash to allow me to publicize the collections
    # receipts may contain certain private data related to payment and account that I may need to watch out for, so hash that as well with a
    # "".join ...
    # Have about ~1250 items currently in the items collection based around 75 trips
    # Lets not waste certain pulls so only make api calls to distinct UPCs.
    # ...
    # The crucuial routes seem to map directly to my two routes as of now via. {Trips} => /Locations (One Trip of Many Items Occurs at One Location) 

def parse_ingredients(ingredient_string):
    # the important tokens are collection indicators and commas
    ingredients_regex = re.compile(r'([\(\{\[,])?([^\]\}\)\{\[\(]+)([\)\}\],]+)?')
    collection_parser = {'[': ']', '{': '}', "(": ")"}
    objects = []
    last_seen = ''
    matches = re.findall(ingredients_regex, ingredient_string)
    for leading_indicator, ingredients, trailing_indicator in matches:
        trailing_indicator = trailing_indicator.replace(',', '')
        leading_indicator = leading_indicator.replace(',', '')
        if (leading_indicator=='') and (trailing_indicator==''):
            for i in ingredients.split(','):
                if i.strip()!='':
                    objects.append({'name': i.strip().title()})
        elif (leading_indicator!='') and (trailing_indicator!='') and (trailing_indicator==collection_parser[leading_indicator]):
            objects[-1].setdefault('subingredients', [])
            ing = [{"name": i.strip().title()} for i in ingredients.split(',') if i.strip()!='']
            if objects[-1].get('subingredients'):
                objects[-1]['subingredients'][-1].setdefault('subingredients', [])
                objects[-1]['subingredients'][-1]['subingredients'].extend(ing)
            else:
                objects[-1]['subingredients'].extend(ing)
        elif (leading_indicator!='') and (trailing_indicator==''):
            objects[-1].setdefault('subingredients', [])
            objects[-1]['subingredients'].extend([{"name": i.strip().title(), "io": True} for i in ingredients.split(',') if i.strip()!=''])
            last_seen = leading_indicator
        else:
            objects[-1]['note'] = list(map(str.title, ingredients.split(',')))
    #pprint.pprint(objects)
    return objects




def parseUPC():
    # this method functionally deals with uneven scraping procedures and updated data handling since I have come to learn the data some more
    # these steps should be able to be reintegrated back into a refactored make_dataset.py
    # the idea would be to reformat the item data based on the now known conditions that can also handle API calls for the same item.
    # the items collection itself and the api items should now have a date_scraped feature to better pair a specific price to a specific location at a set instance in time.
    # ???: the api calls for a specific product can be filtered by the specific locationId, where the response will return the information iff the product is currently available @ that location.
    # TODO:
        # breakdown serving size right now approx. \d+{count} \(\d+ g(ram(s))\) to metric equivalents (ml, L, mg, g, kg)
        # breakdown price equation (rn. ct x $\d\.\d+/each) <= though price equation always accounts for only product_original_price
            # can have count and weight, count or volume and count.
                # ct. has many different forms ranging from bottles/cans/ct/each/pk/rolls/sq ft
                # volume has fl oz/gal/pt/qt/L
                # weight has oz/lb/Lb/Oz
        # convert product size from imperial to metric
        # calculate missing serving size by summing the available nutrient information. Should add up to the gram representation of serving size

    # for restructuring full document
    sales_re = re.compile(r'^SC\s*([A-z0-9\s]+)\s*(\d+\.\d+)[\s-]*(B|T|X)?$')
    item_re = re.compile(r"^\s*(.+)(\d+\.\d+)[\s|-](B|T|X)$")
    receipt_total_re = re.compile(r'TOTAL NUMBER OF ITEMS SOLD\s*=(\d+)')
    receipt_calculation_re = re.compile(r'((\d)(\.\d+)?(\D+)?)\s*@\s*(\d+)?\/?(\d+\.\d+)(\/\D+)?') # 1: full quantity string {fullstring, wholeUnits, partialUnits, unitSignifier} @ {quantityprice}]}

    # reformat string numbers back to numbers (sans upc)
    client = MongoClient()
    db = client.groceries # db
    # skip repeats of first page scrape
    results = list(db.items.find({}, skip=92))
    trips = list(db.trips.find({}, skip=5))
    upc_re = re.compile(r"/\d+")
    ingredients_regex = re.compile(r'((\(|\{|\[)(.+))|((.+)(\)|\}|\]))')
    additional_date_regex = re.compile(r'20[1-2][0-9]-[0-1][0-9]-[0-3][0-9]')
    reviews_regex = re.compile(r'(\d+) reviews with (\d{1}) star[s]?\.')
    upcs = set()
    grammer = {'g': 1, 'mg': 1000, 'mcg': 1_000_000}
    # address backup -> to checkout timestamp
    # standardize address backup by using order_number and gathering am/pm distinction (since the majority of purchases already have their times in military time use this format)
    nonfuel_orders = re.compile(r'In-store')
    # Fix checkout time stamps of Fuel purchases via additional_date_regex
    # For fuel purchases and other nontime bound data, the last four digits of the order number match exactly to receipt times where we have available data
    # get rid of address backup 
    price_collection = []
    # items currently all have: _id, cart_number, item_index, image, product_name,
            # item_link, UPC, price_equation, product_size, product_promotional_price, product_original_price
                # 1043 have health_info and ingredients
                # 363 have avg_ratings, reviews and ratings_distribution
    upcLessItems = {}
    for r in results:
        upc = r.get('UPC')
        # {'macros': {'measure': {$regex: /mcg/}}}
        metric_re = re.compile(r'(\d+\.?\d*)(m?c?g|IU)')
        # get location id from cart number
        location = r['cart_number'].split('/')[-1].split('~')
        locationid = location[0]+location[1]
        time = r['cart_number'][-4:]
        timestamp = location[2] + " " + f"{time[:2]}:{time[2:]}"
        timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%S").timestamp()
        if upc==None:
            if r.get('product_name').strip() not in upcLessItems.keys():
                upc = str(hash(r.get('product_name').strip()))
                upc = re.sub(r'[^\d]', '', upc)[:13]
                upcLessItems[r.get('product_name').strip()] = upc
                r['UPC'] = upc
            else:
                r['UPC'] = upcLessItems[r.get('product_name').strip()] 
                upc = upcLessItems[r.get('product_name').strip()] 

        

        if upc not in upcLessItems.keys():
            # upc is a link
            if len(re.findall(upc_re, upc)) > 0:
                r['UPC'] = ''.join(re.findall(upc_re, upc)).replace('/', '')
            upcs.add(f"{r['UPC']};{locationid}")
        r['upc'] = r['UPC']
        r.pop("UPC")

        # place subnutrients inside macros (subnutrients for macros ) and remove joining columns
        if 'health_info' in r:
            remove_indices=[]
            for i, nutrient in enumerate(r['health_info']['macros']):
                sub = nutrient.pop('is_sub')
                nutrient.pop('is_macro')
                micro = nutrient.pop('is_micro')
                joiner = nutrient.pop('nutrient_joiner')
                nutrient['measure'] = nutrient['measure'].replace('International Unit', 'IU')
                amount, measure = re.sub(metric_re, r'\1 \2', nutrient['measure']).split(' ')
                if measure != 'IU':
                    amount = float(amount) / grammer[measure]
                    measure = 'g'
                nutrient['measure'] = f"{amount} {measure}"
                

                if nutrient['daily_value']=='':
                    nutrient['daily_value']="0%"
                if sub:
                    r['health_info']['macros'][joiner].setdefault('subnutrients', [])
                    r['health_info']['macros'][joiner]['subnutrients'].append(nutrient)
                    remove_indices.append(i)
                elif micro:
                    r['health_info'].setdefault('micros', [])
                    r['health_info']['micros'].append(nutrient)
                    remove_indices.append(i)
            r['health_info']['macros'] = [nutr for ind, nutr in enumerate(r['health_info']['macros']) if ind not in remove_indices]
    
        
        # destructure ingredients
        if 'ingredients' in r:
            # check for collection like tokens \[ \{ \(
            # tokens seem to be multifaceted in their representations of collections of combined food items in combined food items
            # if collection indicator is closed within the single ingredient string the pointer points to an ingredient alias
            # else the ingredients array must be searched until the next same token is found.
            # Since array was created via a simple split on comma, there also appears to be rogue periods (\.) that indicate a line break that also must be parsed
            # Other common phrases are Contains 2% or less of" 
            legalese_regex = re.compile(r"((contains)(\s2% or less of)?[^A-z]*)", re.IGNORECASE)
            ingredients = r.get('ingredients')
            ingredients = [re.sub(legalese_regex, "", i).strip() for i in ingredients]
            ingredients_string = ", ".join(ingredients)
            ingredients_string = ingredients_string.replace(';', ',').replace('.', ', ').replace('}]', ']]')
            r['health_info']['ingredients'] = parse_ingredients(ingredients_string)
            r.pop('ingredients')            

        r['cart_number'] = hash(r.get('cart_number').replace('detail', 'image'))

        equation = r.get('price_equation')
        equation = [re.sub(r'[^\.\d]', '', e).strip() for e in equation.split('x')]
        r['price_equation'] = {'quantity': float(equation[0]), 'price': float(equation[1])}
        r['product_promotional_price'] = float(re.sub(r'[^\.\d]', '', r['product_promotional_price']))#/r['price_equation']['quantity']
        r['product_original_price'] = float(re.sub(r'[^\.\d]', '', r['product_original_price']))#/r['price_equation']['quantity']

        price_collection.append({"promo": round(r['product_promotional_price'], 3),\
            "regular": round(r['product_original_price'], 3),\
                "upc": r.get('upc'),\
                    'locationId': locationid,\
                    "acquistion_timestamp": timestamp,\
                        'isPurchase': True, 
                        "quantity": equation[0],
                        "cart_number": r.get('cart_number'),
        })
        r['acquistion_timestamp'] = timestamp
        r['locationId'] = locationid            
        # parse ratings
        if 'ratings_distribution' in r:
            
            ratings_list =  re.findall(reviews_regex, r['ratings_distribution'])
            temp_list = [0, 0, 0, 0, 0]
            for k, v in ratings_list:
                temp_list[int(v)-1] = int(k)

            r['ratings_distribution'] = temp_list
            r['reviews'] = int(re.sub(r"\(|\)", '', r['reviews']))
            r['avg_rating'] = float(r['avg_rating'])
        
        if ('health_info' in r ):
            if ('overall_health_score' in r.get('health_info')):
                r['health_info']['overall_health_score'] = int(r['health_info']['overall_health_score'].replace('percentage', ''))

    for _ in trips:
        # exact time of order is the trailing 4 digits of the order number
        # standarize all dates with accurate times
        _['checkout_timestamp'] = "".join([x for x in re.findall(additional_date_regex, _.get('order_number'))]).replace('-', '/')
        new_time = str(_['order_number'].split('~')[-1][-4:])
        _['checkout_timestamp'] += " " + new_time[:2] + ':' + new_time[2:]
        if re.findall(nonfuel_orders, _.get('checkout_timestamp'))!=[]:
                # remove blank special purchase type for nonfuel orders
                # will rename to in-store purchase which may be helpful for API down the road
            _['special_purchase_type'] = "".join([x for x in re.findall(nonfuel_orders, _.get('checkout_timestamp'))])

        # get Kroger location id embedded in trip summary link
        location = _['order_number'].split('/')[-1].split('~')
        _['locationId'] = location[0]+location[1]
        # standard joining feature
        _['cart_number'] = hash(_.get('order_number')) # , 
        _.pop('order_number')
        # before hash search full document for (B|T|X)$ and fuzzy match
        # break down items to by abbreviation, tax status, receipt_price
        # and then of course selection of savings w/ status code  (SC), all string data and amount saved 
        newItems = []
        lastItem = 0
        weight_switch = ''
        # sales_re = re.compile(r'^SC\s*([A-z\s]+)+(\d+\.\d+)[\s-]*(B|T|X)?$')
        # item_re = re.compile(r"\s*([^\d]+)+(\d+\.\d+)[\s|-](B$|T$|X$)")
        for i, docstring in enumerate(_['full_document']):
            salesObject = {}
            if re.findall(sales_re, docstring)!=[]:
                name, cost, taxStatus = re.findall(sales_re, docstring)[0]
                name = name.strip()
                newItems[lastItem].setdefault('sales', [])
                if taxStatus=='':
                    newItems[lastItem]['sales'].append({'item': name, 'cost': float(cost)})
                else:
                    newItems[lastItem]['sales'].append({'item': name, 'cost': float(cost), 'taxStatus': taxStatus})
            elif re.findall(item_re, docstring)!=[]:
                name, cost, taxStatus = re.findall(item_re, docstring)[0]
                name = name.strip()
                if re.findall(r"\d", name[-1])!=[]:
                    cost = name[-1] + cost
                    name =  name[:-1].strip()
                rec_obj = {'item': name, 'receipt_price': float(cost), 'taxStatus': taxStatus}
                if weight_switch:
                    rec_obj['weight_amount'] = float(weight_switch)
                    weight_switch = ''
                newItems.append(rec_obj)
                lastItem = newItems.index(rec_obj)
            elif re.findall(receipt_calculation_re, docstring)!=[]:
                matches = re.findall(receipt_calculation_re, docstring)[0]
                weight_receipt = matches[1] + matches[2]
                weight_switch = weight_receipt

        _['items'] = newItems
        _['full_document'] = hash(_.get('full_document').__str__())
        

    with open('./data/collections/items.json', 'w') as file:
        file.write(dumps(results))
    
    with open('./data/collections/trips.json', 'w') as file:
        file.write(dumps(trips))

    with open('./data/collections/prices.json', 'w') as file:
        file.write(dumps(price_collection))
    

    return upcs

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
        object= json.loads(res.text)
        print('ACQUIRED: ', acquistion_time)
        print('EXPIRES: ', acquistion_time + datetime.timedelta(seconds=object.get('expires_in')))
        pprint.pprint(object)
        return object.get('access_token')
    else:
        raise ValidationError('The POST request failed')



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
            object = json.loads(response.text)
            print(object)
            object = object.get('data')
            
            # add the implicit queried location id to response
            object['locationId'] = location
            # add timestamp of scrape for future data analysis
            object['acquistion_timestamp'] = datetime.datetime.now().timestamp()
            data.append(object)
            time.sleep(1)
        except json.decoder.JSONDecodeError:
            print(i)
            print(response)
            time.sleep(12)
        if i % 10 == 0:
            print(f"DONE WITH {i}. {len(itemLocationPairs)-i} TO GO @ {datetime.datetime.now()}")

            

    with open('./data/API/itemsAPI.json', 'r+') as file:
        prev_objs_list = json.loads(file.read())
        prev_objs_list.extend(data)

    with open('./data/API/itemsAPI.json', 'w') as file:
        file.write(json.dumps(prev_objs_list))

    print(f'{len(data)} items written to disk')

    return None

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



def extract_nested_values(it):
    if isinstance(it, list):
        for sub_it in it:
            yield from extract_nested_values(sub_it)
    elif isinstance(it, dict):
        for key, value in it.items():
            yield {key: list(extract_nested_values(value)), "count":1, 'type': type(value)}
    else:
        yield {'count':1, 'type': type(it)}
    
# now with combined items 

def getFuzzyMatch(items, trips):
    removePriceRegex = r'\d+\.\d+.+'
    countRegex = r'^(\d)+.+\s*x'
    for t in trips:
        matches = items
        receiptItems = sorted(t.get('items'), key=lambda x: x.get('item'))
        choicesX = [x.get("name") for x in matches]
        #counts = [choicesX.extend(int(x.get('quantity'))*[x.get('name')]) for x in matches]
        print(len(choicesX))
        chx=[]
        for recItem in receiptItems:
            # need a check to see if lbs in quantity measurement
            price = recItem.get('receipt_price')
            product = recItem.get('item')
            weight_switch = recItem.get('weight_amount')
            if 'sales' in recItem:
                for s in recItem.get('sales'):
                    price += s['cost']
            fuzz_matches = process.extract(product, choicesX, limit=15)
            matchObjects = list(filter(lambda x: x.get('name') in map(lambda x: x[0], fuzz_matches), matches))
            matchPrices = np.array([((price-(fuzzM.get('quantity') * fuzzM.get('promo') ))**2)**.5 for fuzzM in matchObjects])
            matchPrices = np.concatenate((matchPrices,np.array([((price-(fuzzM.get('quantity') * fuzzM.get('regular') ))**2)**.5 for fuzzM in matchObjects])))# 
            matchPrices = np.concatenate((matchPrices, np.array([((price-(1*fuzzM.get('regular') ))**2)**.5 for fuzzM in matchObjects])))
            matchObjects = matchObjects * 3
            fuzz_matches = fuzz_matches * 3
            
            matchGuess = [matchObjects[i] for i, p  in enumerate ( matchPrices ) if p < 0.01]
            if len(matchGuess)>1:
                name = process.extractOne(product, list(map(lambda y: y.get('name'), matchGuess)))
                matchGuess = list(filter(lambda d: d.get('name')==name[0], matchGuess))
                if len(matchGuess)>1:# print(matchGuess, product)
                    matchGuess=matchGuess[0]
            elif len(matchGuess)==1:
                matchGuess=matchGuess[0]
                
            print(product)

            # print(product, "==> ", matchGuess, '===$ ', matchPrice)
            # fuzz_match = fuzz_matches[np.argmin(matchPrice)]
            # print('FUZZMATCH::', fuzz_match, matchPrice, matchGuess)
            # iterations = 1
            # if weight_switch:
            #     iterations = int(weight_switch)
            # try:
            #     float_quantity = list(filter(lambda x: x.get('name')==matchGuess.get('name'), matches))[0].get('quantity')
            # except TypeError:
            #     print('fuzz', matchGuess.get('name')) # 
            #     raise ValueError
            # if float_quantity % 1 > 0:
            #     iterations = int(float_quantity)
            # for i in range(iterations):
            #     choicesX.pop(choicesX.index(matchGuess['name']))
            chx.append((product, '>>>>>>', matchGuess['name'], "====", f"{price}:::::{matchGuess['promo']}", matchGuess['promo'],))
            


        print(len(chx))
        for c in sorted(chx, key=lambda v: v[5], reverse=True):
            print('\n')
            print(c)
            print('\n')
            
    return None


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




upcSET= set({'650233691;01100482'})
# # # # # # API CALLS # # # # # # 
getItemInfo(upcSET)
# getStoreLocation({'01100482', '01100685', '01100438'})
# # # # # # # # # # ## # # # # #
#trips = json.loads(open('./data/collections/trips.json', 'r').read())
# # # # # MATCH RECEIPTS TO ITEMS # #  # # # #
# getFuzzyMatch(items=items, trips=trips)
# # # # # # # # # # ## # # # # # # # # # # # #
# # # # # CREATE PRICE COLLECTIONS # # # # # #
#getPrices(apiItems)
#combineItems(api=apiItems, scraped=items)
# # # # # # # # # # ## # # # # # # # # # # # #
# # upcSET = parseUPC()
# items = json.loads(open('./data/collections/items.json', 'r').read())
# apiItems = json.loads(open('./data/API/itemsAPI.json', 'r').read())
# # combineItems(api=apiItems, scraped=items)
# # getItemInfo(upcSET) # LAST API CALL @ 9:40 PM 4/11/2022

# prices = json.loads(open('./data/collections/combinedPrices.json', 'r').read())
# combinedItems = json.loads(open('./data/collections/combinedItems.json', 'r').read())
# storesAPI = json.loads(open('./data/API/myStoresAPI.json', 'r').read())
# trips = json.loads(open('./data/collections/trips.json', 'r').read())

# pprint.pprint(combinedItems[12])

# atrip = -1056238256466118559
# afil = list(filter(lambda x: atrip in x.get('carts'), combinedItems))
# atri =list(filter(lambda x: atrip==x.get('cart_number'), trips))
# # print("len of filtered items", len(afil))
# # print("len of receipt items", len(atri))

# cpus = {v for v in map(lambda x: x.get('upc'), afil)}
# # match on upc and cart_number
# matching_prices = list(filter(lambda x: ((x.get('upc') in cpus)and(x.get('cart_number')==atrip)), prices))
# print("len of price entries", len(matching_prices))
# matching_prices = sorted(matching_prices, key=lambda x: x['upc'])
# afil = sorted(afil, key=lambda x: x['upc'])
# priced = []
# for pr, it in zip(matching_prices, afil):
#     it.update(pr)
#     it['name'] = it['names'][0]
#     priced.append({k:v for k,v in it.items() if k in ['promo', 'quantity', 'regular', 'name', 'upc', 'categories']})
    
# # print(priced[1])
# # pprint.pprint(list(filter(lambda x: x.get('upc') in {'0021077300000', '0001111004519'}, afil)))
# getFuzzyMatch(items=priced, trips=atri)

# return items and price (as quant * promo) to help fuzzy matching

#pprint.pprint([l.get('upc') for l in afil])

def counter(JSON):
    keyer = {}

    for j in JSON:
        if isinstance(j, dict):
            for key in j.keys():
                if key in keyer:
                    keyer[key]+=1
                    if isinstance(j[key], str) and (j[key]==''):
                        keyer[key]-=1
                    elif isinstance(j[key], list) and (j[key]==[]):
                        keyer[key]-=1
                    elif isinstance(j[key], dict) and (j[key]=={}):
                        keyer[key]-=1
                else:
                    keyer[key]=1
                    if isinstance(j[key], str) and (j[key]==''):
                        keyer[key]-=1
                    elif isinstance(j[key], list) and (j[key]==[]):
                        keyer[key]-=1
                    elif isinstance(j[key], dict) and (j[key]=={}):
                        keyer[key]-=1
        else:
            for key in j:
                if key in keyer:
                    keyer[key]+=1
                    if isinstance(key, str) and (key==''):
                        keyer[key]-=1
                    elif isinstance(key, list) and (key==[]):
                        keyer[key]-=1
                    elif isinstance(key, dict) and (key=={}):
                        keyer[key]-=1
                else:
                    keyer[key]=1
                    if isinstance(key, str) and (key==''):
                        keyer[key]-=1
                    elif isinstance(key, list) and (key==[]):
                        keyer[key]-=1
                    elif isinstance(key, dict) and (key=={}):
                        keyer[key]-=1 
    pprint.pprint(sorted(keyer.items(), key=lambda  x: x[1], reverse=True))
    # all_keys = list(filter(lambda x: len(x.keys())>2, JSON))
    #all_keys = list(filter(lambda x: x.keys()==keyer.keys(), JSON))
    #pprint.pprint(all_keys[0])
    return None

# counter(filter(lambda x: x!=None, map(lambda x: x.get('categories'), combinedItems)))
# print(len(combinedItems))




