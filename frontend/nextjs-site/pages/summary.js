const fs = require('fs')
const js_summary = require('json-summary') 
const {difference} = require('set-operations')
const {MongoClient} = require('mongodb')

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


// aldi : graphql?operationName=Items
    //  : item_attributes/...item_trackingParams.item_id,...
    // : opetationName=collectionProductsWithFeaturedProducts 
function readAndMove(target){
    let allItems = []
    let allItemAttributes = []
    let allCollections = []
    let fullPrices = []
    let fullInventories = []
    let files = fs.readdirSync(target, {encoding: 'utf8', withFileTypes: true})
    files = files.filter((d)=> d.isFile())
    let iter = 0
    for (let file of files){
        console.log(file.name)
        data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
        data = JSON.parse(data)
        let collections = data.filter((d)=>d.url.includes('CollectionProducts'))
        let items = data.filter((d)=>d.url.includes('operationName=Items'))
        let itemAttributes = data.filter((d)=>d.url.includes('item_attributes'))
        let locationId = "23150" // col[0].data.collectionProducts.items[0].id.match(/items_(\d+)-\d+/)[1] | "23150"

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
                v.pricing.promotionEndsAt ? fullPrices.slice(-1)[0].expirationDate = v.pricing.promotionEndsAt : v;
                allItemAttributes.push(cleanup(v))
            })
        })
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
        if (collections.length > 0){
            collections.map((d)=>{
                d.data.collectionProducts.items.map((di)=>{
                    fullInventories.push({
                        'utcTimestamp': new Date(d.acquisition_timestamp),
                        'item_id': di.viewSection.trackingProperties.item_id,
                        'stockLevel': di.viewSection.trackingProperties.stock_level,
                        'locationId': locationId,
                        'availability_score': di.viewSection.trackingProperties.stock_level
                    })
                })
                allItems = allItems.concat(cleanup(d.data.collectionProducts.items))
                allCollections.push(cleanup(d.data.collectionProducts.collection))
            })
        }
        
        // collectionProducts.collection.id <- department id = items.categories.id
                            // .collection.name <- department name = items.categories.name
                            // .collection.slug / .collection.legacyPath <- department identifiers     
                            // .collevtion.viewSection.trackingProperties.parent_collection_id !null
        // collectionProducts.items <- can be empty []
        // collectionProducts.items.id <- item_23150(store_id)-18446660(productId)
                                // .name <- item name
                                // .size <- customerFacingSize
                                // .productId <- main product id
                                // .legacyId , .legacyV3Id (item_legacyId?), 
                                // quantityAttributes.quantityType : "each / weight"
                                // availability.available <- true/false
                                // availability.stockLevel <-stockLevel (inStock, outOfStock, highlyInStock) = inventories.stockLevel
                                // .viewSection.itemImage.url <- items.images = {main: true, perspective: 'front', 'url': .viewSection.itemImage.url} 
                                // .viewSection.on_sale_ind = { on_sale, retailer, buy_one_get_one, cpg_coupon }
                                // .viewSection.trackingProperties.stock_level, .blackout, .availability_score, .
                            // .dietary.viewSection.attributesString!==null <- product categorization tah
        
        

        let collectionProductsColumns = {
        'collection': ['id', 'name', 'slug', 'legacyPath', 'viewSection.trackingProperties.source_type/source_value/collection_type/collection_id/element_details.element_value/?parent_collection_id'],
        'items': ['id', 'name', 'size', 'productId', 'legacyId', 'legacyV3Id', 'quantityAttributes.quantityType/viewSection.unitString/unitAriaString',
        'availability.stockLevel', 'viewSection.itemImage.url/trackingProperties.element_details.product_id/retailer_location_id/?on_sale_ind./product_id,item_id,stock_level,availability_score,available_ind,?tags,?comboPromotions'],
        'itemAttributes': ['itemId', 'itemUpdatedAt', 'trackingParams.product_id/item_id/?policy_id/on_sale_ind.*/name/pricing.price/pricePerUnit/pricingUnit/productType/?promotionEndsAt/badge.*']
        }   

        // let totalItems = []
        // let colItems = []
        // col.map((d)=>{
        //     totalItems = totalItems.concat(d.data.collectionProducts.items)
        //     colItems = colItems.concat(d.data.collectionProducts.itemIds)
        // })
        // console.log('col length = ', totalItems.length, colItems.length)
        // console.log(Object.keys(cleanup(totalItems[0])))
        // //console.log(cleanup(totalItems[0]))
        // totalItems = []
        // item.map((d)=>totalItems = totalItems.concat(d.data.items))
        // console.log('item length = ', totalItems.length)
        // console.log(cleanup(col[0].data.collectionProducts.items[0].id).match(/items_(\d+)-\d+/)[1])
        // //console.log(cleanup(totalItems[0]))
        // totalItems = []
        // itemA.map((d)=>
        //     totalItems = totalItems.concat(d.view)
        // )
        // console.log('itemAttributesLength = ', totalItems.length)
        // console.log(cleanup(totalItems[1]))
        //console.log(cleanup(totalItems.filter((d)=>d.pricing.productType==='normal'))[1])

        
        // console.log(decodeURIComponent(itemA[0].url))
        // console.log(decodeURIComponent(item[0].url))
        // console.log(decodeURIComponent(col.slice(-1)[0].url))

        

            // same as CollectionProducts w/
                // .tags: ['storeBrand], .comboPromotions: [] 
            // url, acquisition_timestamp, view
            // view: {itemId : item_1489353135(item_id), itemUpdatedAt: a utcTimestamp, viewAttributes:[],
            /* trackingParams: {
                policy_id: <INT>,
                product_id: <INT>,
                clipped_state: <BOOL>,
                item_id: <Int> = super.itemId.replace(item_),
                name: <String>,
                on_sale_ind: {on_sale, retailer, buy_one_get_one, cpg_coupon, +clipped_cpg_coupon},
                display_position: -1,
                search_id && region_id : null/'',
            }, pricing: {
                price: "$3.25",
                fullPrice: null,
                priceAffix, priceAffixAria, disclaimer, fullPriceLabel, 
                pricePerUnit: "$0.10/fl oz",
                pricingUnit: "31 fl oz",
                productType: "normal",
                promotionEndsAt: "2022-07-17T06:59:59.999Z",
                badge: {
                    type: 'clip_coupon', 
                    label: 'Save $0.50',
                    sublabel: "with coupon offer",
                    label_with_price, express_placement : null
                },
                deal: null
            } }
            
            */
        //console.log(JSON.stringify(itemA, null, 3))
        
    }
    // let summary = JSON.stringify(js_summary.summarize(allItems), null, 4)
    // let prefix = target.split('/').slice(-2,-1)[0]
    // let type = ''
    // fs.writeFileSync(`./collections.json`, JSON.stringify(summary, null, 2))


    insertData(fullPrices, 'prices')
    insertData(fullInventories, 'inventories')
    return null

}

readAndMove('../../../scripts/requests/server/collections/aldi')
// for (let targetDir of targetDirs){
//     readAndMove(target=targetDir)
// }
