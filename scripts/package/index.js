// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
puppeteer.use(StealthPlugin())

async function getTestWebsite(){
  // for testing request interception and loading elements from DOM 
    const browser = await puppeteer.launch({
        headless: false,
        executablePath: "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe", 
        dumpio: false,
        args: ["--start-maximized"],
        devtools: true
    });
    k = 0
    let [page] = await browser.pages()
    await page.setViewport({width: 1920, height: 1080})
    await page.setRequestInterception(true);
    let myA;
    page
    .on('console', message =>{
      console.log(`${message.type().toUpperCase()} ${message.text()}`)
      console.log(myA, message.text())
    })
    .on('pageerror', ({ message }) => console.log(message))
    .on("request", intReq=> {
      if (intReq.isInterceptResolutionHandled()) return;
      intReq.continue();
    })
    .on('response', async (response) =>{
      if (!response.url().endsWith("whoami")){
        return
      }else { 
        console.log(`${response.status()} ${response.url()}`);
        console.log(await response.text())
      };
      
    })
    .on('requestfailed', request =>
      console.log(`${request.failure().errorText} ${request.url()}`), "\n")
    await page.goto("https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Your_first_WebExtension")
    console.log("Done...")
    
    const TextValue = await page.$eval("a", el => el.text)
    console.log("As Text Value ", TextValue)
    return null
}

const getNestedObject = (nestedObj, pathArr) => {
  return pathArr.reduce((obj, key) =>
      (obj && obj[key] !== 'undefined') ? obj[key] : undefined, nestedObj);
}

function setIterations(body, path, by){
  /**
   * @param body - the response body of request that contains totals  <Object>
   * @param path - the path to query based on structure of wanted response <Array>
   * @param by - the optional path or number of items determining the limit to the call. Sometimes can be found along number of records, while other time calls handle based on amount of on-screen/rendered DOM elements.  

   * @return iterations 
  */
  var limit; 
  if (Array.isArray(by)){
    limit = getNestedObject(body, by); 
  } else if (typeof(by)==="number"){
    limit = by
  }
  return Math.floor(+getNestedObject(body, path) / by ) + 1
}

getTestWebsite()