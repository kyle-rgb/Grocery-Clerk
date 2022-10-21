# Calls to Transform Nodejs Script
* Publix:
  > store id = 121659 {via instacart}
    - Items:
      - `processInstacartItems('../../../scripts/requests/server/collections/publix/items/', "121659", uuid="legacyId")`
    - Coupons:
      - `summarizeNewCoupons("../../../scripts/requests/server/collections/publix/coupons/", {
        "id": {keep: true},
        "dcId": {keep: true},
        "waId": {keep: true},
        "savings": {to: "value", convert: function(x){let n =  Number(x.replaceAll(/.+\$/g, '')); if (isNaN(n)){n=x} return n}},
        "description": {to: "shortDescription"},
        "redemptionsPerTransaction" : {to: "redemptionsAllowed"},
        "minimumPurchase": {to: "requirementQuantity"},
        "categories": {keep: true},
        "imageUrl": {keep: true},
        "brand": {to: "brandName"},
        "savingType": {to: "type"},
        "dc_popularity": {to: "popularity"}
        }, uuid="id")`
* Aldi:
  > store id = 23150 {via instacart}
  * Items:
    * `processInstacartItems('../../../scripts/requests/server/collections/aldi/items/', "23150", uuid="legacyId")`
* Family Dollar:
  > store_id = 2314 {not via instacart} 
  * Items:
    * `processFamilyDollarItems("../../../scripts/requests/server/collections/familydollar/items/", defaultLocation="2394")`
  * Instacart Items:
    * `processInstacartItems('../../../scripts/requests/server/collections/familydollar/instacartItems/', "2394", uuid="legacyId")`
  * Coupons
    * `summarizeNewCoupons("../../../scripts/requests/server/collections/familydollar/coupons/", {
        "mdid": {to: "id"},
        "brand": {to: "brandName"},
        "offerType": {to: "type"},
        "description": {to: "shortDescription"},
        "terms": {keep: true},
        "category": {to: "categories", convert: (x)=>{
            return x.name
        }},
        "tags": {to: "categories", convert: (x)=> {
            return x.map((d)=>d.replace(/fd-/, '').trim().split('-').map((d)=>d[0].toUpperCase()+d.slice(1).toLowerCase()).join('-')).flat()
        }},
        "redemptionStartDateTime": {to: 'startDate', convert: (x)=> new Date(x.iso)},
        "expirationDateTime": {to: 'expirationDate', convert: (x)=> new Date(x.iso)},
        "clipStartDateTime": {to: 'clipStartDate', convert: (x)=> new Date(x.iso)},
        "clipEndDateTime": {to: 'clipEndDate', convert: (x)=> new Date(x.iso)},
        "offerSortValue": {to: 'value', convert: (x)=>+x},
        "minPurchase": {to: 'requirementQuantity', convert: (x)=>+x},
        "redemptionsPerTransaction": {to: 'redemptionsAllowed'},
        "imageUrl": {keep: true},
        "enhancedImageUrl": {keep: true},
        "type": {to: "isManufacturerCoupon", convert: (x)=>x==="mfg"? true:false},
        "popularity": {keep: true},
        "clippedCount": {keep: true}
    }, uuid="id")`
* Food Depot:
  > locationId = 407 {exists in url}
  * Items:
    * `summarizeFoodDepot('../../../scripts/requests/server/collections/fooddepot/items/')`
  * Coupons:
    * `summarizeNewCoupons("../../../scripts/requests/server/collections/fooddepot/coupons/", {
        "saveValue": {to: "value", convert: function (x) {return Number(x/100)}},
        "expireDate": {to: "endDate", convert: function (x) {return new Date(x)}},
        "effectiveDate": {to: "endDate", convert: function (x) {return new Date(x)}},
        "offerId": {keep: true},
        "targetOfferId": {keep: true},
        "category": {to: "categories", convert: function(x) {return [x]}},
        "image": {to: "imageUrl", convert: function (x){return x.links.lg}},
        "brand": {to: "brandName"},
        "details": {to: "terms"},
        "offerType": {to: "type" }
        }, uuid="targetOfferId")`
