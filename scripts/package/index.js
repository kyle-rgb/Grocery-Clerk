// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
const { get } = require("http")
const {ReadableStream, WritableStream} = require("node:stream")
const fs = require("fs")
const readline = require("readline");
const EventEmitter = require('node:events');
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { isArrayLikeObject } = require('lodash');

puppeteer.use(StealthPlugin())

async function getTestWebsite() {
  // for testing request interception and loading elements from DOM
  // sample request returns gzip encoded stream
  const browser = await puppeteer.launch({
    headless: false,
    slowmo: 500, 
    executablePath:
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    dumpio: false,
    args: ["--start-maximized","--profile-directory=Profile 1"],
    userDataDir: "C:\\c\\Profiles",
    devtools: false,
    timeout: 0
  });
  // process.on("SIGTERM", ()=>{
  
  // })
  if (process.platform === "win32") {
    var rl = require("readline").createInterface({
      input: process.stdin,
      output: process.stdout
    });
  
    rl.on("SIGINT", function () {
      process.emit("SIGINT");
    });
  }
  
  

  offset = 0;
  let [page] = await browser.pages();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.setRequestInterception(true);
  page
    // .on("console", (message) => {
    //   console.log(`${message.type().toUpperCase()} ${message.text()}`);
    // })
    .on("pageerror", ({ message }) => console.log("<MESSAGE>", message))
    .on("request", (intReq) => {
      if (intReq.isInterceptResolutionHandled()) return;
      intReq.continue();
    })
    .on("response", async (res) => {
      try {
      let wantedUrl = /experience\/v1\/games\?|\/v2\/standings\?|\/v2\/stats\/live\/game-summaries\?/
      // if (res.isInterceptResolutionHandled()) return; // https://api.nfl.com/football/v2/stats/live/game-summaries?season=2022&seasonType=REG&week=2
      // https://api.nfl.com/football/v2/standings?seasonType=REG&week=2&season=2022&limit=100
      let url = await res.url();
      if (!url.match(wantedUrl)) {
        return;
      } else {
        data = await res.json();
        if (Array.isArray(data)){
          data  = {data: data, acquisition_timestamp: Date().now(), url: url  }
        }
        console.log(offset, ">>>>", url)
        offset = await writeJSONs("./games.json", data=data, offset);
        return; 
      }} catch (err){
        console.log("error with ", res, "@ ", err)
      } 
    })
    .on("domcontentloaded", ()=>{
      console.log("DOM CONTENT HAS LOADED @ ", new Date())
    });
    // .on(
    //   "requestfailed",
    //   (request) =>
    //     console.log(`${request.failure().errorText} ${request.url()}`)
    // );
  await page.goto(
    "https://www.nfl.com/"
  );
  console.log("Went to NFL.com");
  await page.waitForSelector("ul.d3-o-tabs__wrap").then(()=>{console.log("found tabs")})
  let els = await page.$$("ul.d3-o-tabs__wrap > li > button ")
  el = els[1];
  await el.click();
  await el.click();
  console.log("click registered")
  // page.$x("//a").then((a)=>{
  //   a.map(async (z)=>{
  //     href = await z.getProperty("href");
  //     console.log(await href.jsonValue())
  //   })
  // })



  return null;
}

const getNestedObject = (nestedObj, pathArr) => {
  return pathArr.reduce(
    (obj, key) => (obj && obj[key] !== "undefined" ? obj[key] : undefined),
    nestedObj
  );
};

function setIterations(body, path, by) {
  /**
   * @param body - the response body of request that contains totals  <Object>
   * @param path - the path to query based on structure of wanted response <Array>
   * @param by - the optional path or number of items determining the limit to the call. Sometimes can be found along number of records, while other time calls handle based on amount of on-screen/rendered DOM elements.  

   * @return iterations 
  */
  var limit;
  if (Array.isArray(by)) {
    limit = getNestedObject(body, by);
  } else if (typeof by === "number") {
    limit = by;
  }
  return Math.floor(+getNestedObject(body, path) / by) + 1;
}

