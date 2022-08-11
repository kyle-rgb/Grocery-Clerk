const fs = require('fs')
const {union, intersection, difference } = require('set-operations')

var pub = fs.readFileSync('../../../data/publixitemsSummary.json')

pub = JSON.parse(pub)

let trackParamsPub = pub.items["0"].items.view.items["0"].items.trackingParams.keys

var aldi = fs.readFileSync('../../../data/aldiSummary.json')
aldi = JSON.parse(aldi)
let trackParamsAldi = aldi.items["0"].items.view.items["0"].items.trackingParams.keys


// console.log('union = ', union(trackParamsAldi, trackParamsPub, false))
// console.log('intersect = ', intersection(trackParamsAldi, trackParamsPub, false))
// console.log('(aldi-pub)diff = ', difference(trackParamsAldi, trackParamsPub, false))
// console.log('(aldi-pub)diff = ', difference(trackParamsPub, trackParamsAldi, false))

// console.log('diff = ', difference(trackParamsPub, trackParamsAldi, false))

var pubKeys = []
var aldiKeys = []
function summaryObjectDecompose (summary, list){
    if (summary.type==='Array'){
        return summaryObjectDecompose(summary.items["0"], list)
    } else if (summary.type==='Object'){
        list.push(summary.keys)
        return summaryObjectDecompose(summary.items, list)
    } else if (summary.type===undefined){
        Object.keys(summary).map((key)=>summaryObjectDecompose(summary[key], list))
    }

}

summaryObjectDecompose(pub, pubKeys)
console.log('^'.repeat(75))
summaryObjectDecompose(aldi, aldiKeys)
aldiKeys.forEach((d,i)=> {
    let matches = pubKeys.map((pk)=>intersection(pk, d, true).length)
    let max = Math.max(...matches)
    console.log(pubKeys[matches.indexOf(max)])
    console.log(d)
    if ((difference(pubKeys[matches.indexOf(max)], d)).size!==difference(d, pubKeys[matches.indexOf(max)]).size){
        console.log(difference(d, pubKeys[matches.indexOf(max)]))
        console.log((difference(pubKeys[matches.indexOf(max)], d)))
    }
    console.log('*'.repeat(100))
})

