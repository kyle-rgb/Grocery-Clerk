
from pprint import pprint
import time, re, random, datetime as dt, os, json, urllib
import pyautogui as pag

from pymongo import MongoClient
import pyperclip as clip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidArgumentException
from selenium.webdriver.common.keys import Keys

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
    elif collection_name == 'prices':
        res = db.prices.insert_many(entries)
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
    reviews_regex = re.compile(r'(\d+) reviews with (\d{1}) star[s]?\.')
    legalese_regex = re.compile(r"((contains)(\s2% or less of)?[^A-z]*)", re.IGNORECASE)
    grammer = {'g': 1, 'mg': 1000, 'mcg': 1_000_000}
    driver.switch_to.new_window("tab")
    time.sleep(4)
    try:
        driver.get(link)
        time.sleep(6)
    except InvalidArgumentException:
        return item_details
    # UPC
    try: 
        item_details['upc'] = driver.find_element(By.CSS_SELECTOR, "span.ProductDetails-upc").text.replace("UPC:", "").strip()
    except:
        item_details['upc'] = link.split('/')[-1]
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
        hierarchy_switch = -1
        for x, n in enumerate(nutrients):
            
            title_and_amount = n.find_element(By.CSS_SELECTOR, 'span.NutrientDetail-TitleAndAmount')
            is_macro = "is-macronutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
            is_micro = "is-micronutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
            is_sub = "is-subnutrient" in title_and_amount.find_element(By.CSS_SELECTOR, 'span').get_attribute('class')
            title_and_amount = title_and_amount.text.replace("\n", ": ").replace("Number of International Units", "IU")
            title, amt = re.sub(r"([A-Za-z]+)(\d\.?\d*){1}", r"\1:\2", title_and_amount).split(':')
            daily_value = n.find_element(By.CSS_SELECTOR, 'span.NutrientDetail-DailyValue').text.replace("\n", ": ").replace("Number of International Units", "IU")
            daily_value = '0%' if daily_value == '' else daily_value 
            if ((is_macro) & (~is_sub)):
                hierarchy_switch += 1
                item_details['health_info']['macros'].append({'name': title, 'measure': amt,'daily_value': daily_value, "subnutrients": []})
            elif((is_macro) & (is_sub)):
                item_details['health_info']['macros'][hierarchy_switch]['subnutrients'].append({'name': title, 'measure': amt,'daily_value': daily_value})
            else:
                item_details['health_info'].setdefault('micros', [])
                item_details['health_info']['micros'].append({'name': title, 'measure': amt,'daily_value': daily_value, "subnutrients": []})

        ingredients_info = nutrition_we.find_elements(By.CSS_SELECTOR, 'p.NutritionIngredients-Ingredients')
        for p in ingredients_info:
            txt = p.text.strip()
            txt = txt.replace("Ingredients\n", "")
            txt = txt.replace(';', ',').replace('.', ', ').replace('}]', ']]')
            txt = re.sub(legalese_regex, '', txt)
            item_details['health_info']['ingredients'] = parse_ingredients(txt)

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
                item_details['health_info']['overall_health_score'] = int(health_rating.replace('percentage', ''))
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
        not_loaded_check = driver.find_element(By.CSS_SELECTOR, "div.bv_avgRating_component_container").text
        # Ratings Distribution
        if not_loaded_check.strip() == '':
            time.sleep(3)
            # nonfood product rating
            ratings_text = driver.find_element(By.CSS_SELECTOR, "div.bv-inline-histogram-ratings").text
        else:
            ratings_text = driver.find_element(By.CSS_SELECTOR, "div.bv-inline-histogram-ratings").text

        
        ratings_list =  re.findall(reviews_regex, ratings_text)
        temp_list = [0, 0, 0, 0, 0]
        for k, v in ratings_list:
            temp_list[int(v)-1] = int(k)

        item_details['ratings_distribution'] = temp_list
        # nonfood product rating
        

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
    prices = []
    items = driver.find_elements(By.CSS_SELECTOR, 'div.PH-ProductCard-productInfo')
    # Find all products as List
    for we in items[:3]:
        document = {}
        # trip identfier
        locate_data = url.split('/')[-1][:-6]
        document['cart_number'] = locate_data
        document['bin'] = True
        locationId = "".join(locate_data.split('~')[:2])
        acquistion_timestamp = dt.datetime.strptime(locate_data.split('~')[2] + " " + locate_data.split('~')[-1][-4:], "%Y-%m-%d %H%S").timestamp()
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
            document["upc"] = re.findall(r"\d+", item_link)[0]
        except NoSuchElementException:
            document['product_name'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--m.PH-ProductCard-item-description.font-secondary.heading-s.mb-4').text
            document['item_link'] = ''
            # Item Quantity and   # Price per Item
        document['product_size'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--xs.PH-ProductCard-item-description-size.text-default-500.mb-4').text
        price_equation =  we.find_element(By.CSS_SELECTOR, 'span.kds-Text--s').text
        price_equation = price_equation.split('x')
        quantity = float(re.sub(r'[^\d\.]', "", price_equation[0]))
        unitPrice = float(re.sub(r'[^\d\.]', "", price_equation[1]))
        #document['price_equation'] =
            # shortDescription of Volume / Ct / Weight
        
        try:
            # Promotional Price {span class="kds-Price-promotional-dropCaps"}
            promo_price = we.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text.replace('\n', '')
            promo_price = round(float(re.sub(r"[^\.\d]", "", promo_price)) / quantity, 2)
            orig_price = we.find_element(By.CSS_SELECTOR, 's.kds-Price-original').text.replace('\n', '')
            orig_price = round(float(re.sub(r"[^\.\d]", "", orig_price)) / quantity, 2)
        except NoSuchElementException:
            orig_price = we.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text.replace('\n', '')
            orig_price = round(float(re.sub(r"[^\.\d]", "", orig_price)) / quantity, 2)

        
        if document['image'] != '': # No Image indicates a functionally dead webpage with no data
            time.sleep(1)
            moreInfo = getItemInfo(document['item_link'], driver) # Change this to item_link
            document.update(moreInfo)
            time.sleep(1.5)
            
        data.append(document)
        prices.append({
            "name": document.get('product_name'),
            "promo": promo_price,\
            "regular": orig_price,\
                "upc":document['upc'],\
                    'locationId': locationId,\
                    "acquistion_timestamp": acquistion_timestamp,\
                        'isPurchase': True,
                        "quantity": quantity,\
                            "cart_number": document.get('cart_number'),
            }) 

        pprint(document)
        pprint(prices[-1])
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0]) 
    return data, prices




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
    ## full_address_re= re.compile(r".+(GA$|GA\s+\d{5}$)") 
    
    # Wanted Bolded Texts
    fuel_re = re.compile(r"Fuel Points Earned Today:|Fuel Points This Order:")
    cumulative_fuel_re = re.compile(r"Total .+ Fuel Points:")
    last_month_fuel_re = re.compile(r"Remaining .+ Fuel Points:")
    cashier_re = re.compile(r"Your cashier was")
    tax_re = re.compile(r"TAX")
    savings_total_re = re.compile(r"TOTAL SAVINGS \(.+\)")
    sales_total_re = re.compile(r".+BALANCE")


    last_item_index = 0
    weight_switch = ''
    item_re = re.compile(r"^\s*(.+)(\d+\.\d+)[\s|-](B|T|X)$")
    sales_re = re.compile(r'^SC\s+([A-z0-9\s]+)\s*(\d+\.\d+)[\s-]*(B|T|X)?$')
    receipt_calculation_re = re.compile(r'((\d)(\.\d+)?(\D+)?)\s*@\s*(\d+)?\/?(\d+\.\d+)(\/\D+)?')
    order = link[:-6]# .split('/')[-1]
    receipt_document['cart_number'] = order
    receipt_document['checkout_timestamp'] = order.split('~')[2] + " " + order.split('~')[-1][-4:-2] + ":" + order.split('~')[-1][-2:]
    receipt_document['locationId'] = "".join(order.split('~')[:2])
    # Get Receipt Image
    try:
        receipt = driver.find_element(By.CSS_SELECTOR, 'div.imageContainer')
        nodes = receipt.find_elements(By.CSS_SELECTOR, 'div.imageTextLineCenter')
        receipt_document["bin"] = True
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
            elif re.match(cashier_re, text ) != None:
                receipt_document['cashier'] = re.sub(cashier_re, "", text).strip()
            elif re.match(last_month_fuel_re, text) != None:
                receipt_document['last_month_fuel_points'] = re.sub(last_month_fuel_re, "", text)
            elif re.match(payment_type_re,text) != None:
                receipt_document['payment_type'] = text
            elif re.match(savings_total_re, text ) != None:
                receipt_document['total_savings'] = re.sub(savings_total_re, "", text).strip()
            elif re.match(sales_total_re, text ) != None:
                receipt_document['total'] = re.sub(sales_total_re, "", text).strip()
            elif re.match(tax_re,text) != None:
                receipt_document['tax'] = re.sub(tax_re, "", text).strip()
            else:
                if re.match(sales_re, text) != None:
                    if receipt_document['items'][last_item_index].get('sales') == None:
                        name, cost, taxStatus = re.findall(sales_re, text)[0]
                        name = name.strip()
                        receipt_document['items'][last_item_index].setdefault('sales', [])
                        if taxStatus=='':
                            receipt_document['items'][last_item_index]['sales'].append({'item': name, 'cost': float(cost)})
                        else:
                            receipt_document['items'][last_item_index]['sales'].append({'item': name, 'cost': float(cost), 'taxStatus': taxStatus})
                elif re.match(item_re, text)!=None:
                    name, cost, taxStatus = re.findall(item_re, text)[0]
                    name = name.strip()
                    if re.findall(r"\d", name[-1])!=[]:
                        cost = name[-1] + cost
                        name =  name[:-1].strip()
                    rec_obj = {'item': name, 'cost': float(cost), 'taxStatus': taxStatus}
                    if weight_switch:
                        rec_obj['weight_amount'] = float(weight_switch)
                        weight_switch = ''
                    receipt_document['items'].append(rec_obj)
                    last_item_index = receipt_document['items'].index(rec_obj)
                elif re.findall(receipt_calculation_re, text)!=[]:
                    matches = re.findall(receipt_calculation_re, text)[0]
                    weight_receipt = matches[1] + matches[2]
                    weight_switch = weight_receipt    
    except NoSuchElementException:
        ## Reroute Specialized Trips that Fuel Based
        driver.get(link.replace('image', 'detail'))
        time.sleep(5)
        payment_re = re.compile(r'AMEX|DEBIT|VISA')
        try:
            #receipt_document['address'] = driver.find_element(By.CSS_SELECTOR, 'span.kds-Text--l.mb-0').text
            #receipt_document['checkout_timestamp'] = driver.find_element(By.CSS_SELECTOR, 'h2.kds-Heading.kds-Heading--m').text.replace('Fuel', '').strip()
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
            # receipt_document['cart_number'] = link

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
    pprint(receipt_document)
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0]) # bring back to current dashboard page
    return receipt_document

