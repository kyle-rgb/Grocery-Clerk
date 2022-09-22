// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
const axios = require('axios'); 
require("dotenv").config();
const fs = require("fs")
const readline = require("readline");
const EventEmitter = require('node:events');
const { spawn } = require('child_process')
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { ProtocolError } = require('puppeteer');
const { symbol } = require('d3');

puppeteer.use(StealthPlugin())

async function getTestWebsite() {
  // for testing request interception and loading elements from DOM
  // sample request returns gzip encoded stream
  const browser = await puppeteer.launch({
    headless: false,
    slowMo: 500, 
    executablePath:
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    dumpio: false,
    args: ["--start-maximized","--profile-directory=Profile 1"],
    userDataDir: "C:\\c\\Profiles",
    devtools: false,
    timeout: 0,
    defaultViewport: {
      width: 1920,
      height: 1080
    }
  });
  try {
    // process.on("SIGTERM", ()=>{
    
    // })
    if (process.platform === "win32") {
      var rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
      });
    }
    offset = 0;
    let fileName = "./games.json"
    let [page] = await browser.pages();
    await page.setViewport({ width: 1920, height: 1080 });
    await page.setRequestInterception(true);
    page
      // .on("console", (message) => {
      //   console.log(`${message.type().toUpperCase()} ${message.text()}`);
      // })
      //.on("pageerror", ({ message }) => console.log("<MESSAGE>", message))
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
          offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
          return; 
        }} catch (e) {
          if (e instanceof ProtocolError) return;
          console.log("error with ", res, "@ ", e) 
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
    let input1 = await page.waitForSelector("input")
    var value = await input1.getProperty("value").then(async (val)=>await val.jsonValue()) ;
    console.log("input 1 values was ", value, " !")
    await page.waitForSelector("ul.d3-o-tabs__wrap").then(()=>{console.log("found tabs")})
    let els = await page.$$("ul.d3-o-tabs__wrap > li > button ")
    el = els[1];
    await el.click();
    await el.click();
    let setOnce = 0; 
    console.log("click registered")
    y = 5  
    setTimeout(async ()=> {
      await browser.close();
      console.log("closing browser session. <o.0> ");
      id = setInterval(async (a=y)=>{
        console.log("exiting in ", a); 
        y--
        if(y<1){
          await wrapFile(fileName)
          process.exit(); 
        }
      }, 1000);
    }, 120000)
    page.$x("//a").then((a)=>{
      a.map(async (z)=>{
        href = await z.getProperty("href");
        setOnce++;
        if (setOnce===3){
          href = await href.jsonValue();
          console.log("would be run once... =", href);
          await page.waitForNetworkIdle({idleTime: 1000});
          await z.hover();
          await z.click({button : "middle", delay: 200});
          await page.waitForTimeout(3000);
          pages = await browser.pages()
          pages[1].bringToFront(); 
        }
      })
    })
  } catch (err){
    await browser.close();
    await wrapFile("./games.json");
    console.log(err)
    return null;
  }
  return null;
}

const getNestedObject = (nestedObj, pathArr) => {
  return pathArr.reduce(
    (obj, key) => (obj && obj[key] !== "undefined" ? obj[key] : undefined),
    nestedObj
  );
};

async function writeResponse(fileName, response, url, offset) { 
  // check file existence to set character. 
  let fileExists = fs.existsSync(fileName);
  if (!fileExists){
    fs.appendFile(fileName, "[", (err)=>{
      if (err) throw err; 
    })
  }
  let data = await response.buffer();
  let metaData = `{"url": "${url}", "acquisition_timestamp": ${Date.now()},`
  let close = new Buffer.from("},")
  // handle lists
  if (data.at(0)===91){
    metaData+=`"data":`;
    metaData = new Buffer.from(metaData);
    data = Buffer.concat([metaData, data, close]);
  } else {
    // else add as attributes to object
    close = new Buffer.from(','); 
    metaData = new Buffer.from(metaData); 
    data = Buffer.concat([metaData, data.subarray(1), close]);
  }
  let len = data.length;  
  await writeJSONs(fileName, data=data, offset);
  return len
}

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

