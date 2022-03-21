from django.http import JsonResponse
from django.shortcuts import render
from pymongo import MongoClient
from urllib.parse import quote_plus
from api_keys import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD

#### API
def get_items(request):
    # Initialize connection; Mongo will connect on first operation
    uri = "mongodb://%s:%s@%s" % (quote_plus(MONGO_INITDB_ROOT_USERNAME), quote_plus(MONGO_INITDB_ROOT_PASSWORD), quote_plus("mongo")) ########
    client = MongoClient(uri)
    db = client.groceries # db
    reqObj = []
    items = db.items  # items
    trips = db.trips.find_one({}, {'_id': 0})
    for i in items.find({}, {'_id': 0}):
        reqObj.append(i)
    
    text = request.GET.get("type", "")
    if text == 'items':
        return JsonResponse(reqObj, safe=False)
    else:
        return JsonResponse(trips, safe=False)

#### Backend Template Pages
def start_page(request):
    return render(request, 'backend/index.html')