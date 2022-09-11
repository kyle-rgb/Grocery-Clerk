const fs = require('fs')
const js_summary = require('json-summary') 
const {difference} = require('set-operations')
const {MongoClient} = require('mongodb')
const util = require('util')
const { spawn } = require('child_process')

let targetDirs = [ '../../../scripts/requests/server/collections/fooddepot/items', '../../../scripts/requests/server/collections/fooddepot/coupons',
'../../../scripts/requests/server/collections/publix/items', '../../../scripts/requests/server/collections/publix/coupons',
'../../../scripts/requests/server/collections/aldi']

function cleanup(object){
    Object.entries(object).forEach(([k, v])=>{
        if (v && typeof v ==='object'){
            cleanup(v);
        }
        if (v && typeof v ==='object' && !Object.keys(v).length || v===null || v === undefined || v === '' || k === '__typename' || v === 'none' || (Object.keys(object).length===1 && typeof v === 'boolean' && !v)) {
            if (Array.isArray(object)) {
                object.splice(k, 1)
            } else {
                delete object[k];
            }
        }
    })
    return object
}

function insertData(listOfObjects, collectionName){
    if (listOfObjects.length===0) {
        throw new Error("bulkWrite Operations Cannot Write an Empty list!")
        return
    }
    const client = new MongoClient(process.env.MONGO_CONN_URL)
    const dbName = 'new'

    async function main(){
        await client.connect();
        console.log('Connected successfully to server')
        const db = client.db(dbName)
        const collection = db.collection(collectionName);
        let cursor = await collection.insertMany(listOfObjects)
        console.log(`inserted ${cursor.insertedCount} into ${collectionName}`)
        return 'done.'
    }

    main()
        .then(console.log)
        .catch(console.error)
        .finally(()=> client.close())
}

async function insertFilteredData(id, collectionName, newData = undefined, dbName = 'new'){
    const client = new MongoClient(process.env.MONGO_CONN_URL)
    await client.connect();
    console.log('Connected successfully to server')
    const db = client.db(dbName)
    const collection = db.collection(collectionName);
    var projection = {}
    projection[id] = 1
    var filters = {}
    filters[id] = {"$exists": true}
    let cursor = collection.find({...filters}, {'project': {...projection}})
    const results = await cursor.toArray()
    const currentSet = new Set(results.map((d)=> d[id]))
    newData = newData.filter((d)=> !currentSet.has(d[id]))
    if (newData.length===0){
        console.log('no new data to enter')
    } else {
        let ct = await collection.insertMany(newData)
        console.log('inserted ', ct.insertedCount, ' into ', collectionName)
    }
    client.close()
    return results
}