function getScrollingData(page, wait) {
  /**
   * @for apps that bind calls to ui elements in a single page app = {FoodDepot, Publix, FamilyDollar, Aldi}
   * press end to fire call and wait for render of api element to UI interface
   * wraps end keyboard press into setTimeout
   */
  setTimeout(() => {
    page.keyboard.press("End");
  }, wait);
  return null;
}

function normalizeDay(string) {
  /**
   * @for use in normalizing store data
   */
  return null;
}

function switchUrl(x, y, url) {
  /**
   * @for use in web navigation in web scraping
   */
}

function eatThisPage(reset = false) {
  /**
   * @for sending signal remaining data in the extension to server and closing browser.
   */
}

function loadExtension() {
  /**
   * @for managing request parsing, interception and communicaton to flask server for writing copied api calls
   */
  return null;
}

async function setUpBrowser(task, url = null) {
  /**
   * @for starting browser task, loading extension and handling location based services on websites on new browser instance
   * @note : request interception should occur only once page has setup been completed to prevent wrong location data.
   */

  const ZIPCODE = process.env.ZIPCODE;
  const PHONE_NUMBER = process.env.PHONE_NUMBER;
  var page ; 
  switch (task) {
    case "krogerCoupons":
      // * kroger coupons: exit out of promotional modals (usually 1||2), click change store button, click find store, remove default zipcode in input, write wanted zipcode to input, press enter, select wanted modalitiy button (In-Store),
      // wait for page reload, select dropdown for filtering coupons, press arrow down and enter, wait for page reload
      let availableModalities = ["PICKUP", "DELIVERY", "SHIP", "IN_STORE"];
      var wantedModality;
      var wantedAddress;
      await page.$$("button.CurrentModality-button").click();

      page.$("input[autocomplete='postal-code']", async (input) => {
        input.click();
        page.keyboard.type("$zipcode");
        page.keyboard.press("Enter");
        let modalityButton = await page.$$(
          `button[data-testid='ModalityOption-Button-${wantedModality}']`
        );
        modalityButton.click();
      });

      let storeSelectDivs = await page.$$(
        "div.ModalitySelector--StoreSearchResult"
      ); // returns divs that holds button and address
      let wantedStoreDiv = await storeSelectDivs.$$eval(
        "div[data-testid='StoreSearchResultAddress'] > div",
        (elems) => elems.filter((el) => el.innerText === wantedAddress)[0]
      ); // innerText of inner div has street address, city, state
      wantedStoreDiv.$("button", (el) => el.click()); // button to choose store
      // reload not required should be handled by set iterations already, button clicking can commence
      break;
    case "krogerTrips":
      // kroger trips: click account button, my purchases select drop down link, unselect persist login check box, click sign in
      // requires credentials to be saved in browser profile
      // @requires: login
      var username, password;
      await page.$("button.WelcomeButtonDesktop", (el) => el.hover()); // activate dropdown
      await page.$("a[href='/mypurchases']", (el) => el.click()); // set redirect
      await page.$("input#SignIn-rememberMe", (el) => el.click());
      if (requireCreditentials) {
        await page.$("input#SignIn-emailInput", (el) => {
          el.click();
          page.keyboard.type(username);
        }); // if necessary
        await page.$("input#SignIn-passwordInput", (el) => {
          el.click();
          page.keyboard.type(password);
        }); // if necessary
      }
      await page.$("button#SignIn-submitButton", (el) => el.click()); // submit
      setTimeout(() => {
        setIterations(
          "https://www.kroger.com/mypurchases/api/v1/receipt/summary/by-user-id",
          (path = ["length"]),
          (by = 5)
        );
      }, 10000);
      break;
    case "aldiItems":
      // * aldi items: wait for free delivery banner to load, select pickup button, wait for page reload, click location picker button,
      // select location by address text in locations list section and click wanted stores button, wait for page reload
      var wantedModality;
      availableModalities = ["Pickup", "Delivery"];
      var wantedStore = "10955 Jones Bridge Road";
      let modalityButton = await page.$$eval(
        "div[aria-label='service type'] > button",
        (els) => els.filter((el) => el.text == wantedModality)
      );
      modalityButton.click();
      /** @todo : write helper for instacart location handling via MapBox API  */
      await page.$("div.css-1advtqp-PickupLocationPicker").click();
      await page
        .$(
          "div[aria-label='Pickup Locations List'] > section > button[type='button']"
        )
        .click();
      await page.$("address", (el) => el.parentElement.click());
      await page.$("button[type='submit']", (el) => el.click());
      let locationsList = await page.$("ul[aria-labelledby='locations-list']");
      let wantedIndex = await locationsList.$$eval(
        "span > div > div > h3",
        (elems) =>
          elems
            .map((d, i) => {
              if (d.textContent === wantedStore) {
                return i;
              }
            })
            .filter((d) => d)
      )[0];
      wantedIndex += 4; // to by pass headers and turn index to tab presses
      await page.$("h2#locations-list", (el) => el.click());
      for (let i = 1; i < wantedIndex; i++) {
        await page.press("Tab");
      }
      await page.press("Enter");
      await page.press("Enter");
      break;
    case "publixItems":
    // * publix items: enter in zipcode, press enter, select login button from new modal, enter in email+pass for publix or save in browser profile, press login,
    // wanted store and shopping modality should be saved, but refer to above aldi instructions to select a new store,
    // @requires: login
    await page.$("input[data-testid='homepage-address-input']", (el)=> {
      el.click();
      page.keyboard.type(ZIPCODE)
      page.press('Enter')
    })
    let authModal = await page.$("div.AuthModal__Content")
    authModal.$$eval("button", (elems)=> {
      let login =  elems.filter((el)=>el.textCotent==="Log in")[0];
      login.click();
    })
    // login credentials already in browser profile; store is saved to account for now, otherwise use same location / modality handling for instacart site as those above for aldi.
    await page.$("form > div > button", (el)=> el.click());
    break;  
  
  case "publixCoupons":
  // * publix coupons: navigate to all-deals, wait for api response, wait for copied response
  // needs to be whitelisted for accessing location or (
  // click choose a store button from navbar
  //enter in zipcode
  //press enter
  //click on store link element that matches wanted location's address)
  var wantedAddress; 
  await page.goto("https://www.publix.com")
  await page.$("div.store-search-toggle-wrapper button", (el)=>el.click())
  await page.$("input[data-qa='store-search-input']", (el)=>{
    el.hover();
    el.click();
  })
  await page.keyboard.type(ZIPCODE);
  await page.$("button[title='Store Search']", (el)=>{
    el.click()
  })
  wantedStoreDiv = await page.$$eval("div.store-pod", (elems)=>{
    return elems.filter((el)=> el.$("p.address", (address)=> address===wantedAddress))
  })
  await wantedStoreDiv.$("button.choose-store-button", (el)=>el.click())
  // wait for reload
  await page.waitForNavigation({waitUntil:"domcontentloaded"})
  // navigate to https://www.publix.com/savings/all-deals
  break;
  case "foodDepotItems":
    // * food depot items: navigate to store page, enter zipcode into input box, select store based on address, click start shopping button
    // or started immediately at specific store website
    break;
  case "foodDepotCoupons":
     /**
      * food depot coupons: navigate to coupon site, enter phone number into input#phone, press enter, wait for automation on phone to send verification text,
      * IPhone Automation will extract code and send a request to a temporary server with the code, once the request is recieved, the server will forward it to node and enter it in to
      * modal's next input, shutdown server, press enter, wait for api request with authetication,
      * @requires verification via mobile, needs to be coordinated with iPhone Automations. (10 min window on verfication, should be simple if automation of task (DAG) amd automation of phone shortcut occur at same time always).
    */
    await page.$("input#phone", (el)=>{
      el.type(PHONE_NUMBER, {delay: 200})
    })
    await page.$("button.button-login.default", (el)=>{
      el.click()
    })
    // wait for recieve text => screenshot => extractText => apply Regex => get Regex Match Group => send webrequest from phone with url-encoded code => request from same server for amount 
    
    
    var parsedVerificationCode = get("http://"+SERVER_IP+":5000/getValidate", async (res, err)=>{
      if (!res.statusCode===200) throw err;
      let code = await res.json().code 
      res.on("end", ()=> {
        // async call shutdown on server once verify has been called
        get("http://"+SERVER_IP+":5000/shutdown")
      })
      return res.json().code;
    })
    await page.$("code-input", (el)=>{
      el.type(parsedVerificationCode, {delay: 200})
    })

    // will send code on completed 
    await page.waitForNavigation({
      waitUntil: "networkidle0"
    })
    
    
    
    break;
  case "dollarGeneralItems":
    // * dollar general items: 
    // navigate to page,
    // force refresh,
    // select store menu,
    //select button.store-locator-menu__location-toggle,
    // select input#store-locator-input,
    // type zipcode,
    // press enter,
    // select li.store-list-item who's span-list-item__store-address-1 == wanted store address,
    // wait for reload
    // wait for iterations to be set, click button.splide__arrow.split__arrow--next
    await page.goto("https://www.dollargeneral.com/c/on-sale")
    iterations = setIterations(body, path=["categoriesResult", "ItemList", "PaginationInfo", "TotalRecords"], by=["categoriesResult", "ItemList", "PaginationInfo", "ExpectedRecordsPerPage"])
    let saleItemClass = "li.pickup-search-results__result-item"
    for (i=0; i<iterations; i++){
      await page.$("button.splide__arrow--next", (el)=> {
        el.click()
      })
      await page.waitForNavigation({
        waitUntil: "networkidle0"
      })
    }
    break;
  case "dollarGeneralCoupons":
    // * dollar general coupons:
    var wantedAddress;
    // navigate to page,
    await page.goto("https://www.dollargeneral.com/dgpickup/deals/coupons")
    // force refresh to allow access to drop down
    await page.reload()
    // select store menu,
    await page.$("div.aem-header-store-locator > button", (el)=>el.click()) // Array.from(document.querySelectorAll())
    // select button.store-locator-menu__location-toggle,
    await page.$("button.store-locator-menu__location-toggle", (el)=>el.click())
    // select input#store-locator-input,
    await page.$("input#store-locator-input", (el)=>{
      el.click();
      // delete placeholder
      for (i = 0 ; i<5 ; i++){
        page.keyboard.press("Backspace")
      }
      // type zipcode,
      page.keyboard.type(ZIPCODE);
      // submit new location
      page.$("button.location-form__apply-button", (el)=>el.click())
    })
    // select li.store-list-item who's span-list-item__store-address-1 == wanted store address,
    let wantedStoreElem = await page.$$eval("li.store-list-item", (elems)=>{
      return elems.filter((el)=> el.$("span.store-list-item__store-address-1"), (el)=>el.textContent===wantedAddress)[0]
    })
    await wantedStoreElem.$("button[data-selectable-store-text='Set as my store']")
    // wait for reload,
    // wait for iterations to be set
    let iterations = setIterations(body={}, path=["PaginationInfo", "TotalRecords"], by=["PaginationInfo", "ExpectedRecordsPerPage"])
    //then press button.button coupons-results__load-more-button until all coupons are delivered to page;
    for (i=0 ; i<iterations-1; i++){
      await page.$("button.button coupons-results__load-more-button", (el)=>{
        el.click()
      })
    }
    await page.press("Home")
    break;
  case "familyDollarItems":
    // * family dollar items: go to specific url that shows all items, press end, click select drop down for maximum items (96), wait for page refresh
    await page.goto("https://www.familydollar.com/categories?N=categories.1%3ADepartment%2Bcategories.2%3AHousehold&No=0&Nr=product.active:1")
    await page.$("occ-select select", async (el)=>{
      await el.hover()
      await page.click();
      await page.keyboard.press("ArrowDown")
      await page.keyboard.press("ArrowDown")
      await page.keyboard.press("Enter")
    })
    break;
  case "familyDollarInstacartItems":
    // * family dollar instacart items: differs from other instacart sites as it is delivery only 
    // navigate to store page
    await page.goto("https://sameday.familydollar.com/store/family-dollar/storefront")
    // click on delivery button
    await page.$$eval("button[type='button']", (elems)=>elems.slice(-1)[0].click())
    //input address location
    await page.$$eval("address", (el)=>{
      el.parentElement.parentElement.click()
    })
    //click save address button
    await page.$("div[aria-label='Choose address'] button[type='submit']", (el)=> el.click())
    //wait for reload
    break;
  case "familyDollarCoupons":
    // * family dollar coupons:
    var wantedStore = "3201 Tucker Norcross Rd Ste B2, Tucker, GA 30084-2152";
    // navigate to smart-coupons page,
    await page.goto("https://www.familydollar.com")
    // click your store link in nav bar,
    await page.$("a[text='FIND A STORE']", (el)=> el.click())
    // enter zip code into input,
    await page.$("input#inputaddress", (el)=> {
      el.click();
      page.keyboard.type(ZIPCODE);
      page.press("Enter")
    })
    // select store by address,
    var targetStoreModal = await page.$$eval("li.poi-item", (elems)=>{
      return elems.filter((el)=> {
        el.$("div.address-wrapper", (address)=> {address.textContent===wantedStore})
      })[0]
    })
    await targetStoreModal.$("div.mystoreIcon > span > a", (el)=>el.click())
    // wait for redirect
    // handle coupon navigation, request interception, and writing response to disk in separate func.  
    break;
  }
  return null;
}

