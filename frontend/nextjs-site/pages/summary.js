const fs = require('fs')
const js_summary = require('json-summary') 

 let targetDirs = [ '../../../scripts/requests/server/collections/fooddepot/items', '../../../scripts/requests/server/collections/fooddepot/coupons',
 '../../../scripts/requests/server/collections/publix/items', '../../../scripts/requests/server/collections/publix/coupons',
 '../../../scripts/requests/server/collections/aldi']
function clean(obj) {
    newObj = {}
    Object.entries(obj).map((d, i)=> {
        k = d[0]
        v = d[1]
        if (!(v==={} | v===null | v==='' | v===[])){
            typeof(v)==='object' ? newObj[k]=clean(v) : newObj[k]=v;
        }
    })
    return newObj
}

// aldi : graphql?operationName=Items
    //  : item_attributes/...item_trackingParams.item_id,...
    // : opetationName=collectionProductsWithFeaturedProducts 
function readAndMove(target){
    let allItems = []
    let files = fs.readdirSync(target, {encoding: 'utf8', withFileTypes: true})
    files = files.filter((d)=> d.isFile())
    let iter = 0
    for (let file of files){
        data = fs.readFileSync(target+"/"+file.name, {encoding: 'utf8'})
        data = JSON.parse(data)
        allItems = allItems.concat(data)
        if (iter==1){
            console.log(file)
            let col = allItems.filter((d)=>d.url.includes('CollectionProducts'))
            console.log(typeof(col[1]))
            console.log(clean(col[1]))
            
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
            let item = allItems.filter((d)=>d.url.includes('operationName=Items'))[1]
            item = item.data.items.filter((d)=>Object.values(d.viewSection.trackingProperties.on_sale_ind).includes(true))
                // same as CollectionProducts w/
                    // .tags: ['storeBrand], .comboPromotions: [] 
            let itemA = allItems.filter((d)=>d.url.includes('item_attributes'))[1]
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
        iter++
        
    }
    // let summary = JSON.stringify(js_summary.summarize(allItems), null, 4)
    // let prefix = target.split('/').slice(-2,-1)[0]
    // let type = ''
    
    // target.includes('aldi') ? prefix='aldi' : type=target.split('/').slice(-1)[0];

    // fs.writeFileSync(`../../../data/${prefix}${type}Summary.json`, summary)
    
    return null

}

readAndMove('../../../scripts/requests/server/collections/aldi')

// for (let targetDir of targetDirs){
//     readAndMove(target=targetDir)
// }