function processInstacartItems(target, defaultLocation=null, uuid){
    let storeRegex = /publix|aldi|kroger|dollargeneral|familydollar|fooddepot/
    let targetHeirarchy = target.match(storeRegex)
    targetHeirarchy = target.slice(targetHeirarchy.index)
    let allItems = []
    let allItemAttributes = []
    let allCollections = []
    let fullPrices = []
    let fullInventories = []
    let fullCollectionItemIds = []
    let t = 0
    let files = fs.readdirSync(target, {encoding: 'utf8', withFileTypes: true})
    files = files.filter((d)=> d.isFile())
    for (let file of files){
        console.log(file.name)
        file.name.slice(-9, -5) === "aldi" ? defaultLocation="23170": defaultLocation;
        data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
        data = JSON.parse(data)
        let collections = data.filter((d)=>d.url.includes('CollectionProducts'))
        let items = data.filter((d)=>d.url.includes('operationName=Items'))
        let itemAttributes = data.filter((d)=>d.url.includes('item_attributes'))
        let locationId = defaultLocation 
        console.log('collections.length', collections.length)
        console.log('items.length', items.length)
        console.log('item_attributes.length', itemAttributes.length)
        itemAttributes.map((d)=>{
            d.view.map((v)=>{
                fullPrices.push({
                    'utcTimestamp': new Date(d.acquisition_timestamp),
                    'item_id': v.trackingParams.item_id,
                    'quantity': 1,
                    'value': parseFloat(v.pricing.price.replace('$', '')),
                    'locationId': locationId,
                    'isPurchase': false
                });
                v.pricing.promotionEndsAt ? fullPrices.slice(-1)[0].expirationDate = new Date(v.pricing.promotionEndsAt) : v;
                allItemAttributes.push(cleanup(v))
            })
        })

        if (items.length > 0){
            items.map((d)=> {
                d.data.items.map((di)=>{
                    fullInventories.push({
                        'utcTimestamp': new Date(d.acquisition_timestamp),
                        'item_id': di.viewSection.trackingProperties.item_id,
                        'stockLevel': di.viewSection.trackingProperties.stock_level,
                        'locationId': locationId,
                        'availability_score': di.viewSection.trackingProperties.stock_level
                    })
                })
                allItems = allItems.concat(cleanup(d.data.items))
            })
        }
        if (collections.length > 0){
            collections.map((d)=>{
                d.data.collectionProducts.items.map((di)=>{
                    fullInventories.push({
                        'utcTimestamp': new Date(d.acquisition_timestamp),
                        'item_id': di.viewSection.trackingProperties.item_id,
                        'stockLevel': di.viewSection.trackingProperties.stock_level,
                        'locationId': locationId,
                        'availability_score': di.viewSection.trackingProperties.availability_score
                    })
                })
                fullCollectionItemIds = fullCollectionItemIds.concat(d.data.collectionProducts.itemIds)
                allItems = allItems.concat(cleanup(d.data.collectionProducts.items))
                let collections_entry = cleanup(d.data.collectionProducts.collection)
                collections_entry.itemIds = d.data.collectionProducts.itemIds;
                allCollections.push(collections_entry)
            })
        }

        let collectionProductsColumns = {
        'collection': ['id', 'name', 'slug', 'legacyPath', 'viewSection.trackingProperties.source_type/source_value/collection_type/collection_id/element_details.element_value/?parent_collection_id'],
        'items': ['id', 'name', 'size', 'productId', 'legacyId', 'legacyV3Id', 'quantityAttributes.quantityType/viewSection.unitString/unitAriaString',
        'availability.stockLevel', 'viewSection.itemImage.url/trackingProperties.element_details.product_id/retailer_location_id/?on_sale_ind./product_id,item_id,stock_level,availability_score,available_ind,?tags,?comboPromotions'],
        'itemAttributes': ['itemId', 'itemUpdatedAt', 'trackingParams.product_id/item_id/?policy_id/on_sale_ind.*/name/pricing.price/pricePerUnit/pricingUnit/productType/?promotionEndsAt/badge.*']
        }   
    }
    var toCollectionItems = []
    var uniqueItems = new Set()
    allItems.map((d)=> {
        if (!uniqueItems.has(d.id)){
            toCollectionItems.push({
                id: d.id,
                productId: d.productId,
                legacyId: d.legacyId,
                legacyV3Id: d.legacyV3Id,
                description: d.name,
                customerFacingSize: d.size,
                soldBy: d.quantityAttributes.viewSection.unitAriaString,
                images: [{url: d.viewSection.itemImage.url, perspective: 'front', main: true}],
            })
            d.tags ? toCollectionItems.slice(-1)[0].isStoreBrand = true : d;
            d.dietary ? 'attributeSections' in d.dietary.viewSection ? toCollectionItems.slice(-1)[0].dietary = d.dietary.viewSection.attributeSections.map((x)=>x.attributeString):  toCollectionItems.slice(-1)[0].dietary = d.dietary.viewSection.attributeString:  d;
            uniqueItems.add(d.id)
        }
    })


    allItemAttributes.map((d)=>{
        let matches = toCollectionItems.filter((y)=>y.legacyV3Id===d.itemId)
        if (matches.length>0){
            matches = matches[0]
            matches.pricingUnit ? matches.pricingUnit = d.pricing.pricingUnit : d;
            matches.productType = d.pricing.productType
            matches.priceAffix ? matches.priceAffix = d.pricing.priceAffix : d;
        }    
    })

    
    // console.log(util.inspect(toCollectionItems.slice(10, 14), false, null, true))
    console.log(toCollectionItems.length, fullPrices.length, fullInventories.length)
    insertFilteredData(uuid, "items", toCollectionItems)
    insertData(fullPrices, 'prices')
    insertData(fullInventories, 'inventories')
    fs.mkdirSync('../../../data/collections/'+targetHeirarchy, {recursive: true})
    for (file of files){
        fs.renameSync(target+file.name, `../../../data/collections/${targetHeirarchy}`+file.name)
    }

    return null

}

const zipUp = () => {
    const cmd = spawn("7z",["a","../../../data/archive.7z", "../../../data/collections" , "-mhe", "-sdel"])
    cmd.stdout.on("data", (data)=>{
        console.log(data.toString())
        if (data.includes("password")){
            cmd.stdin.write(process.env.EXTENSION_ARCHIVE_KEY+"\n", (err)=>{
                if (err){console.error(err)}
            })
        }
    })
    cmd.stderr.on("data", (data)=> {
        console.error("ERROR: ", data)
    })
    cmd.on("close", (code)=> console.log(`child process exited with a code of ${code}`))
    return null
}