function getStoreData() {
  /** intercepts and copies store level data
   */
  return null;
}

function loadMoreAppears() {
  /**
   * evaluates if further pagination is necessary for dollar general promotional items
   * can now be handled to page's individual setIterations to determine more user input is necessary
   */

  let iterations = setIterations(
    response,
    ["eligibleProductsResult", "PaginationInfo", "TotalRecords"],
    ["eligibleProductsResult", "PaginationInfo", "ExpectedRecordsPerPage"]
  );
  if (iterations == 1) {
    return;
  } else {
    for (let i = 1; i < iterations; i++) {
      page.$eval(
        "button.button eligible-products-results__load-more-button",
        (elem) => elem.click()
      );
      // some wait element for ui elements to render
    }
  }
  return null;
}

function getArrow() {
  /** specific helper function for family dollar internal items */
  // for ui arrow / currently down
  return null;
}

async function writeJSONs(path, data, offset){
  /**
   * @param path : path to new file
   * @param dataToAdd: string represenation of newly acquired Response Jsons.
   */
  startChar = offset==0 ? "[": ",";

  fs.open(path, "a", (err, fd)=> {
    if (err?.code === "EEXIST"){
      // data can be appended
      console.log("File already Exists")
    } else if (err){
      throw err;
    }
    // write to file 
    console.log("Writing to File...")
    data = startChar + JSON.stringify(data)
    buffer = new Buffer.from(data);
    fs.write(fd, buffer, 0, buffer.length, positon=offset, (err)=>{
      if (err) throw err ; 
      fs.close(fd, ()=> {
        console.log("file wrote successfully")
        offset += buffer.length 
      })
    });
  })
 return offset; 

}


