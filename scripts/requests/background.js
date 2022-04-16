function logURL(requestDetails) {
    console.log("Loading: " + requestDetails.url);
    console.log("details: ", requestDetails)

    listener(requestDetails)

  }


function listener(details) {
    let filter = browser.webRequest.filterResponseData(details.requestId);
    let decoder = new TextDecoder("utf-8");
    let encoder = new TextEncoder();
    console.log('fired')
  
    filter.ondata = event => {
      let str = decoder.decode(event.data, {stream: true});
      // Just change any instance of Example in the HTTP response
      // to WebExtension Example.
      str = str.replace(/Example/g, 'WebExtension Example');
      console.log('string', str)
      filter.write(encoder.encode(str));
      filter.disconnect();
    }
    console.log('done listening........')
  
    return {};
  }

browser.webRequest.onBeforeRequest.addListener(
    logURL,
    {urls: ["<all_urls>"],  types: ["xmlhttprequest", "object"]},
    ['blocking']
  );

browser.webRequest.onBeforeRequest.addListener(
  listener,
  {urls: ["/"], types: ["xmlhttprequest", "object"]},
  ["blocking"]
)