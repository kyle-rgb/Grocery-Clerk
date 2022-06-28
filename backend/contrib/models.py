from django.db import models
from datetime import datetime


# Create your models here.

# One for Trips
from pymongo.write_concern import WriteConcern
from pymodm import MongoModel, fields, connect

connect("mongodb://localhost:27017/my-app", alias='my-app')

class Inventories(MongoModel):
    stockLevel = fields.CharField()
    locationId = fields.CharField()
    utcTimestamp = fields.IntegerField()
    upc = fields.CharField()
    availableToSell = fields.IntegerField()
    sellerKey = fields.IntegerField()

    class Meta:
        write_concern = WriteConcern(j=True) # to journal
        connection_alias = 'my-app'

class Items(MongoModel):
    description = fields.CharField()
    soldInStore = fields.BooleanField()
    upc = fields.CharField()
    images = fields.ListField()
    categories = fields.ListField()
    modalities = fields.ListField()
    customerFacingSize = fields.CharField()
    familyTree = fields.DictField()
    homeDeliveryItem = fields.BooleanField()
    shipToHome = fields.BooleanField()
    snapEligible = fields.BooleanField()
    taxonomies = fields.ListField()
    temperatureIndicator = fields.CharField()
    familyTreeV1 = fields.DictField()
    idV1 = fields.CharField()
    brand = fields.DictField()
    IsBopisEligible = fields.BooleanField()
    dimensions = fields.DictField()
    sellBy = fields.CharField()
    orderBy = fields.CharField()
    countriesOfOrigin = fields.CharField() # 
    weight = fields.CharField()
    romanceDescription = fields.CharField()
    ratings = fields.DictField()
    familyCode = fields.ListField()
    nutrition = fields.DictField()
    taxGroupCode = fields.CharField()
    hazmatFlag = fields.BooleanField()
    mimimumOrderQuantity = fields.IntegerField()
    maximumOrderQuantity = fields.IntegerField()
    tareValue = fields.IntegerField()
    alcoholFlag = fields.BooleanField()
    heatSensitive = fields.BooleanField()
    prop65Warning = fields.CharField()
    prop65 = fields.DictField()
    weightPerUnit = fields.CharField()
    monetizationId = fields.ListField()
    shipsWithColdPack = fields.BooleanField()
    isWeighted = fields.BooleanField()
    barCodes = fields.ListField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class priceModifiers(MongoModel):
    type = fields.CharField()
    amount = fields.FloatField()
    promotionId = fields.CharField()
    redemptions = fields.IntegerField()
    redemptionKeys = fields.ListField()
    total = fields.FloatField()
    couponType = fields.CharField()
    reportingCode = fields.CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Prices(MongoModel):
    value = fields.FloatField()
    quantity = fields.IntegerField()
    type = fields.CharField()
    upc = fields.CharField()
    utcTimestamp = fields.IntegerField()
    isPurchase = fields.BooleanField()
    locationId = fields.CharField()
    modalities = fields.ListField()
    effectiveDate = fields.CharField()
    expirationDate = fields.CharField()
    sellerKey = fields.IntegerField()
    offerIds = fields.CharField()
    transactionId = fields.CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Promotions(MongoModel):
    startDate = fields.CharField()
    value = fields.CharField()
    requirementQuantity = fields.IntegerField()
    id = fields.IntegerField()
    brandName = fields.CharField()
    categories = fields.ListField()
    imageUrl = fields.CharField()
    redemptionsAllowed = fields.IntegerField()
    terms = fields.CharField()
    shortDescription = fields.CharField()
    type = fields.CharField()
    expirationDate = fields.CharField()
    krogerCouponNumber = fields.CharField()
    productUpcs = fields.ListField()
    requirementDescription = fields.CharField()
    modalities = fields.ListField()
    endDate = fields.FloatField()
    isManufacturerCoupon = fields.BooleanField()
    offerCode = fields.CharField()
    companyName = fields.CharField()
    offerType = fields.CharField()
    redemptionFreq = fields.CharField()
    imageUrl2 = fields.CharField()
    offerGS1 = fields.CharField()
    cashbackCashoutType = fields.CharField()
    specialSavings = fields.ListField()
    clipStartDate = fields.FloatField()
    clipEndDate = fields.FloatField()
    enhancedImageUrl = fields.CharField()
    popularity = fields.IntegerField()
    clippedCount = fields.IntegerField()
    isSharable = fields.BooleanField()
    
    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Sellers(MongoModel):
    sellerId = fields.CharField()
    sellerName = fields.CharField()
    id = fields.IntegerField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Stores(MongoModel):
    locationId = fields.CharField()
    chain = fields.CharField()
    address = fields.DictField()
    geolocation = fields.DictField()
    name = fields.CharField()
    hours = fields.DictField()
    phone = fields.CharField()
    departments = fields.ListField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Trips(MongoModel):
    totalSavings = fields.FloatField()
    loyaltyId = fields.CharField()
    locationId = fields.CharField()
    terminalNumber = fields.CharField()
    transactionId = fields.CharField()
    tax = fields.ListField()
    tenderType = fields.CharField()
    total = fields.FloatField()
    subtotal = fields.FloatField()
    fulfillmentType = fields.CharField()
    utcTimestamp = fields.CharField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'

class Runs(MongoModel):
    function = fields.ListField()
    time = fields.FloatField()
    description = fields.CharField()

    class Meta:
        write_concern = WriteConcern()
        connection_alias = 'my-app'

class Users(MongoModel):
    userId = fields.CharField()
    loyaltyId = fields.CharField()
    trips = fields.ListField()

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = 'my-app'