/* publix: extensions{}, url, acquistion_timestamp <- meta-data
    data:
    { collectionProducts:
        {
            collection:
                {id: "a9179" <collection id>,
                name: "Frozen Produce" <collection name>,
                slug: "a9179-frozen-produce" <id+name>,
                legacyPath: "departments/1106/aisles/9179",
                viewSection: {
                    trackingProperties: {
                        source_type:"collection", source_value:"a9179", collection_type:"department", parent_collection_id:"1106",
                        element_details:{
                            element_id:"a9179", element_type:"collection", element_value: "Frozen Produce"
                        },
                        collection_id:"a9179"
                    },
                    __typename:"CollectionsResponseBackedCollectionSection"
                },
                __typename: "CollectionsCollection"}}
            selectedFilters:[],
            orderBy:"bestMatch",
            itemIds:["items_23150-20391806"],
            featuredProducts: [],
            viewSection: {
                trackingProperties: {
                    ranking_request_id: null
                }
            },
          __typename}
            items: {
                id: "items_23150-20391806", <item id>
                name: "Kellogg's Pop-Tarts Toaster Pastries, Breakfast Foods, Kids Snacks, Frosted Strawberry", <item name>
                size: "20 oz", <item size>
                productId: "20391806", <item id>
                legacyId: "1482171545", <item id>
                legacyV3Id: "item_1482171545", <"item_" + item legacyId>
                configurableProductId: null,
                retailer: {
                    isUltrafast: bool,
                    __type:  "RetailersRetailer"
                },
                dietary: {
                    viewSection: {
                        attributesString: null,
                        attributesSections: [],
                        __typename: "ItemsResponseBackedDietarySection"
                    }
                },
                productRating: "",
                quantityAttributesEach: {
                    increment: 1,
                    initial: 1,
                    max: 150,
                    min: 1,
                    quantityType: "each", <item sale type>
                    selectOptions: [1, 9],
                    defaultSelectOptions: 1,
                    viewSection: {
                        maxedOutString: "Max 150 per order", <max item order>
                        minReachedString: null,
                        unitAriaString: "item", <item soldBy>
                        unitPluralAriaString: "items", <item soldBy>
                        unitPluralString: "ct", <item soldBy>
                        unitString: "ct", <item soldBy>
                        iconUnitTypeVisibilityVariant: "hide",
                        variableWeightDisclaimerString: null, 
                        __typename: "ItemsResponseBackedQuantityAttributesSection"
                    }
                },
                quantityAttributesWeight: {  },
                quantityAttributes: { => same as quantityAttributesEach
                    increment: 1,
                    initial: 1,
                    max: 150,
                    min: 1,
                    quantityType: "each", <item soldBy>
                    selectOptions: [1, 9],
                    defaultSelectOptions: 1,
                    viewSection: {
                        maxedOutString: "Max 150 per order",
                        minReachedString: null,
                        unitAriaString: "item", 
                        unitPluralAriaString: "items",
                        unitPluralString: "ct", 
                        unitString: "ct",
                        iconUnitTypeVisibilityVariant: "hide",
                        variableWeightDisclaimerString: null, 
                        __typename: "ItemsResponseBackedQuantityAttributesSection"
                    }
                },
                availability: {
                    available: boolean,
                    stockLevel: "inStock" | "lowStock", <item inventory indicator => stockLevel>
                    viewSection: {
                        stockLevelLabelString: null,
                        outOfStockCtaString: null, 
                        similarItemsActionVariant: "none",
                        warningIconImage: null,
                        __typename: "AvailabilityResponseBackedAvailabilitySection"
                    }
                },
                variantGroup: null,
                variantGroupId: null,
                variantDimensionValues: [],
                viewSection: {
                    itemImage: {
                        altText: null,
                        templateUrl:"https://www.instacart.com/image-server/{width=}x{height=}/filters:fill(FFF,true):format(jpg)/d2lnr5mha7bycj.cloudfront.net/product-image/file/large_5c697d8c-b45a-4c34-82fb-14f9971e4811.jpg",
                        url : "https://d2lnr5mha7bycj.cloudfront.net/product-image/file/large_5c697d8c-b45a-4c34-82fb-14f9971e4811.jpg"
                            <item image => images.front>
                    },
                    trackingProperties: {
                        element_attributes: {
                            low_stock_level: boolean
                        },
                        low_stock_label: boolean,
                        element_details: {
                            element_type: "item",
                            product_id: "20391806", <item id>
                            retailer_location_id: "23150", <locationId>
                            element_id: "items_23150-20391806" <combo of all>
                        },
                        on_sale_ind: { <promotions>
                            on_sale: boolean,
                            retailer: boolean,
                            buy_one_get_one: boolean,
                            cpg_coupon: boolean
                        },
                        product_id:"20391806", <item id>
                        item_id: "1482171545", <item id>
                        stock_level: "in_stock" || "out_of_stock", <inventories>
                        blackout: boolean, <inventories>
                        availability_score:0.93, <inventories>
                        available_ind: boolean, <inventories>
                        low_stock_variant: "none", 
                        balance_on_hand_qty: null,
                        boh_stock_level: null,
                        boh_hybrid_score: null,
                        boh_last_updated_at: null 
                    },
                    itemCardRatingVariant:"hidden",
                    itemCardQuickAddVariant:"control",
                    itemCardDiscountBadgeVariant:"hide",
                    itemCardLowStockLevelVariant:"visible",
                    quantityAttributesVariant:"eachAndWeight",
                    itemCardHideQuickAddPriceVariant:"show",
                    lowStockVariant:"none",
                    boughtXTimesString:null,
                    requestAddString:null,
                    servingSizeString:null,
                    variantDimensionsString:null,
                    __typename:"ItemsResponseBackedItemSection"
                },
                tags: ["storeBrand"], <items brand> 
                comboPromotions: [],
                __typename: "ItemsItem"
            },
        featuredProducts: [],
        viewSection: {trackingProperties: {ranking_request_id}},
        view: {
            itemId: "item_1846311039", <items id>
            itemUpdatedAt: 1654662660, <prices utcTimestamp"
            viewAttributes: [],
            trackingParams: {
                item_card_impression_id: "6a6defc3-44e4-4d62-98a2-d77b00eebe41",
                product_id:20262645, <items id>
                item_id:1846311039, <items id>
                name:"Bread Specially Selected 6 ct. Brioche Buns", <items name>
                on_sale_ind: { <promotions>
                    on_sale: boolean,
                    retailer: boolean,
                    buy_one_get_one: boolean,
                    cpg_coupon: boolean,
                    clipped_cpg_coupon: boolean
                },
                display_position: -1,
                search_id: null,
                region_id: null,
                policy_id: 825362495,  <promotions>
                clipped_state: boolean  <promotions>
        },
        pricing: {
            price: "$4.35", <prices value> -> prices.value as float
            fullPrice: null,
            priceAffix: null,
            priceAffixAria: null,
            pricePerUnit: "$0.41/oz", <prices quantity>
            pricingUnit: "10.58oz", <prices quantity> -> prices.quantity as float
            pricingUnitSecondary: null,
            productType: "normal", -> ~ prices.type
            disclaimer: null,
            fullPriceLabel: null,
            promotionEndsAt: "2022-07-01T06:59:59.999Z", <prices expirationDate> -> prices.expirationDate as datetime
            badge: {
                type: "clip_coupon", <promotions> 
                label: "Buy 2 Save $0.50", <promotions> / <prices>
                sublabel: "with coupon offer", <promotions>
                label_with_price: null,
                express_placement: null
            },
            deal: null
        }
    },
    view : [
        itemId: "item_111417049012", <items>
        itemUpdatedAt: 1655959707, <items utcTimestamp>
        viewAttributes: [],
        trackingParams: {
            item_card_impression_id: "3aea54ca-0077-48bf-844f-269872473613", <items id>
            product_id: 71154, <items id> 
            item_id: 111417049012,  <items id> 
            name: "Condiments Hellmann's Mayonnaise Dressing With Olive Oil Mayo", <items name>
            on_sale_ind: { <promotions>
                on_sale, retailer, buy_one_get_one, cpg_coupon, clipped_cpg_coupon => boolean
            },
            display_position: -1,
            search_id: null,
            region_id: "",
            item_tasks: ["guided_qualification_modal"],
            policy_id: 825362364,
            clipped_states: boolean, <promotions>
            cart_id: 854947928
        },
        pricing: {
            price: "$7.09", <prices> 
            fullPrice: "$20.39", <prices> 
            priceAffrix: "/ lb",
            priceAffixAria: "per pound",
            pricePerUnit: "$0.24/fl oz", <prices> 
            pricingUnit: "30 fl oz", <items soldBy>
            pricingUnitSecondary: null,
            productType: "normal",
            disclaimer: "Sale ends in 5 days", <promotions expirationDate>
            fullPriceLabel: "Reg: ",
            promotionEndsAt: "2022-06-29T08:00:00.000Z", <promotions expirationDate>
            badge: { <promotions>
                type: "sale", label: "2% off", sublabel: "with coupon offer",
                label_with_price: null, express_placement: null 
            },
            deal: null
        }
    ]
*/

