
import os, sys, math, time, datetime as dt, pprint, re, random

import pandas as pd, numpy as np, time, json
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from pymongo import MongoClient
from urllib.parse import quote_plus
from api_keys import MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD


def connectToDatabase():
    # Going to add Entries to Locally running DB w/ same structure as Container application
    # Then migrate them over to Container DB
    # "mongodb+srv://username:password@cluster0-jtpxd.mongodb.net/admin"
    uri = "mongodb+srv://%s:%s@%s" % (quote_plus(MONGO_INITDB_ROOT_USERNAME), quote_plus(MONGO_INITDB_ROOT_PASSWORD), quote_plus("172.26.0.2"))
    client = MongoClient(uri)
    db = client.groceries # db
    # items = db.items  # items
    trips = db.trips.find_one({}, {'_id': 0})
    print(trips)



def getItemInfo(link, driver):
    # TODO: Parse item details from array to factored out object with specific K:V pairs for Nutrition and Availability
    # TODO: Match ID to API Search for Further Structured Information for Items
    # TODO: Want to Combine It with Receipts Array<Items> for all information pertaining to the certain item. 

    # Either way we know the order of items on the trip dashboard matches that on the reciepts. So each Iteam will need the equivalent index to flesh out current Item array into an Object array with all pertinent data
        # that refers back to the trip. 
    # /product?<search terms> :: productID<String>,UPC<String>,aisleLocations<Array>,brand<String>,categories<Array>,countryOrigin<String>,description<String>,items<Array>,itemInformation<Object of 3D Points>,temperature<Object>, images<Array of Objects w/[id, perspective, default=true/false, sizes<Array of Objects w/[id, size, url]>]> 
    # /product/id
    driver.switch_to.new_window("tab")
    driver.get(link)
    item_details = {}
    # UPC
    item_details['UPC'] = driver.find_element(By.CSS_SELECTOR, "span.ProductDetails-upc").text.replace("UPC:", "").strip()
    try:
        # nonfood product rating
        item_details['avg_rating'] = driver.find_element(By.CSS_SELECTOR, "div.bv_avgRating_component_container.notranslate").text
        # Number of Reviews
        item_details['reviews'] = driver.find_element(By.CSS_SELECTOR, "div.bv_numReviews_text").text.replace("(", "").replace(")", "")
    except NoSuchElementException:
        # Parse Out Nutritional Information housed in items_info [calories, health_rating, Tags:['Kosher', 'NonGMO', 'Organic'], info: {'Ingredients': '', 'Allergen Info': '', 'Disclaimer'},
        # serving_size, nutrients: {"name", "type":['macro', 'sub', 'micro'], "subnutrients": [{}, {}], values: ['DV%', 'Weight']}]]
        item_details.setdefault("ingredients", [])
        item_details.setdefault("health_info", {"macros": [], 'calories': 0, 'ratings':[]})
        item_details.setdefault("serving_size", {})
        
        # Get Nutritional Inforamtion
        try:
            nutrition_we = driver.find_element(By.CSS_SELECTOR, 'div.Nutrition')
            # Servings Amount Per Container
            item_details['serving_size']['by_weight'] = nutrition_we.find_element(By.CSS_SELECTOR, 'div.NutritionLabel-ServingSize').text.replace("Serving size\n", "")
                # Calories Per Serving
            item_details['health_info']['calories'] = nutrition_we.find_element(By.CSS_SELECTOR, 'div.NutritionLabel-Calories').text.replace("Calories\n", "")
                # Macronutrients and Subnutrients
            nutrients = nutrition_we.find_elements(By.CSS_SELECTOR, 'div.NutrientDetail')
            hierarchy_switch = 0
            for x, n in enumerate(nutrients):
                
                title_and_amount = n.find_element(By.CSS_SELECTOR, 'span.NutrientDetail-TitleAndAmount')
                is_macro = "is-macronutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
                is_micro = "is-micronutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
                is_sub = "is-subnutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
                if ((is_macro) & (~is_sub)):
                    hierarchy_switch = x
                else:
                    hierarchy_switch = hierarchy_switch
                title_and_amount = title_and_amount.text.replace("\n", ": ").replace("Number of International Units", "IU")
                title_and_amount = re.sub(r"([A-Za-z]+)(\d\.?\d*){1}", r"\1:\2", title_and_amount).split(':')
                daily_value = n.find_element(By.CSS_SELECTOR, 'span.NutrientDetail-DailyValue').text.replace("\n", ": ").replace("Number of International Units", "IU")
                item_details['health_info']['macros'].append({'name': title_and_amount[0], 'measure': title_and_amount[1],'daily_value': daily_value, 'is_macro': is_macro, 'is_micro': is_micro, 'is_sub': is_sub, 'nutrient_joiner': hierarchy_switch})

            try:
                nutrition_container = nutrition_we.find_element(By.CSS_SELECTOR, 'div.Nutrition-Rating-Indicator-Container')
                ratings = nutrition_container.find_elements(By.CSS_SELECTOR, 'div.NutritionIndicators-wrapper')
                for r in ratings:
                    item_details['health_info']['ratings'].append(r.get_attribute('title'))
                try:
                    health_rating = nutrition_container.find_element(By.CSS_SELECTOR, 'div.Nutrition-Rating-Container > div > svg > text')
                    item_details['health_info']['overall_health_score'] = health_rating.text
                    ingredients_info = nutrition_we.find_elements(By.CSS_SELECTOR, 'p.NutritionIngredients-Ingredients')
                    for p in ingredients_info:
                        item_details['ingredients'] = list(map(str.strip, p.text.replace("Ingredients\n", "").split(",")))
                except NoSuchElementException:
                    nutrition_container = nutrition_we.find_element(By.CSS_SELECTOR, 'div.Nutrition-Rating-Container')
                    ingredients_info = nutrition_we.find_elements(By.CSS_SELECTOR, 'p.NutritionIngredients-Ingredients')
                    for p in ingredients_info:
                        item_details['ingredients'] = list(map(str.strip, p.text.replace("Ingredients\n", "").split(",")))
                finally:
                    item_details = item_details
            except:
                item_details = item_details
        except NoSuchElementException:
            item_details = item_details
    finally:
        item_details = item_details
    
        
        

    driver.close()

    return item_details