function summarizeFoodDepot(target){
    // totalItems = 182,177
    // Items 
        // Categories.map((d)=>d.Id, d.ParentCategoryId?, d.PriorityRank, d.Name)
            // => item.categories = [{item.Categories.map((d)=> {return {code: d.Id, }})}]
        // Id <- main id, ProductCatalogueId
        // ImageUrl
        
        // IsAlcohol, IsTobacco
        // IsChargedByWeight, IsSoldByWeight
        // IsFeatured

        // MaxOrderQuantity, MinOrderQuantity, QuantityDefault, QuantityInterval
        // MeasuredCode = each | per lb
        // Name
        // Tags = [{Name, Value}] => {Kosher, Low Fat, Gluten Free, Dairy Free, Sugar Free, Lactose Free, Halal, Low Sodium, Fat Free, Organic, Vegan, Peanut Free, Egg Free}
            // Brand ==> x.toLowerCase()
        // TaxRate

    // Promotions
        // HasCoupons
    
    // Prices
        // Price
        // PriceRegular
        // PriceSaving = PriceRegular - Price
        // PriceType = StoreSpecial | Regular
        // ~Savings = Savings %
        // ?UnitPrice
        // ?WeightPerUnit

    //! Categories {DecorationImageUrl: x2, Id: x2, ImageUrl: x1, IsAlcohol:  x2, IsTobacco: x2, Name: , ParentCategoryId: x1, PriorityRank: x2 <- Greater Means More General Catagory, Version: x2}
        // Id, ParentCategoryId?, PriorityRank, Name :: Items
    //! Deposit 0 <- remove
    //! HasCoupons true/false :: Promotions
    //! Id :: Items
    //! ImageUrl :: Items
    //! IsAlcohol :: Items
    //! IsChargedByWeight :: Items 
    //! IsFeatured :: Items (monetizationId) | Promotions
    //! IsSoldByWeight :: Items 
    //! IsTobacco :: Items
    //! MaxOrderQuantity :: Items
    //! MeasureCode :: each | per lb
    //! MinOrderQuantity :: Items / Prices ? 
    //! Name :: Items
    // Price :: Prices
    // PriceRegular :: Prices
    // PriceSaving :: Prices 
    // PriceType :: StoreSpecial | Regular
    // ProductCatalogueId 
    // ProductOptionIds
    // PromotionId :: Promotions 
    // QuantityDefault :: Prices / Items 
    // QuantityInterval :: Prices / Items 
    // Savings <- Savings Percentage
    // Tags 224,440 / 156,196 [Name: {Brand, Kosher=Y, Low Fat=Y, Gluten Free=Y, Organic=Y, Fat Free=Y, 
        // Dairy Free, Sugar Free, Lactose Free, Halal, Low Sodium, Vegan, Peanut Free, Egg Free}]
        // lower to compare then title  :: Items {brandName, nutrition Info} 
    // TaxRate :: Prices
    // UnitOfMeasureText? average weight per = $8.75 per lb. Approx 1.75 lb each :: Prices
    // UnitPrice 840 :: Prices
    // WeightPerUnit 840 :: Prices
    target.endsWith('/') ? target : target+="/";
    let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    files = files.filter((d)=>d.isFile())
    var storeRegex = /fooddepot/
    let targetHeirarchy = target.match(storeRegex)
    targetHeirarchy = target.slice(targetHeirarchy.index)
    targetHeirarchy.endsWith("/") ? targetHeirarchy : targetHeirarchy+="/"; 
    var totalData = []
    var allPrices = []
    var allItems = []
    var itemIdSet = new Set()
    itemAttributes = new Set(['categories', 'Id', 'ProductCatalogueId', 'images', 'sellBy', 'orderBy', 'description', 'nutrition', 'brand', 'taxGroupCode'])
    for (let file of files){
        console.log(file.name)
        data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
        data = JSON.parse(data)
        totalData = totalData.concat(data)
        let items = data.filter((d)=>d.url.includes('products?'))
        for (let itemSet of items){
            let utcTimestamp = new Date(itemSet.acquisition_timestamp);
            let url = itemSet.url
            let path = url.split('/')
            let locationId = path[path.indexOf('stores')+1]
            itemSet = itemSet.Result.Products.map((d)=>cleanup(d))
            itemSet.map((item)=>{
                item.PriceSaving===0 ? allPrices.push({
                    isPurchase: false,
                    utcTimestamp: utcTimestamp,
                    value: Math.floor(item.Price*1.1*100)/100,
                    quantity: item.QuantityDefault,
                    id: item.Id,
                    locationId: locationId,
                    type: item.PriceType 
                }) : allPrices.push({
                    isPurchase: false,
                    utcTimestamp: utcTimestamp,
                    value: Math.floor(item.Price*1.1*100)/100,
                    quantity: item.QuantityDefault,
                    id: item.Id,
                    locationId: locationId,
                    type: item.PriceType
                }, {
                    isPurchase: false,
                    utcTimestamp: utcTimestamp,
                    value: Math.floor(item.PriceRegular*1.1*100)/100,
                    quantity: item.QuantityDefault,
                    id: item.Id,
                    locationId: locationId,
                    type: 'Regular'
                });
                if ('WeightPerUnit' in item){
                    allPrices.push({
                        isPurchase: false,
                        utcTimestamp: utcTimestamp,
                        value: Math.floor(item.UnitPrice*1.1*100)/100,
                        quantity: item.WeightPerUnit,
                        id: item.Id,
                        locationId: locationId,
                        type: 'Average'
                    })
                }

                item.categories = []
                item.Categories.map((d)=>{
                    if ('ParentCategoryId' in d){
                        item.categories.push({name: d.Name, id: d.Id})
                    } else {
                        item.categories.push({name: d.Name, id: d.Id})
                    }
                })
                item.images = [{url: item.ImageUrl, perspective: 'front', main: true, size: "medium"}]  
                delete item.ImageUrl
                item.desciption = item.Name;
                delete item.Name;
                if (item.IsSoldByWeight){
                    item.sellBy = 'WEIGHT'
                    item.orderBy = 'WEIGHT'    
                } else {
                    item.sellBy = 'UNIT'
                    item.orderBy = "UNIT"
                }
                
                if (item.Tags){
                    for (let tag of item.Tags){
                        if (tag.Name==='Brand'){
                            let brand = tag.Value.toLowerCase().trim().split(' ')
                            .map((word)=> {return word.charAt(0).toUpperCase() + word.slice(1)}).join(' ');
                            item.brand = brand
                        } else if (tag.Value==="Y") {
                            let nutritionalCategory = tag.Name.replace(' ', '')
                            item.nutrition===undefined ? item.nutrition = {} : 1; 
                            item.nutrition[nutritionalCategory] = true
                        }
                    }
                }

                item.taxGroupCode = item.TaxRate
                let itemDoc = {}
                Object.keys(item).filter((d)=>itemAttributes.has(d)).map((d)=> itemDoc[d]=item[d])
                if (!itemIdSet.has(itemDoc.Id)){
                    allItems.push(itemDoc)
                    itemIdSet.add(itemDoc.Id)
                }
                
            })
        }
    }
    insertFilteredData("Id", 'items', allItems)
    insertData(allPrices, 'prices')
    fs.mkdirSync('../../../data/collections/'+targetHeirarchy, {recursive: true})
    for (let file of files){
        fs.renameSync(target+file.name, `../../../data/collections/${targetHeirarchy}`+file.name)
    }

    return null
}