async function setUpBrowser(task) {
  /**
   * @for starting browser task, loading extension and handling location based services on websites on new browser instance
   * @note : request interception should occur only once page has setup been completed to prevent wrong location data.
   * @param  task : a camelCase string that is franchise + {wantedScrapedPageCategory} 
   */
  function dumpFrameTree(frame, indent){
    console.log(indent, frame.url());
    for (const child of frame.childFrames()){
      dumpFrameTree(child, indent+ '      ')
    }
  }
  async function asyncFilter(arr, predicate){
    // map predicate must return values if condition
    return Promise.all(arr.map(predicate)).then((results)=>arr.filter((_, idx)=> results[idx] || results[idx]===0))
  }


  const ZIPCODE = process.env.ZIPCODE; 
  const PHONE_NUMBER = process.env.PHONE_NUMBER;
  const SERVER_IP = process.env.SERVER_IP;
  var browser;
  try { 
    browser = await puppeteer.launch({
      headless: false,
      slowMo: 956, 
      executablePath:
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      dumpio: false,
      args: ["--start-maximized","--profile-directory=Profile 1"],
      userDataDir: "C:\\c\\Profiles",
      defaultViewport: {width: 1920, height: 1080},
      devtools: false,
      timeout: 0
    });
    var zipInput, wantedModality, wantedAddress; 
    let [page] = await browser.pages();
    page.on("domcontentloaded", ()=>{
      console.log("DOM LOADED AT", Date.now());
      return 
    })
    switch (task) {
      case "krogerCoupons": {
          // * kroger coupons: exit out of promotional modals (usually 1||2), click change store button, click find store, remove default zipcode in input, write wanted zipcode to input, press enter, select wanted modalitiy button (In-Store),
          // wait for page reload, select dropdown for filtering coupons, press arrow down and enter, wait for page reload
          /**
           * @tests passed
           * 
          */  
          let availableModalities = ["PICKUP", "DELIVERY", "SHIP", "IN_STORE"];
          var wantedModality = "PICKUP";
          var wantedAddress = "2301 College Station Road\nAthens, GA";
          await page.goto("https://www.kroger.com")
          await page.waitForNetworkIdle({idleTime: 2200})
          let introModals = await page.$$("button.kds-DismissalButton.kds-Modal-closeButton")
          if (introModals){
            for (let modal of introModals){
              await modal.click(); 
            }
          }
          await page.$eval("button.CurrentModality-button", (el)=>el.click());
          zipInput = await page.$("input[autocomplete='postal-code']");
          placeHolder = await zipInput.getProperty("value").then(async (v)=>await v.jsonValue());
          console.log("placeHolder was", placeHolder, " ", placeHolder.length)
          for (let j=0;j<placeHolder.length;j++){
            await zipInput.press("Backspace");
          }
          await zipInput.type("30605", {delay: 125}); // ZIPCODE
          await page.keyboard.press("Enter");
          modalityButton = await page.waitForSelector(
            `button[data-testid='ModalityOption-Button-${wantedModality}']`
          );
          await modalityButton.click();
          // outText of inner div has street address, city, state
          var targetStoreModals = await page.$$("div.ModalitySelector--StoreSearchResult") 
          console.log(targetStoreModals)
          var [targetStoreModal] = await asyncFilter(targetStoreModals, async (storeItem, index)=> {
            let address = await storeItem.$eval("div[data-testid='StoreSearchResultAddress']", (el)=>el.outerText)
            if (address === wantedAddress){ 
              return index
            } 
          })
          await Promise.all([
            // wait for reload
            page.waitForResponse(res=> res.url().endsWith("start-my-cart"), {timeout: 15000}), 
            // button to choose store
            targetStoreModal.$eval("button", (el) => el.click()),
          ])

          console.log("\nSuccess!")
          break;
      }
      case "krogerTrips": {
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
      }
      case "aldiItems": {
        /**
           * @tests passed => can be extended to other instacaRT pages exactly. publix/familydollar 
           * 
        */
          // * aldi items: wait for free delivery banner to load, select pickup button, wait for page reload, click location picker button,
          // select location by address text in locations list section and click wanted stores button, wait for page reload
          var wantedModality;
          var ZIPSTREET = "Dewberry Trail" ; // street that corresponds to zipcode
          availableModalities = ["Pickup", "Delivery"];
          var wantedAddress = "10955 Jones Bridge Road";

          await page.goto("https://shop.aldi.us/store/aldi/storefront")
          await page.waitForNetworkIdle({idleTime: 4000})
          // click pickup modal // defaults to delivery
          var [modalityButton] = await page.$$eval(
            "div[aria-label='service type'] > button",
            (els) => els.filter((el) => el.textContent == wantedModality)
          );
          // click pickup button && wait for refresh
          await Promise.all([
            page.waitForNetworkIdle({idleTime:2000}),
            modalityButton.click()
          ]);
          // click on pickup location picker
          let [locationPicker] = await page.$x("//div[contains(@class, 'PickupLocationPicker')/button[@aria-haspopup]");
          await locationPicker.click();
          // wait for map modal to appear
          await page.waitForSelector("div.__reakit-portal", {visible: true});
          // click near zip button to launch choose address modal
          await page
            .$(
              "div[aria-label='Pickup Locations List'] > section > button[aria-haspopup='dialog']"
            )
            .click();
          let inputZip = await page.$("#streetAddress");
          // do not have to press enter b/c autocomplete request occurs when typing
          // await inputZip.type(ZIPCODE);
          // let addrSuggestion = await page.$x("//div[contains(@class, 'AddressSuggestionList']");
          // await addrSuggestion.click();
          //
          await inputZip.type(ZIPSTREET);
          addrSuggestions = await page.$x("//div[contains(@class, 'AddressSuggestionList']");
          var [targetLocation] = await asyncFilter(addrSuggestions, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText")
            if (address.includes(ZIPSTREET)){ 
              return index
            } 
          });
          await page.waitForSelector("div.__reakit-portal form button").then(async (submit)=> await submit.click());
          await page.waitForNetworkIdle({idleTime: 2000})
          var targetStoreModals = await page.$$("ul[aria-labelledby='locations-list'] > li > button"); 
          var [targetStoreModal] = await asyncFilter(targetStoreModals, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText")
            if (wantedAddress && address.includes(wantedAddress)){
              return index
            } else if (!wantedAddress && index<=0){
              return index // return first entry if wantedAddress not set
            }
          });
          await targetStoreModal.click();
          await page.waitForNetworkIdle({idleTime: 2500})
          console.log("Success!")
          break;
      }
      case "publixItems": {
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
      }  
      case "publixCoupons": {
      // * publix coupons: navigate to all-deals, wait for api response, wait for copied response
      // needs to be whitelisted for accessing location or (
      // click choose a store button from navbar
      //enter in zipcode
      //press enter
      //click on store link element that matches wanted location's address)
      var wantedAddress; 
      await page.goto("https://www.publix.com")
      await page.$eval("div.store-search-toggle-wrapper button", (el)=>el.click())
      let storeSearchButton = await page.waitForSelector("input[data-qa='store-search-input']", {visible: true}) ; 
      await storeSearchButton.hover();
      await storeSearchButton.click(); 
      await storeSearchButton.type(ZIPCODE, {delay: 200}) 
      await page.$eval("button[title='Store Search']", (el)=>{
        el.click();
      })
      // filter by address ; default store pods based on zip code : 15 stores . 
      wantedStoreDiv = await page.$$eval("div.store-pod", (elems)=>{
        return elems.filter((el)=> el.$("p.address", (address)=> address===wantedAddress))
      })
      await wantedStoreDiv.$("button.choose-store-button", (el)=>el.click())
      // wait for reload
      await page.waitForNavigation({waitUntil:"domcontentloaded"});
      await page.waitForNetworkIdle({idleTime: 2000})
      // navigate to https://www.publix.com/savings/all-deals
      break;
      }
      case "foodDepotItems": {
        // * food depot items: navigate to store page, enter zipcode into input box, select store based on address, click start shopping button
        // or started immediately at specific store website
        // test worked.
        await page.goto("https://shop.fooddepot.com/online"); // <Promise <?HTTPResponse>>
        clickAndCollectButton = await page.waitForSelector("button.landing-page-button__button"); // <Promise ElementHandle>
        await clickAndCollectButton.click(); // <Promise, resolves>
        zipInput = await page.$("input.zip-code-input"); // <Promise <?ElementHandle>>
        await zipInput.type(ZIPCODE, {delay: 666}); // <Promise Resolves>
        await page.keyboard.press('Enter'); //  <Promise Resolves> 
        let firstStoreLink = await page.waitForSelector("tr.landing-page-store-row button.button.landing-page__store-go-button"); // <Promise ?ElementHandle>
        await firstStoreLink.click(); // <Promise Resolves>
        break;
      }
      case "foodDepotCoupons":{
        /**
          * food depot coupons: navigate to coupon site, enter phone number into input#phone, press enter, wait for automation on phone to send verification text,
          * IPhone Automation will extract code and send a request to a temporary server with the code, once the request is recieved, the server will forward it to node and enter it in to
          * modal's next input, shutdown server, press enter, wait for api request with authetication,
          * @requires verification via mobile, needs to be coordinated with iPhone Automations. (10 min window on verfication, should be simple if automation of task (DAG) amd automation of phone shortcut occur at same time always).
        */
        // nav to page => AppCard App That Requires MFA
        await page.goto(`http://www.fooddepot.com/coupons/`);
        let phoneInput = await page.waitForSelector("input#phone");
        await phoneInput.type(PHONE_NUMBER, {delay: 400})
        await page.$eval("button.button-login.default", async (el)=>{
          await el.click();
        })
        var parsedVerificationCode = await getFoodDepotCode(); 
        await page.$("code-input", (el)=>{
          el.type(parsedVerificationCode, {delay: 200})
        })

        // will send code on completed 
        await page.waitForNavigation({
          waitUntil: "networkidle0"
        })
        break;
      }
      case "dollarGeneralItems":{
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
      }
      case "dollarGeneralCoupons": {
        var secondLoadSwitch; 
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
        let setStoreButton = await wantedStoreElem.$("button[data-selectable-store-text='Set as my store']")
        // wait for reload,
        await Promise.all([setStoreButton.click(), page.waitForNavigation({waitFor: "networkidle0"})])
        break;
      }
      case "familyDollarItems": {
        /**
           * @tests passed
           * 
        */
        // * family dollar items: go to specific url that shows all items, press end, click select drop down for maximum items (96), wait for page refresh
        await page.goto("https://www.familydollar.com/categories?N=categories.1%3ADepartment&No=0&Nr=product.active:1")
        let selectDiv = await page.$$(".oc3-select > div > select");
        selectDiv = selectDiv[1]
        await selectDiv.hover()
        await selectDiv.click();
        await selectDiv.press("ArrowDown")
        await selectDiv.press("ArrowDown")
        await Promise.all([
          selectDiv.press("Enter"),
          page.waitForNavigation({waitUntil: "domcontentloaded"})
        ])
        console.log("Success!")
        break;
      }
      case "familyDollarInstacartItems": {
        /**
           * @tests passed
           * 
          */
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
      }
      case "familyDollarCoupons": {
      /**
         * @tests passed
         * 
        */
      // * family dollar coupons:
      var wantedStore = "1165 Ralph D Abernathy Blvd Sw,\nAtlanta, GA 30310-1757";
      // navigate to smart-coupons page,
      await page.goto("https://www.familydollar.com")
      // click your store link in nav bar,
      page.$eval("a[text='FIND A STORE']", (el)=> el.click())
      // redirects to /store-locator
      await page.waitForNavigation({waitUntil: "networkidle0"})
      // enter zip code into input,
      var locatorIFrame = await page.waitForSelector("#storeLocator");
      frameZip = await locatorIFrame.contentFrame();
      var inputZip = await frameZip.$("input") 
      await inputZip.type(ZIPCODE);
      await inputZip.press("Enter");
      await page.waitForTimeout(2000)
      var targetStoreModals = await frameZip.$$("li.poi-item")
      // select store by address,
      var [targetStoreModal] = await asyncFilter(targetStoreModals, async (poiItem, index)=> {
        let address = await poiItem.$eval("div > div.address-wrapper", (el)=>el.outerText)
        console.log(address.replace("\n", "\\n"))
        if (address === wantedStore){ 
          return index
        } 
      })
      console.log(targetStoreModal);
      await Promise.all([
        targetStoreModal.$eval("div > div.mystoreIcon > span > a", (el)=>el.click()),
        page.waitForNavigation({timeout: 15000, waitUntil: "networkidle0"})
      ]);
      let locataionChangedModal = await page.waitForSelector("div.modal.occ-notifications-modal.in a.modal-close")
      await locataionChangedModal.click();
      console.log("Success!")
      break;
      }
      // 
  } } catch (e) {
    console.log(e)
  } finally {
    await browser.close();
  }
  return null // [browser, page];
}

