var setMaster = new Set() 
var masterArray = []
var iWasSet = false
var settingStores = false
var scrapingUrls = [
  "*://*.kroger.com/cl/api*",
  "*://*.kroger.com/atlas/v1/product/v2/products*",
  "*://*.kroger.com/mypurchases/api/v1/receipt*", // Kroger: Coupons, Products/Prices, Trips
  "*://*.kroger.com/products/api/products/details-basic", // for buy 5, save $5 -- general items
  "*://ice-familydollar.dpn.inmar.com/v2/offers*",
  "*://dollartree-cors.groupbycloud.com/api*", // Family Dollar : Coupons, Products
  "*://*.dollargeneral.com/bin/omni/coupons/products*",
  "*://*.dollargeneral.com/bin/omni/coupons/recommended*", // Dollar General: Products, Coupons 
  "https://www.dollargeneral.com/bin/omni/pickup/categories*", // Dollar General Sale Items 
  "*://*.noq-servers.net/api/v1/application/stores/*/products?*",
  "*://*.appcard.com/baseapi/1.0/token/*/offers/unclipped_recommendation_flag*", 
  "*://production-us-1.noq-servers.net/api/v1/application/coupon*",// Food Depot : Products, 3rd Party Coupons, 1st Party Coupons
  "*://services.publix.com/api*", 
  "*://delivery.publix.com/*/view/item_attributes*",
  "*://delivery.publix.com/graphql?operationName=Items*",
  "*://delivery.publix.com/graphql?operationName=CollectionProductsWithFeaturedProducts*", // // Publix 1st Party Coupons and Instacart Price and Items
  "*://shop.aldi.us/*/view/item_attributes*", // Aldi Instacart Prices and Items
  "*://shop.aldi.us/graphql?operationName=Items*",
  "*://shop.aldi.us/graphql?operationName=CollectionProductsWithFeaturedProducts*",
  "*://sameday.familydollar.com/*/view/item_attributes*",
  "*://sameday.familydollar.com/graphql?operationName=Items*", 
  "*://sameday.familydollar.com/graphql?operationName=CollectionProductsWithFeaturedProducts*"
]

if (settingStores){
  scrapingUrls = [
    "https://storelocations.familydollar.com/rest/locatorsearch*", // family dollar
    "https://www.dollargeneral.com/bin/omni/pickup/storeDetails*", // dollar general
    "https://www.dollargeneral.com/bin/omni/pickup/storeSearch*", // dollar general
    "*://*.liquidus.net/*", // aldi store search
    "https://stores.aldi.us/stores?q=*",
    "https://services.publix.com/api/v1/storelocation*", // publix 1st party site search
    "https://production-us-1.noq-servers.net/api/v1/application/stores*", // food depot stores
    "https://production-us-1.noq-servers.net/api/v1/application/franchises*", // food depot stores
    "https://shop.aldi.us/graphql?operationName=AvailablePickupRetailerServices*", // NEW : aldi 
    "https://delivery.publix.com/graphql?operationName=AvailablePickupRetailerServices*" // NEW: publix
  ]
}

async function createType(){
  let typeT = await browser.tabs.query({active: true}).then((tabs)=>{
    var t = ''
    let t2 =''
    let reg = /kroger|aldi|publix|dollargeneral|familydollar|fooddepot/
    let regKroger = /mypurchases|cashback|coupons|Buy5Save1|Buy3Save6|Buy2Save10|\?N=/
    let regFamilyDollar = /\?N=|smart-coupons|sameday/
    let regPublix = /savings/
    let regFoodDepot = /coupons/
    var fileTypes = {'mypurchases': 'trips', 'cashback': 'cashback', "coupons": "digital",
    "Buy5Save1": "buy5save1", "Buy3Save6": "buy3save6", '?N=': 'items', 'smart-coupons': 'coupons',
    "Buy2Save10": "buy2save10", 'sameday': 'instacartItems'}
    var fileTypePub = {'savings': 'coupons'}
    for (let tab of tabs){
      if (tab.url.match(reg)!=null){
        let match = tab.url.match(reg)[0]
        t = match
        match=='aldi' ? t2="items" : t2;
        match=='kroger'? t2=fileTypes[tab.url.match(regKroger)[0]]: t2;
        match=='familydollar'? t2=fileTypes[tab.url.match(regFamilyDollar)[0]] : t2;
        match=='publix' ? tab.url.match(regPublix)!==[] & tab.url.match(regPublix)!==null ? t2=fileTypePub[tab.url.match(regPublix)[0]] : t2='items' : t2;
        match=='fooddepot' ? tab.url.match(regFoodDepot)!==[] & tab.url.match(regFoodDepot)!==null ? t2=tab.url.match(regFoodDepot)[0] : t2='items' : t2;
        match=='dollargeneral' ? tab.url.match(/on-sale/) ? t2='items' : t2='promotions' : t2;
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

function verifyURLIntegrity(responseDetails) {
    if (responseDetails.statusCode >= 205){
      fetch(`http://127.0.0.1:5000/issues`, {method: 'POST', body: responseDetails.url + `${responseDetails.statusCode}`}) 
    } 
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
          } else if (details.url.match(/https\:\/\/www.kroger.com\/mypurchases\/api\/v1\/receipt\/summary\/by\-user\-id/)) {
            setIterations(new_obj.data.count).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/www\.dollargeneral\.com\/bin\/omni\/coupons\/recommended\?/)!==null & iWasSet==false){
            setIterations(new_obj.PaginationInfo.TotalRecords).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/dollartree-cors\.groupbycloud\.com\/api\/v1\/search/)){
            setIterations(new_obj.totalRecordCount).then((bool) => {iWasSet=bool})
          } else if (details.url.match(/https\:\/\/www\.kroger\.com\/mypurchases\/api\/v1\/receipt\/summary\/by-user-id/)){
            setIterations(new_obj.data.length).then((bool)=> {iWasSet=bool})
            new_obj = []
          } else if (details.url.match(/https\:\/\/www\.dollargeneral\.com\/bin\/omni\/pickup\/categories.+/)!==null & iWasSet===false){
            setIterations(new_obj.categoriesResult.categories.ItemCount).then((bool)=> {iWasSet=bool})
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
      let type = t ;
      response = fetch(`http://127.0.0.1:5000/docs?${type}`, {method: "POST", body: JSON.stringify(masterArray)})
      setTimeout(()=>{
        masterArray = []
        fetch(`http://127.0.0.1:5000/i?directive=true`, {method: "POST", body: ''})
      }, 3000)
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
// general listener for normal scraping events
chrome.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: scrapingUrls, 
  types: ["xmlhttprequest", "object"]},
  ["blocking"]
)

chrome.webRequest.onCompleted.removeListener(
  listener,
  {urls: scrapingUrls, 
  types: ["xmlhttprequest", "object"]},
  ["blocking"]
)

chrome.webRequest.onCompleted.addListener(
  verifyURLIntegrity,
  {urls: ["<all_urls>"],
  types: ["xmlhttprequest", "object"]}, 
)