# Trip Level Data : Collection<Items> https://www.kroger.com/mypurchases/api/v1/receipt/details https://www.kroger.com/atlas/v1/purchase-history/details
# Trip and Account Metadata and More Precise Data on the Sales  
# More Precise Item information (UPC to join to receipt), ingredients, ratings, health_info, etc. 


def getMyData(): # https://www.kroger.com/products/api/products/recommendations
    # Process Flow: Setup Browser -> Get Purchases Dashboard -> Collect Cart URLS -> foreach cart getCart(cart_page){contains GetItems} and getReceipt(reciept_page) 
    # Purchase Dashboard, Acquire links for each trip on the page and buttons to next page, get links for each item and finish with receipt acquistion
    # Setup Driver
    client = MongoClient()
    db = client.groceries
    last_scrape = db.prices.find({'isPurchase': True}).sort("acquisition_timestamp")
    last_scrape = dt.datetime.fromtimestamp(max(map(lambda x: x.get('acquistion_timestamp') , last_scrape)))
    options = webdriver.ChromeOptions()  # https://www.kroger.com/atlas/v1/recommendations/v1/better-for-you?filter.gtin13=0007022100718&page.offset=0&page.size=1903
    options.add_argument("start-maximized")
    options.add_argument("disable-blink-features=AutomationControlled")
    # Load Credentials from Browser Profile
    options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options)
    driver.implicitly_wait(3.5)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36"})
    
    testBinary = True
    while testBinary:
        ans = input("press enter to continue")
        if ans == '':
            testBinary=False
        else:
            raise ValueError('No other response allowed')
    time.sleep(5)
    dashboard_url_base = 'https://www.kroger.com/mypurchases?tab=purchases&page='
    dashboard_index = 1
    driver.get(dashboard_url_base + f"{dashboard_index}")
    ### Website SignIn ###
    time.sleep(10.25)
    signInBtn = driver.find_element(By.ID, 'SignIn-submitButton')
    signInBtn.click()
    time.sleep(9.5)
    pages = driver.find_elements(By.CSS_SELECTOR, "nav.kds-Pagination > a")
    last_page = [p.text for p in pages][-1]
    last_page = int(last_page)

    for i in range(1, last_page):
        ##### Trip Selection #####
        driver.get(dashboard_url_base+str(i))
        time.sleep(9)
        trips = driver.find_elements(By.LINK_TEXT, 'See Order Details')
        wait  = random.randint(20, 60)/10
        time.sleep(wait)
        for trip in trips:
            starting_url = trip.get_attribute('href')
            date = starting_url.split('/')[-1].split("~")[2]
            date = dt.datetime.strptime(date, "%Y-%m-%d")
            if date <= last_scrape:
                break
            ### receipt is the same url with detail replaced with image (of receipt)
            receipt_url = trip.get_attribute('href').replace('detail', 'image')
            time.sleep(wait)
            data, prices = getCart(starting_url, driver)
            receipt_document = getReceipt(receipt_url, driver)
            insertData(data, 'items')
            insertData(prices, 'prices')
            insertData(receipt_document, 'trips')
            time.sleep(random.randint(20, 50)/10)
        print(f"Finished with Page {i}")
    driver.quit()