function scrollDown(sleep = 10) {
  /**
   * helper to wrap sleep and end press together, iterations can be intergrated into this
   * for instacart stores: body to watch for iterations is graphql?operationName=CollectionProductsWithFeaturedProducts
   * wait for parent collection (i.e. d297-dairy-eggs) same as slug of opened tab,
   * setIterations =(body, ["data", "collectionProducts", "itemIds", "length"])
   */
  setTimeout(() => page.keyboard.press("End"), sleep);
  return null;
}

async function getKrogerCoupons(CSSSelector) {
  /**
   * @param CSSSelector = CSS path to See All Items Buttons.
   * button.kds-Button.CouponCard-viewQualifyingProducts
   */

  let buttons = await page.$$(CSSSelector);
  for (let button of buttons) {
    await button.hover();
    await button.click();
    // wait on api response
    setTimeout(() => {
      // exit of modal
      page.keyboard.press("Escape");
    }, 8000);
  }
}

async function getKrogerTrips(page){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @prerequisite : login was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */

  await page.setRequestInterception(true)
  var wantedRequestRegex = /\/mypurchases\/api|\/atlas\/v1\/product\/v2\/products/
  page.on("response", async (interceptedRequest)=>{
    if (interceptedRequest.isInterceptResolutionHandled()) return;
    if (interceptedRequest.url().match(wantedRequestRegex)){
      let res = await interceptedRequest.response()
      res = await res.json()
    }
    // write response to trips file 
  })
  
  const nextButton = async () => {
    await page.$eval("button.kds-Pagination-next", (el)=> {
    if (el.hasAttribute("disabled")){
      return false;
    } else {
      return el
    }
  })}
  while( nextButton() ){
    // click to next page
    await nextButton().click();
    // await product card render, images of items purchased to be rendered 
    await page.waitForSelector("div.PH-PurchaseCard-iconRow.flex");     
  }
}