function getStoreData() {
  /** intercepts and copies store level data
   */
  return null;
}

async function writeJSONs(path, data, offset){
  /**
   * @param path : path to new file
   * @param dataToAdd: string represenation of newly acquired Response Jsons.
   */
  fs.open(path, "a", (err, fd)=> {
    if (err?.code === "EEXIST"){
      // data can be appended
      console.log("File already Exists")
    } else if (err){
      throw err;
    }
    // write to file 
    console.log("Writing to File...");
    buffer = data;
    fs.write(fd, buffer, 0, buffer.length, positon=offset, (err)=>{
      if (err) throw err ; 
      fs.close(fd, ()=> {
        console.log("file wrote successfully")
      })
    });
  })
 return null; 

}

async function wrapFile(fileName){
  let bytes = fs.statSync(fileName).size;
  let buffer = new Buffer.from("]")
  const fd = await fs.promises.open(fileName, "r+");
  await fd.write(buffer, 0, 1, positon=bytes-1);
  return "Done"
}

async function getKrogerTrips(page, browser){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param browser : the current browser instance
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
    let url = await interceptedRequest.url();   
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
  await page.waitForNetworkIdle({idleTime: 5500});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finsihed : ", fileName) ;
  return null;
  
}

async function getKrogerCoupons(page, browser){
    /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param brower : The current Browser instance. 
   * @prerequisite : location setup was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */ 
    var apiEmitter = new EventEmitter(); 
    var offset = 0;
    var wantedRequestRegex = /atlas\/v1\/product\/v2\/products\?|\/cl\/api\/coupons\?/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = "../requests/server/collections/familydollar/items/" + fileName; 
    await page.setRequestInterception(true)
    page.on("response", async (res)=>{
      if (res.isInterceptResolutionHandled()) return;
      try {
        let url = await res.url() ;
        if (url.match(wantedRequestRegex)){
          data = await res.buffer();
          offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
          return; 
        }
        return ; 
      } catch (err){
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
    for (let coupon of currentCoupons){
      await coupon.click();
      await page.waitForNetworkIdle({waitUntil: 3300});
      await page.keyboard.press("Escape");
    }
    await page.waitForNetworkIdle({idleTime: 3000});
    await browser.close();
    await wrapFile(fileName);
    console.log("file finsihed : ", fileName) ;
    return null;
}

async function getInstacartItems(page, browser){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param browser : the current browser instance. 
   * @prequisite setUpBrowser() successful. 
   */
  let unwantedPattern = /(outdoor|toys|bed|electronics|clothing-shoes-accessories|office-crafts-party-supplies|greeting-cards|storm-prep|tailgating|popularfloral|shop-now)$/
  let storePatterns = /(aldi|familydollar|publix)/
  let currentUrl = await page.url();
  let store = currentUrl.match(storePatterns)[0]
  let folder = store==="familydollar"? "instacartItems" : "items";
  let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  let path = "../requests/server/collections/" + [store, folder].join("/") ;
  let offset = 0;
  fileName = path+fileName ; 
  let wantedXPath = "//ul[contains(@class, 'StoreMenu')]/li/a" // XPath for custom CSS Classes Generated by Instacart
  // set request interception on page
  await page.setRequestInterception(true);
  var wantedResponseRegex =  /item_attributes|operationName=Items|operationName=CollectionProductsWithFeaturedProducts/;
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
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
      pageHeight = newHeight;
      await page.keyboard.press("End");
      await page.waitForNavigation({waitUntil: "networkidle0"});
      await page.waitForTimeout(4000);
      newHeight = await body.getProperty("offsetHeight");
    }
  }
  await page.waitForNetworkIdle({idleTime: 3000});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finsihed : ", fileName) ; 
  return null;
}

async function getPublixCoupopns(browser, page){ 
  /**
   * @param browser : the currnet browser instance . 
   * @param page : the current page instance. 
   * @prerequiste : setUpBrowser() set location successfully. 
   */
  // set request interception on page
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/publix/coupons/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedResponseRegex = /services.publix.com\/api\/.*\/savings\?/
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  await page.goto("https://www.publix.com/savings/all-deals");
  await page.waitForNetworkIdle({idleTime: 3000});
  await browser.close();
  console.log("file finsihed : ", fileName) ; 
  return null; 
}

async function getDollarGeneralCoupons(browser, page){ 
  /**
   * @prerequisite : setUpBrowser() ran successfully; 
   * @urlsToWatch : ["*://*.dollargeneral.com/bin/omni/coupons/products*", "*://*.dollargeneral.com/bin/omni/coupons/recommended*"];
   * @pathToFile : `../requests/server/collections/dollargeneral` : /items, /promotions 
   * @DOMElementsToTrack : []
   * @DOMElementsToUse : []
  */
  // set request interception on page
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/dollargeneral/promotions/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  const newPagePromise = new Promise(x => browser.once('targetcreated', target => x(target.page()))); 
  fileName = path+fileName ; 
  var wantedResponseRegex = /\/bin\/omni\/coupons\/(products|recommended)/
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  // page has reloaded to correct wanted location;
  // wait for iterations to be set 
  // then press button.button.coupons-results__load-more-button until all coupons are rendered to page;
  var loadMoreButton = await page.waitForSelector("button.button.coupons-results__load-more-button", {timeout: 6000});
  while (loadMoreButton!==null){
    await page.keyboard.press("End"); 
    await loadMoreButton.hover();
    await loadMoreButton.click(); 
    await page.waitForNetworkIdle({idleTime: 3000, timeout: 15000});
    loadMoreButton = await page.waitForSelector("button.button.coupons-results__load-more-button", {timeout: 6000})
  }
  // start back at top of the page ; 
  await page.press("Home");
  // now get all carousel nodes and begin 
  items = await page.$$("li.coupons_results-list-item a.deal-card__image-wrapper");
  left = items.length ; 
  for (item of items){
    await item.click({button: 'middle'})
    let newTab = await newPagePromise;
    await newTab.bringToFront(); 
    await newTab.waitForNetworkIdle({
      idleTime: 2000,
    })
    // check for item modal to be present
    let eligibleItems = await newTab.waitForSelector("section.couponPickDetails__products-wrapper.row", {timeout: 10000, visible: true}) ; 
    if (eligibleItems){
      let loadMoreButton = await eligibleItems.$("button.button.eligible-products-results__load-more-button") ;
      while (loadMoreButton){
        await loadMoreButton.click();
        await newTab.waitForNetworkIdle({idleTime: 3000})
        loadMoreButton = await eligibleItems.$("button.button.eligibel-products-results__load-more-button") ; 
      }
    };
    // exit out of page and return page to promotions tab ; 
    await newTab.close();
    console.log("finished promotion. ", left, " left.")
    left--;    
};
  await page.waitForNetworkIdle({idleTime: 3000});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finsihed : ", fileName) ; 
  return null;
  
}

async function getDollarGeneralItems(browser, page){
  /**
   * @prerequisite : setUpBrowser() successfully set location. 
   * @param browser : the current browser instance.
   * @param page : the current page instance.
   */
  // set request interception on page
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/dollargeneral/items/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedResponseRegex = /https\:\/\/www\.dollargeneral\.com\/bin\/omni\/pickup\/categories\?/
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  // go to sale page.
  await page.goto("https://www.dollargeneral.com/c/on-sale");
  await page.waitForNetworkIdle({waitUntil: 3300})
  let button = await page.$("button[data-target='pagination-right-arrow']") ; 
  let disabled = await button.getProperty("disabled")
  while (!disabled){
    button.click();
    await page.waitForNavigation();
    await page.waitForNetworkIdle({idleTime: 3500});
    button = await page.$("button[data-target='pagination-right-arrow']") ; 
    disabled = await button.getProperty("disabled")
  };
  await page.waitForNetworkIdle({idleTime: 3000});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finsihed : ", fileName) ; 
  return null
}

async function getFamilyDollarPromotions(browser, page){
  /**
   * @prerequisite : setUpBrowser() worked. 
   * @param browser : the existing browser instance
   * @param page : the starting page ; 
   */
  // set request interception on page
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/familydollar/coupons/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedRequestRegex = /ice-familydollar\.dpn\.inmar\.com\/v2\/offers\?/  
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedRequestRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  await page.goto("https://www.familydollar.com/smart-coupons")
  await page.waitForNetworkIdle({idleTime: 3000});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finsihed : ", fileName) ; 
  return null; 
}

async function getFamilyDollarItems(browser, page){
  /**
    * @param browser: the current browser instance .
    * @param page : PageElement from Successfully Launched Browser. 
    * @prequisite setUpBrowser() successful. Iterations Set to 96. 
    */
    // set request interception on page
    await page.setRequestInterception(true);
    var offset = 0;
    var wantedRequestRegex = /dollartree-cors\.groupbycloud\.com\/api/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = "../requests/server/collections/familydollar/items/" + fileName; 
    page.on("response", async (res)=> {
      let url = await res.url() ;
      if (url.match(wantedRequestRegex)){
        data = await res.buffer();
        offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
        return; 
      }
      return ; 
    })
    await page.goto("https://www.familydollar.com/categories?N=categories.1%3ADepartment&No=0&Nr=product.active:1");
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

    await page.waitForNetworkIdle({waitUntil: 3000}); 
    await wrapFile(fileName);
    await browser.close(); 
    console.log("finished file", fileName);
    return null
}

async function getFoodDepotItems(browser, page,){
  /**
   * @param browser : the current browser instance
   * @param page : the current page instance
   * @prerequisites : setUpBrowser() succeeded
   */
  /**
   * @prerequisite : setUpBrowser() successfully set location. 
   * @param browser : the current browser instance.
   * @param page : the current page instance.
   */
  // set request interception on page
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/dollargeneral/items/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  var wantedResponseRegex = /production-us-1\.noq-servers\.net\/api\/v.+\/stores\/.+\/products\?/
  var baseUrl = "https://shop.fooddepot.com"; 
  fileName = path+fileName;
  var pageHeight, newHeight; 
  // on store home page.
  let shopNowButton = await page.$("#site-main-menu__button")
  await shopNowButton.hover();
  await shopNowButton.click(); 
  let shopAllButton = await page.waitForSelector("li.site-main-menu__item > a")
  await shopAllButton.click();
  await page.waitForNavigation;
  await page.waitForNetworkIdle({idleTime:2000});
  // get all departments
  let allCategories = await page.$$("i.category-sibling-links__item > a")
  let categoryUrls = allCategories.map(async(el)=>{
    let href = await el.getProperty("href");
    if (!href.endsWith("shop/all")){
      return baseUrl + href;
    }
  }).filter((link)=>link);

  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+=await writeResponse(fileName=fileName, response=data, url=url, offset=offset)
      return; 
    }
    return ; 
    })

  for (let categoryUrl of categoryUrls){
    // go to each category page
    await page.goto(categoryUrl);
    await page.waitForNavigation({waitUntil: "networkidle0"});
    let body = await page.waitForSelector("body");
    pageHeight = await body.getProperty("offsetHeight")
    await page.keyboard.press("End");
    await page.waitForNetworkIdle({waitUntil: 2500});
    newHeight = await body.getProperty("offsetHeight");
    while (pageHeight !== newHeight){
      pageHeight=newHeight;
      await page.keyboard.press("End");
      await page.waitForNetworkIdle({waitUntil: 2500});
      newHeight = await body.getProperty("offsetHeight");
    }
  }
  await page.waitForNetworkIdle({waitUntil: 3000}); 
  await wrapFile(fileName);
  await browser.close(); 
  console.log("finished file", fileName);
  return null
}

