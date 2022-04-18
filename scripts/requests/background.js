// Add the new header to the original array,
// and return it.
// var window = require('window-utils').activeWindow
// var indexedDB = (window.indexedDB || window.mozIndexedDB)
// var req = indexedDB.open('78zDB')

var master = "";

function setCookie(e) {
  let setMyCookie = {
    name: "Set-Cookie",
    value: "my-cookie1=my-cookie-value1; SameSite=None; Secure"
  };
  e.responseHeaders.push(setMyCookie);
  console.log('myResponseH', e.responseHeaders, browser.downloads)
  // let download = browser.downloads.download({saveAs: true, url: "http://127.0.0.1:5000/docs"})
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
    console.log('fired')
  
    filter.ondata = event => {
      let str = decoder.decode(event.data, {stream: true});
      // Just change any instance of Example in the HTTP response
      // to WebExtension Example.
      str = str.replace(/Example/g, 'WebExtension Example');
      master += "|" + str
      console.log(details.requestId, typeof(str), str)
      console.log('master=', master)
      filter.write(encoder.encode(str));
      filter.disconnect();
    }
    console.log('done listening........')
    console.log('filter', typeof(filter), filter)
    return {};
  }

browser.contextMenus.create({
  id: 'eat-page',
  title: "Eat this Page"
})

browser.contextMenus.onClicked.addListener(function(info, tab) {
  let download = browser.downloads.download({saveAs: true, url: "http://127.0.0.1:5000/docs", body: master})
  console.log('download', download)
  // if (info.menuItemId == "eat-page"){
  //   browser.tabs.executeScript({
  //     file: "page-eater.js"
  //   })
  // }
})


browser.webRequest.onBeforeRequest.addListener(
    logURL,
    {urls: ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"],  types: ["xmlhttprequest", "object"]},
    ['blocking']
  );

browser.webRequest.onBeforeRequest.addListener(
  listener,
  {urls:  ["*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"], types: ["xmlhttprequest", "object"]}, 
  ["blocking"]
)

// Listen for onHeaderReceived for the target page.
// Set "blocking" and "responseHeaders".
// browser.webRequest.onHeadersReceived.addListener(
//   setCookie,
//   {urls: ["<all_urls>"]},
//   ["blocking", "responseHeaders"]
// );