async function getKrogerCoupons(page){
    /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @prerequisite : location setup was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */
    var wantedProductsRegex = /atlas\/v1\/product\/v2\/products\?/
    var wantedCouponsRegex = /\/cl\/api\/coupons\?/
    var apiEmitter = new EventEmitter(); 
    var jsons = []
    await page.setRequestInterception(true)
    page.on("response", async (res)=>{
      if (res.isInterceptResolutionHandled()) return;
      try {
        let url = await res.url();
        if (!url.match(wantedCouponsRegex) && !url.match(wantedProductsRegex)) {
          return;
        } else {
          res = await res.text()
          jsons.push(JSON.parse(res))
          if (url.match(wantedProductsRegex)){
            apiEmitter.emit("productsLoaded");
          } else {
            apiEmitter.emit("couponsLoaded")
          }
          return; 
        }} catch (err){
          console.log("error with ", res, "@ ", err)
        } 
    })
     // close out of intro modals
     await page.$$eval("button.kds-DismissalButton.kds-Modal-closeButton", (elems)=>{
      elems.map((el)=>el.click())
     })
     let currentCoupons = await page.$$eval("button.CouponCard-viewQualifyingProducts")
     let startingLength = currentCoupons.length;
     apiEmitter.on("couponsLoaded", async ()=>{
      moreCoupons = await page.$$("button.CouponCard-viewQualifyingProducts")
      currentCoupons.push(moreCoupons.slice(startingLength));
      startingLength = currentCoupons.length;
     })
     currentCoupons.map(async (el)=>{
      el.click();
      apiEmitter.on("productsLoaded", async ()=> {
        await page.waitForTimeout(8000);
        page.keyboard.press("Escape")
      })
     })

}


