// hi
// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
require("dotenv").config();
const fs = require("fs")
const { platform } = require("os")
const EventEmitter = require('node:events');
const http = require("node:http")
const { Command } = require('commander')
const {setTimeout} = require("timers/promises")
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const { ProtocolError, TimeoutError } = require('puppeteer');

puppeteer.use(StealthPlugin())

const BROWSER_OPTIONS = platform() === "linux" ? {
  headless: false,
  slowMo: 900, 
  executablePath:"google-chrome-stable",
  dumpio: false,
  args: ["--start-maximized", "--no-sandbox"],
  defaultViewport: {width: 1920, height: 1080},
  devtools: false,
  timeout: 0
} : {
  headless: false,
  slowMo: 900,
  executablePath: "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  dumpio: true,
  devtools: false,   
  args: ["--start-maximized", "--profile-directory=Profile 1", "--new-window", "--disable-features=site-per-process"],
  userDataDir : "C:\\c\\Profiles",
  timeout: 0,
  defaultViewport: {
    width: 1920,
    height: 1080
  }
} ;



const getNestedObject = (nestedObj, pathArr) => {
  return pathArr.reduce(
    (obj, key) => (obj && obj[key] !== "undefined" ? obj[key] : undefined),
    nestedObj
  );
};

async function writeResponse(fileName, response, url, offset) { 
  // check file existence to set character. 
  let fileExists = fs.existsSync(fileName);
  //fileName.endsWith("/") ? undefined : fileName+="/" 
  if (!fileExists){
    fs.mkdirSync(fileName.slice(0, fileName.lastIndexOf("/")), {recursive: true})
    fs.appendFile(fileName, "[", (err)=>{
      if (err) throw err; 
    })
  }
  try {
    // make sure response is a proper JSON before any write happens
    if (!response.ok()) throw new Error(`did not write b/c response code was : ${response.status()}`)
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


async function setUpBrowser(task) {
  /**
   * @for starting browser task, loading extension and handling location based services on websites on new browser instance
   * @note : request interception should occur only once page has setup been completed to prevent wrong location data.
   * @param  task : a camelCase string that is franchise + {wantedScrapedPageCategory} 
   */

  async function checkForErrorModal(){
    let errorVisible  = await page.$eval("#global-message-modal", (el)=>el.getAttribute("aria-hidden"));
    errorVisible = errorVisible === 'false'? !!errorVisible : !errorVisible; 
    if (errorVisible){
      // force refresh to allow access if alert modal appears when accessing drop down
      await page.$eval("#global-message-modal button.global-modal__close-button", (el)=>el.click())
      await page.waitForTimeout(8000)
      await page.reload();
      // set internal wait;
      await page.waitForTimeout(8000)
      return true;
    }
    return false;
  }
  var ZIPCODE = process.env.ZIPCODE; 
  const PHONE_NUMBER = process.env.PHONE_NUMBER;
  var browser, page, passDownArgs = {};
  try { 
    BROWSER_OPTIONS.headless = task === "foodDepotPromotions";
    browser = await puppeteer.launch(BROWSER_OPTIONS);
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
      case "krogerSpecial":
      case "krogerPromotions": {
          /** kroger coupons: exit out of promotional modals (usually 1||2), click change store button, click find store, remove default zipcode in input, write wanted zipcode to input, press enter, select wanted modalitiy button (In-Store),
           * wait for page reload, select dropdown for filtering coupons, press arrow down and enter, wait for page reload
          */ 
          let availableModalities = ["PICKUP", "DELIVERY", "SHIP", "IN_STORE"];
          var wantedModality = "PICKUP";
          var wantedAddress = "3559 Chamblee Tucker Rd"; // "4357 Lawrenceville Hwy"
          await page.goto("https://www.kroger.com")
          await page.waitForTimeout(5500)
          let introModals = await page.$$("button.kds-DismissalButton.kds-Modal-closeButton")
          if (introModals){
            for (let modal of introModals){
              await modal.click(); 
            }
          }
          await page.$eval("button.CurrentModality-button", (el)=>el.click());
          zipInput = await page.$("input[autocomplete='postal-code']");
          placeHolder = await zipInput.getProperty("value").then((v)=> v.jsonValue());
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
          // page.waitForNetworkIdle({idleTime: 4500})
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
          await page.waitForTimeout(10000)
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
          let locationIdRegex = /GetRetailerLocationAddress&variables=%7B%22id%22%3A%22(.+?)%22%7D/
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
          // click pickup button && wait for refresh
          await Promise.all([
            page.waitForNetworkIdle({idleTime:2000}),
            modalityButton.click()
          ]);
          // click on pickup location picker (store picker)
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
            await page.waitForNetworkIdle({idleTime: 4000})
            await page.keyboard.press("Enter");
            page.on("response", async (response)=> {
              if (Object.keys(passDownArgs).length<1 && response.url().match(locationIdRegex)){
                passDownArgs["locationId"] = response.url().match(locationIdRegex)[1];
              }
            })
            
          }
          await page.waitForNetworkIdle({idleTime: 15500})
          break;
      }
      case "publixItems": {
        /**
         * @tests passed
         */
        var ZIPSTREET = "Old Norcross Tucker Rd" ; // street that corresponds to zipcode
        var availableModalities = ["Pickup", "Delivery"];
        var wantedStoreAddress = "4650 Hugh Howell Rd";
        let locationIdRegex = /GetRetailerLocationAddress&variables=%7B%22id%22%3A%22(.+?)%22%7D/
        var instacartLocationId; 
        var wantedModality = availableModalities[0]; // @param?
        await page.goto("https://delivery.publix.com/store/publix/storefront")
        await page.waitForTimeout(14000)
        // click pickup modal // defaults to delivery
        var modalityButtons =await page.$$("div[aria-label='service type'] > button");
        var modalityButton = await asyncFilter(modalityButtons, async (storeItem, index)=> {
          let address = await storeItem.getProperty("innerText").then((jsHandle)=> jsHandle.jsonValue());
          if (address.includes(wantedModality)){ 
            return index
          } 
        });
        // click pickup button && wait for refresh
        await Promise.all([
          page.waitForTimeout(13000),
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
            } else if (!wantedStoreAddress && index<=0){
              return index // return first entry if wantedAddress not set, i.e. closest store to given address
            }
          });
          await targetStoreModal.click();
          // allow time for mapbox requests to complete & so mapbox comes into focus
          await page.waitForTimeout(10000)
            await page.keyboard.press("Enter");
            page.on("response", async (response)=> {
              if (Object.keys(passDownArgs).length<1 && response.url().match(locationIdRegex)){
                passDownArgs["locationId"] = response.url().match(locationIdRegex)[1];
              }
            })
            
          }
          await page.waitForTimeout(15500)
        break;
      }  
      case "publixPromotions": {
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
      await page.waitForTimeout(12000)
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
      case "foodDepotPromotions":{
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
        let frameCoupons = await appCardIFrame.contentFrame();
        if (appCardIFrame){
          let phoneInput = await frameCoupons.$("#phone");
          if (!phoneInput){
            console.log("already logged in")
            break;
          }
          console.log(PHONE_NUMBER)
          for (i=0; i<PHONE_NUMBER.length; i++){
            await phoneInput.type(PHONE_NUMBER[i], {delay: 100})

          }
          
          console.log("wrote phone number")
          await frameCoupons.$eval("button.button-login.default", async (el)=>{
            el.click();
          })
          console.log("clicked login button")
          var parsedVerificationCode = await getFoodDepotCode(); 
          let codeInput = await frameCoupons.waitForSelector("code-input")
          await codeInput.type(parsedVerificationCode, {delay: 200})
          // will send code typeFinish on completed 
          await page.waitForTimeout(12000)
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
          await frameCoupons.waitForTimeout(13000)
        }
        break;
      }
      case "dollarGeneralItems":{
        // * dollar general coupons:
        var wantedStoreAddress = "4312 Chamblee Tucker Road";
        var wasError, step = 0, tries = 0;
        // provide break points for evaluating existance of error modal at different steps of the setup procedure. If ever error, restart process with known workaround.        
        // navigate to homepage : 
        await page.goto("https://www.dollargeneral.com/deals/weekly-ads")
        await page.waitForTimeout(12000)
        do {
          if (step===0){
            tries++;
            if (tries>4){
              throw new Error(`Error Modal Continutes on All Setup Pages after ${tries} tries.`)
            }
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
            await page.waitForTimeout(5000)
            let wantedStoreDivs = await page.$$("li.store-list-item");
            var wantedStoreDiv = await asyncFilter(wantedStoreDivs, async (storeItem, index)=> {
            address = await storeItem.getProperty("innerText").then(async (jsHandle)=> await jsHandle.jsonValue());
            if (address.includes(wantedStoreAddress)){ 
                return index
              } 
            });
            // "span.store-list-item__store-address-1"
            let setStoreButton = await wantedStoreDiv.$("button[data-selectable-store-text='Set as my store']")
            // wait for reload,
            await Promise.all([setStoreButton.click(), page.waitForTimeout(8800)])
            break;
          }
          wasError = await checkForErrorModal(); 
          step = wasError ? 0 : step+1;
        } while (step<2);
        break;
        }
      case "dollarGeneralPromotions": {
        // * dollar general coupons:
        var wantedStoreAddress = "4312 Chamblee Tucker Road";
        var wasError, step = 0, tries = 0;
        // provide break points for evaluating existance of error modal at different steps of the setup procedure. If ever error, restart process with known workaround.        
        // navigate to homepage : 
        await page.goto("https://www.dollargeneral.com/deals/weekly-ads")
        await page.waitForTimeout(12000)
        do {
          if (step===0){
            tries++;
            if (tries>4){
              throw new Error(`Error Modal Continutes on All Setup Pages after ${tries} tries.`)
            }
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
            await page.waitForTimeout(5000)
            let wantedStoreDivs = await page.$$("li.store-list-item");
            var wantedStoreDiv = await asyncFilter(wantedStoreDivs, async (storeItem, index)=> {
            address = await storeItem.getProperty("innerText").then(async (jsHandle)=> await jsHandle.jsonValue());
            if (address.includes(wantedStoreAddress)){ 
                return index
              } 
            });
            // "span.store-list-item__store-address-1"
            let setStoreButton = await wantedStoreDiv.$("button[data-selectable-store-text='Set as my store']")
            // wait for reload,
            await Promise.all([setStoreButton.click(), page.waitForTimeout(8800)])
            break;
          }
          wasError = await checkForErrorModal(); 
          step = wasError ? 0 : step+1;
        } while (step<2);
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
        await page.waitForTimeout(11000) 
        // click your store link in nav bar,
        page.$eval("a[text='FIND A STORE']", (el)=> el.click())
        // redirects to /store-locator
        await page.waitForTimeout(9000)
        // enter zip code into input,
        var locatorIFrame = await page.waitForSelector("#storeLocator");
        console.log("got #storeLocator")
        frameZip = await locatorIFrame.contentFrame();
        var inputZip = await frameZip.$("input") 
        await inputZip.type(ZIPCODE);
        await inputZip.press("Enter");
        console.log("waiting for network idle 4")
        await page.waitForTimeout(6000)
        var targetStoreModals = await frameZip.$$("li.poi-item")
        // select store by address,
        var targetStoreModal = await asyncFilter(targetStoreModals, async (poiItem, index)=> {
          let address = await poiItem.$eval("div > div.address-wrapper", (el)=>el.outerText)
          if (address === wantedStore){ 
            return index
          } 
        })
        console.log("waiting for navigation")
        await Promise.all([
          targetStoreModal.$eval("div > div.mystoreIcon > span > a", (el)=>el.click()),
          page.waitForTimeout(15000)
        ]);
        let locationChangedModal = await page.$("div.modal.occ-notifications-modal.in a.modal-close");
        if (locationChangedModal){
          await locationChangedModal.click();
        }
        await page.goto("https://www.familydollar.com/categories")
        await page.waitForTimeout(8000)
        break;
      }
      case "familyDollarInstacartItems": {
        // * family dollar instacart items: differs from other instacart sites as it is delivery only 
        var ZIPSTREET = "Old Norcross Tucker Rd" ;
        var instacartRegex = /=ShopCollection/
        var instacartIds = {}; 
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
          if (address.includes(ZIPCODE)){ 
            return index
          } 
        });
        await targetLocation.click(); 
        //click save address button
        var addressSubmit = await page.waitForSelector("div[class$='UserAddressManager'] button[type='submit']");
        page.on("response", async (res)=> {
          if (Object.keys(passDownArgs).length<1 && res.url().match(instacartRegex)){
            let shopIdObject = await res.json()
            shopIdObject = shopIdObject.data.shopCollection;
            passDownArgs["instacartShopId"] = shopIdObject.id
            passDownArgs["locationId"] = shopIdObject.shops["0"].id
            passDownArgs["retailerId"] = shopIdObject.shops["0"].retailer.id
            passDownArgs["retailerLocationId"] = shopIdObject.shops["0"].retailerLocationId
          }
        })

        // click and wait for reload
        await addressSubmit.click()
        await page.waitForTimeout(15500)
        break;
      }
      case "familyDollarPromotions": {
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
      await page.waitForTimeout(12000)
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
        if (address === wantedStore){ 
          return index
        } 
      })
      await Promise.all([
        targetStoreModal.$eval("div > div.mystoreIcon > span > a", (el)=>el.click()),
        page.waitForTimeout(15000)
      ]);
      let locataionChangedModal = await page.waitForSelector("div.modal.occ-notifications-modal.in a.modal-close")
      await Promise.all([
        locataionChangedModal.click(),
        page.waitForTimeout(7000)
      ])
      break;
      }
      case "": {        
        break;
      }
      
  }
  console.log("Success!") 
} catch (e) {
    console.log(e.stack)
    console.log(e)
    throw new Error("startup error ")
  }
  // will pass down location ids where applicable and browser, page and run ObjectId  
  passDownArgs.browser = browser
  passDownArgs.page = page
  await page.removeAllListeners('response')
  return passDownArgs;
}

