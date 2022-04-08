import time, re, random

from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException

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


def insertData(entries, collection_name):
    # Going to add Entries to Locally running DB w/ same structure as Container application
    # Then migrate them over to Container DB
    # Wrapper to always use insert many
    if type(entries) != list:
        entries = [entries]
    client = MongoClient()
    db = client.groceries # db
    # items = db.items  # items
    res = 0
    if collection_name == 'trips':
        res = db.trips.insert_many(entries)
        res = len(res.inserted_ids)
    elif collection_name == 'items':
        res = db.items.insert_many(entries)
        res = len(res.inserted_ids)
    else:
        client.close()
        raise ValueError
    print(f"Inserted {res} documents in {collection_name}")
    client.close()

    return None


def getItemInfo(link, driver):
    # BUG: Items need UPCs, it is data fed by the link, but the span selection does not work

    # TODO: Match ID to API Search for Further Structured Information for Items
    # TODO: Want to Combine It with Receipts Array<Items> for all information pertaining to the certain item. 

    # Either way we know the order of items on the trip dashboard matches that on the reciepts. So each Iteam will need the equivalent index to flesh out current Item array into an Object array with all pertinent data
        # that refers back to the trip. 
    # /product?<search terms> :: productID<String>,UPC<String>,aisleLocations<Array>,brand<String>,categories<Array>,countryOrigin<String>,description<String>,items<Array>,itemInformation<Object of 3D Points>,temperature<Object>, images<Array of Objects w/[id, perspective, default=true/false, sizes<Array of Objects w/[id, size, url]>]> 
    # /product/id
    item_details = {}
    driver.switch_to.new_window("tab")
    time.sleep(4)
    try:
        driver.get(link)
        time.sleep(6)
    except InvalidArgumentException:
        return item_details
    # UPC
    try: 
        item_details['UPC'] = driver.find_element(By.CSS_SELECTOR, "span.ProductDetails-upc").text.replace("UPC:", "").strip()
    except NoSuchElementException:
        # will be only number in link
        code_re = re.compile(r"/\d+")
        fallback_code = "".join(re.findall(code_re, link))
        item_details['UPC'] = fallback_code.replace('/', "")
    finally:
        item_details['UPC'] = link
        
        # Get Nutritional Inforamtion
        # Parse Out Nutritional Information housed in items_info [calories, health_rating, Tags:['Kosher', 'NonGMO', 'Organic'], info: {'Ingredients': '', 'Allergen Info': '', 'Disclaimer'},
        # serving_size, nutrients: {"name", "type":['macro', 'sub', 'micro'], "subnutrients": [{}, {}], values: ['DV%', 'Weight']}]]
    try:
        nutrition_we = driver.find_element(By.CSS_SELECTOR, 'div.Nutrition')
        #item_details.setdefault("ingredients", [])
        item_details.setdefault("health_info", {"macros": [], 'calories': 0, 'ratings':[], 'serving_size': ''})
        # Servings Amount Per Container
        item_details['health_info']['serving_size'] = nutrition_we.find_element(By.CSS_SELECTOR, 'div.NutritionLabel-ServingSize').text.replace("Serving size\n", "")
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
            try:      
                item_details['health_info']['macros'].append({'name': title_and_amount[0], 'measure': title_and_amount[1],'daily_value': daily_value, 'is_macro': is_macro, 'is_micro': is_micro, 'is_sub': is_sub, 'nutrient_joiner': hierarchy_switch})
            except:
                # BUG: Micronutrients with no amount listed by still given a percentage mess-up title and amount
                item_details['health_info']['macros'].append({'title_and_amount': str(title_and_amount),'daily_value': daily_value, 'is_macro': is_macro, 'is_micro': is_micro, 'is_sub': is_sub, 'nutrient_joiner': hierarchy_switch})

        ingredients_info = nutrition_we.find_elements(By.CSS_SELECTOR, 'p.NutritionIngredients-Ingredients')
        for p in ingredients_info:
            item_details['ingredients'] = list(map(str.strip, p.text.replace("Ingredients\n", "").split(",")))

        try:
            ratings = nutrition_we.find_elements(By.CSS_SELECTOR, 'div.NutritionIndicators-wrapper')
            if len(ratings) != 0:
                for r in ratings:
                    item_details['health_info']['ratings'].append(r.get_attribute('title'))
        except NoSuchElementException:
            item_details=item_details


        try:
            try:
                nutrition_rating_container =  nutrition_we.find_element(By.CSS_SELECTOR, 'div.Nutrition-Rating-Container')
                health_rating = nutrition_rating_container.find_element(By.TAG_NAME, 'svg').get_attribute('aria-label')
                item_details['health_info']['overall_health_score'] = health_rating
            except :
                item_details=item_details
            finally:
                item_details = item_details
        except:
            item_details = item_details
    except NoSuchElementException:
        item_details = item_details
    finally:
        item_details = item_details
    try:
        # nonfood product rating
        item_details['avg_rating'] = driver.find_element(By.CSS_SELECTOR, "div.bv_avgRating_component_container").text
        # Number of Reviews
        item_details['reviews'] = driver.find_element(By.CSS_SELECTOR, "div.bv_numReviews_text").text
        # Ratings Distribution
        item_details['ratings_distribution'] = driver.find_element(By.CSS_SELECTOR, "div.bv-inline-histogram-ratings").text

        if item_details['avg_rating'].strip() == '':
            time.sleep(3)
            # nonfood product rating
            item_details['avg_rating'] = driver.find_element(By.CSS_SELECTOR, "div.bv_avgRating_component_container").text
            # Number of Reviews
            item_details['reviews'] = driver.find_element(By.CSS_SELECTOR, "div.bv_numReviews_text").text
            # Ratings Distribution
            item_details['ratings_distribution'] = driver.find_element(By.CSS_SELECTOR, "div.bv-inline-histogram-ratings").text

    except NoSuchElementException:
        item_details=item_details
    driver.close() # close item page
    driver.switch_to.window(driver.window_handles[1]) # brings you back to trip page
    return item_details



