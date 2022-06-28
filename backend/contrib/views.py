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
    db = client.new # db
    print(db.collection_names())
    text = request.GET.get("type", "")
    try:
        result = db[text].find_one({}, {"_id": 0})
    except:
        result = {'error': 'collection does not exist'}
    return JsonResponse(result, safe=False)

#### Backend Template Pages
def start_page(request):
    return render(request, 'backend/index.html')