* Dollar General
  > locationId = 13141
  * Items:
    * ``processDollarGeneralItems("../../../scripts/requests/server/collections/dollargeneral/items", couponParser={
        OfferCode: {to: "offerCode"},
        OfferGS1: {to: "offerGS1", bool: true},
        OfferDescription: {to: "shortDescription", convert: (x)=> {
            if (x.OfferSummary.match(/^save/i)){
                if (x.OfferDescription.match(/^on[^e]/i)) x.OfferDescription = " " + x.OfferDescription;
                else x.OfferDescription = " on " + x.OfferDescription;
                return x.OfferSummary + x.OfferDescription
            } else {
                return x.OfferDescription 
            }
        }},
        BrandName: {to: "brandName"},
        CompanyName: {to: "companyName"},
        OfferType: {to: "offerType"},
        OfferDisclaimer: {to: "terms", bool: true},
        IsManufacturerCoupon: {to: "isManufacturerCoupon"},
        RewaredCategoryName: {to: "categories"},
        OfferActivationDate: {to: "startDate", convert: (dateMyTz)=> {return new Date(dateMyTz)}},
        OfferExpirationDate: {to: "expirationDate", convert: (dateMyTz)=> {return new Date(dateMyTz)}},
        RewaredOfferValue: {to: "value"},
        MinQuantity: {to: "requirementQuantity"},
        RedemptionLimitQuantity: {to: "redemptionsAllowed"},
        RecemptionFrequency: {to: "redemptionFreq"},
        Image1: {to: "imageUrl"},
        Image2: {to: "imageUrl2"},
        OfferID: {to:"productUpcs", convert: (offerId, mapWithItemKeys) => {
            return offerId in mapWithItemKeys ? Array.from(mapWithItemKeys[offerId]) : [];
        }}
    },
    itemParser={
        UPC: {to: "upc"},
        Description: {to: "description"},
        Image: {to: "images", convert: (img)=> {
            return [{url: img, perspective: 'front', main: true, size: "xlarge"}]
        }},
        IsSellable: {to: "soldInStore"}, 
        IsBopisEligible: { keep: 1},
        IsGenericBrand: {keep: 1},
        modalities: {create: (item)=> {
            let mParse = {"IsSellable": "IN_STORE", "isShipToHome": "SHIP", "isPopshelfShipToHome": "SHIP", "IsBopisEligible": "PICKUP"}
            return Object.entries(item).map(([k, v])=> {return k in mParse && v? k : 0;}).filter((k)=>k).map((truthyKey)=> {return mParse[truthyKey]})
        }, to: "modalities"},
        RatingReviewCount: {bool: 0, to: "ratings", convert: (ratingCount, ratingAverage)=> {
            if (ratingCount){
                return {avg: ratingAverage, ct: ratingCount}
            }
        }},
        Categories: {bool:true, convert: (x)=> {
            return x.split("|")
        }},
        _prices: {convert: (full_item, locationId, utcTimestamp) => { 
            let returnValues = [];
            returnValues.push({"value": full_item.OriginalPrice, "type": "Regular", "isPurchase": false,
            "locationId": locationId, "utcTimestamp": utcTimestamp, "upc": full_item.UPC, "quantity": 1,
            modalities: full_item.modalities });
            if (full_item.OriginalPrice !== full_item.Price){
                returnValues.push({"value": full_item.Price, "type": "Sale", "isPurchase": false,
                "locationId": locationId, "utcTimestamp": utcTimestamp, "upc": full_item.UPC, "quantity": 1,
                modalities: full_item.modalities });
            }
            return returnValues;
        }},
        _inventories: {convert: (full_item, locationId, utcTimestamp)=> {
            let itemStatus = full_item.InventoryStatus; 
            itemStatus = itemStatus ==1? "TEMPORARILY_OUT_OF_STOCK" : itemStatus == 2 ? "LOW" : "HIGH"; 
            return {"stockLevel": itemStatus, "availableToSell": full_item.AvailableStockStore, "locationId": locationId,
            "utcTimestamp": new Date(utcTimestamp), "upc": full_item.UPC}
        }}
    })``
  * Coupons:
    * `processDollarGeneralItems("../../../scripts/requests/server/collections/dollargeneral/promotions", couponParser={
        OfferCode: {to: "offerCode"},
        OfferGS1: {to: "offerGS1", bool: true},
        OfferDescription: {to: "shortDescription", convert: (x)=> {
            if (x.OfferSummary.match(/^save/i)){
                if (x.OfferDescription.match(/^on[^e]/i)) x.OfferDescription = " " + x.OfferDescription;
                else x.OfferDescription = " on " + x.OfferDescription;
                return x.OfferSummary + x.OfferDescription
            } else {
                return x.OfferDescription 
            }
        }},
        BrandName: {to: "brandName"},
        CompanyName: {to: "companyName"},
        OfferType: {to: "offerType"},
        OfferDisclaimer: {to: "terms", bool: true},
        IsManufacturerCoupon: {to: "isManufacturerCoupon"},
        RewaredCategoryName: {to: "categories"},
        OfferActivationDate: {to: "startDate", convert: (dateMyTz)=> {return new Date(dateMyTz)}},
        OfferExpirationDate: {to: "expirationDate", convert: (dateMyTz)=> {return new Date(dateMyTz)}},
        RewaredOfferValue: {to: "value"},
        MinQuantity: {to: "requirementQuantity"},
        RedemptionLimitQuantity: {to: "redemptionsAllowed"},
        RecemptionFrequency: {to: "redemptionFreq"},
        Image1: {to: "imageUrl"},
        Image2: {to: "imageUrl2"},
        OfferID: {to:"productUpcs", convert: (offerId, mapWithItemKeys) => {
            return offerId in mapWithItemKeys ? Array.from(mapWithItemKeys[offerId]) : [];
        }}
    },
    itemParser={
        UPC: {to: "upc"},
        Description: {to: "description"},
        Image: {to: "images", convert: (img)=> {
            return [{url: img, perspective: 'front', main: true, size: "xlarge"}]
        }},
        IsSellable: {to: "soldInStore"}, 
        IsBopisEligible: { keep: 1},
        IsGenericBrand: {keep: 1},
        modalities: {create: (item)=> {
            let mParse = {"IsSellable": "IN_STORE", "isShipToHome": "SHIP", "isPopshelfShipToHome": "SHIP", "IsBopisEligible": "PICKUP"}
            return Object.entries(item).map(([k, v])=> {return k in mParse && v? k : 0;}).filter((k)=>k).map((truthyKey)=> {return mParse[truthyKey]})
        }, to: "modalities"},
        RatingReviewCount: {bool: 0, to: "ratings", convert: (ratingCount, ratingAverage)=> {
            if (ratingCount){
                return {avg: ratingAverage, ct: ratingCount}
            }
        }},
        Categories: {bool:true, convert: (x)=> {
            return x.split("|")
        }},
        _prices: {convert: (full_item, locationId, utcTimestamp) => { 
            let returnValues = [];
            returnValues.push({"value": full_item.OriginalPrice, "type": "Regular", "isPurchase": false,
            "locationId": locationId, "utcTimestamp": utcTimestamp, "upc": full_item.UPC, "quantity": 1,
            modalities: full_item.modalities });
            if (full_item.OriginalPrice !== full_item.Price){
                returnValues.push({"value": full_item.Price, "type": "Sale", "isPurchase": false,
                "locationId": locationId, "utcTimestamp": utcTimestamp, "upc": full_item.UPC, "quantity": 1,
                modalities: full_item.modalities });
            }
            return returnValues;
        }},
        _inventories: {convert: (full_item, locationId, utcTimestamp)=> {
            let itemStatus = full_item.InventoryStatus; 
            itemStatus = itemStatus ==1? "TEMPORARILY_OUT_OF_STOCK" : itemStatus == 2 ? "LOW" : "HIGH"; 
            return {"stockLevel": itemStatus, "availableToSell": full_item.AvailableStockStore, "locationId": locationId,
            "utcTimestamp": new Date(utcTimestamp), "upc": full_item.UPC}
        }}
    })`