// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
const axios = require('axios'); 
require("dotenv").config();
const fs = require("fs")
const readline = require("readline");
const EventEmitter = require('node:events');
const { spawn } = require('child_process');
const {MongoClient, UnorderedBulkOperation} = require('mongodb');
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { ProtocolError, TimeoutError } = require('puppeteer');


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
    args: [
      "--start-maximized",
      "--profile-directory=Profile 1",
    ],
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

    await page.waitForTimeout(500000)

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
  try {
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
  } catch (err){
    if (err instanceof ProtocolError){
      console.log("error loading buffer for", url)
      console.log(err)
      console.log(response.headers())
    } else {
      console.log("general error = ", err)
      console.log("for url : ", url)
      console.log(response.headers())
    }
    return 0
  }
}

function dumpFrameTree(frame, indent){
  console.log(indent, frame.url());
  for (const child of frame.childFrames()){
    dumpFrameTree(child, indent+ '      ')
  }
}

async function asyncFilter(arr, predicate){
  // map predicate must return values if condition
  return Promise.all(arr.map(predicate)).then((results)=>{
    results = results.filter((i)=>i);
    if (results.length===0){
      return arr[0]
    } else {
      return arr[results[0]]
    }
  })
}

async function setUpBrowser(task) {
  /**
   * @for starting browser task, loading extension and handling location based services on websites on new browser instance
   * @note : request interception should occur only once page has setup been completed to prevent wrong location data.
   * @param  task : a camelCase string that is franchise + {wantedScrapedPageCategory} 
   */
  let dbArgs = {};
  dbArgs["task"] = task
  let entryID = await insertRun(setUpBrowser, "runs", "node_call", dbArgs, false, undefined,
  `Puppeteer Node.js Call for Scrape of ${setUpBrowser.name} for ${new Date().toLocaleDateString()}`)

  async function checkForErrorModal(){
    let errorVisible  = await page.$eval("#global-message-modal", (el)=>el.getAttribute("aria-hidden"));
    console.log("type from getAttribute", typeof errorVisible, ' ', errorVisible)
    errorVisible = errorVisible === 'false'? !errorVisible : !!errorVisible; 
    if (!errorVisible){
      // force refresh to allow access if alert modal appears when accessing drop down
      await errorModal.$eval("#global-message-modal button.global-modal__close-button", (el)=>el.click())
      await page.waitForNetworkIdle({idleTime: 2000})
      await page.reload();
      return true;
    }
    return false;
  }

  var ZIPCODE = process.env.ZIPCODE; 
  const PHONE_NUMBER = process.env.PHONE_NUMBER;
  var browser, page;
  try { 
    browser = await puppeteer.launch({
      headless: task===""? true : false,
      slowMo: 888, 
      executablePath:
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      dumpio: true,
      args: [
        "--start-maximized",
        "--profile-directory=Profile 1",
      ],
      userDataDir: "C:\\c\\Profiles",
      defaultViewport: {width: 1920, height: 1080},
      devtools: false,
      timeout: 0
    });
    var zipInput, wantedModality, wantedAddress; 
    [page] = await browser.pages();
    page.on("domcontentloaded", ()=>{
      console.log("DOM LOADED AT", Date.now());
      return 
    })
    page.on("load", ()=>{
      console.log("FULL CONTENT LOADED @ ", Date.now());
      return 
    })
    switch (task) {
      case "krogerCoupons": {
          // * kroger coupons: exit out of promotional modals (usually 1||2), click change store button, click find store, remove default zipcode in input, write wanted zipcode to input, press enter, select wanted modalitiy button (In-Store),
          // wait for page reload, select dropdown for filtering coupons, press arrow down and enter, wait for page reload
          /**
           * @tests passed
          */  
          let availableModalities = ["PICKUP", "DELIVERY", "SHIP", "IN_STORE"];
          var wantedModality = "PICKUP";
          var wantedAddress = "3559 Chamblee Tucker Rd"; // "4357 Lawrenceville Hwy"
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
          placeHolder = await zipInput.getProperty("value").then((v)=> v.jsonValue());
          console.log("placeHolder was", placeHolder, " ", placeHolder.length)
          for (let j=0;j<placeHolder.length;j++){
            await zipInput.press("Backspace");
          }
          await zipInput.type(ZIPCODE, {delay: 125}); // ZIPCODE
          await page.keyboard.press("Enter");
          modalityButton = await page.waitForSelector(
            `button[data-testid='ModalityOption-Button-${wantedModality}']`
          );
          await modalityButton.click();
          if (wantedModality === "PICKUP" || wantedModality === "IN_STORE"){
            // outerText of inner div has street address, city, state
            var targetStoreModals = await page.$$("div.ModalitySelector--StoreSearchResult") 
            var targetStoreModal = await asyncFilter(targetStoreModals, async (storeItem, index)=> {
              let address = await storeItem.$eval("div[data-testid='StoreSearchResultAddress']", (el)=>el.outerText)
              if (address.includes(wantedAddress)){ 
                return index
              } 
            })
            // button to choose right store
            await targetStoreModal.$eval("button", (el) => el.click());
          } 
          page.waitForNetworkIdle({idleTime: 4500})
          break;
      }
      case "krogerTrips": {
          // kroger trips: click account button, my purchases select drop down link, unselect persist login check box, click sign in
          // requires credentials to be saved in browser profile
          // @requires: login
          await page.goto("chrome://settings")
          await page.waitForTimeout(9999)
          const USERNAME_KROGER = process.env.USERNAME_KROGER;
          const PASSWORD_KROGER = process.env.PASSWORD_KROGER;
          await page.goto("https://www.kroger.com");
          await page.waitForNetworkIdle({idleTime: 2000});
          let introModals = await page.$$("button.kds-DismissalButton.kds-Modal-closeButton")
          if (introModals){
            for (let modal of introModals){
              await modal.click(); 
            }
          }
          await page.$eval("a[href='/mypurchases']", (el) => el.click()); // set redirect
          let rememberCreditentialsButton = await page.waitForSelector("#SignIn-rememberMe"); // deselect
          await rememberCreditentialsButton.click()
          let emailInput = await page.$("#SignIn-emailInput")
          let passwordInput = await page.$("#SignIn-passwordInput");
          await emailInput.type(USERNAME_KROGER, {delay: 120});
          await passwordInput.type(PASSWORD_KROGER, {delay: 150});

          break; 
      }
      case "aldiItems": {
        /**
           * @tests passed => can be extended to other instacaRT pages exactly. publix/familydollar 
           * 
        */
          // * aldi items: wait for free delivery banner to load, select pickup button, wait for page reload, click location picker button,
          // select location by address text in locations list section and click wanted stores button, wait for page reload
          var ZIPSTREET = "Old Norcross Tucker Rd" ; // street that corresponds to zipcode
          var availableModalities = ["Pickup", "Delivery"];
          var wantedStoreAddress = "1669 Scott Boulevard";
          var wantedModality = availableModalities[0]; // @param?
          console.log(wantedModality, `div[class$='${wantedModality === "Delivery" ? wantedModality+"Address" : wantedModality+"Location"}Picker'] button[aria-haspopup]`)
          await page.goto("https://shop.aldi.us/store/aldi/storefront")
          await page.waitForNetworkIdle({idleTime: 4000})
          // click pickup modal // defaults to delivery
          var modalityButtons =await page.$$("div[aria-label='service type'] > button");
          var modalityButton = await asyncFilter(modalityButtons, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (address === wantedModality){ 
              return index
            } 
          });
          console.log(modalityButton)
          console.log(await modalityButton.getProperty("innerText").then((j)=>j.jsonValue()));
          // click pickup button && wait for refresh
          await Promise.all([
            page.waitForNetworkIdle({idleTime:2000}),
            modalityButton.click()
          ]);
          // click on pickup location picker
          let locationPicker = await page.$(`div[class$='${wantedModality === "Delivery" ? wantedModality+"Address" : wantedModality+"Location"}Picker'] button[aria-haspopup]`);
          await locationPicker.click();
          // wait for map modal to appear
          await page.waitForSelector(`div.__reakit-portal div[aria-label='${wantedModality === "Delivery" ? "Choose address" : "Choose a pickup location" }']`,
          {visible: true});
          if (wantedModality === "Pickup"){
            // click zip button to launch choose address modal
            await page.$eval("button[class$='AddressButton']", (el)=>el.click());

          }
          
          let inputZip = await page.waitForSelector("#streetAddress");
          // do not have to press enter b/c autocomplete request occurs when typing
          await inputZip.type(ZIPSTREET);
          addrSuggestions = await page.$$("div[class$='AddressSuggestionList']");
          var targetLocation = await asyncFilter(addrSuggestions, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (address.includes(ZIPCODE)){ 
              return index
            } 
          });
          await targetLocation.click();
          await page.waitForSelector("div.__reakit-portal form button").then(async (submit)=> await submit.click());
          // below to select pickup for specific store, choosing the delivery option would revert you back to main page
          if (wantedModality==="Pickup"){
            var targetStoreModals = await page.$$("ul[aria-labelledby='locations-list'] > li > button"); 
            var targetStoreModal = await asyncFilter(targetStoreModals, async (storeItem, index)=> {
              let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
              if (wantedStoreAddress && address.includes(wantedStoreAddress)){
                return index
              } else if (!wantedStoreAddress && index<=0){
                return index // return first entry if wantedAddress not set, i.e. closest store to given address
              }
            });
            await targetStoreModal.click();
            // allow time for mapbox requests to complete & so mapbox comes into focus
            await page.waitForNetworkIdle({idleTime: 1000})
            await page.keyboard.press("Enter");
          }
          await page.waitForNetworkIdle({idleTime: 5500})
          break;
      }
      case "publixItems": {
        /**
         * @tests passed
         */
        var ZIPSTREET = "Old Norcross Tucker Rd" ; // street that corresponds to zipcode
        var availableModalities = ["Pickup", "Delivery"];
        var wantedStoreAddress = "4650 Hugh Howell Rd";
        var wantedModality = availableModalities[0]; // @param?
        console.log(wantedModality, `div[class$='${wantedModality === "Delivery" ? wantedModality+"Address" : wantedModality+"Location"}Picker'] button[aria-haspopup]`)
        await page.goto("https://delivery.publix.com/store/publix/storefront")
        await page.waitForNetworkIdle({idleTime: 4000})
        // click pickup modal // defaults to delivery
        var modalityButtons =await page.$$("div[aria-label='service type'] > button");
        var modalityButton = await asyncFilter(modalityButtons, async (storeItem, index)=> {
          let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
          if (address.includes(wantedModality)){ 
            return index
          } 
        });
        console.log(modalityButton)
        console.log(await modalityButton.getProperty("innerText").then((j)=>j.jsonValue()));
        // click pickup button && wait for refresh
        await Promise.all([
          page.waitForNetworkIdle({idleTime:2000}),
          modalityButton.click()
        ]);
        // click on pickup location picker
        let locationPicker = await page.$(`div[class$='${wantedModality === "Delivery" ? wantedModality+"Address" : wantedModality+"Location"}Picker'] button[aria-haspopup]`);
        await locationPicker.click();
        // wait for map modal to appear
        await page.waitForSelector(`div.__reakit-portal div[aria-label='${wantedModality === "Delivery" ? "Choose address" : "Choose a pickup location" }']`,
        {visible: true});
        if (wantedModality === "Pickup"){
          // click zip button to launch choose address modal
          await page.$eval("button[class$='AddressButton']", (el)=>el.click());
        }
        
        let inputZip = await page.waitForSelector("#streetAddress");
        // do not have to press enter b/c autocomplete request occurs when typing
        await inputZip.type(ZIPSTREET);
        var addrSuggestions = await page.$$("div[class$='AddressSuggestionList']");
        var targetLocation = await asyncFilter(addrSuggestions, async (storeItem, index)=> {
          let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
          if (address.includes(ZIPCODE)){ 
            return index
          } 
        });
        await targetLocation.click();
        await page.waitForSelector("div.__reakit-portal form button").then(async (submit)=> await submit.click());
        // below to select pickup for specific store, choosing the delivery option would revert you back to main page
        if (wantedModality==="Pickup"){
          var targetStoreModals = await page.$$("ul[aria-labelledby='locations-list'] > li > button"); 
          var targetStoreModal = await asyncFilter(targetStoreModals, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (wantedStoreAddress && address.includes(wantedStoreAddress)){
              return index
            }
          });
          await targetStoreModal.click();
          // allow time for mapbox requests to complete & so mapbox comes into focus
          await page.waitForNetworkIdle({idleTime: 1000})
          await page.keyboard.press("Enter");
        }
        await page.waitForNetworkIdle({idleTime: 5500})
        break;
      }  
      case "publixCoupons": {
      // * publix coupons: navigate to all-deals, wait for api response, wait for copied response
      // needs to be whitelisted for accessing location or (
      // click choose a store button from navbar
      //enter in zipcode
      //press enter
      //click on store link element that matches wanted location's address)
      var wantedStoreAddress = "4650 Hugh Howell Rd"; 
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
      let wantedStoreDivs = await page.$$("div.store-pod")
      var wantedStoreDiv = await asyncFilter(wantedStoreDivs, async (storeItem, index)=> {
        let address = await storeItem.$("p.address")
        address = await address.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
        if (address.includes(wantedStoreAddress)){ 
          return index
        } 
      });
      await Promise.all([
        page.waitForNavigation({waitUntil:"load"}),
        wantedStoreDiv.$eval("button.choose-store-button", (el)=>el.click())
      ])
      await 
      // wait for reload
      await page.waitForNetworkIdle({idleTime: 4000})
      // navigate to https://www.publix.com/savings/all-deals
      break;
      }
      case "foodDepotItems": {
        // * food depot items: navigate to store page, enter zipcode into input box, select store based on address, click start shopping button
        // or started immediately at specific store website
        // test worked.
        var wantedAddress = "Douglasville Hwy 5"
        await page.goto("https://shop.fooddepot.com/online"); // <Promise <?HTTPResponse>>
        clickAndCollectButton = await page.waitForSelector("button.landing-page-button__button"); // <Promise ElementHandle>
        await clickAndCollectButton.click(); // <Promise, resolves>
        zipInput = await page.$("input.zip-code-input"); // <Promise <?ElementHandle>>
        await zipInput.type(ZIPCODE, {delay: 666}); // <Promise Resolves>
        await page.keyboard.press('Enter'); //  <Promise Resolves> 
        let firstStoreLink = await page.waitForSelector("tr.landing-page-store-row button.button.landing-page__store-go-button"); // <Promise ?ElementHandle>
        await Promise.all([
          firstStoreLink.click(), // <Promise Resolves>
          page.waitForNavigation({"waitUntil": "load"})
        ])
        break;
      }
      case "foodDepotCoupons":{
        /**
          * food depot coupons: navigate to coupon site, enter phone number into input#phone, press enter, wait for automation on phone to send verification text,
          * IPhone Automation will extract code and send a request to a temporary server with the code, once the request is recieved, the server will forward it to node and enter it in to
          * modal's next input, shutdown server, press enter, wait for api request with authetication,
          * @requires verification via mobile, needs to be coordinated with iPhone Automations. (10 min window on verfication, should be simple if automation of task (DAG) amd automation of phone shortcut occur at same time always).
        */
        var wantedAddress = null// "3696 Highway 5";
        await page.goto(`https://www.fooddepot.com/coupons/`, {waitUntil: "load"});
        // nav to page => AppCard App That Requires MFA ; allow additional time for shortcut to run
        page.setDefaultTimeout(timeout=120000)
        var appCardIFrame = await page.$("#ac-iframe");
        console.log(appCardIFrame)
        let frameCoupons = await appCardIFrame.contentFrame();
        console.log(frameCoupons.url())
        if (appCardIFrame){
          let phoneInput = await frameCoupons.$("#phone");
          if (!phoneInput){
            await page.screenshot({fullPage: true, "path": "./pic.png"})
            throw new Error("no id phone. already logged in")
          }
          console.log(phoneInput)
          await phoneInput.type(PHONE_NUMBER, {delay: 400})
          console.log("wrote phone number")
          await frameCoupons.$eval("button.button-login.default", async (el)=>{
            await el.click();
          })
          console.log("clicked login button")
          var parsedVerificationCode = await getFoodDepotCode(entryID); 
          let codeInput = await frameCoupons.waitForSelector("code-input")
          await codeInput.type(parsedVerificationCode, {delay: 200})
          // will send code typeFinish on completed 
          await page.waitForNetworkIdle({
            idleTime: 5500
          })
        }
        
        if (wantedAddress){
            // handle change in wanted location if  
          var moreButton = await frameCoupons.$("button[aria-label='More']");
          await moreButton.click();
          await page.waitForTimeout(3000);
          var dropDownButtons = await frameCoupons.$$("div.mat-menu-content > button[role='menuitem']")
          var modalityButton = await asyncFilter(dropDownButtons, async (item, index)=> {
            let buttonText = await item.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (buttonText.includes("Store Info")){ 
              return index
            } 
          });
          console.log(modalityButton)
          await modalityButton.click();
          await page.waitForTimeout(3000);
          var availableStores = await frameCoupons.$$("li[app-branch-info]")
          var wantedStore = await asyncFilter(availableStores, async (storeItem, index)=> {
            let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (address.includes(wantedAddress) && !address.includes("Ecomm")){ 
              return index
            }
          });
          await wantedStore.$eval("button#more-info", (el)=>el.click());
          await wantedStore.$eval("div.branch-info-collapse.is-iframe.is-open button", (el)=>el.click())
          var finalizeNewStore = await frameCoupons.waitForSelector("app-active-branch button.modal-btn.default")
          await finalizeNewStore.click()
          await frameCoupons.waitForNetworkIdle({idleTime: 3000})
        }
        break;
      }
      case "dollarGeneralItems":{
        // * dollar general items: 
        var wantedStoreAddress = "4312 Chamblee Tucker Road";
        var wasError; 
        var step = 0
        var tries = 0;
        // provide break points for evaluating existance of error modal at different steps of the setup procedure. If ever error, restart process with known workaround.        
        do {
          if (step===0){
            tries++;
            if (tries>4){
              throw new Error(`Error Modal Continutes on All Setup Pages after ${tries} tries.`)
            }
            // navigate to homepage : 
            await page.goto("https://www.dollargeneral.com/dgpickup")
            await page.waitForNetworkIdle({idleTime: 3000})
            // select store menu,
            await page.$eval("div.aem-header-store-locator > button", (el)=>el.click()) 
          } else if (step===1){
              // select button.store-locator-menu__location-toggle,
            await page.$eval("button.store-locator-menu__location-toggle", (el)=>el.click())
            // select input#store-locator-input,
            let zipInput = await page.waitForSelector("input#store-locator-input");
            await zipInput.click();
            // delete placeholder
            for (i = 0 ; i<5 ; i++){
              page.keyboard.press("Backspace")
            }
            // type zipcode,
            await page.keyboard.type(ZIPCODE, {delay: 100});
            // submit new location
            await page.$eval("button.location-form__apply-button", (el)=>el.click())
            // select li.store-list-item who's span-list-item__store-address-1 == wanted store address,
            let wantedStoreDivs = await page.$$("li.store-list-item");
            var wantedStoreDiv = await asyncFilter(wantedStoreDivs, async (storeItem, index)=> {
            address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
            if (address.includes(wantedStoreAddress)){ 
                return index
              } 
            });
            // "span.store-list-item__store-address-1"
            let setStoreButton = await wantedStoreDiv.$("button[data-selectable-store-text='Set as my store']")
            // wait for reload,
            await Promise.all([setStoreButton.click(), page.waitForNetworkIdle({idleTime: 6000})])
          }
          wasError = await checkForErrorModal(); 
          step = wasError ? 0 : step+1;
        } while (!wasError);
        break; 
        }
      case "dollarGeneralCoupons": {
        // * dollar general coupons:
        var wantedStoreAddress = "4312 Chamblee Tucker Road";
        var wasError, step = 0, tries = 0;
        // provide break points for evaluating existance of error modal at different steps of the setup procedure. If ever error, restart process with known workaround.        
        do {
          console.log("i was done")
          if (step===0){
            tries++;
            console.log("i was done 1")
            if (tries>4){
              throw new Error(`Error Modal Continutes on All Setup Pages after ${tries} tries.`)
            }
            // navigate to homepage : 
            await page.goto("https://www.dollargeneral.com/dgpickup")
            await page.waitForNetworkIdle({idleTime: 5000})
            // select store menu,
            await page.$eval("div.aem-header-store-locator > button", (el)=>el.click()) 
          } else if (step===1){
            console.log("i was done 2")
              // select button.store-locator-menu__location-toggle,
            await page.$eval("button.store-locator-menu__location-toggle", (el)=>el.click())
            // select input#store-locator-input,
            let zipInput = await page.waitForSelector("input#store-locator-input");
            await zipInput.click();
            // delete placeholder
            for (i = 0 ; i<5 ; i++){
              page.keyboard.press("Backspace")
            }
            // type zipcode,
            await page.keyboard.type(ZIPCODE, {delay: 100});
            // submit new location
            await page.$eval("button.location-form__apply-button", (el)=>el.click())
            // select li.store-list-item who's span-list-item__store-address-1 == wanted store address,
            await page.waitForTimeout(5000)
            let wantedStoreDivs = await page.$$("li.store-list-item");
            console.log(wantedStoreDivs)
            var wantedStoreDiv = await asyncFilter(wantedStoreDivs, async (storeItem, index)=> {
            address = await storeItem.getProperty("innerText").then(async (jsHandle)=> await jsHandle.jsonValue());
            console.log(address)
            if (address.includes(wantedStoreAddress)){ 
                return index
              } 
            });
            console.log(wantedStoreDiv)
            // "span.store-list-item__store-address-1"
            let setStoreButton = await wantedStoreDiv.$("button[data-selectable-store-text='Set as my store']")
            // wait for reload,
            await Promise.all([setStoreButton.click(), page.waitForNetworkIdle({idleTime: 3000})])
            break;
          }
          wasError = await checkForErrorModal(); 
          step = wasError ? 0 : step+1;
          console.log(wasError, step)
        } while (!wasError);
        break;
      }
      case "familyDollarItems": {
        /**
           * @tests passed
           * 
        */
        // * family dollar items: go to specific url that shows all items, press end, click select drop down for maximum items (96), wait for page refresh
        var wantedStore = "3201 Tucker Norcross Rd Ste B2,\nTucker, GA 30084-2152";
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
        await page.waitForNetworkIdle({idleTime: 4000})
        var targetStoreModals = await frameZip.$$("li.poi-item")
        // select store by address,
        var targetStoreModal = await asyncFilter(targetStoreModals, async (poiItem, index)=> {
          let address = await poiItem.$eval("div > div.address-wrapper", (el)=>el.outerText)
          if (address === wantedStore){ 
            return index
          } 
        })
        console.log(targetStoreModal);
        await Promise.all([
          targetStoreModal.$eval("div > div.mystoreIcon > span > a", (el)=>el.click()),
          page.waitForNavigation({timeout: 15000, waitUntil: "load"})
        ]);
        let locationChangedModal = await page.$("div.modal.occ-notifications-modal.in a.modal-close");
        if (locationChangedModal){
          await locationChangedModal.click();
        }
        await page.goto("https://www.familydollar.com/categories?N=categories.1%3ADepartment&No=0&Nr=product.active:1")
        await page.waitForNetworkIdle({idleTime: 3500})
        break;
      }
      case "familyDollarInstacartItems": {
        // * family dollar instacart items: differs from other instacart sites as it is delivery only 
        var ZIPSTREET = "Old Norcross Tucker Rd" ;
        // navigate to store page
        await page.goto("https://sameday.familydollar.com/store/family-dollar/storefront")
        // click on delivery button
        await page.$eval("button:not([aria-label])[type]", (elem)=>elem.click())
        //input address location
        var inputZip = await page.waitForSelector("#streetAddress")
        await inputZip.type(ZIPSTREET, {delay: 125})
        var addrSuggestions = await page.$$("div[class$='AddressSuggestionList']");
        var targetLocation = await asyncFilter(addrSuggestions, async (storeItem, index)=> {
          let address = await storeItem.getProperty("innerText").then((v)=>v.jsonValue())
          console.log(address.replaceAll("\n", "\\n"))
          if (address.includes(ZIPCODE)){ 
            return index
          } 
        });
        await targetLocation.click(); 
        //click save address button
        var addressSubmit = await page.waitForSelector("div[class$='UserAddressManager'] button[type='submit']");
        await addressSubmit.click()
        //wait for reload
        await page.waitForNetworkIdle({idleTime: 3000})
        break;
      }
      case "familyDollarCoupons": {
      /**
         * @tests passed
         * 
        */
      // * family dollar coupons:
      var wantedStore = "3201 Tucker Norcross Rd Ste B2,\nTucker, GA 30084-2152";
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
      var targetStoreModal = await asyncFilter(targetStoreModals, async (poiItem, index)=> {
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
      await Promise.all([
        locataionChangedModal.click(),
        page.waitForNavigation({waitUntil: "load"})
      ])
      break;
      }
      case "": {        
        break;
      }
      
  }
  console.log("Success!") 
} catch (e) {
    console.log(e)
  }
  insertRun(setUpBrowser, "runs", "node_call", dbArgs, true, entryID,
  `Puppeteer Node.js Call for Scrape of ${setUpBrowser.name} for ${new Date().toLocaleDateString()}`)
  return [browser, page, entryID];
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
  await fd.close();
  return "Done"
}