async function getInstacartItems(page, unwantedPattern){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param unwantedPattern : list of available navigations to filter out.
   * @prequisite setUpBrowser() successful. 
   */
  unwantedPattern = /(floral|shop-now)$/ // for aldi 
  unwantedPatternPublix = /(greeting-cards|storm-prep|tailgating|popular)$/
  unwantedPatternFamilyDollar = /(outdoor|toys|bed|electronics|clothing-shoes-accessories|office-crafts-party-supplies|)$/

  storePatterns = /(aldi|familydollar|publix)/
  let currentUrl = await page.url();
  let store = currentUrl.match(storePatterns)[0]
  let folder = store==="familydollar"? "instacartItems" : "items";
  let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_");
  let filePath = "../requests/server/collections/" + [store, folder, fileName].join("/") + ".json";
  let offset = 0;

  let wantedXPath = "//ul[contains(@class, 'StoreMenu')]/li/a" // XPath for custom CSS Classes Generated by Instacart
  // set request interception on page
  await page.setRequestInterception(true);
  // handle associated events: Url Captures to Inform Iteration Times + File Creation
  page
  .on("request", async (interceptedRequest)=> {
    if (interceptedRequest.isInterceptResolutionHandled()) return ;
    interceptedRequest.continue(); 
  })
  .on("response", async(res)=> {
    let url = await res.url();
    // handle file writing
    var wantedUrlsRegex = /item_attributes|operationName=Items|operationName=CollectionProductsWithFeaturedProducts/;
    if (url.match(wantedUrlsRegex)){
      var data = await res.json();
      if (Array.isArray(data)){
        data = {data: data}
      }
      data.url = await res.url();
      data.acquisition_timestamp = Date.now()
      offset = await writeJSONs(filePath, data=data, offset=offset)

    }
  })
  let wantedCategoryLinks = await page.$$(wantedXPath)
  wantedCategoryLinks=wantedCategoryLinks.map(async (link)=> {
    href = await link.getProperty("href");
    href = await link.jsonValue();
    if (href.match(unwantedPattern)){
      return href;
    } else {
      return null
    }
  }).filter((a)=>a); // perform filter on unwanted links ... 
  for (let link of wantedLinks){
    // navigate to page ;
    // wait for request where (collections_all_items_grid) in wanted request
    // once loaded responses have been copied, evalulate document.body.offsetHeight to see if more items are available. 
    var pageHeight, newHeight; 
    await page.goto(link);
    await page.waitForNavigation({waitUntil: "networkidle0"});
    var body = await page.$("body")
    pageHeight = await body.getProperty("offsetHeight");
    await page.keyboard.press("End");
    await page.waitForNavigation({waitUntil: "networkidle0"});
    newHeight = body.getProperty("offsetHeight")
    while (pageHeight !== newHeight){
      newHeight = pageHeight;
      await page.keyboard.press("End");
      await page.waitForNavigation({waitUntil: "networkidle0"});
      await page.waitForTimeout(4000);
      newHeight = await body.getProperty("offsetHeight");
    }

  }
}

