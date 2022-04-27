var master = "";
var setMaster = new Set() 

function setCookie(e) {
  let setMyCookie = {
    name: "Set-Cookie",
    value: "my-cookie1=my-cookie-value1; SameSite=None; Secure"
  };
  e.responseHeaders.push(setMyCookie);
  console.log('myResponseH', e.responseHeaders, chrome.downloads)
  // let download = chrome.downloads.download({saveAs: true, url: "http://127.0.0.1:5000/docs"})
  return {responseHeaders: e.responseHeaders};
}

function logURL(requestDetails) {
    console.log("Loading: " + requestDetails.url);
    console.log("details: ", requestDetails)

    listener(requestDetails)

  }


function listener(details) {
    let filter = chrome.webRequest.filterResponseData(details.requestId);
    let decoder = new TextDecoder("utf-8");
    let encoder = new TextEncoder();
    let originRegex = /api.*|atlas.*/g
    let i = 0;
    console.log('fired')
    filter.onstart = event => {
      console.log(`${details.requestId} stream received, commence processing......`)
      
      let origin = decodeURI(details.url.match(originRegex))
      master += "|" + origin + ":" 
    }
    filter.ondata = event => {
      let str = decoder.decode(event.data, {stream: true});
      console.log("event", details.requestId, 'chunkObtained', 'buffer', event.data)
      console.log('str', str)
      master += str
      filter.write(encoder.encode(str))
      console.log('filter reachEnd of first data stream:', filter.status)
    }

    filter.onstop = event => {
      getI(details.requestId).then((ii) => {
        if (ii===0){
          master += ", "
        }
        console.log('master=', master, master.length)
      })
      
      filter.disconnect();
      console.log(`filter disconnected ${details.requestId}`, filter.constructor.name, filter.status, setMaster)
      
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

chrome.contextMenus.create({
  id: 'eat-page',
  title: "Eat this Page"
})

chrome.contextMenus.onClicked.addListener(function(info, tab) {
  let download = chrome.downloads.download({saveAs: true, url: "http://127.0.0.1:5000/docs", body: master})
  console.log(`download received && ${master.length} string cleared.`)
  master= ''
  console.log(`${master.length}`)
  // if (info.menuItemId == "eat-page"){
  //   chrome.tabs.executeScript({
  //     file: "page-eater.js"
  //   })
  // }
})


chrome.webRequest.onBeforeRequest.addListener(
    logURL,
    {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"],  types: ["xmlhttprequest", "object"]}, // ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"]
    ['blocking']
  );

chrome.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"], types: ["xmlhttprequest", "object"]}, // 
  ["blocking"]
)

// Listen for onHeaderReceived for the target page.
// Set "blocking" and "responseHeaders".
chrome.webRequest.onHeadersReceived.addListener(
  setCookie,
  {urls: ["<all_urls>"]},
  ["blocking", "responseHeaders"]
);

chrome.webRequest.onHeadersReceived.addListener(
  logURL,
  {urls: ["<all_urls>"]},
  ["blocking", "responseHeaders"]
);

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