async function getKrogerTrips(browser, page, _id){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param browser : the current browser instance
   * @prerequisite : login was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getKrogerTrips, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getKrogerTrips.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  var path = "../requests/server/collections/kroger/trips/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var wantedResponseRegex = /\/mypurchases\/api\/v.\/receipt\/details|\/atlas\/v1\/product\/v2\/products/
  path += fileName
  var offset = 0 ;
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      offset+=await writeResponse(fileName=path, response=res, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  await Promise.all([
    page.waitForNavigation({waitUntil: "load"}),
    page.$eval("#SignIn-submitButton", (el) => el.click())
  ])
  await page.waitForNetworkIdle({idleTime: 4000})
  
  const nextButton = async () => {
    let isNext = await page.$eval("button.kds-Pagination-next", (el)=>!el.disabled);
    if (isNext){
      return await page.$("button.kds-Pagination-next")
    } else {
      return false
    }
  }
  let element = await nextButton()
  console.log(element)
  let yy = 1;
  let st = null;
  while( element ){
    st = Date.now()
    // click to next page
    await element.click();
    // await product card render, images of items purchased to be rendered 
    await page.waitForNetworkIdle({idleTime: 8000})
    await page.waitForSelector("div[aria-label='Purchase History Order']");
    element = await nextButton();
    yy++
    console.log(element, yy, ' ', (Date.now()-st)/1000, ' seconds')
  }
  await page.waitForNetworkIdle({idleTime: 5500});
  await browser.close();
  await wrapFile(fileName);
  console.log("file finished : ", fileName);
  await browser.close();
  console.log("exiting....")
  insertRun(getKrogerTrips, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getKrogerTrips.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null;
}

async function getKrogerCoupons(browser, page, type, _id){
    /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param brower : The current Browser instance. 
   * @prerequisite : location setup was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */ 
    if (!['cashback', 'digital'].includes(type)){
      throw new Error(`Type is not right . Avaialable Values: 'cashback' or 'digital' `)
    }
    let dbArgs = {};
    ["browser", "page", "type"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
    insertRun(getKrogerCoupons, "runs", "node_call", dbArgs, false, _id,
    `Puppeteer Node.js Call for Scrape of ${getKrogerCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
    
    // set url based on type 
    var promotionUrl = type === "digital" ? "https://www.kroger.com/savings/cl/coupons" : "https://www.kroger.com/savings/cbk/cashback" ;  
    var apiEmitter = new EventEmitter(); 
    var offset = 0;
    var wantedRequestRegex = /atlas\/v1\/product\/v2\/products\?|\/cl\/api\/coupons/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = `../requests/server/collections/kroger/${type}/` + fileName; 
    await page.goto(promotionUrl);
    page.on("response", async (res)=>{
      let url = res.url() ;
      if (url.match(wantedRequestRegex)){
        let req = res.request()
        let method = req.method()
        if (method!=="OPTIONS"){
          if (url.includes("coupons?")){
            console.log("emitting coupons event")
            apiEmitter.emit("couponsLoaded")
          }
          offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
        }
        return; 
      }
      return ; 
    })
    
    await page.waitForNetworkIdle({idleTime: 4500})
    // close out of intro modals
    let introModals = await page.$$("button.kds-DismissalButton.kds-Modal-closeButton")
    for (intro of introModals){
      await intro.click();
    }
    let sortButton = await page.$("select[data-testid='catalogue-sort']")    
    await sortButton.click();
    await sortButton.press("ArrowDown");
    await sortButton.press("ArrowDown");
    await sortButton.press("Enter");
    await page.waitForNetworkIdle({idleTime: 4000})
    let currentCoupons = await page.$$("button.CouponCard-viewQualifyingProducts")
    let startingLength = currentCoupons.length;
    apiEmitter.on("couponsLoaded", async ()=>{
      moreCoupons = await page.$$("button.CouponCard-viewQualifyingProducts")
      currentCoupons = currentCoupons.concat(moreCoupons.slice(startingLength));
      startingLength = currentCoupons.length;
    })
    for (let i = 0 ; i < currentCoupons.length ; i++){
      let coupon = currentCoupons[i]
      await coupon.click();
      await page.waitForNetworkIdle({idleTime: 8000});
      await page.keyboard.press("Escape");
      console.log("CCs Length", currentCoupons.length, " finished @", i)
    }
    await page.waitForNetworkIdle({idleTime: 3000});
    await browser.close();
    await wrapFile(fileName);
    console.log("file finished : ", fileName) ;
    insertRun(getKrogerCoupons, "runs", "node_call", dbArgs, true, _id,
    `Puppeteer Node.js Call for Scrape of ${getKrogerCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
    return null;
}

async function getInstacartItems(browser, page, _id){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param browser : the current browser instance. 
   * @prerequisite setUpBrowser() successful.
   * @todo : clicks on individual product cards gives way to item specific pages / modals that provide ItemDetailData (more info on specific item), =RelatedItems (Similar Products), =ComplementaryProductItems (Products Bought in Tandem), =ProductNutritionalInfo (More Nutritional Items)
   * & =RecipesByProductId (links to recipes page on instacart site, which provide all items for recipes and their prices)
        * given that this data is mostly static, It could be collected Incrementally Over Scrapes. It would have to occur over time given the large catalogue of items (1000+ items). 
   */
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getInstacartItems, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getInstacartItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)

  let unwantedPattern = /(outdoor|toys|bed|electronics|clothing-shoes-accessories|office-crafts-party-supplies|greeting-cards|storm-prep|tailgating|popular|floral|shop-now)$/
  let storePatterns = /(aldi|familydollar|publix)/
  let currentUrl = await page.url();
  let store = currentUrl.match(storePatterns)[0]
  let folder = store==="familydollar"? "instacartItems" : "items";
  let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  fileName = "../requests/server/collections/" + [store, folder, fileName].join("/") ;
  let offset = 0;
  var wantedResponseRegex =  /item_attributes|operationName=Items|operationName=CollectionProductsWithFeaturedProducts/;
  let allCategoryLinks = await page.$$eval("ul[aria-labelledby='sm-departments'] > li > a", (elems)=> elems.map((a)=>a.href)) // departments side panel
  allCategoryLinks = allCategoryLinks.filter((a)=>!a.match(unwantedPattern)).slice(1)
  let apiEmitter = new EventEmitter();

  async function setFlag(ee, waitTime = 4500, timeout = 45000){
    let times = 0;
    let previousTimes = 0;
    let pageEnded = 0;
    let intervalId; 
    ee.on("fileDone", ()=> {
      times++
    })
    intervalId = setInterval(()=> {
      if (times && previousTimes===times){
        console.log(`times = ${times} previousTimes = ${previousTimes}`)
        clearInterval(intervalId)
        ee.emit("resolve")
      } else if (!times && !previousTimes && pageEnded>=3) {
        // end of page has been reach
        clearInterval(intervalId);
        ee.emit("resolve")
      } else {
        console.log(`times = ${times} previousTimes = ${previousTimes}`)
        previousTimes = times
        pageEnded++ 
      }
    }, waitTime)
    return new Promise((resolve, reject)=> {
      ee.on("resolve", ()=> {
        resolve(true)
      })
      setTimeout(()=>{
        reject(new Error("Resolve Was Not Called in 45 Seconds")) 
      }, timeout)
    })
  }

  for (let link of allCategoryLinks){
    // navigate to page ;
    // wait for request where (collections_all_items_grid) in wanted request
    // once loaded responses have been copied, evalulate document.body.offsetHeight to see if more items are available. 
    var pageHeight, newHeight;
    // handle response
    page.on("response", async (res)=> {
      let url = res.url() ;
      if (url.match(wantedResponseRegex)){
        offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
        apiEmitter.emit("fileDone")
        return; 
      }
      return ; 
    })
    await page.goto(link);
    await setFlag(apiEmitter)    
    console.log("went to ", link)
    pageHeight = await page.$eval("body", (body)=> body.offsetHeight)
    await page.keyboard.press("End");
    await setFlag(apiEmitter)
    newHeight = await page.$eval("body", (body)=> body.offsetHeight)
    var lastStart = Date.now();
    while (pageHeight !== newHeight){
      console.log(pageHeight, " pageHeight")
      pageHeight = newHeight;
      await page.keyboard.press("End");
      await setFlag(apiEmitter)
      newHeight = await page.$eval("body", (el)=>el.offsetHeight)
      console.log(newHeight, " newHeight. Iteration Took ", (Date.now() - lastStart) / 1000, " secs");
      lastStart = Date.now()
    }
    console.log("finished ", link)
  }
  await page.waitForTimeout(10000)
  await browser.close();
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ; 
  insertRun(getInstacartItems, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getInstacartItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null;
}

async function getPublixCoupons(browser, page, _id){ 
  /**
   * @param browser : the currnet browser instance . 
   * @param page : the current page instance. 
   * @prerequiste : setUpBrowser() set location successfully. 
   */
  // set request interception on page
  //await page.setRequestInterception(true);
  // page.on('request', (req)=> {
  //   if (req.isInterceptResolutionHandled()) return;
  //   else req.continue()
  // })
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  let entryID = await insertRun(getPublixCoupons, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getPublixCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)

  var path = "../requests/server/collections/publix/coupons/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedResponseRegex = /services\.publix\.com\/api\/.*\/savings\?/

  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      let reqMethod = res.request().method();
      if (reqMethod!=="OPTIONS"){
        let start = Date.now()
        console.log("started async writeResponse @ ", start)
        offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
        console.log("writeResponse ended @ ", Date.now(), ' which took ', Date.now() - start, " seconds >.< ")
      }
      return; 
    }
    return ; 
  })
  await page.goto("https://www.publix.com/savings/all-deals");
  await page.waitForNetworkIdle({idleTime: 8000});
  await wrapFile(fileName);
  await browser.close();
  console.log("file finished : ", fileName) ;
  insertRun(getPublixCoupons, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getPublixCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null; 
}

async function getDollarGeneralCoupons(browser, page, _id){ 
  /**
   * @param browser: the passed browser instance from SetupBrowser()
   * @param page: the passed page instance from SetupBrowser()
  */
  // set request interception on page
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getDollarGeneralCoupons, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getDollarGeneralCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  
  var badRequests = [];
  var path = "../requests/server/collections/dollargeneral/promotions/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  var reqSet = new Set();
  const newPagePromise = new Promise(x => browser.once('targetcreated', target => x(target.page()))); 
  fileName = path+fileName ; 
  var wantedResponseRegex = /\/bin\/omni\/coupons\/(products|recommended)/
  await page.setRequestInterception(true);
  page.on("request", (req)=> {
    if (req.isInterceptResolutionHandled()) return ;
    else {
      reqSet.add(req.url())
      req.continue()
    };
  })
  await page.goto("https://www.dollargeneral.com/dgpickup/deals/coupons", {timeout: 240000})
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  page.on("requestfinished", (req)=> {
    reqSet.delete(req.url())
  })
  // page has reloaded to correct wanted location;
  // wait for iterations to be set 
  // then press button.button.coupons-results__load-more-button until all coupons are rendered to page;
  var loadMoreButton = await page.waitForSelector("button.button.coupons-results__load-more-button", {timeout: 6000});
  while (loadMoreButton!==null){
    await loadMoreButton.hover();
    await loadMoreButton.click(); 
    await page.waitForNetworkIdle({idleTime: 3000, timeout: 15000});
    loadMoreButton = await page.$("button[class='button coupons-results__load-more-button button--black']")
  }
  // start back at top of the page ; 
  await page.keyboard.press("Home");
  // now get all carousel nodes and begin 
  var items = await page.$$eval("li.coupons_results-list-item a.deal-card__image-wrapper", (elems)=>elems.map((e)=>{return e.getAttribute("href")}));
  let left = items.length
    for (let itemlink of items){
      try {
        console.log("https://www.dollargeneral.com"+itemlink)
        await page.goto("https://www.dollargeneral.com" + itemlink)
        await page.waitForNetworkIdle({
          idleTime: 8000,
        })
        // check for item modal to be present
        let eligibleItems = await page.$("section[class='couponPickupDetails__products-wrapper row']") ; 
        console.log(eligibleItems)
        if (eligibleItems){
          let loadMoreButton = await eligibleItems.$("button[class='button eligible-products-results__load-more-button']") ;
          console.log(loadMoreButton)
          while (loadMoreButton){
            await loadMoreButton.click();
            await page.waitForNetworkIdle({idleTime: 6500})
            loadMoreButton = await eligibleItems.$("button[class='button eligible-products-results__load-more-button']") ; 
            console.log(loadMoreButton)
          }
        };
        // exit out of page and return page to promotions tab ; 
        //await newTab.close();
      } catch (err){
        if (err instanceof TimeoutError){
          console.log("Timeout Error => ", err)
          badRequests.push(itemlink)
          console.log(reqSet)
        } else {
          console.log("New Error", err);
          badRequests.push(itemlink)
        }
      }
        left--;    
        console.log("finished promotion. ", left, " left.")
  };
    await page.waitForNetworkIdle({idleTime: 3000});
    await wrapFile(fileName);
    console.log("file finished : ", fileName) ;
    if (badRequests.length>0){
      console.log(`Writing ${badRequests.length} to file ./temp.json.`)
      let br = JSON.stringify(badRequests);
      await fs.promises.writeFile("./temp.json", br)
    }
  insertRun(getDollarGeneralCoupons, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getDollarGeneralCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null;
}

async function getDollarGeneralItems(browser, page, _id){
  /**
   * @prerequisite : setUpBrowser() successfully set location. 
   * @param browser : the current browser instance.
   * @param page : the current page instance.
   */
  // set request interception on page
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getDollarGeneralItems, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getDollarGeneralItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)

  var path = "../requests/server/collections/dollargeneral/items/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedResponseRegex = /https\:\/\/www\.dollargeneral\.com\/bin\/omni\/pickup\/categories\?/
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedResponseRegex)){
      offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  // go to sale page.
  await page.goto("https://www.dollargeneral.com/c/on-sale");
  await page.waitForNetworkIdle({idleTime: 3600})
  let button = await page.$("button[data-target='pagination-right-arrow']") ; 
  let disabled = await button.getProperty("disabled").then((jsHandle)=>jsHandle.jsonValue())
  console.log(button, disabled)
  while (!disabled){
    await Promise.all([
      button.click(),
      page.waitForTimeout(9000)
    ])
    await page.waitForTimeout(7000);
    button = await page.$("button[data-target='pagination-right-arrow']") ; 
    disabled = await button.getProperty("disabled").then((jsHandle)=>jsHandle.jsonValue())
    console.log(button, disabled)
  };
  await page.waitForTimeout(6000);
  await browser.close();
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ;
  insertRun(getDollarGeneralItems, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getDollarGeneralItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null
}

async function getFamilyDollarCoupons(browser, page, _id){
  /**
   * @prerequisite : setUpBrowser() worked. 
   * @param browser : the existing browser instance
   * @param page : the starting page ; 
   */
  // set request interception on page
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  let entryID = await insertRun(getFamilyDollarCoupons, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getFamilyDollarCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  
  var path = "../requests/server/collections/familydollar/coupons/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedRequestRegex = /ice-familydollar\.dpn\.inmar\.com\/v2\/offers\?/
  
  page.on("response", async (res)=> {
    let url = await res.url() ;
    if (url.match(wantedRequestRegex)){
      offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  await Promise.all([
    page.goto("https://www.familydollar.com/smart-coupons"),
    page.waitForNavigation({waitUntil: "load"}),
    page.waitForNetworkIdle({idleTime: 3000})
  ])
  //await browser.close();
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ;
  await insertRun(getFamilyDollarCoupons, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getFamilyDollarCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null; 
}

async function getFamilyDollarItems(browser, page, _id){
  /**
    * @param browser: the current browser instance .
    * @param page : PageElement from Successfully Launched Browser. 
    * @prequisite setUpBrowser() successful. Iterations Set to 96. 
    */
    // set request interception on page
    let dbArgs = {};
    ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
    insertRun(getFamilyDollarItems, "runs", "node_call", dbArgs, false, _id,
    `Puppeteer Node.js Call for Scrape of ${getFamilyDollarItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
    

    var offset = 0;
    var wantedRequestRegex = /dollartree-cors\.groupbycloud\.com\/api/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = "../requests/server/collections/familydollar/items/" + fileName; 
    page.on("response", async (res)=> {
      let url = await res.url() ;
      if (url.match(wantedRequestRegex)){
        offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
        return; 
      }
      return ; 
    })
    
    let selectDiv = await page.$$(".oc3-select > div > select");
    selectDiv = selectDiv[1]
    await selectDiv.hover()
    await selectDiv.click();
    await selectDiv.press("ArrowDown")
    await selectDiv.press("ArrowDown")
    await Promise.all([
      selectDiv.press("Enter"),
      // wait for reload
      page.waitForResponse(res=> res.url().includes("api/v1/search"), {timeout: 15000}), 
    ])
    await page.waitForNetworkIdle({idleTime: 2000})

    let iterations = await page.$eval("span.category-count", (el)=>{
      return +el.textContent.replaceAll(/(\(|\))/g, "")
    })
    iterations = Math.floor(iterations/96) + 1;
    // wait for page reload
    
    for (let i=1; i<iterations; i++){
      await Promise.all([
        page.$eval("a[aria-label='Next']", (el)=>el.click()),
        page.waitForNetworkIdle({idleTime: 6500})
      ])
      console.log("finished ", i , " ", iterations-i, " left ")
    }

    await page.waitForNetworkIdle({idleTime: 3000}); 
    await wrapFile(fileName);
    //await browser.close(); 
    console.log("finished file", fileName);
    insertRun(getFamilyDollarItems, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getFamilyDollarItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
    return null
}

async function getFoodDepotItems(browser, page, _id){
  /**
   * @param browser : the current browser instance
   * @param page : the current page instance
   * @prerequisites : setUpBrowser() succeeded
   * @todo : synchronous image loading & rendering is blocking network causing requests to complete and images to appear on page before next request is called, filled and rendered.
   * This occurs is 40 item batches so waiting for network to be silent takes much longer. Images to async fill / render is more images are loaded (aka a new API call is initiated by a End button press)
   * This network blocking effect effectively triples wait times for large pages (1000+ items). Meaning 37 40 item batch calls ~= 38 mins for 15+ categories.
   * See Setup Calls to See if API can just be intercepted and changed to write to file w.o. worrying about site
   * @note : request intercept handling is not necessary for requests where you do not intend to change requests data, querystring parameters or header values.
   * responses for these requests can be handled  
   */
  // set request interception on page
  //await page.setRequestInterception(true);
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getFoodDepotItems, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getFoodDepotItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)

  await page.setDefaultTimeout(0)
  var path = "../requests/server/collections/fooddepot/items/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  var wantedResponseRegex = /production-us-1\.noq-servers\.net\/api\/v.+\/stores\/.+\/products\?/
  fileName = path+fileName;
  var pageHeight, newHeight; 
  page.on("response", async (res)=> {
    let url = res.url() ;
    if (url.match(wantedResponseRegex)){
      let req= res.request();
      if (req.method()!=="OPTIONS"){ // filter out preflight request
        console.log(url, req, req.method(), )  
        offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset) 
      } else {
        console.log(req.method())
      }
      return;
    }
    return ; 
  })
  // on store home page.
  let shopNowButton = await page.$("#site-main-menu__button")
  await shopNowButton.hover();
  await shopNowButton.click(); 
  console.log("got main button")
  let shopAllButton = await page.waitForSelector("li.site-main-menu__item > a")
  await Promise.all([
    shopAllButton.click(),
    page.waitForNavigation({waitUntil: 'load'}),
    page.waitForNetworkIdle({idleTime:2000})
  ])
  // get all departments
  let allCategories = await page.$$eval("li.category-sibling-links__item > a", (els)=> els.map((el)=>{
    if (!el.href.endsWith("shop/all")){
      return el.href
    }
  }))
  allCategories=allCategories.filter((c)=>c)
  console.log(allCategories)
  for (let categoryUrl of allCategories){
    console.log('starting ', categoryUrl)
    // go to each category page
    await Promise.all([
      page.goto(categoryUrl),
      page.waitForNavigation({waitUntil: "load"})
    ])
    console.log("CATEGORY PAGE LOADED")
    let body = await page.$("body");
    pageHeight = await body.getProperty("offsetHeight").then((jsHandle)=> jsHandle.jsonValue())
    console.log(pageHeight)
    await page.keyboard.press("End");
    await page.waitForNetworkIdle({idleTime: 4000});
    newHeight = await body.getProperty("offsetHeight").then((jsHandle)=> jsHandle.jsonValue());
    console.log(newHeight)
    let u = 1; 
    while (pageHeight !== newHeight){
      pageHeight=newHeight;
      console.log(newHeight)
      await page.keyboard.press("End");
      await page.waitForNetworkIdle({idleTime: 5500}); // what is blocking syncrohous calls if end is not pressed again, images will stall and render one by one before next image resource is called
      u++;
      newHeight = await body.getProperty("offsetHeight").then((jsHandle)=> jsHandle.jsonValue());
      console.log(newHeight, u)
    }
    console.log('finished ', categoryUrl, ' @ index: ', allCategories.indexOf(categoryUrl), ' of ', allCategories.length-1)
  }
  await page.waitForNetworkIdle({idleTime: 3000}); 
  await wrapFile(fileName);
  await browser.close(); 
  console.log("finished file", fileName);
  insertRun(getFoodDepotItems, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getFoodDepotItems.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null
}

async function getFoodDepotCoupons(browser, page, _id){ 
  /**
   * @param browser : the current browser instance. 
   * @param page : the current page instance.
   * @requirements : setUpBrowser("foodDepotCoupons") was successful. 
   */
  // note : navigation to other stores promotions can only occur after MFA login 
  // page = await browser.pages()
  // page = page[0]
  let dbArgs = {};
  ["browser", "page"].map((kwarg, i)=>  dbArgs[kwarg] = arguments[i])
  insertRun(getFoodDepotCoupons, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getFoodDepotCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  var path = "../requests/server/collections/fooddepot/coupons/"
  var fileName = new Date().toLocaleDateString().replaceAll("/", "_") + ".json";
  var offset = 0;
  let wantedResponseRegex = /unclipped_recommendation_flag/
  fileName = path + fileName ;
  page.on("response", async (res)=> {
    let url = res.url();
    if (url.match(wantedResponseRegex)){
      offset+= await writeResponse(fileName=fileName, response=res, url=url, offset=offset);
    }
    return ;
  })
  await page.goto("https://www.fooddepot.com/coupons/")
  await page.waitForTimeout(23000)
  await wrapFile(fileName);
  await browser.close();
  console.log("finished file", fileName);
  insertRun(getFoodDepotCoupons, "runs", "node_call", dbArgs, true, _id,
  `Puppeteer Node.js Call for Scrape of ${getFoodDepotCoupons.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
  return null;
}

const getFoodDepotCode = async (_id) => {
  let dbArgs = {};
  insertRun(getFoodDepotCode, "runs", "node_call", dbArgs, false, _id,
  `Puppeteer Node.js Call for Scrape of ${getFoodDepotCode.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)

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
      passedValidateCode = logs.match(/code=(\d+)/)[1]
      console.log("code from phone", passedValidateCode);
      cmd.kill("SIGTERM")
    }
  })

return new Promise((resolve, reject) => {
  cmd.on("close", (code, signal)=>{
    console.log(`child process exited with a code of ${code} due to receipt of ${signal}`)
    insertRun(getFoodDepotCode, "runs", "node_call", dbArgs, true, _id,
    `Puppeteer Node.js Call for Scrape of ${getFoodDepotCode.name.replace("get", "")} for ${new Date().toLocaleDateString()}`)
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


async function insertRun(functionObject, collectionName, executionType, funcArgs, close=false, _id=undefined, description=null){
  /**
   * @param 
   */
  const client = new MongoClient(process.env.MONGO_CONN_URL);
  const dbName = 'new';
  var document, result; 
  await client.connect();
  console.log("Connected to Server")
  const db = client.db(dbName);
  const collection = db.collection(collectionName);
  // wrap functions metadata, determine type, get min started at, get total duration 
  if (close){
    if (!_id) throw new Error("_id must be present for update operations"); // updates top-level run time metrics and closes function
    // @ every close function time must be incremented, duration must be incremented
    // subtract time to log function execution time
    // increment duration by this difference
    let filter = {"_id": _id} 
    let update = {
      "$set": {
        "duration": { 
          "$divide": [{"$subtract": ["$$NOW", "$startedAt"]}, 1000]
        },
        "endedAt": "$$NOW"
      }}
    await collection.updateOne(filter, [update]);
    let updateElementPipeline = {
        $set:  {
          "functions": {
              $map: {
                input: "$functions",
                in:{
                  $cond: {
                    if: {$eq: ["$$this.function", functionObject.name]},
                    then: {$mergeObjects: ["$$this", {"endedAt": "$$NOW", "duration": {"$divide" : [{$subtract: ["$$NOW", "$$this.startedAt"]}, 1000]}}]},
                    else: "$$this"}
                  } 
              }
          }}
      }
      await collection.updateOne(filter, [updateElementPipeline]);
      console.log("updated 1 document into ", collectionName)
      result = _id
    } else if (_id) { // pushes next embedded function document into functions array of Run Document
    let filter = {"_id": _id} 
    let timestamp = new Date()
    result = _id
    let update = {
      "$set": {
        "duration": { 
          "$divide": [{"$subtract": [timestamp, "$startedAt"]}, 1000]
        },
        "endedAt": timestamp,
      }
    };
    await collection.updateOne(filter, [update]);
    update = {"$push": {"functions": {
      function: functionObject.name,
      description: description,
      vars: funcArgs,
      duration: 0,
      startedAt: timestamp
    }}};
    await collection.updateOne(filter, update);
    console.log("updated 1")
  }else { // creates original run document 
    let startedAt = new Date(); 
    document = {
      executeVia: executionType,
      startedAt: startedAt,
      duration: 0,
      functions: [
        {
          function: functionObject.name,
          description: description,
          vars: funcArgs,
          duration: 0,
          startedAt: startedAt
        }
      ]
    }
    result = (await collection.insertOne(document)).insertedId
    console.log("inserted 1 document into ", collectionName)
    // returns inserted run document for update operations once function has successfully completed
  }
  await client.close()
  return result
}
// puppeteer.launch({
//   headless: false,
//   slowMo: 0, 
//   executablePath:
//     "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
//   dumpio: true,
//   args: ["--start-maximized","--profile-directory=Profile 1"],
//   userDataDir: "C:\\c\\Profiles",
//   defaultViewport: {width: 1920, height: 1080},
//   devtools: false,
//   timeout: 0
// }).then((browser)=> {
//   browser.pages().then((pages)=>{
//     let page = pages[0]
//     page.goto("chrome://settings")
  
//   })
// })

setUpBrowser(task="").then(async ([browser, page, entryID])=> {
  await getFoodDepotCoupons(browser, page, entryID)
})