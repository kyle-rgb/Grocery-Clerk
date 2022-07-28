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
// console.log('diff = ', difference(trackParamsAldi, trackParamsPub, false))

// console.log('diff = ', difference(trackParamsPub, trackParamsAldi, false))

/* publix: extensions{}, url, acquistion_timestamp
    data:
    { collectionProducts:
        { collection:
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
            id: "items_23150-20391806",
            name: "Kellogg's Pop-Tarts Toaster Pastries, Breakfast Foods, Kids Snacks, Frosted Strawberry",
            size: "20 oz",
            productId: "20391806",
            legacyId: "1482171545",
            legacyV3Id: "item_1482171545",
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
                    unitAriaString: "item",
                    unitPluralAriaString: "items",
                    unitPluralString: "ct", 
                    unitString: "ct",
                    iconUnitTypeVisibilityVariant: "hide",
                    variableWeightDisclaimerString: null, 
                    __typename: "ItemsResponseBackedQuantityAttributesSection"
                }
            },
            quantityAttribuesWeight: {  },
            quantityAttributes: {
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
                stockLevel: "inStock" | "out_of_stock",
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
                },
                trackingProperties: {
                    element_attributes: {
                        low_stock_level: boolean
                    },
                    low_stock_label: boolean,
                    element_details: {
                        element_type: "item",
                        product_id: "20391806",
                        retailer_location_id: "23150",
                        element_id: "items_23150-20391806"
                    },
                    on_sale_ind: {
                        on_sale: boolean,
                        retailer: boolean,
                        buy_one_get_one: boolean,
                        cpg_coupon: boolean
                    },
                    product_id:"20391806",
                    item_id: "1482171545",
                    stock_level: "in_stock" || "out_of_stock",
                    blackout: boolean,
                    availability_score:0.93,
                    available_ind: boolean,
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
            tags: ["storeBrand"],
            comboPromotions: [],
            __typename: "ItemsItem"
        },
        featuredProducts: [],
        viewSection: {trackingProperties: {ranking_request_id}},
        view: {
            itemId: "item_1846311039",
            itemUpdatedAt: 1654662660,
            viewAttributes: [],
            trackingParams: {
                item_card_impression_id: "6a6defc3-44e4-4d62-98a2-d77b00eebe41",
                product_id:20262645,
                item_id:1846311039,
                name:"Bread Specially Selected 6 ct. Brioche Buns",
                on_sale_ind: {
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
                clipped_state: boolean
        },
        pricing: {
            price: "$4.35",
            fullPrice: null,
            priceAffix: null,
            priceAffixAria: null,
            pricePerUnit: "$0.41/oz",
            pricingUnit: "10.58oz",
            pricingUnitSecondary: null,
            productType: "normal",
            disclaimer: null,
            fullPriceLabel: null,
            promotionEndsAt: "2022-07-01T06:59:59.999Z",
            badge: {
                type: "clip_coupon",
                label: "Buy 2 Save $0.50",
                sublabel: "with coupon offer",
                label_with_price: null,
                express_placement: null
            },
            deal: null
        }
    },
    view : [
        itemId: "item_111417049012",
        itemUpdatedAt: 1655959707,
        viewAttributes: [],
        trackingParams: {
            item_card_impression_id: "3aea54ca-0077-48bf-844f-269872473613",
            product_id: 71154,
            item_id: 111417049012,
            name: "Condiments Hellmann's Mayonnaise Dressing With Olive Oil Mayo",
            on_sale_ind: {
                on_sale, retailer, buy_one_get_one, cpg_coupon, clipped_cpg_coupon => boolean
            },
            display_position: -1,
            search_id: null,
            region_id: "",
            item_tasks: ["guided_qualification_modal"],
            policy_id: 825362364,
            clipped_states: boolean,
            cart_id: 854947928
        },
        pricing: {
            price: "$7.09",
            fullPrice: "$20.39",
            priceAffrix: "/ lb",
            priceAffixAria: "per pound",
            pricePerUnit: "$0.24/fl oz",
            pricingUnit: "30 fl oz",
            pricingUnitSecondary: null,
            productType: "normal",
            disclaimer: "Sale ends in 5 days",
            fullPriceLabel: "Reg: ",
            promotionEndsAt: "2022-06-29T08:00:00.000Z",
            badge: {
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
        { collection:
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
            id: "items_23150-20391806",
            name: "Kellogg's Pop-Tarts Toaster Pastries, Breakfast Foods, Kids Snacks, Frosted Strawberry",
            size: "20 oz",
            productId: "20391806",
            legacyId: "1482171545",
            legacyV3Id: "item_1482171545",
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
                    unitAriaString: "item",
                    unitPluralAriaString: "items",
                    unitPluralString: "ct", 
                    unitString: "ct",
                    iconUnitTypeVisibilityVariant: "hide",
                    variableWeightDisclaimerString: null, 
                    __typename: "ItemsResponseBackedQuantityAttributesSection"
                }
            },
            quantityAttribuesWeight: {  },
            quantityAttributes: {
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
                stockLevel: "inStock" | "out_of_stock",
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
                },
                trackingProperties: {
                    element_attributes: {
                        low_stock_level: boolean
                    },
                    low_stock_label: boolean,
                    element_details: {
                        element_type: "item",
                        product_id: "20391806",
                        retailer_location_id: "23150",
                        element_id: "items_23150-20391806"
                    },
                    on_sale_ind: {
                        on_sale: boolean,
                        retailer: boolean,
                        buy_one_get_one: boolean,
                        cpg_coupon: boolean
                    },
                    product_id:"20391806",
                    item_id: "1482171545",
                    stock_level: "in_stock" || "out_of_stock",
                    blackout: boolean,
                    availability_score:0.93,
                    available_ind: boolean,
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
            tags: ["storeBrand"],
            comboPromotions: [],
            __typename: "ItemsItem"
        },
        featuredProducts: [],
        viewSection: {trackingProperties: {ranking_request_id}},
        view: {
            itemId: "item_1846311039",
            itemUpdatedAt: 1654662660,
            viewAttributes: [],
            trackingParams: {
                item_card_impression_id: "6a6defc3-44e4-4d62-98a2-d77b00eebe41",
                product_id:20262645,
                item_id:1846311039,
                name:"Bread Specially Selected 6 ct. Brioche Buns",
                on_sale_ind: {
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
                clipped_state: boolean
        },
        pricing: {
            price: "$4.35",
            fullPrice: null,
            priceAffix: null,
            priceAffixAria: null,
            pricePerUnit: "$0.41/oz",
            pricingUnit: "10.58oz",
            pricingUnitSecondary: null,
            productType: "normal",
            disclaimer: null,
            fullPriceLabel: null,
            promotionEndsAt: "2022-07-01T06:59:59.999Z",
            badge: {
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
console.log(Boolean([]))

// aldi: 









