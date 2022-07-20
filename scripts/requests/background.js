var setMaster = new Set() 
var masterArray = []
var iWasSet = false
var settingStores = false


async function createType(){
  let typeT = await browser.tabs.query({active: true}).then((tabs)=>{
    var t = ''
    let t2 =''
    let reg = /kroger|aldi|publix|dollargeneral|familydollar|fooddepot/
    let regKroger = /mypurchases|cashback|coupons|Buy5Save1|\?N=/
    let regFamilyDollar = /\?N=|smart-coupons/
    let regPublix = /savings/
    let regFoodDepot = /coupons/
    var fileTypes = {'mypurchases': 'trips', 'cashback': 'cashback', "coupons": "digital", "Buy5Save1": "buy5save1", '?N=': 'items', 'smart-coupons': 'coupons'}
    var fileTypePub = {'savings': 'coupons'}

    for (let tab of tabs){
      if (tab.url.match(reg)!=null){
        let match = tab.url.match(reg)[0]
        t = match
        match=='kroger'? t2=fileTypes[tab.url.match(regKroger)[0]]: t2='';
        match=='familydollar'? t2=fileTypes[tab.url.match(regFamilyDollar)[0]] : t2;
        match=='publix' ? tab.url.match(regPublix)!==[] & tab.url.match(regPublix)!==null ? t2=fileTypePub[tab.url.match(regPublix)[0]] : t2='items' : t2;
        match=='fooddepot' ? tab.url.match(regFoodDepot)!==[] & tab.url.match(regFoodDepot)!==null ? t2=tab.url.match(regFoodDepot)[0] : t2='items' : t2;
        settingStores ? t2='stores' : t2;
      }
    }
    return `type=${t}&folder=${t2}`
  })
  return typeT  

}

async function setIterations(count){
    let res = await fetch('http://127.0.0.1:5000/i').then((d)=>{return d.json()}).then((j)=> {return j})
    if (res.wait){
      let res2 = await fetch(`http://127.0.0.1:5000/i?i=${count}`, {method: 'POST'}).then((d)=>{return d.json()}).then((j)=> {return j})
    }
    return null
}

function logURL(requestDetails) {
    console.log("Loading: " + requestDetails.url);
    console.log("details: ", requestDetails)   
    return null
  }

function listener(details) {
    let filter = chrome.webRequest.filterResponseData(details.requestId);
    let decoder = new TextDecoder("utf-8");
    let encoder = new TextEncoder();
    let originRegex = /api.*|atlas.*/g
    let tempString = ''
    console.log('fired')
    filter.onstart = event => {
      console.log(`${details.requestId} stream received, commence processing......`)
    }
    filter.ondata = event => {
      let str = decoder.decode(event.data, {stream: true});
      //console.log("event", details.requestId, 'chunkObtained', 'buffer: ', event.data)
      tempString += str
      filter.write(encoder.encode(str))
      str = null
      // console.log('filter reachEnd of first data stream:', filter.status)
    }

    filter.onstop = event => {
      getI(details.requestId).then((ii) => {
        if (ii===0){
          let new_obj = JSON.parse(tempString)
          if (Array.isArray(new_obj)){
            new_obj = {data: new_obj}
          }
          new_obj.url = details.url
          if (details.url.match(/https\:\/\/www\.kroger\.com\/cl\/api\/coupons\?couponsCountPerLoad/)!==null & iWasSet==false){
            setIterations(new_obj.data.count).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/www\.dollargeneral\.com\/bin\/omni\/coupons\/recommended\?/)!==null & iWasSet==false){
            setIterations(new_obj.PaginationInfo.TotalRecords).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/dollartree-cors\.groupbycloud\.com\/api\/v1\/search/)){
            setIterations(new_obj.totalRecordCount).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/www\.kroger\.com\/mypurchases\/api\/v1\/receipt\/summary\/by-user-id/)){
            setIterations(new_obj.data.length).then((bool)=> {iWasSet=bool})
            new_obj = []
          }
          new_obj.acquisition_timestamp = Date.now()
          masterArray.push(new_obj)
          masterArray = pruneArray(masterArray)
        }
      })
      
      filter.disconnect();
      
    }

    return {};
  }

async function getI(i){
  if (setMaster.has(i)){
    return i
  } else {
    setMaster.add(i)
    return 0
  }
}

function pruneArray(array){
  if (array.length >35){
    createType().then((t) => {
      let type = t ;
      response = fetch(`http://127.0.0.1:5000/docs?${type}`, {method: "POST", body: JSON.stringify(array)})
      return null
  })
    return []
  } else {
    return array
  }
}

chrome.contextMenus.create({
  id: 'eat-page',
  title: "Eat this Page"
})