def getCart(url, driver):
    randint= random.randint(10, 100) / 10
    time.sleep(5+randint)
    driver.switch_to.new_window("tab")
    driver.get(url)
    time.sleep(8)
    data = []
    items = driver.find_elements(By.CSS_SELECTOR, 'div.PH-ProductCard-productInfo')
    # Find all products as List
    for scan_number, we in enumerate(items):
        document = {}
        document['cart_number'] = url
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

        if document['image'] != '': # No Image indicates a functionally dead webpage with no data
            time.sleep(1)
            moreInfo = getItemInfo(document['item_link'], driver) # Change this to item_link
            document.update(moreInfo)
            time.sleep(1.5)
            
        data.append(document)

    insertData(data, 'items')
    driver.close()
    driver.switch_to.window(driver.window_handles[0]) 
    return None




# Iterate Through Pages, then press <button aria-label='Next page'>

def getReceipt(link, driver):
    # Merged Receipt and Trip Since Trip Level Information Does Not Give Me Much More than Analyzing the Receipt
    # Marked By SC but does not have specialty DOM tags or classes, all entries exist in rows and will need to be pulled out via RegEx
    # Receipt can tap into elevated Savings Type (eCpn=Loaded App Coupon, Mega Event Savings=Limited Savings Event, KROGER SAVINGS=Regular Plus Card Savings)
    # Could Also Get Kroger's shortName for Items
    # Date and time of checkout, location of store, type of payment, savings breakdown (STR CPN & KRO PLUS SAVINGS), TOTAL COUPONS, TOTAL SAVINGS (\d+ pct.), checkout lane / cashier,
    # Fuel Points Earned Today (Total-Tax), Total Month Fuel Points, Remaining Fuel Points from Last Month 
    # Additional Rewards Spending, Additional Rewards Expiration Date
    driver.switch_to.new_window("tab")
    time.sleep(1.5)
    driver.get(link)
    randint = random.randint(20, 60) / 10
    time.sleep(1+randint)
    receipt_document={} 
    # Wanted Not Bolded Text
    payment_type_re= re.compile(r".+Purchase\s*")
    full_address_re= re.compile(r".+(GA$|GA\s+\d{5}$)") 
    
    # Wanted Bolded Texts
    fuel_re = re.compile(r"Fuel Points Earned Today:|Fuel Points This Order:")
    cumulative_fuel_re = re.compile(r"Total .+ Fuel Points:")
    last_month_fuel_re = re.compile(r"Remaining .+ Fuel Points:")
    street_address_re = re.compile(r"\d+.+(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|parkway|pkwy|circle|cir|boulevard|blvd)+")
    cashier_re = re.compile(r"Your cashier was")
    sales_re = re.compile(r'^SC')
    tax_re = re.compile(r"TAX")
    savings_total_re = re.compile(r"TOTAL SAVINGS \(.+\)")
    sales_total_re = re.compile(r".+BALANCE")
    time_re = re.compile(r"\d{2}/\d{2}/\d{2} \d{2}:\d{2}")

    last_item_index = 0
    checkout_time_re = re.compile(r"Time:")
    checkout_date_re = re.compile(r"Date:")
    item_re = re.compile(r".+(B$|T$)")
    # Get Receipt Image
    try:
        receipt = driver.find_element(By.CSS_SELECTOR, 'div.imageContainer')
        nodes = receipt.find_elements(By.CSS_SELECTOR, 'div.imageTextLineCenter')
        receipt_document['order_number'] = link
        receipt_document['full_document'] = list(map(lambda x: x.text, nodes))
        for index, bn in enumerate(nodes):
        # FINISHED: Match Sales w/ Items (Could be Done Via Price Matching w/ Exceptions for Same Prices Since Receipt Names are abbreviations)
        # Sales Come After Product Scan, Can Be Multiple Different Promotions, All begin with SC; Skip Ct/Wgt Data as Items already Store this Information
        # As I iterate through the sales list I need to provide a reference number to point back to the correct item
            receipt_document.setdefault('checkout_timestamp', '')
            receipt_document.setdefault('address', '')
            receipt_document.setdefault('items', [])
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
            elif re.match(time_re, text) != None:
                receipt_document['address_backup'] = re.match(time_re, text)[0]
            elif re.match(street_address_re, text.lower()) != None:
                receipt_document['address'] =  text + " " + receipt_document['address']
            elif re.match(cashier_re, text ) != None:
                receipt_document['cashier'] = re.sub(cashier_re, "", text).strip()
            elif re.match(payment_type_re,text) != None:
                receipt_document['payment_type'] = text
            elif re.match(savings_total_re, text ) != None:
                receipt_document['total_savings'] = re.sub(savings_total_re, "", text).strip()
            elif re.match(sales_total_re, text ) != None:
                receipt_document['total'] = re.sub(sales_total_re, "", text).strip()
            elif re.match(tax_re,text) != None:
                receipt_document['tax'] = re.sub(tax_re, "", text).strip()
            elif re.match(last_month_fuel_re, text) != None:
                receipt_document['last_month_fuel_points'] = re.sub(last_month_fuel_re, "", text)
            else:
                if re.match(sales_re, text) != None:
                    if receipt_document['items'][last_item_index].get('savings') == None:
                        receipt_document['items'][last_item_index]['savings'] = [text]
                    else:
                        receipt_document['items'][last_item_index]['savings'].append(text)
                elif re.match(item_re, text)!=None:
                    receipt_document['items'].append({"item": bn.text.strip()})
                    last_item_index = receipt_document['items'].index({"item": bn.text.strip()}) 
        
    except NoSuchElementException:
        ## Reroute Specialized Trips that Fuel Based
        driver.get(link.replace('image', 'detail'))
        time.sleep(5)
        payment_re = re.compile(r'AMEX|DEBIT|VISA')
        try:
            receipt_document['address'] = driver.find_element(By.CSS_SELECTOR, 'span.kds-Text--l.mb-0').text
            receipt_document['checkout_timestamp'] = driver.find_element(By.CSS_SELECTOR, 'h2.kds-Heading.kds-Heading--m').text.replace('Fuel', '').strip()
            # total savings in a span with a negative sign
            money_details = driver.find_element(By.CSS_SELECTOR, 'div.purchase-detail-footer')
            spans = money_details.find_elements(By.TAG_NAME, 'span')
            span_texts = list(map(lambda x: x.text, spans))
            payment = [s for s in span_texts if re.match(payment_re, s)]
            savings = [text for text in span_texts if text.startswith('-')]
            if savings==[]:
                savings = "$0.00"
            else:
                savings = savings[0].replace('-', '')
            receipt_document['total_savings'] = savings
            receipt_document['full_document'] = span_texts
            receipt_document['payment_type'] = payment[0]
            # total
            receipt_document['total'] = driver.find_element(By.CSS_SELECTOR, 'span[data-test="payment-summary-total"]').text
            receipt_document['special_purchase_type'] = 'Fuel'
            receipt_document['order_number'] = link

            insertData(receipt_document, 'trips')
            driver.close()
            driver.switch_to.window(driver.window_handles[0]) # bring back to current dashboard page
            return None

        except ValueError:
            receipt_document=receipt_document

    finally:
        receipt_document = receipt_document
     # All Savings, but Also Tax, Balance and Saving Aggregations
    # Iterate through nodes get ones who match the re's and assign them the proper name to the return document

    # Get TAX and TOTAL Savings

    #nodes= nodes[:10]
    
    insertData(receipt_document, 'trips')
    driver.close()
    driver.switch_to.window(driver.window_handles[0]) # bring back to current dashboard page
    return None

