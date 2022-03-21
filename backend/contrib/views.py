from django.http import JsonResponse
from django.shortcuts import render
from pymongo import MongoClient
import json


#### API
def get_items(request):
    # Initialize connection; Mongo will connect on first operation
    client = MongoClient('localhost', 27017)
    db = client.groceries # db
    reqObj = []
    items = db.carts  # items
    trips = db.trips.find_one({}, {'_id': 0})
    for i in items.find({}, {'_id': 0}):
        reqObj.append(i)
    
    text = request.GET.get("type", "")
    if text == 'items':
        return JsonResponse(reqObj, safe=False)
    else:
        return JsonResponse(trips)


#### Backend Template Pages
def start_page(request):
    return render(request, 'backend/index.html')