async function getFoodDepotCoupons(browser, page){ 
  /**
   * @param browser : the current browser instance. 
   * @param page : the current page instance.
   * @requirements : setUpBrowser("foodDepotCoupons") was successful. 
   */
  // note : navigation to other stores promotions can only occur after MFA login 
  await page.waitForNetworkIdle({idleTime:3000});
  await page.setRequestInterception(true);
  var path = "../requests/server/collections/dollargeneral/coupons/"
  var fileName = new Date().toLocaleDateString() + ".json";
  var offset = 0;
  let wantedResponseRegex = /https\:\/\/appcard\.com\/baseapi\/.*\/token\/.*\/offers\/unclipped_recommendation_flag/
  let wantedAddress;
  fileName = path + fileName ;
  page.on("response", async (res)=> {
    let url = await res.url();
    if (url.match(wantedResponseRegex)){
      data = await res.buffer();
      offset+= await writeResponse(fileName=fileName, response=data, url=url, offset=offset);
    }
    return ;
  })
  // optional pick another store location
  let button = await page.$("button.desktop-menu");
  await button.click(); 
  let storeInfoButton = await page.waitForSelector.$("button.mat-focus-indicator.mat-menu-item")
  await storeInfoButton.click();
  // accepts city of state input 
  let locationInput = await page.waitForSelector("div.search-stores > input");
  await locationInput.type(wantedAddress);
  let moreInfoButton = await page.$("button#more-info");  
  await moreInfoButton.click();
  let preferredLocation = await page.waitForSelector("div.preferred-branch-wrapper > button");
  await preferredLocation.click();
  let confirmButton = await page.waitForSelector("duv.modal-footer.ng-start-inserted > button.modal-btn.default")
  await confirmButton.click(); 
  await page.waitForNetworkIdle({waitUntil: 5000});
  await wrapFile(fileName);
  await browser.close();
  console.log("finished file", fileName);
  return null;
}

