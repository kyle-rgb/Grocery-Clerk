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
    col = request.GET.get("type", "")
    limit = int(request.GET.get("limit", ""))
    skip = int(request.GET.get("start", ""))
    filterVars = {}
    if limit:
        filterVars['limit']=limit
    if skip:
        filterVars['skip']=skip
    try:
        result = list(db[col].find({}, projection={"_id": 0}, **filterVars))
    except BaseException as err:
        print(err)
        result = {'error': 'collection does not exist'}

    print(result[1])

    return JsonResponse(result, safe=False)

def count_items(request, collection=''):
    uri = os.environ.get("MONGO_CONN_URL")
    client = MongoClient(uri)
    db = client['new']
    collection = collection
    res = db[collection].aggregate(pipeline=[{'$group': {'_id':None, 'count': { '$sum': 1 } }}, {'$project': {'_id': 0}}])
    res = [x for x in res][0]

    return JsonResponse(res)

def get_full_item(request):
    uri = os.environ.get('MONGO_CONN_URL')
    client = MongoClient(uri)
    db = client['new']
    collection = request.GET.get("collection", "")
    slug = request.GET.get("slug", "")
    res = db[collection].aggregate(pipeline=[{'$match': {'upc': slug}}, {'$lookup': {'from': 'prices', 'localField': 'upc', 'foreignField': 'upc', 'as': 'prices'}}, {'$project': {'_id':0, 'prices': {'_id': 0}}}])
    result = list(res)[0]
    return JsonResponse(result, safe=True)

#### Backend Template Pages
def start_page(request):
    return render(request, 'backend/index.html')