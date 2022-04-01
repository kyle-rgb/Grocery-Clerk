import re, requests, datetime, time, json, pprint
from django.forms import ValidationError

from base64 import b64encode, b64decode
from requests_oauthlib import OAuth2Session
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

# DOCS: https://developer.kroger.com/reference/#section/Refresh-Token-Grant
### HEADERS ####
# Authorization: Basic {base64(client_id:client_secret)}
### ROUTE ####
# for cilent id based operation (im guessing mostly cart and data about client)
# f"https://api.kroger.com/v1/connect/oauth2/authorize?scope={SCOPES}&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
# for more basic information: 
# f"https://api.kroger.com/v1/connect/oauth2/token?scope=product.compact&response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

# When making an access token request, the authorization header must be in the following form, where your client_id and client_secret are joined by a single colon and base64 encoded.

def parseUPC():
    # TODO: Get UPC using REGEX via the link tag in the item document
    # match on trip joining column and return UPC and correct location ID to pass to API
    client = MongoClient()
    db = client.groceries # db
    results = list(db.items.find({}))
    trips = list(db.trips.find({}))
    upc_re = re.compile(r"/\d+")
    additional_date_regex = re.compile(r'20[1-2][0-9]-[0-1][0-9]-[0-3][0-9]')
    upcs = set()
    # address backup -> to checkout timestamp
    # standardize address backup by using order_number and gathering am/pm distinction (since the majority of purchases already have their times in military time use this format)
    nonfuel_orders = re.compile(r'In-store')
    # Fix checkout time stamps of Fuel purchases via additional_date_regex
    # For fuel purchases and other nontime bound data, the last four digits of the order number match exactly to receipt times where we have available data
    # get rid of address backup

    for r in results:
        upc = r.get('UPC')
        r['cart_number'] = hash(r.get('cart_number').replace('detail', 'image'))
        if upc != None:
            # upc is a link
            if len(re.findall(upc_re, upc)) > 0:
                r['UPC'] = ''.join(re.findall(upc_re, upc)).replace('/', '')
            upcs.add(r['UPC'])

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
        _['cart_number'] = hash(_.get('order_number'))
        _.pop('order_number')
        _['full_document'] = hash(_.get('full_document').__str__())

    with open('./collections/items.json', 'w') as file:
        file.write(dumps(results))
    
    with open('./collections/trips.json', 'w') as file:
        file.write(dumps(trips))


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



def getStoreLocation(zipCode):    
    # TODO: Search API Endpoint for stores to gather additional store level information that can be applied with trips
        # /locations/<LOCATION_ID> :: address<Object>, chain<String>, phone<String>, departments<Array of Objects w/[departmentId, name, phone, hours<Object w/ weekdays<Objects w/ Hours>>]>, geolocation<Object>, hours<Object>, locationId<String>, name<String>
        # Web App can provide general information about the store chain, hours, departments, etc. 
        # IDEA: Store information can be combined with /cart route to quickly compare prices across close stores, submit cart reorders across stores and see if an order is possible given the time the client app is accessed.
        # This will give me general cart information and allow me to accurately query products via the correct store.
    # TODO: Add Location Id to the trip collection via the address attribute
    token = getToken()
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    # endpoint
    endpoint = 'https://api.kroger.com/v1/locations'
    params = f"?filter.zipCode.near={zipCode}"
    # will be a list of 10 closest stores to zip
    response = requests.get(endpoint+params, headers=headers)
    with open('./API/storesAPI.json', 'w') as file:
        file.write(response.text)

    print('locations written to disk')

    return None

def getItemInfo(upcSet):
    # TODO: call f"https://api.kroger.com/v1/products/{ID}?filter.locationId={LOCATION_ID}"
    # bring in Bearer token in headers and Accept application/json
    token = getToken()
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    # endpoint
    endpoint = 'https://api.kroger.com/v1/products'
    data = []

    for upc in upcSet:
        params = f'/{upc}' # ?filter.locationId={LOCATION_ID}
        response = requests.get(endpoint+params, headers=headers)
        data.append(json.loads(response.text))

    with open('./API/itemsAPI.json', 'w') as file:
        file.write(json.dumps(data))

    print(f'{len(data)} items written to disk')

    return None


upcSET = parseUPC()
getItemInfo(upcSET)
getStoreLocation(30084)