function summarizeNewCoupons(target, parser, uuid){
    // let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    // files = files.filter((d)=>d.isFile())
    // for (let file of files){
    //     console.log(file.name)
    //     data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
    // }
    // ---Publix---
    /* IsPersonalizationEnabled,
    PersonalizedStoreNumber = ~locationId from publix internal site,
    url = no relevant params,
    acquisition_timestamp,
    ---store data leaks--
    Stores, HolidaySummary, StatusCode, StatusMessage
    Savings { [
        "id": "hexString", 
        "dcId": 2880318,
        "?baseProductId": "RIO-PCI-207605",
        "waId": -2025301544,
        "savings": "$0.90",
        "finalPrice": 2.99,
        "?title": "Deer Park Spring Water, 100% Natural",
        "?description": "12 - 12 fl oz (355 ml) plastic bottles [144 fl oz ",
        "imageUrl": "https://...",
        "minimumPurchase": 1, 
        "redemptionsPerTransaction": 1,
        "originalDeal": 3.89,
        "originalMinimumPurchase": 2,
        "wa_startDate": "0001-01-01T00:00:00Z",
        "wa_endDate": "0001-01-01T00:00:00Z",
        "wa_startDateFormatted": "1/1",
        "wa_endDateFormatted": "1/1",
        "wa_postStartDate": "0001-01-01T00:00:00Z",
        "wa_postEndDate": "0001-01-01T00:00:00Z",
        "dc_startDate": "0001-01-01T00:00:00Z",
        "dc_endDate": "0001-01-01T00:00:00Z",
        "dc_startDateFormatted": "1/1",
        "dc_endDateFormatted": "1/1",
        "dc_popularity": 9999,
        "categories": ["grocery"] | ["beer-and-wine"] ... ,
        "brand": "4C",
        "savingType": "Tpr",
        "isPrintable": true/false,
        "isRelevant": true/false,
        "?relevancy": 1098,
        "isClipped": true/false,
        "isSneakPeak": true/false,
        "personalizationType": "Unknown",
        "?tprGroupId": 101315,
        "?Terms": 1088,
        "?enhancedImageUrl": "https...",
        "?finePrint": "(Only Sizes Marked &quot;Family Size&quot;)",
        "?department": "Crackers",
        "?additionalDealInfo": "SAVE UP TO $3.50",
        "?additionalSavings": "SAVE $1.00",
        "?dc_brand": "Publix",
        "?apiDescription": "Save $1.00 Off The Purchase of One (1) Publix...",
        "?priceQualifier": "WITH MFR DIGITAL COUPON",
    ] }

    ---Food Depot---
    {
        "offers": [ <= app cards
            {
                "details": "limit 1 coupon per purchase ...",
                "image": {
                    "links": {lg, md, sm}<= links to pictures,
                    "id": "66359",
                    "ratio": "square"
                },
                "description": "any One (1) of ..." ,
                "title": "$1.00 OFF",
                "offerId": "49744",
                "targetOfferId": "3370744",
                "brand": "Angel Soft Bath Tissue",
                "expireDateString": "Exp 07/10/22",
                "saveValue": "100",
                "offer_recommendation_flag": 0,
                "expireDate": "2022-07-10T23:59:59",
                "effectiveDate": "2022-05-29T00:01:00",
                "sameTransactionRedeem": false/true,
                "category": "Household" ,
                "offerType": "buy_x_get_y_at_z_dollars_off_trig_list",
                "activated": true/false,
            }
        ],
        "url": "",
        "acquistionTimestamp": Int,
        "HasErrors, HasNoErrors, Result <= Previous Store Level Data": null,
        "Result": [{
            "Brand": ,"Colgate Toothpaste" 
            "Category": "Personal Care",
            "DisplayEndDate": "2022-08-20T23:59:59",
            "DisplayStartDate": "2022-08-14T00:01:00",
            "ExpirationDate": "2022-08-20T23:59:59",
            "Id": 406 || 407,
            "ImageUrl": "https://appcard-web-images.s3.amazonaws.com/69329_200x200",
            "Index": 10,
            "IsItemLevel": true/false,
            "IsNew": true/false,
            "IsRedeemableOnline": true,
            "LongDescription": ' only one coupon per purchase ...',
            "RequirementDescription": "on THREE (3) bubly 8 packs",
            "ShortDescription": "$1.00 OFF",
            "Status": "Available",
            "Value": 1
        }]
    }
    
    */ 
    if (!parser){
        throw new Error('You Must Pass in a Parser to Parse!');
    }

    let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    files = files.filter((d)=>d.isFile())
    allCoupons = []
    let storesRegex = /fooddepot|publix/
    var parserKeys = Object.keys(parser)
    let targetHeirarchy = target.match(storesRegex)
    targetHeirarchy = target.slice(targetHeirarchy.index)
    targetHeirarchy.endsWith("/") ? targetHeirarchy : targetHeirarchy+="/"; 
    for (let file of files){
        console.log(target+"/"+file.name, files.length)
        data = fs.readFileSync(target+'/'+file.name, {encoding: 'utf-8'})
        let chunk = JSON.parse(data)
        if (!Array.isArray(chunk)){
            chunk = [chunk]
        }
        chunk = chunk.filter((d)=> d.url.includes('savings') || d.url.includes('coupons') || d.url.includes('offers'))
        chunk.map((d)=> cleanup(d))
        if (target.includes('fooddepot')){
            chunk = chunk.filter((d)=>d.url.includes('appcard'))
            chunk = chunk.map((d)=>{return d.offers})
            chunk = chunk.flat()
        } else {
            chunk = chunk.map((c)=>{return c.Savings}).flat()
        }
        
        chunk.map((d)=> {
            let newPromo = {}
            let relKeys = parserKeys.filter((pk)=> pk in d)
            for (let key of relKeys){
                let actions = parser[key]
                actions.convert ? d[key] = actions.convert(d[key]) : 0;
                actions.to ? newPromo[actions.to] = d[key] : 0;
                actions.keep ? newPromo[key] = d[key] : 0;
            }
            allCoupons.push(newPromo)
        })
    }
    
    insertFilteredData(uuid, 'promotions', allCoupons)
    fs.mkdirSync('../../../data/collections/'+targetHeirarchy, {recursive: true})
    for (let file of files){
        fs.renameSync(target+file.name, `../../../data/collections/${targetHeirarchy}`+file.name)
    }

    return null
}
function processFamilyDollarItems(target, defaultLocation="2394"){
    // need new for family dollar items => prices, items, promotions<-items 
    /* parser = {
            "id": "870e9eea-83dd-dfb7-fef7-0d9e9460f1ba",
            "area": "productionFamilyTree",
            "records": [{
                collection: "productionFDProducts", 
                allMeta: {
                    new: "N", 
                    display_price: "$5.50", // <prices> 
                    active_flag: true||false, 
                    canonical: "https://www.familydollar.com/aleve-pm-12-hours-pain-reliever-caplets/FD9000442", // <web link >
                    title: "Aleve PM 12 Hour Pain Reliever Caplets", // <item description>
                    show_web_store_flag: "Y", // item selling qualities <Boolean>, item's modalities (i.e. online)
                    visualVariant: {
                        nonvisualVariant: [{
                            available_in_store_only: "Y", // item's modalities 
                            split_case_available: "Y", // item's size options (quantity ranges)
                            meta_description: "Aleve PM 12 Hour Pain Reliever Caplets", // item's description 
                            height_dimension: "2 in.", // item's dimensions
                            width_dimension: "3.75 in.", // item's dimensions
                            depth_dimension: "1.5 in.", // items's dimensions
                            clearance: "N", // item's selling qualities <Boolean> 
                            sku_id: "900442", // item's id 
                            UPCs: "000000025866591882", // item's id <???>check to see if for individual item or pack / case of items>  
                            meta_keywords: "Aleve PM 12 Hour Pain Reliever Caplets", // item's web keywords 
                            minimum_quantity: 3, // item's minimumQuantity
                            DTDINDICATOR: "Y", // 42_251
                            volume_dimension: "4 oz.", // item's size
                            flavor: ["Honey"], // item categorization 
                            assortment_details: "10-ct Packs of Carepak? Clear Medium Nasal Strips", // pack assortment details ~item's categorization
                            length_dimension: "2.25 in.", //item's dimensions
                            weight_dimension: "7 oz.", // item's weight 10_280
                            scent: "Berry", // 5067 item's categorization 
                            gbi_features_and_benefits: ["Made in USA"], // item's categorization
                            diameter_dimension: "1.75 in.", // item's dimensions 
                            microwave_safe: "N", // item's qualities <Boolean> 
                            bedding_size: "T", // item's size qualities 
                            bpa_free: "Y",  // item's size qualities <Boolean> 
                            fit: "Infant/Toddler", // item's size qualities 
                            sock_size: "2T-4T", // item's size qualities 
                            wine_type: "Pink Wine", // item's categorization 
                            wine_varietal: "Pink Moscato", // item's categorization 
                            beverage_pack_size: "Single", // item's size (pack)
                            burn_time: "2 Hours", // item's category specific quantity
                            shoe_size:  "7", // item's size
                            gbi_nutritional_info: ["Gluten Free"], // item's nutritional info
                            gluten_free: "Y", // item's nutritional qualities <Boolean> 
                            sugar_free: "Y", // item's nutritional qualities <Boolean> 
                            window_treatment: "Curtain", // item's specific categorization 
                            curtain_type: "Rod Pocket Curtain", // item's specific categorization
                            valance_type: "Rod", // item's specific categorization 
                            gbi_care_and_cleaning: ["Microwave Safe"], // item's qualities 
                            dishwasher_safe: "Y", // item's qualities <Boolean> 
                            food_safe: "Y", // item's plastic qualities <Boolean> 
                            page_count: "13" // item's size (Books)
                        }],
                        image_file: "https://www.familydollar.com/ccstore/v1/images/?source=/file/v4531726475687999671/products/FD900442.jpg&height=940&width=940", // item's ImageUrl
                        colors: "Clear", // item's qualities 
                        material: "Elastic", // item's qualities 
                        pattern: "Striped", // item's qualities 
                        finnish: "Metallic", // item's qualities 
                        assortment_by_style_color: "Event Assortment"
                    },
                    shop_by: "In Store Only", // item's modalities 
                    price: 99.99, // prices
                    product_id: "900442", // item id 
                    name: "Aleve PM 12 Hours", // item name / description 
                    split_case_multiple: "3", // item's sellBy multiple 
                    attributes: [{
                        split_case_available: "Y", // item selling quantities <Boolean>
                        call_center_only: "N", // item selling qualties <Boolean>
                        average_rating_rounded: 3, // item's ratings
                        average_rating_andup: [1, 2, 3, 4], // item's ratings
                        case_price: 198, // prices :: item bulk quantities
                        casepack: "36", // prices quantity :: item's soldBy the { n } case 
                        num_reviews: 375, // item's ratings
                        average_rating: 4.8827, // item's ratings
                        combustible: "Y", // item qualities <Boolean> 
                        display_type: "Peggable", // item web qualities 
                        requires_batteries: "Y", // item's qualities <Boolean>
                        battery_size: "AA", // item's qualities <Boolean>
                        licensed_product: ["Dreamworks&reg; Trolls&trade"], // item's Brand Names (need to be decoded of HTML text)
                        comes_with_batteries: "Y", // item's qualities <Boolean> 
                        flammable: "Y", // item's qualities <Boolean> 
                        arrival_date:  "20211019", // item's modalities specific data 
                        contains_wheat: "Y", // item's nutritional tags <Boolean>
                        contains_dairy: "Y", // item's nutritional tags  <Boolean>
                        contains_nuts: "Y", // item's nutritional tags  <Boolean>
                        contains_soy: "Y", // item's nutritional tags  <Boolean>
                        contains_egg: "Y", // item's nutritional tags  <Boolean>
                        collection:  "Birthday", // further categorical data for item
                        pet: "Cat" , // <category> 
                        travel_size: "Y" // item's packaging info <Boolean> 

                    }],
                    id: "9004422", // product <id>
                    categories: [{ // item's familyTree, item's categories
                        "1": "Department", 
                        "2": "Health & Wellness",
                        "3": "Medicines & Treatments",
                        "4": "Pain Relievers",
                        "leaf": "Pain Relievers"
                    }],
                    brand: ["Aleve&reg;"],  // brandName
                    categoryId: ["fs-pain-relievers"], // <item category>
                    description: "As a parent, you know how tough it is when your child is sick. You can help them recover faster with Children's Triaminic® Multi-Symptom Fever&Cold Medicine.\
                    Tiraminic® provides relief from fever, runny and stuffy nose, aches and pains, sore throat, and cough. Plus, the grape flavor helps it go down easily.\
                    You'll feel better when they feel better. For children ages 6-11. A full case includes 24 bottles of medicine.", // static item descriptor == romanceDescrition
                    badges: [{  // boolean categories
                        made_in_usa: "Y",
                        wow: "Y",
                        limited_quantities: "Y",
                        bonus_buy: "Y", 
                    }],
                    dry_clean_only: "N", // boolean categories
                    _groupbyinc: {clickBoost: 21},
                    sale_price: "0.00", // prices
                    clearence: "N", // boolean categories
                    promo_price: "Sale", // promotional price type
                    apparel_size: "Unisex One Size Fits Most" , // item sizes 

                },
                _id: "adf49fdc76689a5a5d6b629743492fa7", // <id> 
                _u: "https://dollartree1productionFDProducts.com/900442", // <web::id>
                _t: "Aleve PM 12 Hour Pain Reliever Caplets" // <item description>
            }],
            "totalRecordCount": 5184,
            "biasingProfile": "DefaultBiasing",
            "template": {name: "default"},
            "pageInfo": {recordStart: 1, recordEnd: 4992},
            "matchStrategy": { // sdel
                "name": "Strong Match",
                "rules": [{
                    terms: 3,
                    mustMatch: 80,
                    percentage: false,
                    termsGreaterThan: 4
                }]
            },
            "warnings": ["selected sort field 'shop_by_sort' does not exist in any record"],
            "availableNavigation": [{ // <sdel>
                name: "visualVariant.nonvisualVariant.available_in_store_only",
                displayName: "Product Availability",
                type: "Value",
                refinements: {type: "Value", count: 4058, value: "N"},
                range: false||true,
                or: true||false,
                modeRefinements: true||false,
            }],
            "selectedNavigation": [{ // <sdel>
                name: "categories.1",
                displayName: "Categories L1",
                refinements: [{
                    type: "Value", value: "Department"
                }],
                _id: "4641bce57677ced52b4483c82c959dc0",
                range: true||false,
                or: true||false,
            }],
            "originalRequest": { // <sdel>
                collection: "productionFDProducts",
                area: "productionFamilyDollar",
                skip: 5280,
                pageSize: 96,
                disableAutocorrection: false||true,
                sort: [{
                    type: "Field",
                    field: "new",
                    order: "Descending",
                }],
                fields: ["*"],
                refinements: [{
                    type: "Value",
                    navigationName: "categories.1",
                    value: "Department"
                }], 
                pruneRefinements: true||false, 
            },
            "metadata": { //<for prices>
                cached: true||false,
                recordLimitReach: true||false,
                totalTime: 126,
                experiment: {experimentId: "gbi-wisdom-also-bought", experimentVariant: "ab-v-1"}
            },
            "empty": "N", // <sdel> 
            "url": {}, // <sdel> 
            "acquisition_timestamp": Number // <for prices>
    }*/
    
    var newParser = {
        combustible: {keep: true},
        made_in_usa: {keep: true},
        flammable: {keep: true},
        microwave_safe: {keep: true},
        bpa_free: {keep: true},
        dry_clean_only: {keep:true},
        dishwasher_safe: {keep: true},
        travel_size: {keep: true},
        food_safe: {keep: true},
        scent: {keep: true},
        flavor: {keep: true},
        wine_type: {keep:true},
        wine_varietal: {keep: true},
        id: {keep: "true"},
        description: {to: "romanceDescription", convert: function(x){return `<p>${x}</p>`}},
        minimum_quantity: {to: "minimumOrderQuantity"},
        categories: {to: "taxonomies", convert: function(x){
            let cats = x[0]
            let cparse = {"2": "department", "3": "commodity", "4": "subCommodity"}
            Object.keys(cats).map((k)=> {
            if (Object.keys(cparse).includes(k)){
                cats[cparse[k]] = cats[k]
                delete cats[k];
            } else {
                delete cats[k];
            }})
            return cats;
        }},
        UPCS: {to: "upc"},
        canonical: {to: "link"}
    }
    let storeRegex = /publix|aldi|kroger|dollargeneral|familydollar|fooddepot/
    let targetHeirarchy = target.match(storeRegex)
    targetHeirarchy = target.slice(targetHeirarchy.index)
    var allItems = []
    var allPrices = []
    let files = fs.readdirSync(target).map((d) => {
        let data = JSON.parse(fs.readFileSync(target+d)).map((x)=>cleanup(x))
        data=data.filter((d)=>"records" in d)
        data.map((z)=> z.records.map((r)=> r["utcTimestamp"]=z.acquisition_timestamp))
        allItems= allItems.concat(data.map((e)=>e.records).flat())
        allItems=allItems.filter((d)=>d)
        console.log(`parsed ${d}. ${allItems.length}`)

    })
    
    allItems = allItems.map((x)=> {
        let am =  x['allMeta']
        if ("badges" in am){
            let badges = am["badges"][0]
            delete am["badges"]
            am = {...am, ...badges}
        }
        delete x["allMeta"]
        let vv = am['visualVariant'][0]['nonvisualVariant'][0]
        delete am['visualVariant'];
        let attr = am['attributes'][0]
        delete am['attributes']
        x = {...am, ...vv, ...attr, ...x}
        Object.entries(x).map(([k, v])=> {if (v==="Y"){x[k]=true} else if (v==="N") {x[k]=false}})
        return x
    }).filter((d)=>"minimum_quantity" in d)
    
    allItems.map((d)=>{
        // minimumQuantity, Case, Sale if Exists
        allPrices.push({
            "quantity": d.minimum_quantity,
            locationId: defaultLocation, 
            isPurchase: false,
            utcTimestamp: new Date(d.utcTimestamp), 
            value: d.price
        })
        d.upc ? allPrices.slice(-1)[0]['upc'] = d.upc : allPrices.slice(-1)[0]['id'] = d.id ;
        // for Case
        if (d.minimum_quantity != d.casepack){
            allPrices.push({
                "quantity": +d.casepack,
                locationId: defaultLocation, 
                isPurchase: false,
                utcTimestamp: new Date(d.utcTimestamp), 
                value: d.price
            })
            d.upc ? allPrices.slice(-1)[0]['upc'] = d.upc : allPrices.slice(-1)[0]['id'] = d.id ;
        }

        if (d.sale_price && d.sale_price!=="0.00"){
            allPrices.push({
                "quantity": d.minimum_quantity,
                locationId: defaultLocation, 
                isPurchase: false,
                utcTimestamp: new Date(d.utcTimestamp), 
                value: d.sale_price
            })
            d.upc ? allPrices.slice(-1)[0]['upc'] = d.upc : allPrices.slice(-1)[0]['id'] = d.id ;
            d.promo_price ? allPrices.slice(-1)[0]['type'] = d.promo_price : null ; 
            if (d.minimum_quantity!=d.casepack){
                allPrices.push({
                    "quantity": +d.casepack,
                    locationId: defaultLocation, 
                    isPurchase: false,
                    utcTimestamp: new Date(d.utcTimestamp), 
                    value: d.sale_price
                })
                d.upc ? allPrices.slice(-1)[0]['upc'] = d.upc : allPrices.slice(-1)[0]['id'] = d.id ;
                d.promo_price ? allPrices.slice(-1)[0]['type'] = d.promo_price : null ; 
            }
            
        }
    })

    allItems.map((x)=> {
        Object.keys(x).map((nk)=>{
            if (nk.startsWith("contains") || nk.startsWith("sugar") || nk.startsWith("gluten")){
                nk.endsWith("free") ? nk=nk.slice(0, -1): nk;
                let nutObj = {}
                if (nk.endsWith("free")){
                    let newKey = nk.split("_").map((str)=> str[0].toUpperCase() +str.slice(1))
                    nutObj[newKey] = x[nk]
                } else if (nk.startsWith("contains")){
                    let newKey = nk.split("_").slice(-1).map((str)=> str[0].toUpperCase() +str.slice(1) + "Free").join("")
                    nutObj[newKey] = !x[nk]
                }
                "nutrition" in x ? x["nutrition"] = {...x["nutrition"], ...nutObj}: x["nutrition"] = nutObj;
                delete x[nk]; 
            } else if (nk.startsWith("weight")){
                x["weight"] = x[nk]
                delete x[nk];
            } else if (nk.endsWith("_dimension")){ 
                let dimObj = {}
                dimObj[nk.replace("_dimension", "")] = x[nk]
                "dimensions" in x ? x["dimensions"] = {...x.dimensions, ...dimObj} : x["dimensions"] = dimObj;
                delete x[nk];
            } else if (nk === "available_in_store_only" && x[nk]){
                x["modalities"] = ["IN_STORE"]
                delete x[nk];
            } else if (nk === "call_center_only" && x[nk]){
                x["modalities"] = ["CALL_CENTER"]
                delete x[nk];
            } else if (nk==="brand"){
                brands = x[nk]
                x[nk] = brands.map((brand)=>{return{name:  brand.replaceAll(/&.+;/g, '')}})
            } else if (nk==="num_reviews" && x[nk]){
                x["ratings"] = {ct: x[nk], avg: x["average_rating"]}
                delete x[nk];
                delete x["average_rating"]
            } else if (nk==="name"){
                let name = x[nk]
                name = name.replace("?", "")
                let customerFacingSize = name.split(",").slice(1).filter((s)=>s.match(/\d+/g)!==null).map((match)=>{return match.trim()})
                x[nk] = name.split(",")[0]
                if (!customerFacingSize===""){
                    x["customerFacingSize"] = customerFacingSize.reverse().join(" / ")
                }
                x["description"] = x[nk]
                delete x[nk];
                
            } else if (Object.keys(newParser).includes(nk)){
                let actions = newParser[nk]
                if (newParser[nk].convert){
                    x[nk] = actions.convert(x[nk])
                }
                if (actions.to){
                    x[actions.to] = x[nk];
                }
                if (actions.keep===undefined){
                    delete x[nk]
                }

            } else {
                delete x[nk]
            }
            
        })
    })
    let idSet = new Set()
    allItems = allItems.filter((i)=>{
        if (idSet.has(i.id)){
            return false;
        } else {
            idSet.add(i.id)
            return true
        }
    })
    insertData(allPrices, "prices")
    insertFilteredData("id", "items", allItems)
    fs.mkdirSync('../../../data/collections/'+targetHeirarchy, {recursive: true})
    files = fs.readdirSync(target)
    for (let file of files){
       fs.renameSync(target+file, `../../../data/collections/${targetHeirarchy}`+file)
    }
    return null
}


