
// Add the new header to the original array,
// and return it.
function setCookie(e) {
  let setMyCookie = {
    name: "Set-Cookie",
    value: "my-cookie1=my-cookie-value1"
  };
  e.responseHeaders.push(setMyCookie);
  console.log('myResponseH', e.responseHeaders)
  return {responseHeaders: e.responseHeaders};
}

function logURL(requestDetails) {
    console.log("Loading: " + requestDetails.url);
    console.log("details: ", requestDetails)

    listener(requestDetails)

  }


function listener(details) {
    let filter = chrome.webRequest.filterResponseData(details.requestId);
    console.log('filterv4', typeof(filter), Object.keys(filter))
    let decoder = new TextDecoder("utf-8");
    let encoder = new TextEncoder();
    console.log('fired')
  
    filter.ondata = event => {
      let str = decoder.decode(event.data, {stream: true});
      // Just change any instance of Example in the HTTP response
      // to WebExtension Example.

      str = str.replace(/Example/g, 'WebExtension Example');
      console.log('string', details.requestId, typeof(str), str)
      filter.write(encoder.encode(str));
      filter.disconnect();
    }
    console.log('done listening........')
    console.log('filter', typeof(filter), filter)
    return {};
  }




chrome.webRequest.onBeforeRequest.addListener(
    logURL,
    {urls: ["<all_urls>"],  types: ["xmlhttprequest", "object"]}, // "*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"
    ['blocking']
  );

chrome.webRequest.onBeforeRequest.addListener(
  listener,
  {urls:  ["<all_urls>"], types: ["xmlhttprequest", "object"]}, // "*://*.kroger.com/cl/api*", "*://*.kroger.com/atlas*"
  ["blocking"]
)

// Listen for onHeaderReceived for the target page.
// Set "blocking" and "responseHeaders".
browser.webRequest.onHeadersReceived.addListener(
  setCookie,
  {urls: ["api/"]},
  ["blocking", "responseHeaders"]
);
