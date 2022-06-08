var setMaster = new Set() 
var masterArray = []


async function createType(){
  let typeT = await browser.tabs.query({active: true}).then((tabs)=>{
    var t = ''
    let reg = /mypurchases|cashback|coupon/
    var fileTypes = {'mypurchases': 'trips', 'cashback': 'cashback', "coupon": 'digital'}
    for (let tab of tabs){
      if (tab.url.match(reg)!=null){
        let match = tab.url.match(reg)[0]
        t = fileTypes[match]
      }
    }
    return t
  })
  return typeT  

}



function logURL(requestDetails) {
    console.log("Loading: " + requestDetails.url);
    console.log("details: ", requestDetails)   
    return null
  }

function getObject(){
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
          new_obj.url = details.url
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
      response = fetch(`http://127.0.0.1:5000/docs?type=${type}`, {method: "POST", body: JSON.stringify(array)})
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
      response = fetch(`http://127.0.0.1:5000/docs?type=${type}`, {method: "POST", body: JSON.stringify(masterArray)})
      return null
    })
  })


// chrome.webRequest.onBeforeRequest.addListener(
//     logURL,
//     {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas/v1/product/v2/products*", "*://*.kroger.com/mypurchases/api/v1/receipt*"],  types: ["xmlhttprequest", "object"]}, // ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"]
//     ['blocking']
//   );
// 
// 

chrome.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas/v1/product/v2/products*",  "*://ice-familydollar.dpn.inmar.com/v2/offers*","*://*.kroger.com/mypurchases/api/v1/receipt*", "*://*.dollargeneral.com/bin/omni/coupons/products*", "*://*.dollargeneral.com/bin/omni/coupons/recommended*"], types: ["xmlhttprequest", "object"]}, // 
  ["blocking"]
)


// chrome.webRequest.onBeforeRequest.addListener(
//   logTab,"
//   {urls: ["<all_urls>"], types: ["xmlhttprequest", "object"]}, // 
//   ["blocking"]
// )

chrome.webRequest.onCompleted.removeListener(
  listener,
  {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas/v1/product/v2/products*",  "*://ice-familydollar.dpn.inmar.com/v2/offers*", "*://*.kroger.com/mypurchases/api/v1/receipt*", "*://*.dollargeneral.com/bin/omni/coupons/products*", "*://*.dollargeneral.com/bin/omni/coupons/recommended*"], types: ["xmlhttprequest", "object"]}, // 
  ["blocking"]
)

// chrome.webRequest.onBeforeRequest.addListener(
//   getObject,
//   {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"], types: ["xmlhttprequest", "object"]}, // 
//   ["blocking"]

// )


// Listen for onHeaderReceived for the target page.
// Set "blocking" and "responseHeaders".
// chrome.webRequest.onHeadersReceived.addListener(
//   setCookie,
//   {urls: ["<all_urls>"]},
//   ["blocking", "responseHeaders"]
// );

// chrome.webRequest.onHeadersReceived.addListener(
//   logURL,
//   {urls: ["<all_urls>"]},
//   ["blocking", "responseHeaders"]
// );

// my-purchases dashboard -> GETs: /mypurchases/api/v1/receipt/details <list of receipts from purchases> :: /mypurchases/api/v1/receipt/details
  // contains all prices, quantities, coupons
  // all items even w/o picture -> Items have coupons in priceModifiers Array
  // in scan order except for those with a monetizationID <ie. currently featured>
  // contains savings, price and brief information
  // ********* HAS PERSONAL PAYMENT INFORMATION **********************

// hands off unique UPCs to products API that contains all important information <prices, inventory and item data, including nutrition> :: /atlas/v1/product/v2/products
  // will only return items with valid UPCs

//// Individual Trip Page

  // Queries Product API for available UPCs for that trip /atlas/v1/product/v2/products

  // Get Receipt Image /mypurchases/api/v1/receipt-image/get-image

//// Individual Receipt Page

  // Get Data Representation of Receipt w/ purchase amounts, store, payment_info and item information :: /atlas/v1/purchase-history/details

    // does not contain every item / takes time to generate post purchase (~5 Hours), only has catalogueData and purchaseData
