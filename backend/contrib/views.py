from django.http import JsonResponse
from django.shortcuts import render
from pymongo import MongoClient
from urllib.parse import quote_plus

import os
#### API
def get_items(request):
    # Initialize connection; Mongo will connect on first operation
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client["new"] # db
    text = request.GET.get("type", "")
    try:
        result = list(db[text].find({}, projection={"_id": 0}, limit=2))
    except BaseException as err:
        print(err)
        result = {'error': 'collection does not exist'}
    return JsonResponse(result, safe=False)

def items(request):
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client['new']
    collection = 'items'
    limit = request.GET.get('limit', '')
    start = request.GET.get('start', '')
    filterObj = {}
    if limit and start:
        res = db[collection].find({}, projection={"_id": 0}, limit=int(limit), skip=int(start))
    else:
        res = db[collection].find({}, projection={'_id': 0}, limit=4)

    res = [ x for x in res]
    return JsonResponse(res, safe=False)
    
def count_items(request):
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client['new']
    collection = 'items'
    res = db[collection].aggregate(pipeline=[{'$group': {'_id':None, 'count': { '$sum': 1 } }}, {'$project': {'_id': 0}}])
    res = [x for x in res][0]

    return JsonResponse(res)

    



#### Backend Template Pages
def start_page(request):
    return render(request, 'backend/index.html')