# Trip Level Data : Collection<Items>
# Trip and Account Metadata and More Precise Data on the Sales 
# More Precise Item information (UPC to join to receipt), ingredients, ratings, health_info, etc. 


def getMyData():
    # Process Flow: Setup Browser -> Get Purchases Dashboard -> Collect Cart URLS -> foreach cart getCart(cart_page){contains GetItems} and getReceipt(reciept_page) 
    # Purchase Dashboard, Acquire links for each trip on the page and buttons to next page, get links for each item and finish with receipt acquistion
    # Setup Driver
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_argument("disable-blink-features=AutomationControlled")
    # Load Credentials from Browser Profile
    options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options)
    driver.implicitly_wait(3.5)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"})
    
    testBinary = True
    while testBinary:
        ans = input("press enter to continue")
        if ans == '':
            testBinary=False
        else:
            raise ValueError('No other response allowed')
    
    time.sleep(7)
    dashboard_url_base = 'https://www.kroger.com/mypurchases?tab=purchases&page='
    dashboard_index = 2
    driver.get(dashboard_url_base + f"{dashboard_index}")
    ### Website SignIn ###
    time.sleep(7)
    signInBtn = driver.find_element(By.ID, 'SignIn-submitButton')
    signInBtn.click()
    time.sleep(6.5)
    pages = driver.find_elements(By.CSS_SELECTOR, "nav.kds-Pagination > a")
    last_page = [p.text for p in pages][-1]
    last_page = int(last_page)

    for i in range(dashboard_index, last_page+1):
        ##### Trip Selection #####
        driver.get(dashboard_url_base+str(i))
        time.sleep(9)
        trips = driver.find_elements(By.LINK_TEXT, 'See Order Details')
        wait  = random.randint(20, 60)/10
        time.sleep(wait)
        for trip in trips:
            starting_url = trip.get_attribute('href')
            ### receipt is the same url with detail replaced with image (of receipt)
            receipt_url = trip.get_attribute('href').replace('detail', 'image')
            time.sleep(wait)
            getCart(starting_url, driver)
            getReceipt(receipt_url, driver)
            time.sleep(random.randint(20, 50)/10)
        print(f"Finished with Page {i}")
    driver.quit()

getMyData() 