/* aldi: [ view, url, acquistion_timestamp, extensions, data ]
    extensions: {cacheControl: {version, hints}} <= can be deleted, browser data
    data:
    { collectionProducts:
        { collection: <items department>
            {id, name, slug, legacyPath,
                viewSection: {
                    trackingProperties: {
                        source_type:"collection", source_value:"1000292", collection_type:"holiday", parent_collection_id:"290",
                        element_details:{
                            element_id:"100292", element_type:"collection", element_value: "Snacks"
                        },
                        collection_id:1000292
                    },
                    __typename:"CollectionsResponseBackedCollectionSection"
                },
                __typename}}
            selectedFilters:[],
            orderBy:"bestMatch",
            itemIds:["items_23150-20391806"],
            featuredProducts: [],
            viewSection: {
                trackingProperties: {
                    ranking_request_id: null
                }
            },
          __typename}
        items: {
            id: "items_23150-20391806", <items ids>
            name: "Kellogg's Pop-Tarts Toaster Pastries, Breakfast Foods, Kids Snacks, Frosted Strawberry", <items name>
            size: "20 oz", <items customerFacingSize>
            productId: "20391806", <items id>
            legacyId: "1482171545", <items id>
            legacyV3Id: "item_1482171545", <items id>
            configurableProductId: null,
            retailer: {
                isUltrafast: bool,
                __type:  "RetailersRetailer"
            },
            dietary: {
                viewSection: {
                    attributesString: null,
                    attributesSections: [],
                    __typename: "ItemsResponseBackedDietarySection"
                }
            },
            productRating: "",
            quantityAttributesEach: {
                increment: 1,
                initial: 1,
                max: 150,
                min: 1,
                quantityType: "each",
                selectOptions: [1, 9],
                defaultSelectOptions: 1,
                viewSection: {
                    maxedOutString: "Max 150 per order",
                    minReachedString: null,
                    unitAriaString: "item",  <items size>
                    unitPluralAriaString: "items", <items size>
                    unitPluralString: "ct", <items size>
                    unitString: "ct", <items size>
                    iconUnitTypeVisibilityVariant: "hide",
                    variableWeightDisclaimerString: null, 
                    __typename: "ItemsResponseBackedQuantityAttributesSection"
                }
            },
            quantityAttribuesWeight: {  },
            quantityAttributes: { <items size>
                increment: 1,
                initial: 1,
                max: 150,
                min: 1,
                quantityType: "each",
                selectOptions: [1, 9],
                defaultSelectOptions: 1,
                viewSection: {
                    maxedOutString: "Max 150 per order",
                    minReachedString: null,
                    unitAriaString: "item",
                    unitPluralAriaString: "items",
                    unitPluralString: "ct", 
                    unitString: "ct",
                    iconUnitTypeVisibilityVariant: "hide",
                    variableWeightDisclaimerString: null, 
                    __typename: "ItemsResponseBackedQuantityAttributesSection"
                }
            },
            availability: {
                available: boolean,
                stockLevel: "inStock" | "lowStock", <inventories>
                viewSection: {
                    stockLevelLabelString: null,
                    outOfStockCtaString: null, 
                    similarItemsActionVariant: "none",
                    warningIconImage: null,
                    __typename: "AvailabilityResponseBackedAvailabilitySection"
                }
            },
            variantGroup: null,
            variantGroupId: null,
            variantDimensionValues: [],
            viewSection: {
                itemImage: {
                    altText: null,
                    templateUrl:"https://www.instacart.com/image-server/{width=}x{height=}/filters:fill(FFF,true):format(jpg)/d2lnr5mha7bycj.cloudfront.net/product-image/file/large_5c697d8c-b45a-4c34-82fb-14f9971e4811.jpg",
                    url : "https://d2lnr5mha7bycj.cloudfront.net/product-image/file/large_5c697d8c-b45a-4c34-82fb-14f9971e4811.jpg" <items images>
                },
                trackingProperties: {
                    element_attributes: {
                        low_stock_level: boolean <inventories>
                    },
                    low_stock_label: boolean, <inventories>
                    element_details: { <items>
                        element_type: "item",
                        product_id: "20391806",
                        retailer_location_id: "23150",
                        element_id: "items_23150-20391806"
                    },
                    on_sale_ind: { <promotions>
                        on_sale: boolean,
                        retailer: boolean,
                        buy_one_get_one: boolean,
                        cpg_coupon: boolean
                    },
                    product_id:"20391806", <items>
                    item_id: "1482171545", <items>
                    stock_level: "in_stock" || "out_of_stock", <inventories>
                    blackout: boolean, <inventories>
                    availability_score:0.93, <inventories>
                    available_ind: boolean, <inventories>
                    low_stock_variant: "none", 
                    balance_on_hand_qty: null,
                    boh_stock_level: null,
                    boh_hybrid_score: null,
                    boh_last_updated_at: null 
                },
                itemCardRatingVariant:"hidden",
                itemCardQuickAddVariant:"control",
                itemCardDiscountBadgeVariant:"hide",
                itemCardLowStockLevelVariant:"visible",
                quantityAttributesVariant:"eachAndWeight",
                itemCardHideQuickAddPriceVariant:"show",
                lowStockVariant:"none",
                boughtXTimesString:null,
                requestAddString:null,
                servingSizeString:null,
                variantDimensionsString:null,
                __typename:"ItemsResponseBackedItemSection"
            },
            tags: ["storeBrand"], <items brand>
            comboPromotions: [],
            __typename: "ItemsItem"
        },
        featuredProducts: [],
        viewSection: {trackingProperties: {ranking_request_id}},
        view: {
            itemId: "item_1846311039", <items id>
            itemUpdatedAt: 1654662660, <items utcTimestamp>
            viewAttributes: [],
            trackingParams: {
                item_card_impression_id: "6a6defc3-44e4-4d62-98a2-d77b00eebe41",
                product_id:20262645, <items>
                item_id:1846311039, <items
                name:"Bread Specially Selected 6 ct. Brioche Buns", <items name>
                on_sale_ind: { <promotions>
                    on_sale: boolean, 
                    retailer: boolean,
                    buy_one_get_one: boolean,
                    cpg_coupon: boolean,
                    clipped_cpg_coupon: boolean
                },
                display_position: -1,
                search_id: null,
                region_id: null,
                policy_id: 825362495,
                clipped_state: boolean <promotions>
        },
        pricing: {
            price: "$4.35", <prices>
            fullPrice: null,
            priceAffix: null,
            priceAffixAria: null,
            pricePerUnit: "$0.41/oz",
            pricingUnit: "10.58oz", <items customerFacingSize>
            pricingUnitSecondary: null,
            productType: "normal",
            disclaimer: null,
            fullPriceLabel: null,
            promotionEndsAt: "2022-07-01T06:59:59.999Z", <prices expirationDate>
            badge: { <promotions>
                type: "clip_coupon",
                label: "Buy 2 Save $0.50",
                sublabel: "with coupon offer",
                label_with_price: null,
                express_placement: null
            },
            deal: null
        }
    }
    */