def getCart(url, driver):
    testBinary = False
    randint= random.randint(20, 60) / 10
    driver.get(url)
    time.sleep(2+randint)
    while testBinary:
        ans = input("press enter to continue")
        if ans == '':
            testBinary=True


    data = []
    items = driver.find_elements(By.CSS_SELECTOR, 'div.PH-ProductCard-productInfo')
    # Find all products as List
    items = items[:10]
    for scan_number, we in enumerate(items):
        document = {}
        document['item_index'] = scan_number
        # dict.setdefault() <- Use for no IMG svgs
            # Image of Product (beware of svgs for products with no images)
        try:
            _link = we.find_element(By.CSS_SELECTOR, 'img.kds-Image-img').get_attribute('src')
        except NoSuchElementException:
            _link = ''
        document['image'] = _link
        
        try:
            # Name of Product :: Interestingly there seems to be Brand Information Coded Into the Name, More Data!
            document['product_name'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--m.PH-ProductCard-item-description.font-secondary.heading-s.mb-4 > a').text
            # Link to Product :: Link to Item Ends with UPC which Can Help Compare Same Items Across Different Stores for Future Price Watching
            item_link= we.find_element(By.CSS_SELECTOR, 'span.kds-Text--m.PH-ProductCard-item-description.font-secondary.heading-s.mb-4 > a').get_attribute('href')
            document['item_link'] = item_link
            document["UPC"] = re.findall(r"\d+", item_link)[0]
        except NoSuchElementException:
            document['product_name'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--m.PH-ProductCard-item-description.font-secondary.heading-s.mb-4').text
            document['item_link'] = ''
            # Item Quantity and   # Price per Item
        document['price_equation'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--s').text
            # shortDescription of Volume / Ct / Weight
        document['product_size'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--xs.PH-ProductCard-item-description-size.text-default-500.mb-4').text
        try:
            # Promotional Price {span class="kds-Price-promotional-dropCaps"}
            document['product_promotional_price'] = we.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text.replace('\n', '')
            document['product_original_price'] = we.find_element(By.CSS_SELECTOR, 's.kds-Price-original').text.replace('\n', '')
        except NoSuchElementException:
            document['product_original_price'] = we.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text.replace('\n', '')

        if document['item_link'] != '':
            time.sleep(1)
            moreInfo = getItemInfo(f"file:///H:/Noderizer/webSamples/item{scan_number+1}.mhtml", driver)
            document.update(moreInfo)
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[0])
            

        data.append(document)
    return data




# Iterate Through Pages, then press <button aria-label='Next page'>

def getReceipt(link, driver):
    # Merged Receipt and Trip Since Trip Level Information Does Not Give Me Much More than Analyzing the Receipt
    # Marked By SC but does not have specialty DOM tags or classes, all entries exist in rows and will need to be pulled out via RegEx
    # Receipt can tap into elevated Savings Type (eCpn=Loaded App Coupon, Mega Event Savings=Limited Savings Event, KROGER SAVINGS=Regular Plus Card Savings)
    # Could Also Get Kroger's shortName for Items
    # Date and time of checkout, location of store, type of payment, savings breakdown (STR CPN & KRO PLUS SAVINGS), TOTAL COUPONS, TOTAL SAVINGS (\d+ pct.), checkout lane / cashier,
    # Fuel Points Earned Today (Total-Tax), Total Month Fuel Points, Remaining Fuel Points from Last Month 
    # Additional Rewards Spending, Additional Rewards Expiration Date
    # TODO: Get Tax, Savings, Trip Cost
    # TODO: Search API Endpoint for stores to gather additional store level information that can be applied with trips
    # /locations/<LOCATION_ID> :: address<Object>, chain<String>, phone<String>, departments<Array of Objects w/[departmentId, name, phone, hours<Object w/ weekdays<Objects w/ Hours>>]>, geolocation<Object>, hours<Object>, locationId<String>, name<String>
    driver.get(link)
    randint = random.randint(20, 60) / 10
    time.sleep(1+randint)
    receipt_document={} 
    # Wanted Not Bolded Text
    payment_type_re= re.compile(r".+Purchase\s*")
    full_address_re= re.compile(r".*GA.*") # <- Would Need to Edit for Additional States
    
    # Wanted Bolded Texts
    fuel_re = re.compile(r"Fuel Points Earned Today:")
    cumulative_fuel_re = re.compile(r"Total .+ Fuel Points:")
    last_month_fuel_re = re.compile(r"Remaining .+ Fuel Points:")
    street_address_re = re.compile(r"\d+.+(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir|boulevard|blvd)+")
    cashier_re = re.compile(r"Your cashier was")
    sales_re = re.compile(r'^SC')
    last_item_index = 0
    checkout_time_re = re.compile(r"Time:")
    checkout_date_re = re.compile(r"Date:")
    item_re = re.compile(r".+(B$|T$)")
    # Get Receipt Image
    receipt = driver.find_element(By.CSS_SELECTOR, 'div.imageContainer')

    nodes = receipt.find_elements(By.CSS_SELECTOR, 'div.imageTextLineCenter') # All Savings, but Also Tax, Balance and Saving Aggregations
    # Iterate through nodes get ones who match the re's and assign them the proper name to the return document

    #nodes= nodes[:10]

    for index, bn in enumerate(nodes):
        # FINISHED: Match Sales w/ Items (Could be Done Via Price Matching w/ Exceptions for Same Prices Since Receipt Names are abbreviations)
        # Sales Come After Product Scan, Can Be Multiple Different Promotions, All begin with SC; Skip Ct/Wgt Data as Items already Store this Information
        # As I iterate through the sales list I need to provide a reference number to point back to the correct item
        receipt_document.setdefault('checkout_timestamp', '')
        receipt_document.setdefault('address', '')
        receipt_document.setdefault('items', [])
        receipt_document.setdefault('sales', [])

        text = bn.text.strip()
        if re.match(fuel_re, text) != None:
            receipt_document['fuel_points_earned'] = re.sub(fuel_re, "", text).strip()
        elif re.match(cumulative_fuel_re, text) != None:
            receipt_document['fuel_points_month'] = re.sub(cumulative_fuel_re, "", text).strip()
        elif re.match(checkout_date_re, text) != None:
            receipt_document['checkout_timestamp'] += re.sub(checkout_date_re, "" , text)
        elif re.match(checkout_time_re, text) != None:
            receipt_document['checkout_timestamp'] += re.sub(checkout_time_re, "" , text)
            receipt_document['checkout_timestamp'] = receipt_document['checkout_timestamp'].strip()
        elif re.match(full_address_re, text) != None:
            receipt_document['address'] = receipt_document['address'] + " " + text
        elif re.match(street_address_re, text.lower()) != None:
            receipt_document['address'] =  text + " " + receipt_document['address']
        elif re.match(cashier_re, text ) != None:
            receipt_document['cashier'] = re.sub(cashier_re, "", text).strip()
        elif re.match(payment_type_re,text) != None:
            receipt_document['payment_type'] = text
        elif re.match(last_month_fuel_re, text) != None:
            receipt_document['last_month_fuel_points'] = re.sub(last_month_fuel_re, "", text)
        else:
            if re.match(sales_re, text) != None:
                receipt_document['sales'].append({'item_index': last_item_index, 'sale_code': text})
            elif re.match(item_re, text)!=None:
                receipt_document['items'].append(bn.text.strip())
                last_item_index = receipt_document['items'].index(bn.text.strip())
    
    return receipt_document # Handoff to tell Browser to Backup My Purchases Dashboard // Should be last 

# Trip Level Data : Collection<Items>
# Trip and Account Metadata and More Precise Data on the Sales 
# More Precise Item information (UPC to join to receipt), ingredients, ratings, health_info, etc. 


def getMyData():
    # TODO: Write function for handling driver construction/navigation/destruction, url acquisition/release, and waiting
    # TODO: Write function to enter data into respective MongoDB tables
    cart_links=[]
    # Setup Driver
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_argument("disable-blink-features=AutomationControlled")
    # Load Credentials from Browser Profile
    options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options)
    driver.implicitly_wait(2)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"})
    time.sleep(5)
    driver.get('file:///H:/Noderizer/webSamples/mypurchases.mhtml') 
    # time.sleep(6)
    # signInBtn = driver.find_element(By.ID, 'SignIn-submitButton')
    # signInBtn.click()
    # time.sleep(3)
    elems = driver.find_elements(By.LINK_TEXT, 'See Order Details')
    # for single page
    elems = elems[:1]
    for e in elems:
        #e.get_attribute('href')
        purchases = getCart("file:///H:/Noderizer/webSamples/Cart.mhtml", driver)
        trips = getReceipt("file:///H:/Noderizer/webSamples/Receipt.mhtml", driver)
        # need link to receipt
        # receiptBtn = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='View Receipt']")
        # receiptBtn.click()
    with open("purchases.json", "w") as f:
        f.write(json.dumps(purchases))

    with open("trips.json", "w") as f:
        f.write(json.dumps(trips))

    
    driver.quit()

# Inside Will Find:
    # Trip Level Data: Total Cost of Purchases, Locations of Store, Order Number, Payment Method, Items/Coupons Together, Tax
    # One Item Level: Link to Kroger's Web Page for Item, Quantity of Item Purchased, Sale Price, Regular Price, Picture of Item;
    # Item Webpage: UPC, Weight, Serving Size, Servings per Container, Ingredients, Nutritional Data
        # Breaks Down Further Nutritional Detail By:
            # Macronutrients (Weight) (% of Daily Recommended Value)
        # Recommendations for Like Products

# User Story => Carts (aka Trips) => Products (Identifying Information, Price, Nutritional Information)
# Analyze Shopping Patterns and How Much I Saved Via Trips

# Meals => Combinations of Purchased Foods => Single Food Products
# Use Purchase History as Gauge for Interest in future promotions and basis for queries for new recipes

# Use API to get prices of past purchases and estimate future trips
# Use API to create same carts for Pickup

connectToDatabase()




# getMyData()