async function getKrogerTrips({ page }){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * 
   * @prerequisite : login was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */
  var path = "/app/tmp/collections/kroger/trips/"
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
  await page.waitForTimeout(8000)
  let introModals = await page.$$("button.kds-DismissalButton.kds-Modal-closeButton")
  if (introModals){
    for (let modal of introModals){
      await modal.click(); 
    }
  }
  await page.waitForTimeout(6000);

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
  let iterations = 1;
  let start = null;
  while( element ){
    start = Date.now()
    // click to next page
    await element.click();
    // await product card render, images of items purchased to be rendered 
    await page.waitForTimeout(14000)
    await page.waitForSelector("div[aria-label='Purchase History Order']");
    element = await nextButton();
    iterations++
    console.log(element, iterations, ' ', (Date.now()-start)/1000, ' seconds')
  }
  await page.waitForTimeout(9000);
  await wrapFile(fileName);
  console.log("file finished : ", fileName);
  console.log("exiting....")
  await page.removeAllListeners('response')
  return null;
}

async function getKrogerPromotions({ page, type}){
    /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @param type : Kroger Promotional Type. Either `cashback` or `digital`
   * @prerequisite : location setup was successful, setUpBrowser was successful 
   * @steps : 
   * 1 - can get iterations via DOM pagination elements now. Get Them
   * 2 - Await Load of User Trips... Carousel Cards are Rendered and Requests are Complete.
   * 3 - Press Arrow. Repeat Until Arrow is Unavailable via CSS class  
  */ 
    if (!['cashback', 'digital'].includes(type)){
      throw new Error(`Type is not right . Avaialable Values: 'cashback' or 'digital' `)
    }
    // set url based on type 
    var promotionUrl = type === "digital" ? "https://www.kroger.com/savings/cl/coupons" : "https://www.kroger.com/savings/cbk/cashback" ;  
    var apiEmitter = new EventEmitter(); 
    var offset = 0;
    var wantedRequestRegex = /atlas\/v1\/product\/v2\/products\?|\/cl\/api\/coupons/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = `/app/tmp/collections/kroger/promotions/${type}/` + fileName; 
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
    
    await page.waitForTimeout(5500)
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
    await setTimeout(7500)// await page.waitForTimeout(5500)
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
      await page.waitForTimeout(8000);
      await page.keyboard.press("Escape");
      console.log("CCs Length", currentCoupons.length, " finished @", i)
    }
    await page.waitForTimeout(3500);
    await wrapFile(fileName);
    console.log("file finished : ", fileName) ;
    await page.removeAllListeners('response')
    return null;
}