const getFoodDepotCode = async () => {
  var SERVER_IP = process.env.SERVER_IP;
  var passedValidateCode; 
  cmd = spawn("C:\\Users\\Kyle\\anaconda3\\python", ["../requests/server/app.py"]);
  cmd.on("error", (e)=>console.error(e));

  cmd.stdout.on("data", (data)=> {
    console.log(data.toString());
  })

  cmd.stderr.on("data", async (data)=>{
    let logs = data.toString(); 
    console.log(data.toString())
    if (logs.includes("/validate")) { 
      passedValidateCode = await axios.get(SERVER_IP+"/getValidate");
      passedValidateCode = passedValidateCode.data.code; 
      console.log("code from phone", passedValidateCode);
      cmd.kill("SIGTERM")
    }
  })

return new Promise((resolve, reject) => {
  cmd.on("close", (code, signal)=>{
    console.log(`child process exited with a code of ${code} due to receipt of ${signal}`)
    resolve(passedValidateCode)
  })
  cmd.on("error", (e)=>{
    console.log("cmdline produced an error");
    reject(e);
  })
  cmd.stdout.on("error", (e)=>{
    console.log("sent to stdout err:", e);
    reject(e);
  })

});
}

// getTestWebsite()
setUpBrowser(task="krogerCoupons")