process.on("SIGINT", function () {
  //graceful shutdown
  console.log("bye bye....");
  fs.appendFileSync("./gamer.json", "]",)
  console.log("successfully closed javascript objects....")
  process.exit()
});

async function getFamilyDollarItems(page){
/**
  * 
  * @param page : PageElement from Successfully Launched Browser. 
  * @prequisite setUpBrowser() successful. Iterations Set to 96. 
  */

  // set request interception on page
  await page.setRequestInterception(true);
  // handle associated events: Url Captures to Inform Iteration Times + File Creation
  page.on("response", async(res)=> {
    let url = await res.url();
    // handle file writing
    if (url.match(responseRegex)){
      var data = await res.json();
      if (Array.isArray(data)){
        data = {data: data}
      }
      data.url = await res.url();
      data.acquisition_timestamp = Date.now()
      offset = await writeJSONs(filePath, data=data, offset=offset)
    }
  })
  await page.goto("https://www.familydollar.com/categories?N=categories.1%3ADepartment&No=0&Nr=product.active:1");
  var offset = 0;
  var responseRegex = /dollartree-cors\.groupbycloud\.com\/api/
  let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  let filePath = "../requests/server/collections/familydollar/items/" + fileName; 
  let iterations = await page.$eval("span.category-count", (el)=>{
    return + el.textContent.replaceAll(/(\(|\))/g, "")
  })
  iterations = Math.floor(iterations/96) + 1;
  // wait for page reload
  
  for (i=0; i<iterations; i++){
    await page.waitForSelector("a.search-product-link");
    await page.waitForTimeout(4000);
    await page.keyboard.press("Enter");
    await page.$("a[aria-label='Next']", (el)=>el.click()); // this is for getFamilyDollarItems
  }
  return null
}






getTestWebsite()