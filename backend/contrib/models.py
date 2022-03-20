from django.db import models
from datetime import datetime


# Create your models here.

# One for Trips
from pymongo.write_concern import WriteConcern

from pymodm import MongoModel, fields

class Receipts(MongoModel):
    checkout_timestamp = fields.DateTimeField()
    address = fields.CharField()
    items = fields.ListField()
    sales = fields.ListField()
    cahsier = fields.CharField()
    payment_type = fields.CharField()
    fuel_points_earned = fields.IntegerField()
    fuel_points_month = fields.IntegerField()
    last_month_fuel_points = fields.IntegerField()


    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'receipts'

    
# One for Items
class Items(MongoModel):
    UPC = fields.IntegerField()
    avg_rating = fields.FloatField()
    reviews = fields.IntegerField()
    ingredients = fields.ListField()
    health_info = fields.DictField()
    serving_size = fields.DictField()
    images = fields.URLField()
    product_name = fields.CharField()
    item_link = fields.URLField()
    price_equation = fields.CharField()
    product_size = fields.CharField()
    product_promotional_price = fields.FloatField()
    product_original_price = fields.FloatField()
    


    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'items'