// processInstacartItems('../../../scripts/requests/server/collections/publix/items/', "121659", uuid="legacyId")
// processInstacartItems('../../../scripts/requests/server/collections/aldi/items/', "23150", uuid="legacyId")
// summarizeNewCoupons("../../../scripts/requests/server/collections/publix/coupons/", {
//     "id": {keep: true},
//     "dcId": {keep: true},
//     "waId": {keep: true},
//     "savings": {to: "value", convert: function(x){let n =  Number(x.replaceAll(/.+\$/g, '')); if (isNaN(n)){n=x} return n}},
//     "description": {to: "shortDescription"},
//     "redemptionsPerTransaction" : {to: "redemptionsAllowed"},
//     "minimumPurchase": {to: "requirementQuantity"},
//     "categories": {keep: true},
//     "imageUrl": {keep: true},
//     "brand": {to: "brandName"},
//     "savingType": {to: "type"},
//     "dc_popularity": {to: "popularity"}
// }, uuid="id")
// summarizeFoodDepot('../../../scripts/requests/server/collections/fooddepot/items/')
// summarizeNewCoupons("../../../scripts/requests/server/collections/fooddepot/coupons/", {
//     "saveValue": {to: "value", convert: function (x) {return Number(x/100)}},
//     "expireDate": {to: "endDate", convert: function (x) {return new Date(x)}},
//     "effectiveDate": {to: "endDate", convert: function (x) {return new Date(x)}},
//     "offerId": {keep: true},
//     "targetOfferId": {keep: true},
//     "category": {to: "categories", convert: function(x) {return [x]}},
//     "image": {to: "imageUrl", convert: function (x){return x.links.lg}},
//     "brand": {to: "brandName"},
//     "details": {to: "terms"},
//     "offerType": {to: "type" }
// }, uuid="targetOfferId")
//processInstacartItems('../../../scripts/requests/server/collections/familydollar/instacartItems/', "2394", uuid="legacyId")
processFamilyDollarItems("../../../scripts/requests/server/collections/familydollar/items/", defaultLocation="2394")
zipUp()