import re, requests
from requests_oauthlib import OAuth2Session
from bson.json_util import dumps
from pymongo import MongoClient




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

    for r in results:
        upc = r.get('UPC')
        r['cart_number'] = hash(r.get('cart_number'))
        if upc != None:
            # upc is a link
            if len(re.findall(upc_re, upc)) > 0:
                r['UPC'] = ''.join(re.findall(upc_re, upc)).replace('/', '')

    for _ in trips:
        _['order_number'] = hash(_.get('order_number'))
        _['full_document'] = hash(_.get('full_document').__str__())

    with open('./items.json', 'w') as file:
        file.write(dumps(results))
    
    with open('./trips.json', 'w') as file:
        file.write(dumps(trips))


    return results

def getStoreLocation():    
    # TODO: Search API Endpoint for stores to gather additional store level information that can be applied with trips
        # /locations/<LOCATION_ID> :: address<Object>, chain<String>, phone<String>, departments<Array of Objects w/[departmentId, name, phone, hours<Object w/ weekdays<Objects w/ Hours>>]>, geolocation<Object>, hours<Object>, locationId<String>, name<String>
        # Web App can provide general information about the store chain, hours, departments, etc. 
        # IDEA: Store information can be combined with /cart route to quickly compare prices across close stores, submit cart reorders across stores and see if an order is possible given the time the client app is accessed.
        # This will give me general cart information and allow me to accurately query products via the correct store.
    # TODO: Add Location Id to the trip collection via the address attribute

    pass

def getItemAPIinfo(parsedUPC, LocationID):
    # TODO: call f"https://api.kroger.com/v1/products/{ID}?filter.locationId={LOCATION_ID}"
    # bring in Bearer token in headers and Accept application/json

    pass


parseUPC()





