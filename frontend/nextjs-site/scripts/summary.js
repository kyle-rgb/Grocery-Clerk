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

function readAndMove(target){
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
        let locationId = "121659" // col[0].data.collectionProducts.items[0].id.match(/items_(\d+)-\d+/)[1] | aldi =  "23150" | publix = "121659"
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
    fs.mkdirSync('../../../data/raw/aldi', {recursive: true})
    for (file of files){
        fs.renameSync(target+file.name, '../../../data/raw/aldi/'+file.name)
    }

    exec(`7z a ../../../data/archive.7z ../../../data/raw -p${process.env.EXTENSION_ARCHIVE_KEY} -mhe -sdel`, (err, stdout, stderr)=>{
        console.log(`stdout: ${stdout}`)
    })

    return null

}

readAndMove('../../../scripts/requests/server/collections/publix/items/')


// console.log(util.inspect(toCollectionItems.slice(10, 14), false, null, true))