async function getKrogerSpecialPromotions({ page }) { 
  /**
   * @setup = getKrogerPromotions.
   * For special promotions that are advertised on website's promotions page, but do not require any loading of promotion to get.
   * Usually revolves around a Special Number of Products and a Required Purchasing Amount. Can power Savings when combined with other available promotions.
   * Product information revolves around two different promotions calls, details-basic and traditional products? seen in Trips and reg Promotions scraping functions.
   * the products.$.price.offerCode feature in /products? will have the internal promotional id for special promotion that can be connected overall to
   * other promotions usually by adding 8000000 + linkedOfferCode to it.
   * Other data on promotion (defaultDescription, nfor (min quantity), nforPrice, expiration date) will be found on products.$.price.storePrices.promo
   * @nb : do not rely exclusively on linkedOfferCode to be the same for all promotions housed on the same promotion page. Similarish type of offers can end up on same page
   * even though their linkedOfferCode's do not match.       
  */
  // capture details-basic and products? api repsonses
  let specialPromoRegex = /(atlas\/v.\/product\/v.\/products\?|products\/details-basic)/
  var path = "/app/tmp/collections/kroger/promotions/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, '_')+".json";
  var offset = 0;
  var specialPromoLinks = [];    
  // navigate to shop-all-promotions and find all special type promotions pages
  await page.goto("https://www.kroger.com/pr/shop-all-promotions")
  await page.waitForTimeout(9000)
  // will give you section divs with tabulated options (for special promotions and regular digital promotions)
  var specialPromoTabDivs = await page.$$("div[class$='.tabs']")
  var specialPromoTabDivs = await asyncFilter(specialPromoTabDivs, async (storeItem, index)=> {
    let modalHeaders = await storeItem.$$eval("h2", (els)=>els.map((el)=>el.innerText))
    console.log(modalHeaders)
    let doesNotContainCoupons = modalHeaders.every((head)=>!head.toLowerCase().includes("coupon"))
    if (doesNotContainCoupons){ 
      return index
    } 
  })
  console.log(specialPromoTabDivs)
  specialPromoTabDivs = [specialPromoTabDivs]
  // handle individual links in tab marked divs; to get other special promotions behind tabs the tabs inside the elements must be clicked to change
  for (let specialPromoTabDiv of specialPromoTabDivs){
    let initialSpecialPromoValue = await specialPromoTabDiv.$eval("a.kds-ProminentLink", (a)=>a.href)
    console.log("special initialSpecialPromoValue = ", initialSpecialPromoValue)
    specialPromoLinks.push(initialSpecialPromoValue);
    let remainingTabs = await specialPromoTabDiv.$$("button[id^='Tabs-tab'][aria-selected='false']")
    console.log("remainingTabs" , remainingTabs)
    for (let remainingTab of remainingTabs){
      tabText = await remainingTab.getProperty("innerText")
      console.log(await tabText.jsonValue())
      console.log("clicking chips")
      await remainingTab.click();
      await remainingTab.click();
      await page.waitForTimeout(7000);
      initialSpecialPromoValue = await specialPromoTabDiv.$eval("a.kds-ProminentLink", (a)=>a.href)
      specialPromoLinks.push(initialSpecialPromoValue)
    }
  }
  console.log("specialPromoLinks = ", specialPromoLinks)
  // will give sections of all special promotions (w/o tabs)
  // var specialPromoSectionLinks = await page.$$eval("div[class$='.sectionwrapper'] a.kds-ProminentLink", (nodes)=>nodes.map((n)=>n.href))
  var specialPromoBubbleLinks = await page.$$eval("div[class$='.imagenav'] a[title][tabindex]", (nodes)=>nodes.map((n)=>n.href))
  specialPromoLinks = specialPromoLinks.concat(specialPromoBubbleLinks)//.concat(specialPromoSectionLinks);
  
  console.log("specialPromoLinks = w/ bubbles =>", specialPromoLinks)
  let bubbleSpecials = specialPromoLinks.filter((href)=>href.match(/pr\/(?!weekly-digital-deals|5x-digital-coupon-event|pickup-delivery-savings-4|boost)/))
  var specialPromoNonBubbleLinks = await page.$$eval("a.kds-Link.kds-ProminentLink", (nodes)=>nodes.map((el)=>el.href))
  console.log(specialPromoNonBubbleLinks)
  specialPromoLinks = specialPromoLinks.concat(specialPromoNonBubbleLinks.filter((link)=>link.match(/search\?/)))
  specialPromoLinks = Array.from(new Set(specialPromoLinks.filter((a)=>a.match(/\/search\?/))))
  // remove link that redirects to standard digital coupon page and adds special promotions
  specialPromoNonBubbleLinks = specialPromoNonBubbleLinks.filter((href)=>href.match(/pr\/(?!weekly-digital-deals|5x-digital-coupon-event|pickup-delivery-savings-4|boost)/))
  specialPromoNonBubbleLinks = specialPromoNonBubbleLinks.concat(bubbleSpecials)
  // iff specialPromoNonBubbleLinks is not empty, it will only send you to that specific promotions page similar to all promotions page
  // where specfic promotion is segmented by item categories. Goal is to process special promotions once we have links for all available special promotions
  // that redirect us to items search page. specialPromoNonBubble links require a few extra steps.
  console.log("specialPromoLinks >>", specialPromoLinks)
  console.log("specialPromoNonBubbleLinks {links that need navigation to own promotions page} >>", specialPromoNonBubbleLinks)
  var reachedSearchPage = false;
  let shopAllLinkArray = [];
  if (specialPromoNonBubbleLinks.length > 0){
    for (let specialLink of specialPromoNonBubbleLinks){
      console.log("specialLink = w/o bubbles", specialLink)
      await page.goto(specialLink);
      await page.waitForTimeout(8500);
      var categoryLinks = await page.$$eval("a.kds-Link.kds-ProminentLink", (nodes)=>nodes.map((el)=>el.href))
      var [shopAllLink] = categoryLinks.filter((a)=>a.includes("ShopAll"));
      // var categoryButtons = await page.$$("a.kds-Link.kds-ProminentLink");
      console.log("shopAllLink = w/o bubbles", shopAllLink)
      shopAllLinkArray.push(shopAllLink);
    }
  }
  page.on("response", async (response)=> {
    if (reachedSearchPage && response.url().match(specialPromoRegex)){
      console.log("captured URL : ", response.url())
      let tempId = page.url().match(/keyword=(.+?)\&/)[1]
      let linkFileName = path+tempId+"/"+fileName 
      offset += await writeResponse(linkFileName, response, url=response.url(), offset)
    }
    return;
  }) 
  if (specialPromoNonBubbleLinks.length>0){
    // go to page find and find search link that comprises the broadest category (should have ShopAll in it and no reference to a specific category.)
    for (let specialLink of shopAllLinkArray){
      console.log("navigating to ", specialLink)
      await page.goto(specialLink)
      reachedSearchPage =  true;
      await page.waitForTimeout(17500);
      // get all categories in departments dropdown then proceed with waiting for and getting load more button
      let departmentFilter = await page.$("span[aria-label='Open the Departments filter']")
      if (departmentFilter===null){
        await page.goto(shopAllLink);
        // get all categories in departments dropdown then proceed with waiting for and getting load more button
        await page.waitForTimeout(15000);
        departmentFilter = await page.$("span[aria-label='Open the Departments filter']")
      }
      await departmentFilter.click(); // will change upon click
      await page.waitForTimeout(8800)
      // get show all categories button
      let loadAllCategoriesButton = await page.$("button[data-test='sliced-filters-show-more-button']");
      await loadAllCategoriesButton.click();
      await page.waitForSelector("button.x-filter.x-sliced-filters__button.x-sliced-filters__button--show-less")
      let categoryFilters = await page.$$("ul.x-staggering-transition-group.x-staggered-fade-and-slide.x-list.x-filters > li > div > div > label > input")
      console.log("categoryFilters = w/o bubbles", categoryFilters)
      for (let j = 0 ; j <categoryFilters.length ; j++){
        categoryFilters = await page.$$("ul.x-staggering-transition-group.x-staggered-fade-and-slide.x-list.x-filters > li > div > div > label > input")
        console.log("categoryFilters ==> ", categoryFilters)

        if (categoryFilters.length<1){
          await page.waitForTimeout(12500)
          departmentFilter = await page.$("span[aria-label='Open the Departments filter']")
          if (departmentFilter === null){
            console.log(departmentFilter, "<<<=== departmentFilter")
            continue;
          }
          await departmentFilter.click(); // will change upon click
          // get show all categories button
          await page.waitForTimeout(5000)
          loadAllCategoriesButton = await page.waitForSelector("button[data-test='sliced-filters-show-more-button']");
          await loadAllCategoriesButton.click();
          await page.waitForTimeout(5000)
          await page.waitForSelector("button.x-filter.x-sliced-filters__button.x-sliced-filters__button--show-less")
          categoryFilters = await page.$$("ul.x-staggering-transition-group.x-staggered-fade-and-slide.x-list.x-filters > li > div > div > label > input")
          await page.waitForTimeout(5500)
        }
        catFilter = categoryFilters[j]
        await catFilter.click();
        await page.waitForTimeout(12500)
        // check for load button
        var loadMoreButton = await page.$('div.PaginateItems button.LoadMore__load-more-button')
        console.log('starting load loop for :', page.url())
        while (loadMoreButton){
          await loadMoreButton.click();
          try{
            let loadMoreResponse = await page.waitForResponse(async (response)=> response.url().match(specialPromoRegex)!==null, {timeout: 20000})
            if (loadMoreResponse.ok()){
              console.log(loadMoreResponse.url(), loadMoreResponse.ok())
              await page.waitForTimeout(6000)
            }
          } catch (err){
            continue; 
          } 
          await page.waitForTimeout(12000)
          loadMoreButton = await page.$('div.PaginateItems button.LoadMore__load-more-button')

          
        };
        console.log("finished category : ", page.url().match(/pl\/(.+?)\//))

      };
      let dirName = page.url().match(/keyword=(.+?)\&/)[1]
      let linkFileName = path+dirName+"/"+fileName 
      await wrapFile(linkFileName)
      console.log("finished ", linkFileName)
      await page.waitForTimeout(8800); // prevent straggling api calls to be recorded. 
    }    
  } else {
    reachedSearchPage = true
  }


  /**
   * @example : [
   * https://www.kroger.com/search?keyword=(((2022P10W1BewitchingBeautyB2G1Free)))&query=2022P10W1BewitchingBeautyB2G1Free&searchType=mktg%20attribute&monet=curated&fulfillment=all&pzn=relevance
   * https://www.kroger.com/search?keyword=(((ATLMustBuySoda3)))&query=ATLMustBuySoda3&searchType=mktg%20attribute&monet=promo&fulfillment=all&pzn=relevance
   * https://www.kroger.com/search?keyword=(((Buy5Save1EachShopAll22102)))&query=Buy5Save1EachShopAll22102&searchType=mktg%20attribute&monet=promo&fulfillment=all&pzn=relevance
   * (nonbubble link) : https://www.kroger.com/search?fulfillment=all&keyword=(((Buy6Save3ShopAll22104)))&monet=promo&page=11&pzn=relevance&query=Buy6Save3ShopAll22104&searchType=mktg%20attribute
  * (nonbubble link show full category) : https://www.kroger.com/pl/dairy-eggs/02?keyword=Buy6Save3ShopAll22104&monet=promo&pzn=relevance&query=Buy6Save3ShopAll22104&searchType=mktg%20attribute&taxonomyId=02&fulfillment=all
  * (ibid): https://www.kroger.com/pl/cleaning-and-household/26?keyword=Buy6Save3ShopAll22104&monet=promo&pzn=relevance&query=Buy6Save3ShopAll22104&searchType=mktg%20attribute&taxonomyId=26&fulfillment=all
  */
  console.log("getting remaining special promo links ...> ", specialPromoLinks)
  var MAX_RETRYS = 0 ; 
  for (let i = 0 ; i < specialPromoLinks.length ; i++ ){
    let link = specialPromoLinks[i]
    let dirName = link.match(/keyword=(.+?)\&/)[1]
    let linkFileName = path+dirName+"/"+fileName 
    await page.goto(link);
    await page.waitForTimeout(13500);
    try {
      // test to see if file exists
      if (!fs.existsSync(linkFileName)){
        await page.goto(link)
        await page.waitForTimeout(17500)
      }

      // find see more button (will not appear there are no more items)
      var loadMoreButton = await page.$('div.PaginateItems button.LoadMore__load-more-button')
      let loadPage = 0
      while (loadMoreButton){
        await loadMoreButton.click();
        await page.waitForResponse(async (response)=> response.url().match(specialPromoRegex)!==null, {timeout: 20000})
        await page.waitForTimeout(6500)
        loadMoreButton = await page.$('div.PaginateItems button.LoadMore__load-more-button')
        console.log(`for ${page.url()} @ load iteration ${loadPage}`)
        loadPage++;
      };
      await page.waitForTimeout(20000)
      await wrapFile(linkFileName)
      console.log("finished ", linkFileName)
      console.log("finished link : ", link)
      MAX_RETRYS=0 ; 
    } catch (err){
      console.log(err);
      console.log("restarting iteration for ", link)
      i--;
      if (MAX_RETRYS > 3) {
        i++;
      } else {
        MAX_RETRYS++; 
      }
    }
    await page.waitForTimeout(9000)
  }
  page.removeAllListeners("response")
  await page.waitForTimeout(23000)
  return null
}


async function getInstacartItems({ page}){
  /**
   * @param page : PageElement from Successfully Launched Browser. 
   * @prerequisite setUpBrowser() successful.
   * @todo : clicks on individual product cards gives way to item specific pages / modals that provide ItemDetailData (more info on specific item), =RelatedItems (Similar Products), =ComplementaryProductItems (Products Bought in Tandem), =ProductNutritionalInfo (More Nutritional Items)
   * & =RecipesByProductId (links to recipes page on instacart site, which provide all items for recipes and their prices)
        * given that this data is mostly static, It could be collected Incrementally Over Scrapes. It would have to occur over time given the large catalogue of items (1000+ items). 
   */
  let unwantedPattern = /(outdoor|toys|bed|electronics|clothing-shoes-accessories|office-crafts-party-supplies|greeting-cards|storm-prep|tailgating|popular|floral|shop-now)$/
  let storePatterns = /(aldi|familydollar|publix)/
  let currentUrl = await page.url();
  let store = currentUrl.match(storePatterns)[0]
  let folder = store==="familydollar"? "instacartItems" : "items";
  let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  fileName = "/app/tmp/collections/" + [store, folder, fileName].join("/") ;
  let offset = 0;
  var wantedResponseRegex =  /item_attributes|operationName=Items|operationName=CollectionProductsWithFeaturedProducts/;
  let allCategoryLinks = await page.$$eval("ul[aria-labelledby='sm-departments'] > li > a", (elems)=> elems.map((a)=>a.href)) // departments side panel
  allCategoryLinks = allCategoryLinks.filter((a)=>!a.match(unwantedPattern))
  console.log(allCategoryLinks)
  let apiEmitter = new EventEmitter();
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

  async function setFlag(ee, waitTime = 4500, timeout = 45000){
    // helper function to make sure files are completed before next page action 
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
        ee.removeAllListeners("resolve")
        ee.removeAllListeners("fileDone")
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
    await page.goto(link);
    await setFlag(apiEmitter);
    console.log("starting scrape of ", link)
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
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ; 
  await page.removeAllListeners('response')
  return null;
}

async function getPublixPromotions({ page }){ 
  /**
   * @param page : the current page instance. 
   * @prerequiste : setUpBrowser() set location successfully. 
   */
  // set request interception on page
  //await page.setRequestInterception(true);
  // page.on('request', (req)=> {
  //   if (req.isInterceptResolutionHandled()) return;
  //   else req.continue()
  // })

  var path = "/app/tmp/collections/publix/promotions/"
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
  await page.waitForTimeout(12000);
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ;
  await page.removeAllListeners('response')
  return null; 
}

async function getDollarGeneralPromotions({ page }){ 
  /**
   * @param browser: the passed browser instance from SetupBrowser()
   * @param page: the passed page instance from SetupBrowser()
  */
  // set request interception on page
  
  var badRequests = [];
  var loadMoreSwitch = 0, lastLoadMoreSwitch = 0; 
  var path = "/app/tmp/collections/dollargeneral/promotions/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  var reqSet = new Set();

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
    await page.waitForTimeout(12000)
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
      await page.waitForTimeout(10_000)
      // check for item modal to be present
      let eligibleItems = await page.$("section[class='couponPickupDetails__products-wrapper row']") ; 
      console.log(eligibleItems)
      if (eligibleItems){
        let loadMoreButton = await eligibleItems.$("button[class='button eligible-products-results__load-more-button']") ;
        console.log(loadMoreButton)
        while (loadMoreButton && (loadMoreSwitch==0 || loadMoreSwitch != lastLoadMoreSwitch)){
          await loadMoreButton.click();
          await page.waitForTimeout(7500);
          loadMoreButton = await eligibleItems.$("button[class='button eligible-products-results__load-more-button']") ; 
          console.log(loadMoreButton)
          lastLoadMoreSwitch = loadMoreSwitch ; 
          let tmpResults = await page.$$(".eligible-products-results__results-list > li");
          loadMoreSwitch = tmpResults.length
          console.log("loadMore ", loadMoreSwitch, "lastLoadMore ", lastLoadMoreSwitch)
        }
        loadMoreSwitch = 0;
        lastLoadMoreSwitch = 0; 
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
      reqSet = new Set([])
      left--;    
      console.log("finished promotion. ", left, " left.")
  };
    await page.waitForTimeout(5000);
    await wrapFile(fileName);
    console.log("file finished : ", fileName) ;
    // if (badRequests.length>0){
    //   console.log(`Writing ${badRequests.length} to file ./temp.json.`)
    //   let br = JSON.stringify(badRequests);
    //   await fs.promises.writeFile("/app/tmp/temp.json", br)
    // }
  await page.removeAllListeners('response')
  return null;
}

async function getDollarGeneralItems({ page }){
  /**
   * @prerequisite : setUpBrowser() successfully set location. 
   * 
   * @param page : the current page instance.
   */
  // set request interception on page
  var path = "/app/tmp/collections/dollargeneral/items/"
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
  await page.waitForTimeout(23000)
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
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ;
  await page.removeAllListeners('response')
  return null
}

async function getFamilyDollarPromotions({ page }){
  /**
   * @prerequisite : setUpBrowser() worked. 
   * @param page : the starting page ; 
   * @bug : kwargs
   */
  // set request interception on page
  
  var path = "/app/tmp/collections/familydollar/promotions/"
  var fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
  var offset = 0 ; 
  fileName = path+fileName ; 
  var wantedRequestRegex = /ice-familydollar\.dpn\.inmar\.com\/v2\/offers\?/
  
  page.on("response", async (res)=> {
    let url = res.url() ;
    let req= res.request();
    if (req.method()!== "OPTIONS" && url.match(wantedRequestRegex)){
      offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
      return; 
    }
    return ; 
  })
  await Promise.all([
    page.goto("https://www.familydollar.com/smart-coupons"),
    page.waitForTimeout(10000)
  ])
  await wrapFile(fileName);
  console.log("file finished : ", fileName) ;
  await page.removeAllListeners('response')
  return null; 
}

async function getFamilyDollarItems({ page }){
  /**
    * @param browser: the current browser instance .
    * @param page : PageElement from Successfully Launched Browser. 
    * @prequisite setUpBrowser() successful. Iterations Set to 96. 
    */
    // set request interception on pa
    var offset = 0;
    var wantedRequestRegex = /(dollartree-cors\.groupbycloud\.com\/api|https:\/\/www\.familydollar\.com\/ccstoreui\/v1\/search)/
    let fileName = new Date().toLocaleDateString().replaceAll(/\//g, "_") + ".json";
    fileName = "/app/tmp/collections/familydollar/items/" + fileName; 
    page.on("response", async (res)=> {
      let url = res.url() ;
      if (url.match(wantedRequestRegex)){
        offset+=await writeResponse(fileName=fileName, response=res, url=url, offset=offset)
        return; 
      }
      return ; 
    })
    
    let selectDiv = await page.$$(".oc3-select > div > select");
    console.log(selectDiv)
    selectDiv = selectDiv[1]
    await selectDiv.hover()
    await selectDiv.click();
    await selectDiv.press("ArrowDown")
    await selectDiv.press("ArrowDown")
    await Promise.all([
      selectDiv.press("Enter"),
      // wait for reload
      page.waitForResponse(res=> res.url().includes("search"), {timeout: 15000}), 
    ])
    console.log("wait")
    await page.waitForTimeout(10000)

    let iterations = await page.$eval("div.occ-left-nav-items-count", (el)=>{
      return +el.textContent.match(/\d+/)[0]
    })
    iterations = Math.floor(iterations/96) + 1;
    // wait for page reload
    
    for (let i=1; i<iterations; i++){
      await Promise.all([
        page.$eval("a[aria-label='Next']", (el)=>el.click()),
        page.waitForTimeout(12000)
      ])
      console.log("finished ", i , " ", iterations-i, " left ")
    }

    await page.waitForTimeout(14000); 
    await wrapFile(fileName);
    console.log("finished file", fileName);
    await page.removeAllListeners('response')
    return null
}

async function getFoodDepotItems({ page }){
  /**
   * 
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

  await page.setDefaultTimeout(0)
  var path = "/app/tmp/collections/fooddepot/items/"
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
    page.waitForTimeout(8800)
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
    await page.waitForTimeout(16500);
    newHeight = await body.getProperty("offsetHeight").then((jsHandle)=> jsHandle.jsonValue());
    console.log(newHeight)
    let u = 1; 
    while (pageHeight !== newHeight){
      pageHeight=newHeight;
      console.log(newHeight)
      await page.keyboard.press("End");
      await page.waitForTimeout(5500); // what is blocking syncrohous calls if end is not pressed again, images will stall and render one by one before next image resource is called
      u++;
      newHeight = await body.getProperty("offsetHeight").then((jsHandle)=> jsHandle.jsonValue());
      console.log(newHeight, u)
    }
    console.log('finished ', categoryUrl, ' @ index: ', allCategories.indexOf(categoryUrl), ' of ', allCategories.length-1)
  }
  await page.waitForTimeout(7500); 
  await wrapFile(fileName);
  await page.removeAllListeners('response');
  console.log("finished file : ", fileName)
  return null
}

async function getFoodDepotPromotions({ page }){ 
  /**
   * 
   * @param page : the current page instance.
   * @requirements : setUpBrowser("foodDepotCoupons") was successful. 
   */
  // note : navigation to other stores promotions can only occur after MFA login 
  // page = await browser.pages()
  // page = page[0]
  await page.waitForTimeout(10000);
  var path = "/app/tmp/collections/fooddepot/promotions/"
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
  await page.reload();
  await page.waitForTimeout(15000);
  await page.waitForTimeout(13000)
  await wrapFile(fileName);
  console.log("finished file", fileName);
  await page.removeAllListeners('response')
  return null;
}

const getFoodDepotCode = async () => {
  var passedValidateCode; 
  // rewrite as node controlled server
  const server = http.createServer();

  server.on("request", (req, res)=>{
    const phoneUrl = new URL(req.url, `http://${req.headers.host}`)
    passedValidateCode = phoneUrl.search.match(/code=(\d+)/)[1]
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      data: {codeRecieved: true}
    }))
    console.log("phoneCode Set");
    server.close();  
  })
  server.listen({port: 5000})

return new Promise((resolve, reject) => {
  server.on("close", ()=> {
    resolve(passedValidateCode)
  })

  server.on("error", (err)=>{
    server.close(); 
    reject(err)
  })
});
}

async function testContainerBrowser(){
  var browser = await puppeteer.launch({
    headless: false,
    slowMo: 2000,
    dumpio: false,
    args: ["--start-maximized", "--no-sandbox"],
    executablePath: "google-chrome-stable",
    defaultViewport: {width: 1920, height: 1080 },
    devtools: false,
    timeout: 0
  });
  console.log("successfully launched browser"); 
  var [page] = await browser.pages(); 
  console.log("opened page"); 
  await page.goto("https://www.kroger.com");
  console.log("went to kroger.com"); 
  await page.waitForTimeout(6000);
  console.log("waited for 4 seconds"); 
  await page.screenshot({
    path: "./img/headlessScreenKrogerHome.png",
    fullPage: true,
  });
  console.log("took home screenshot");
  await page.waitForTimeout(6000);
  await page.goto("https://www.kroger.com/savings/cl/coupons")
  await page.screenshot({
    path: "./img/headlessScreenKrogerCoupons.png",
    fullPage: true,
  });
  console.log("closed")
  return null
}

// allow for temporary setup to show success and mark setup process as a success by airflow


const program = new Command();
// cli specifications
program
  .name("grocery-clerkify")
  .description("A Powerful Containerized Webscraping Package to Access Promotional, Price, Inventory, Item-Level Data Across Multiple Different Stores")
  .version("1.0.0");

program
  .command("scrape")
  .description("scrapes specified data throught containerized browser")
  .option("-a, --aldi <procedure>", "scrape aldi items")
  .option("-fd --family-dollar <procedure>", "scrape family dollar items, instacartItems, promotions")
  .option("-k, --kroger <procedure>", "scrape kroger promotions (cashback | digital), specialPromotions and trips")
  .option("-p, --publix <procedure>", "scrape publix promotions and items")
  .option("-dg, --dollar-general <procedure>", "scrape dollar general promotions and items")
  .option("--food-depot <procedure>", "scrape food depot items and promotions")
  .option("--no-setup", "bypass setup task for browser (for debugging purposes only)")
  .option("--type <type>", "additional argument for kroger scrapes that must be passed down to scraping function")
  .action(async (options)=>{
    var taskParser = {
      aldiItems: getInstacartItems,
      familyDollarItems: getFamilyDollarItems,
      familyDollarInstacartItems: getInstacartItems,
      familyDollarPromotions: getFamilyDollarPromotions,
      krogerPromotions: getKrogerPromotions,
      krogerSpecial: getKrogerSpecialPromotions, 
      krogerTrips: getKrogerTrips,
      publixPromotions: getPublixPromotions,
      publixItems: getInstacartItems,
      dollarGeneralItems: getDollarGeneralItems,
      dollarGeneralPromotions: getDollarGeneralPromotions,
      foodDepotItems: getFoodDepotItems,
      foodDepotPromotions: getFoodDepotPromotions
    };
    let [taskName] = Object.entries(options).filter(([k, v])=>k!=='setup' && k!=='type').map(([k, v])=>k+v[0].toUpperCase()+v.slice(1))
    let taskArgs;
    console.log(options, taskName)
    if (options.setup){
      taskArgs = await setUpBrowser(taskName)
    } else {
      taskArgs = await setUpBrowser(task="")
    }
    taskName==="krogerPromotions"? taskArgs = {...taskArgs, "type": options.type} : taskArgs; 
    await taskParser[taskName](taskArgs)
    await taskArgs.browser.close();
    return undefined
  })

program
  .command("test")
  .description("runs a test script for debugging")
  .option("-d, --data <data>", "message to echo")
  .action(async (options)=> {
    console.log("your data : ", options.data)
    const browser = await puppeteer.launch(BROWSER_OPTIONS)
    console.log(browser.wsEndpoint)
    let [page] = await browser.pages()
    await page.goto("https://www.google.com")
  })

program.parse();