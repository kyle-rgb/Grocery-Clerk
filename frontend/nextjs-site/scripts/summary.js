const fs = require('fs')
const js_summary = require('json-summary') 
const {difference} = require('set-operations')
const {MongoClient} = require('mongodb')
const util = require('util')
const { exec } = require('child_process')

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

function readAndMove(target, defaultLocation=null){
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
    insertData(toCollectionItems, 'items')
    insertData(fullPrices, 'prices')
    insertData(fullInventories, 'inventories')
    fs.mkdirSync('../../../data/raw/'+targetHeirarchy, {recursive: true})
    for (file of files){
        fs.renameSync(target+file.name, `../../../data/raw/${targetHeirarchy}`+file.name)
    }

    return null

}

const zipUp = () => {
    exec(`7z a ../../../data/archive.7z ../../../data/raw -p${process.env.EXTENSION_ARCHIVE_KEY} -mhe -sdel`, (err, stdout, stderr)=>{
        console.log(`stdout: ${stdout}`)
    })
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
    let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    files = files.filter((d)=>d.isFile())
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
    
    // console.log(allItems.length, ' items')
    // console.log(allPrices.length, ' prices')
    insertData(allItems, 'items')
    insertData(allPrices, 'prices')

    return null
}

function summarizeNewCoupons(target){
    // let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    // files = files.filter((d)=>d.isFile())
    // for (let file of files){
    //     console.log(file.name)
    //     data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
    // }
    // ---Publix---
    /* IsPersonalizationEnabled,
    PersonalizedStoreNumber = locationId,
    url = no relevant params,
    acquisition_timestamp,
    Stores, HolidaySummary, StatusCode, StatusMessage
    Savings {  }
    
    */ 



    let files = fs.readdirSync(target, {encoding: 'utf-8', withFileTypes: true})
    files = files.filter((d)=>d.isFile())
    allCoupons = []
    let storesRegex = /fooddepot|publix/
    for (let file of files){
        console.log(file.name)
        data = fs.readFileSync(target+'/'+file.name, {encoding: 'utf-8'})
        let chunk = JSON.parse(data)
        if (!Array.isArray(chunk)){
            chunk = [chunk]
        }
        chunk.map((d)=> cleanup(d))
        allCoupons = allCoupons.concat(chunk)
    }
    let summary = JSON.stringify(js_summary.summarize(allCoupons, {arraySampleCount: allCoupons.length}), null, 3)
    let endName=target.split(/\//).map((d)=>d.match(storesRegex)).filter((d)=>d!==null)[0][0]
    console.log(endName)
    fs.writeFileSync(`./${endName}-summary.json`, summary)
    return null
}
summarizeNewCoupons("../../../scripts/requests/server/collections/publix/coupons")
summarizeNewCoupons("../../../scripts/requests/server/collections/fooddepot/coupons")
// readAndMove('../../../scripts/requests/server/collections/publix/items/', "121659")
// readAndMove('../../../scripts/requests/server/collections/aldi/', "23150")
// summarizeFoodDepot('../../../scripts/requests/server/collections/fooddepot/items')
// zipUp()