def getDigitalPromotions():
    # grab each digital promotion
    # div.CouponCard-wrapper
        # :: # purchase method availability ['In-store', 'Pickup', 'Delivery', 'Ship']
        # :: ON CARD GET attributes = 'data-brand', 'data-category', 'data-testid'
                # get h2['aria-label'] for amount off for promotion
                # common expressions = 'Save {amount} on {quantity}? {product_names joined by commas or 'or's}'
                # click More Details link
                    # => get div.CouponDetails text for qualifications
                        # => has inner divs with promotion restrictions 
                # div[data-qa='modality-availability-banner']
                    # spans show availability by purchase type with the presence of the class ".font-bold"
                # if available a <section.Qualifying Products> appears
                    # from here it will show brief information based on the items eligable for the sale
                    # shows img, product_name, promotional price, regular price and size
                    # to get each item select ul.ProductListView > li
                    # inside select img attributes src (for upc) and alt (for name)
                    # optional attributes: price promotional, sizing and regular price

                # Promotions Collection: 
                    # type: {digital-coupon, cash-back, six-for-three}
                    # expiresAt: Midnight of expiration date EST
                    # qualifyingPurchaseTypes: ['In-Store', 'Pickup', 'Delivery', 'Ship']
                    # restrictions: ''
                    # promotionCategory : ['categories of sale products']
                    # amount

                
        # get amount off 


    return None


