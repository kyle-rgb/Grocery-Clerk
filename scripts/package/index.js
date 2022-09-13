// migrating extension, server intermediary and CV based browser scraping into single package 
const puppeteer = require('puppeteer-extra')
// add stealth plugin and use defaults 
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
puppeteer.use(StealthPlugin())
const readline = require("readline");

async function getTestWebsite() {
  // for testing request interception and loading elements from DOM
  const browser = await puppeteer.launch({
    headless: false,
    executablePath:
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    dumpio: false,
    args: ["--start-maximized"],
    devtools: false,
  });
  k = 0;
  let [page] = await browser.pages();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.setRequestInterception(true);
  page
    .on("console", (message) => {
      //console.log(`${message.type().toUpperCase()} ${message.text()}`);
    })
    .on("pageerror", ({ message }) => console.log(message))
    .on("request", (intReq) => {
      if (intReq.isInterceptResolutionHandled()) return;
      intReq.continue();
    })
    .on("response", async (response) => {
      if (!response.url().endsWith("whoami")) {
        return;
      } else {
        console.log(`${response.status()} ${response.url()}`);
        console.log(await response.text());
      }
    })
    .on(
      "requestfailed",
      (request) =>
        console.log(`${request.failure().errorText} ${request.url()}`),
      "\n"
    );
  await page.goto(
    "https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Your_first_WebExtension"
  );
  console.log("Done...");

  const TextValue = await page.$$("a", (elems) => {
    console.log(typeof elems);
    return elems[42];
  });
  console.log("textValue = ", TextValue[42]);
  setTimeout(async () => {
    await TextValue[211].hover();
    setTimeout(() => {
      TextValue[211].click();
    }, 5000);
  }, 2000);
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
   */

  const ZIPCODE = process.env.ZIPCODE;

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
      let wantedStoreDiv = await storeSelectDivs.$$(
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
    case "aldiItems":
      // * aldi items: wait for free delivery banner to load, select pickup button, wait for page reload, click location picker button,
      // select location by address text in locations list section and click wanted stores button, wait for page reload
      var wantedModality;
      var availableModalities = ["Pickup", "Delivery"];
      var wantedStore = "10955 Jones Bridge Road";
      let modalitiyButton = await page.$$(
        "div[aria-label='service type'] > button",
        (els) => els.filter((el) => el.text == wantedModality)
      );
      modalitiyButton.click();
      await page.$("div.css-1advtqp-PickupLocationPicker").click();
      await page
        .$(
          "div[aria-label='Pickup Locations List'] > section > button[type='button']"
        )
        .click();
      await page.$("address", (el) => el.parentElement.click());
      await page.$("button[type='submit']", (el) => el.click());
      let locationsList = await page.$("ul[aria-labelledby='locations-list']");
      let wantedIndex = await locationsList.$$(
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
    authModal.$$("button", (elems)=> {
      let login =  elems.filter((el)=>el.textCotent==="Log in")[0];
      login.click();
    })
    await page.$("form > div > button", (el)=> el.click()) // login credentials already in browser profile; store is saved to account for now, otherwise use same location / modality handling for instacart site as those above for aldi. 
  }

  // * publix coupons: navigate to all-deals, wait for api response, wait for copied response
  // needs to be whitelisted for accessing location or (click choose a store button from navbar, enter in zipcode, press enter, click on store link element that matches wanted location's address)

  // * food depot items: navigate to store page, enter zipcode into input box, select store based on address, click start shopping button
  // or started immediately at specific store website
  // * food depot coupons: navigate to coupon site, enter phone number into input#phone, press enter, wait for automation on phone to send verification text,
  // IPhone Automation will extract code and send a request to a temporary server with the code, once the request is recieved, the server will forward it to node and enter it in to
  // modal's next input, shutdown server, press enter, wait for api request with authetication,
  // @requires verification via mobile, needs to be coordinated with iPhone Automations. (10 min window on verfication, should be simple if automation of task (DAG) amd automation of phone shortcut occur at same time always).
  // * dollar general items: navigate to page, force refresh, select store menu, select button.store-locator-menu__location-toggle, select input#store-locator-input, type zipcode, press enter, select li.store-list-item who's span-list-item__store-address-1 == wanted store address, wait for reload
  // wait for iterations to be set, click button.splide__arrow.split__arrow--next
  // * dollar general coupons: navigate to page, force refresh, select store menu, select button.store-locator-menu__location-toggle, select input#store-locator-input, type zipcode, press enter, select li.store-list-item who's span-list-item__store-address-1 == wanted store address, wait for reload,
  // wait for iterations to be set and then press button.button coupons-results__load-more-button until all coupons are delivered to page;
  // * family dollar items: go to specific url that shows all items, press end, click select drop down for maximum items (96), wait for page refresh
  // * family dollar instacart items: navigate to store page, click on delivery button, input address location, click save address button, wait for reload
  // * family dollar coupons: navigate to smart-coupons page, click your store link in nav bar, enter zip code into input, press enter, select store by address, wait for redirect, go to smart coupons, wait for api response
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
getTestWebsite()