chrome.contextMenus.onClicked.addListener(function(info, tab) {
    createType().then((t) => {
      let storeUrls = ["https://storelocations.familydollar.com/rest/locatorsearch",
      "https://www.dollargeneral.com/bin/omni/pickup/storeDetails",
      "https://www.dollargeneral.com/bin/omni/pickup/storeSearch",
      "https://graphql-cdn-slplatform.liquidus.net/",
      "https://services.publix.com/api/v1/storelocation",
      "https://production-us-1.noq-servers.net/api/v1/application/stores",
      "https://production-us-1.noq-servers.net/api/v1/application/franchises"
      ]
      let type = t ;
      if (settingStores){
        masterArray.filter((d)=> {
          var isAMatch = false
          for (let storeUrl of storeUrls){
            isAMatch = d.url.startsWith(storeUrl) | isAMatch
          }
          return Boolean(isAMatch)
        })
        response = fetch(`http://127.0.0.1:5000/docs?${type}`, {method: "POST", body: JSON.stringify(masterArray)})
      }else {
        response = fetch(`http://127.0.0.1:5000/docs?${type}`, {method: "POST", body: JSON.stringify(masterArray)})
      }
      masterArray = []
      fetch(`http://127.0.0.1:5000/i?directive=true`, {method: "POST", body: ''})
      iWasSet = false
      return null
    })
  })

document.addEventListener("click", function(e){
  if (!e.target.classList.contains('send-signal')){
    return;
  } else {
    createType().then((t) => {
      let type = t ;
      response = fetch(`http://127.0.0.1:5000/docs?${type}`, {method: "POST", body: JSON.stringify(masterArray)})
      return null
    })  
  }
})


chrome.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas/v1/product/v2/products*", "*://*.kroger.com/mypurchases/api/v1/receipt*", // Kroger: Coupons, Products/Prices, Trips
  "*://*.kroger.com/products/api/products/details-basic", // for buy 5, save $5
  "*://ice-familydollar.dpn.inmar.com/v2/offers*", "*://dollartree-cors.groupbycloud.com/api*", // Family Dollar : Coupons, Products
  "*://storelocations.familydollar.com/rest/locatorsearch*", // Family Dollar Stoes
  "*://*.dollargeneral.com/bin/omni/coupons/products*", "*://*.dollargeneral.com/bin/omni/coupons/recommended*", // Dollar General: Products, Coupons 
  "*://*.dollargeneral.com/bin/omni/pickup/storeSearch*", "*://*.dollargeneral.com/bin/omni/pickup/storeDetails*", // Dollar General Stores
  "*://*.noq-servers.net/api/v1/application/stores/*/products?*", "*://*.appcard.com/baseapi/1.0/token/*/offers/unclipped_recommendation_flag*", // Food Depot : Products, Coupons
  "*://production-us-1.noq-servers.net/api/v1/application/franchises/*/summary","*://production-us-1.noq-servers.net/api/v1/application/stores/*/summary", // Food Depot Stores
  "*://services.publix.com/api*", // Publix Coupons
  "*://delivery.publix.com/*/view/item_attributes*", "*://delivery.publix.com/graphql?operationName=Items", "*://delivery.publix.com/graphql?operationName=CollectionProductsWithFeaturedProducts*", // publix prices and items
  "*://shop.aldi.us/graphql?operationName=CollectionProductsWithFeaturedProducts*", "*://shop.aldi.us/graphql?operationName=Items*", "*://shop.aldi.us/*/view/item_attributes*", // Aldi: Items
  "*://graphql-cdn-slplatform.liquidus.net/", //aldi stores,
  ], 
  types: ["xmlhttprequest", "object"]},
  ["blocking"]
)

chrome.webRequest.onCompleted.removeListener(
  listener,
  {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas/v1/product/v2/products*", "*://*.kroger.com/mypurchases/api/v1/receipt*", // Kroger: Coupons, Products/Prices, Trips
  "*://*.kroger.com/products/api/products/details-basic", // for buy 5, save $5
  "*://ice-familydollar.dpn.inmar.com/v2/offers*", "*://dollartree-cors.groupbycloud.com/api*", // Family Dollar : Coupons, Products
  "*://storelocations.familydollar.com/rest/locatorsearch*", // Family Dollar Stoes
  "*://*.dollargeneral.com/bin/omni/coupons/products*", "*://*.dollargeneral.com/bin/omni/coupons/recommended*", // Dollar General: Products, Coupons 
  "*://*.dollargeneral.com/bin/omni/pickup/storeSearch*", "*://*.dollargeneral.com/bin/omni/pickup/storeDetails*", // Dollar General Stores
  "*://*.noq-servers.net/api/v1/application/stores/*/products?*", "*://*.appcard.com/baseapi/1.0/token/*/offers/unclipped_recommendation_flag*", // Food Depot : Products, Coupons
  "*://production-us-1.noq-servers.net/api/v1/application/franchises/*/summary","*://production-us-1.noq-servers.net/api/v1/application/stores/*/summary", // Food Depot Stores
  "*://services.publix.com/api*", // Publix Coupons
  "*://delivery.publix.com/*/view/item_attributes*", "*://delivery.publix.com/graphql?operationName=Items", "*://delivery.publix.com/graphql?operationName=CollectionProductsWithFeaturedProducts*", // publix prices and items
  "*://shop.aldi.us/graphql?operationName=CollectionProductsWithFeaturedProducts*", "*://shop.aldi.us/graphql?operationName=Items*", "*://shop.aldi.us/*/view/item_attributes*", // Aldi: Items
  "*://graphql-cdn-slplatform.liquidus.net/", //aldi stores,
  ], 
  types: ["xmlhttprequest", "object"]}, // 
  ["blocking"]
)