def simulateUser(link):
    neededLinks = {'cashback': {"no": 214, "button": "./requests/server/cashback.png", "confidenceInterval": .66, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -2008, 'initalScroll': -700},\
        'digital': {"no":256, "button": "./requests/server/signIn.png", "confidenceInterval": .6, 'maxCarousel': 4, 'buttonColor': (56, 83, 151), 'scrollAmount': -2000, 'initalScroll': -800},\
            'dollarGeneral': {'no': 126, "button": "./requests/server/addToWallet.png", "confidenceInterval": .7, 'maxCarousel': 3, 'buttonColor': (0, 0, 0), 'scrollAmount': -1700 ,"moreContent": "./requests/server/loadMore.png",\
                 'initalScroll': -1650}}
    # browser up start will be setting user location, navigating to the page, and placing mouse on first object
    # from here: the code will commence
    # start at top of the screen 
    # align all items https://www.kroger.com/savings/cl/coupons/
    iterations = neededLinks[link]["no"] // 12
    iterations = iterations + 1
    if link!='dollarGeneral':
        time.sleep(3)
        pag.scroll(neededLinks[link]['initalScroll'])
        time.sleep(2)

    # find all buttons
    for i in range(iterations):
        buttons = list(pag.locateAllOnScreen(neededLinks[link]['button'], confidence=neededLinks[link]['confidenceInterval'], grayscale=False))
        buttons = [pag.center(y) for i, y in enumerate(buttons) if (abs(buttons[i].left-buttons[i-1].left) > 100) or (abs(buttons[i].top-buttons[i-1].top)>100)] # > 2
        if link=='dollarGeneral':
            buttons = list(filter(lambda x: x.x<1600, buttons))
        print(f"Located {len(buttons)} Items")
        if len(buttons)>12:
            yaxis = list(map(lambda b: b.y, buttons))
            buttons = [x for x in buttons if yaxis.count(x.y) >= neededLinks[link]['maxCarousel']  and (x.y+1 not in yaxis)]
        print(len(buttons), "buttons")
        for b in buttons:
            pag.moveTo(b)
            x, y = pag.position()
            draws = 0
            direction = 1
            print(pag.position())
            if link!='dollarGeneral':
                pag.moveRel(-186, 0, duration=1.5)
                pag.click()
                # escape out of portal
                time.sleep(7.5)
                pag.press('esc')
                pag.moveRel(186, 0, duration=1.5)
            else:
                pag.moveRel(-70, 0, duration=1.5)
                pag.moveRel(0, -125, duration=1.5)
                # expand items
                pag.keyDown('ctrlleft')
                pag.click()
                time.sleep(3)
                # switch to tab
                # pag.keyDown('shiftleft')
                # pag.keyDown('tab')

                pag.keyUp('ctrlleft')
                # pag.keyUp('shiftleft')
                # pag.keyUp('tab')
                time.sleep(6)
                pag.press('pagedown', 3, interval=0.5)
                # escape out of portal
                moreItems = loadMoreAppears()
                while bool(moreItems):
                    button = moreItems
                    pag.moveTo(button.x, button.y, duration=0.5)
                    pag.click()
                    time.sleep(3)
                    pag.press('pagedown', 3, interval=0.5)
                    moreItems = loadMoreAppears()
                pag.keyDown('ctrlleft')
                pag.keyDown('w')
                pag.keyUp('ctrlleft')
                pag.keyUp('w')
                time.sleep(2.5)

        if i==0 and link=='dollarGeneral':
            pag.scroll(neededLinks[link]['initalScroll'])
        else:
            pag.scroll(neededLinks[link]['scrollAmount'])
        print('finished row {}; {} to go; mouse currently @ {} :: {} seconds left'.format(i, iterations-i, pag.position(), (time.perf_counter()/(i+1))*(iterations-i)))
        time.sleep(2)

    print(f"Processed {neededLinks[link]['no']} in {time.perf_counter()} seconds")
    return None

def newOperation(dataFolder):
    for folder, subfolders, files in os.walk(dataFolder):
        for file in files:
            if file.endswith('FD.json'):
                print(file, files)
                with open(folder+'/'+file, 'r', encoding='utf-8') as f:
                    data =json.loads(f.read())
                coups = []
                items = []
                data = data[0].get('data')
                for d in data:
                    if 'clipType' in d.keys():
                        # existing coupon schema:
                            # uuid: id, krogerCouponNumber
                            # qualifying products: productUPCs
                            # qualifying products categories: brandName, categories
                            # coupon categories: type, cashbackCashoutType, isSharable, forCampaign, specialSavings
                            # web elems: imageUrl, title, requirementDescription
                            # dates: startDate, expirationDate
                            # values: redemptionsAllowed, requirementQuantity, value, 
                        # dg coupon schema
                            # uuid: OfferGS1, OfferID, OfferID=mainCouponId,  OfferCode,
                            # values: RewardQuantity, RedemptionLimitQuantity, MinQuantity, RewardedOfferValue, 
                            # coupon categories: isManufacturerCoupon, OfferType, RecemptionFrequency, BrandName, Companyname
                                # OfferSummary = "Save $3.00", TargetType, RewardedCategoryName
                            # web elems: Image1, Image2, OfferDescription, offerDisclaimer, 
                            # dates: OfferActivationDate, OfferExpirationDate   
                            # TODO: qualifying products = in parent element url
                        # family dollar coupon schema
                            # uuid: mid, 
                            # qualifying products: nihil 
                            # qualifying products categories: nihil 
                            # coupon categories: brand, category{}, clipType, offerType, redemptionGating, redemptionChannels, group, groups, status, ?tags, ?badge
                            # web elems: imageUrl, enhancedImageUrl, description{text}, shortDescription{text}, terms, type{text='mfg'}, 
                            # dates: clipEndDate, clipStartDateTime, clipEndDateTime, clipStartDate, expirationDate, expirationDatetime, redemptionStartDatetime
                            # coupon values: clippedCount, popularity,  minPurchase, offerSortValue, valueSort, valueText, redemptionsPerTransaction, isActive, ?value, 
                        
                        coups.append(d)

                        # for t in d.get('Coupons'):
                        #     coups.append(t)
                    elif 'Items' in d.keys():       
                        for t in d.get('Items'):
                            items.append(t)
                        
                o = {}
                #print(coups)
                for i in coups:
                    for k in i.keys():
                        if k not in o.keys() and bool(i[k]):
                            o[k]=1
                        elif k in o.keys() and bool(i[k]):
                            o[k]+=1
                pprint(sorted(o.items(), key=lambda x: x[1], reverse=True))
                pprint(list(filter(lambda x: x.get('badge'), coups)))
                o = {}
                # for i in items:
                #     for k in i.keys():
                #         if k not in o.keys() and bool(i[k]):
                #             o[k]=1
                #         elif k in o.keys() and bool(i[k]):
                #             o[k]+=1
                # pprint(sorted(o.items(), key=lambda x: x[1], reverse=True))

    # need to then break down [the see order details link]

    return None

def loadMoreAppears(png='./requests/server/moreContent.png'):
    locations = list(pag.locateAllOnScreen(png, confidence=.6, grayscale=False))
    locations = list(map(lambda x: pag.center(x), locations))
    i = 0
    locations = list(filter(lambda x: x.y>418 and x.y<560, locations))
    if locations:
        loc = locations[i]
        x, y = loc
        color = pag.pixel(int(x), int(y))
        if color==(0, 0, 0):
            return loc
        else:
            i+=1

    return None

def deconstructDollars(file='./requests/server/collections/dollargeneral/digital060422DG.json'):
    # Promotions.categories <List> -> {Condiments & Sauces, Beverages, Pasta Sauces Grain, International, Cleaning Products, Baby, Apparel, General, Beauty, Garden & Patio, Meat & Seafood,\
            # Home Decor, Deli, Health, Breakfast, Bakery, Sporting Goods, Pet Care, Hardware, Entertainment, Gift Cards, Dairy, Personal Care, Canned & Packaged, Candy, Tobacco,
            # Frozen, Produce, Snacks, Adult Beverages, Health & Beauty, Baking Goods, Kitchen, Natural & Organic, Electronics, Party}
        # Promotions.type <String> -> {CASH_BACK, STANDARD}
        # Promotions.cashbackCashoutType <String> -> {UNRESTRICTED, NON_RETAILER_ONLY}
        # Promotions.specialSavings <List[<Dicts>]>.name -> {HOTP5: Use up to 5 Times in a Single Transaction, 5X: <-ibid, 4XGCEVENT: GiftCard/Fuel Points, HOTP3:Use Up to Five Times in a Single Transaction, HOMECHEF:Private Label Ready Made Meals,\
            # BPCS:Beauty & Personal Care Savings, SFY:Personalized Savings, CL:Pickup&Delivery Only, NSK:<-ibid, WDD:Weekly Digital Deals}
        # Promotions.modalities <List> -> {DELIVERY, PICKUP, IN_STORE, SHIP}
        # Promotions.redemptionsAllowed -> {-1, 1, 2, 3, 4, 5} <- -1 often corresponds to multiple redemptions in a single trip, should change to reflect this

        # family dollar:
            # all available :
                # XclippedCount => social amount coupon clipped <Int>
                # Xpopularity  => social amount coupon clipped <Int>
                # Xbrand => Company Promotions <String>
                # Xcategory => Code value, name and key for promotional items and promtion <HashMap> 
                # XclipEndDate => ISO Datetime String w/o Time for promotion clip end <HashMap>
                # XclipStartDate => ISO Datetime String w/o Time for promotion clip start <HashMap>
                # XclipType => clip type  <String> {'consumer clip'}
                # Xdescription => "Save ${valueSort} on any ONE ..."<String> ~= shortDescription w/ more exclusions/terms baked in short form
                # XexpirationDate => ISO Datetime String w/o Time for promotion redemption end <HashMap>
                # XimageUrl => href for Promotion Image <String>
                # XminPurchase => Amount Necessary for promotion to execute <Integer>
                # XofferSortValue => String Amount of valueSort of Promotion <String>
                # XofferType => Promotion Category <String> {bogo, cents off, order total, percent off}
                # XredemptionChannels => Promotion Redemption Category <List> {coupon}
                # XredemptionGating => Brand Gating Switch  <String> {NO_GATING}
                # XshortDescription =>  "Save ${valueSort} on any ONE ..."<String>
                # Xterms => Manufacture Legalese <String>
                # Xtype => Coupon Type <String> {mfg, store}
                # Xvalue => cents amount of offer or percentage off for offer <Integer>
                # XvalueSort => Best Value Best Proxy for Coupon (ie. better than value) <Integer>
                # XvalueText => "Save ${valueSort/100}" <String>
                # Xmdid => uuid for promotion <Integer>
                # Xgroup => <String> {'available'}
                # Xgroups => <List> {'available'}
                # Xstatus => <String> {'available'}
                # XenhancedImageUrl => Additional IMG Data for Promotion, Higher Resolution <String>
                # XredemptionsPerTransaction => Amount of Times Coupon Can Be Used in A Transaction <Integer>
                # Xclipped => User Has Clipped Coupon to Account/Wallet <Boolean>
                # XclipStartDateTime => ISO Datetime String w/ Time for promotion clip start <HashMap>
                # XclipEndDateTime => ISO Datetime String w/ Time for promotion clip end <HashMap>
                # XisActive => Coupon Can Still Be Used As of Time of Acquisition <Boolean>
                # XexpirationDateTime => ISO Datetime String w/ Time for promotion redemption end <HashMap>
                # XredemptionStartDateTime  => ISO Datetime String w/ Time for promotion redemption start <HashMap>
                # X?tags => Family Dollar's Product Categories / slugs <List>
                # X?badge => Visual Code for Web Widgets <String> {'', 'new', 'expiring'}
                # X?clippedDates => User Clip Dates for Specific Promotion <List>
                # X?redeemedDates => User Redemption Dates for Promtoion <List>
                # X?contextTypes =>  all empty <List>
                # X?clipRedemptionChannel => all empty <String>

        # dollar general:
            # all available;
                # XDiscountIndicator={0} <Int>,
                # XOfferID => UNIQUE KEY TO CONNECT TO ITEMS api request <HEX STRING>
                # XOfferCode => unique string id to link offer to offer's product page <String>
                # XImage1 => unique string
                # XImage2 => unique string
                # XOfferType => {'BuyXGetYFree', 'AmountOff', 'PercentOff'} <String>
                # XRecemptionFrequency => {'OnceTimeOffer'} <String>
                # XOfferActivationDate => Date When Coupon Can Be Applied <Date String w/ TZ>
                # XOfferExpirationDate => Date When Coupon Ends <Date String w/ TZ> 
                # XOfferDescription => 'Save {amt} on {product}' <String>
                # XBrandname => Brand of Products Which Coupon Applies, <String>
                # XCompanyname => Company That Owns Brand <String>
                # XOfferSummary => Short Representation of Deal, similar to Kroger's Title, "SAVE $1.00", "$1.50 OFF", "Buy 4, Get 1 Free" <String>
                # XIsAutoActivated => {0} <Int>
                # XTargetType => "recommended" <String>
                # XActivationDate => User DT when clippes <Date w/TZ>
                # XRedemptionLimitQuantity => {1} <Integer> 
                # XMinBasketValue => {0} <Integer>
                # XMinTripCount => {0} <Integer>
                # XTimesShopQuantity => {0} <Integer>
                # XMinQuantity => {1, 2, 3, 4, 5} <Integer>
                # XRewaredOfferValue => Specific Amount Saved with Coupon <Float/Int>
                # XRewaredCategoryName => <String> Product Category {'Baby & Toddler', 'Beverages', 'Personal Care & Beauty', 'Baby Care','Household & Paper Products', 'Foods', 'Pet Care', 'Household', 'Dollar General', 'Personal Care', 'Flowers & Gifts', 'Health Care'}
                # XRewardQuantity => Items rewarded by Coupon Redemption <Integer> {0, 1}
                # XIsClipped => Customer specific coupon action <Int> {0, 1}
                # XIsManufactureCoupon => Coupon Originator <Int> {0, 1}
                # X?OfferDisclaimer => Legalese for Coupon <String> 
                # X?OfferFinePrint => all empty <String>
                # X?OfferGS1 => Not all have gs1, OfferCodes Have X in them  <String>
                # X?UPCs => all empty <List>
                # X?OfferFeaturedText => all empty <String>
                # X?Visible => all empty <String>
                # X?AssociationCode => all empty
                # X?MinQuantityDescription => all empty

    # type summarys:
            # strings: krogerCouponNumber, brandName, type, ?cashbackCashoutType, shortDescription, requirementDescription, imageUrl, ?longDescription,
                # value[float as value]    
            # dates: startDate, expirationDate [as UtcTimestamps with timezones]
            # integers: id, requirementQuantity, redemptionsAllowed
            # lists: categories, modalities
            # list of dicts: ?specialSavings
            # booleans: ?isSharable, ?forCampaign,

            # integer: clippecCount, popularity, minPurchase, value, valueSort, mdid, group, status, redemptionsPerTransaction, 
            # string: brand, clipType, description, imageUrl, offerSortValue, offerType, redemptionChannels, redemptionGating, shortDescription, terms, type,
                # valueText, enhancedImageUrl, badge, 
            # dict: category, clipEndDate, clipStartDate, expirationDate, clipStartDateTime, clipEndDateTime, expirationDateTime, redemptionStartDateTime  
            # list: groups, tags, !!clippedDates, !!redeemedDates, !!contextTypes, !!clip Redemption Channels 
            # bool: clipped, isActive

            # integer: DiscountIndicator, IsAutoActivated, RedemptionLimitQuantity, MinBasketValue, MinTripCount, TimesShopQuantity, MinQuantity, RewardQuantity
                # IsClipped, IsManufactureCoupon,   
            # float: RewaredOFfferValue, 
            # string: OfferID, OfferCode, Image1, Image2, OfferType, RecemptionFrequency, OfferActivationDate, OfferExpirationDate, OfferDescription, Brandname,
                # Companyname, OfferSummary, TargetType, !!ActivationDate, RewardedCategoryName, ?OfferDisclaimer, ?OfferGS1, !!OfferFinePrint, !!OfferFeaturedText, !!Visible, !!AssociationCode,
                # !!MinQuantityDescription
            # list: !!UPC

    # TODO Decompose::-> To Equivalent Kroger Document Level Attributes
        # items: Description, UPC, Image, IsGenericBrand, IsSellable, IsBopisEligible, Ratings {AverageRating, RatingReviewCount, }, Category(| separated string)
            # shipToHomeQuantity, isShipToHome
        # inventories: AvailableQty, AvailableStockStore, InventoryStatus,
        # prices: Price, OriginalPrice,
        # quasiPriceModifiers: DealsAvailable, DealStatus, SponsoredProductId, SponsoredAgreementId, SponsoredDisplayRow
        # <bool>: CartQuantity,                         


    with open(file, 'r', encoding='utf-8') as fd:
        data = sorted(json.loads(fd.read()), key=lambda x: x.get('url'))
        products = list(filter(lambda p: 'eligibleProductsResult' in p.keys(), data))
        coupons = filter(lambda p: 'Coupons' in p.keys(), data)
        storeID = file.split('/')[-2]
    newProducts=[]
    newCoupons=[]
    newPrices = []
    newInventory = []
    storeCode = ''
    booleans = {'prices': {'IsSellable': 'IN_STORE', 'IsBopisEligible': 'PICKUP', 'isShipToHome': 'SHIP'}, 'items': {'IsGenericBrand', 'IsBopisEligible', 'isShipToHome'}}
    inventoryKeys= {'1': 'TEMPORARILY_OUT_OF_STOCK', '2': "LOW", "3": 'HIGH'}
    productsForCoupons = {}
    for item in products:
        utcTimestamp = item["acquisition_timestamp"]
        url = item['url']
        params = urllib.parse.parse_qsl(url)
        if bool(storeCode)==False:
            storeCode = list(filter(lambda x: x[0]=='store', params))[0][1]
        couponId = list(filter(lambda x: x[0].endswith('couponId'), params))[0][1]
        itemList = item.get('eligibleProductsResult').get('Items')
        for i in itemList:
            modalities = []
            for key, val in booleans.get('prices').items():
                if i[key]:
                    modalities.append(val)
            if couponId not in productsForCoupons.keys():
                productsForCoupons[couponId] = {i.get('UPC')}
            else:
                productsForCoupons[couponId].add(i.get('UPC'))

            # deconconstuct to prices
            newPrices.append({'value': i.get('OriginalPrice'), 'type': 'Regular', 'isPurchase': False, 'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
            if i.get('OriginalPrice')!=i.get('Price'):
                newPrices.append({'value': i.get('Price'), 'type': 'Sale', 'isPurchase': False, 'locationId': storeCode, 'utcTimestamp': utcTimestamp,\
                'upc': i.get('UPC'), 'quantity': 1 , 'modalities': modalities, })
            # deconstruct to inventories
            itemStatus = inventoryKeys[str(i.get('InventoryStatus'))]
            newInventory.append({'stockLevel': itemStatus, 'availableToSell': i.get('AvailableStockStore'), 'locationId': storeCode, 'utcTimestamp': utcTimestamp, 'upc': i.get('upc')})     
            # deconstuct into Items
            itemDoc = {'description': i.get('Description'), 'upc': i.get('UPC'), 'images': [{'url': i.get('image'), 'perspective': 'front', 'main': True, 'size': 'xlarge'}],\
                'soldInStore': i.get('IsSellable'),"modalities": modalities}

            if i.get('RatingReviewCount')!=0:
                itemDoc['ratings'] = {'avg': i.get('AverageRating'), 'ct': i.get('RatingReviewCount')}
 
            if 'Category' in i:
                itemDoc['categories'] = i.get('Category').split('|')
            
            for ky in booleans.get('items'):
                if bool(i[ky]):
                    itemDoc[ky] = i[ky]
                if ky=='isShipToHome' and bool(i[ky]):
                    print(i)
                    itemDoc['maximumOrderQuantity'] = i.get('shipToHomeQuantity')
            
            newProducts.append(itemDoc)


    for coupon in coupons:
        if 'acquistion_timestamp' in coupon.keys():
            utcTimestamp = coupon.pop('acquistion_timestamp')
        else:
            utcTimestamp = os.path.getctime(file)

        if storeID == 'dollargeneral':
            for coup in coupon.get('Coupons'):
                newC = {}
                # ids => OfferID=id, OfferCode=offerCode, bool(get OfferGS1)
                newC['id'] = coup.get('OfferID')
                newC['offerCode'] = coup.get('OfferCode')
                if bool(coup.get('OfferGS1')):
                    newC['offerGS1'] = coup.get('OfferGS1')
                # Brandname => brandName, CompanyName => companyName, offerType=> type
                # OfferSummary + OfferDescription => shortDescription
                # OfferDisclaimer => terms
                # RewaredCategoryName => categories[]
                newC['brandName'] = coup.get('BrandName') 
                newC['companyName'] = coup.get('CompanyName') 
                newC['offerType'] = coup.get('OfferType')
                if bool(coup.get('OfferDisclaimer')):
                    newC['terms'] = coup.get('OffeDisclaimer') 
                newC['isManufacturerCoupon'] = coup.get('IsManufacturerCoupon') 
                newC['categories'] = [coup.get('RewaredCategoryName')] 
                # OfferActivationDate => startDate  %Y-%m-%dT%H:%M:%S
                # OfferExpirationDate => endDate %Y-%m-%dT%H:%M:%S
                newC['startDate'] = dt.datetime.strptime(coup.get('OfferActivationDate'), '%Y-%m-%dT%H:%M:%S').timestamp()
                newC['endDate'] = dt.datetime.strptime(coup.get('OfferExpirationDate'), '%Y-%m-%dT%H:%M:%S').timestamp()
                # RewaredOfferValue => value
                newC['value'] = coup.get('RewaredOfferValue')
                # MinQuantity => requirementQuantity 
                newC['requirementQuantity'] = coup.get('MinQuantity')
                # RedemptionLimitQuantity => redemptionsAllowed
                newC['redemptionsAllowed'] = coup.get('RedemptionLimitQuantity')
                # + MinTripCount, MinBasketValue, TimesShopQuantity, RecemptionFrequency
                newC['redemptionFreq'] = coup.get('RecemptionFrequency')
                # Image1 => imageUrl, +Image2
                newC['imageUrl'] = coup.get('Image1') 
                newC['imageUrl2'] = coup.get('Image2') 
                booleans = ['MinTripCount', 'MinBasketValue', 'TimesShopQuantity']
                for b in booleans:
                    if bool(coup.get(b)):
                        newC[b] = coup.get(b)
        
        # !!! Family Dollar
        elif storeID == 'familydollar':
        # mid => id
            newC['id'] = coup.get('mid')
        # brand => brandName
            newC['brandName'] = coup.get('brand')
        # offerType => type
            newC['type'] = coup.get('offerType')
        # description => shortDescription
            newC['shortDescription'] = coup.get('description')
        # terms => terms
            newC['terms'] = coup.get('terms')
        # category.get('name') => categories
            newC['categories'] = coup.get('category').get('name')
        # [x.replace('fd-', '').strip().title() for x in tags] +=> categories
            newC['categories'].extend([x.replace('fd-', '').strip().title() for x in coup.get("tags")])
        # redemptionStartDateTime => startDate %Y-%m-%dT%H:%M:%S
        # redemptionEndDateTime => expirationDate %Y-%m-%dT%H:%M:%S
            newC['startDate'] = dt.datetime.strptime(coup.get('redemptionStartDateTime'), '%Y-%m-%dT%H:%M:%S').timestamp()
            newC['endDate'] = dt.datetime.strptime(coup.get('redemptionEndDateTime'), '%Y-%m-%dT%H:%M:%S').timestamp()
        # clipStartDateTime %Y-%m-%dT%H:%M:%S
        # clipEndDateTime
            newC['clipStartDate'] = dt.datetime.strptime(coup.get('clipStartDateTime'), '%Y-%m-%dT%H:%M:%S').timestamp()
            newC['clipEndDate'] = dt.datetime.strptime(coup.get('clipEndDateTime'), '%Y-%m-%dT%H:%M:%S').timestamp()
        # offerSortValue => value
            newC['value'] = coup.get('offerSortValue')
        # minPurchase => requirementQuantity
            newC['requirementQuantity'] = coup.get('minPurchase')
        # redemptionsPerTransaction => redemptionsAllowed
            newC['redemptionsAllowed'] = coup.get('redemptionsPerTransaction')
        # imageUrl => imageUrl, + enchancedImageUrl
            newC['imageUrl'] = coup.get('imageUrl')
            newC['enhancedImageUrl'] = coup.get('enhancedImageUrl')
            if coup.get('type')=='mfg':
                newC['isManufacturerCoupon'] = True
            else:
                newC['isManufacturerCoupon'] = False
        
        # type => isManufacturerCoupon if type=mfg else False
        # +socials :: popularity, clippedCount
            newC['popularity'] = coup.get('popularity')
            newC['clippedCount'] = coup.get('clippedCount')

        newCoupons.append(newC)
        


    return None

def switchUrl(x=327, y=59, url="https://www.dollargeneral.com/dgpickup/deals/coupons?"):
    pag.moveTo(x, y, duration=2.2)
    pag.click(clicks=2, interval=.5)
    clip.copy(url)
    time.sleep(1)
    pag.keyDown('ctrlleft')
    pag.keyDown('v')
    pag.keyUp('ctrlleft')
    pag.keyUp('v')
    return None    

def updateGasoline(files=['061722.json']):
    for file in files:
        with open(f'./requests/server/collections/kroger/trips/{file}', mode='r', encoding='utf-8') as f:
            j = json.loads(f.read())
            tripsData = []
            indices = '' 
            for gi, t in enumerate(j):
                if 'mypurchases' in t.get('url'):
                    for trip_index, trip in enumerate(t.get('data')):
                        for item_index, item in enumerate(trip.get('items')):
                            if item.get('quantity')==0:
                                indices = gi, trip_index, item_index

           
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['pricePaid'] = round(j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['pricePaid']+j[indices[0]]['data'][indices[1]]['items'][indices[2]]['pricePaid'], 2)
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['totalSavings'] = round(j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['totalSavings']+j[indices[0]]['data'][indices[1]]['items'][indices[2]]['totalSavings'], 2)
            j[indices[0]]['data'][indices[1]]['items'][indices[2]-1]['priceModifiers'].extend(j[indices[0]]['data'][indices[1]]['items'][indices[2]]['priceModifiers'])
            j[indices[0]]['data'][indices[1]]['items'].pop(indices[2])
        with open(f'./requests/server/collections/kroger/trips/{file}', mode='w', encoding='utf-8') as f:
            f.write(json.dumps(j))

    return None

#updateGasoline()
#deconstructDollars()
#newOperation('./requests/server/collections/digital/dollars')
######## SCRAPING OPERATIONS # # # # # ## #  # ## # # # # # # # # #  ## # # 
# getMyData() 
# getDigitalPromotions()
#simulateUser("dollarGeneral")
# newOperation()
#switchUrl()