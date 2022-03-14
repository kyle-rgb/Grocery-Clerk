
import os, sys, math, time, datetime as dt, pprint, re

import pandas as pd, numpy as np, time, json
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Get Purchases - Automation via Selenium

options = webdriver.ChromeOptions() 
options.add_argument("start-maximized")
options.add_argument("disable-blink-features=AutomationControlled")
# Load Credentials from Browser Profile
options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"})
time.sleep(2)
driver.get('')
time.sleep(3.5)
# Sign-In to Profile
# elem = driver.find_element(By.ID, 'SignIn-submitButton')
# elem.click()
# time.sleep(5)
# Get to My Trip Details
# elems = driver.find_elements(By.LINK_TEXT, 'See Order Details')
# print(elems)
# for e in elems:
#     print(e.get_attribute('href'))
#time.sleep(2)

# Iterate Through Pages, then press <button aria-label='Next page'>

# Go Into Each Trip's Details
def getTrip():
    # Trip Level:
    # Store Location
    # Purchase Type (pickup, delivery, online, instore etc.)
    # Total Spent, Total Aggregate Savings
    # Items: {An Object of Objects}
        # Item:
            # Image
    pass

def getReceipt():
    # Marked By SC but does not have specialty DOM tags or classes, all entries exist in rows and will need to be pulled out via RegEx
    # Receipt can tap into elevated Savings Type (eCpn=Loaded App Coupon, Mega Event Savings=Limited Savings Event, KROGER SAVINGS=Regular Plus Card Savings)
    # Could Also Get Kroger's shortName for Items
    # Date and time of checkout, location of store, type of payment, savings breakdown (STR CPN & KRO PLUS SAVINGS), TOTAL COUPONS, TOTAL SAVINGS (\d+ pct.), checkout lane / cashier,
    # Fuel Points Earned Today (Total-Tax), Total Month Fuel Points, Remaining Fuel Points from Last Month 
    # Additional Rewards Spending, Additional Rewards Expiration Date
    
    receipt_document={}
    # Wanted Not Bolded Text
    payment_type_re= re.compile(r".+Purchase\s*")
    full_address_re= re.compile(r".+GA.+") # <- Would Need to Edit for Additional States
    
    # Wanted Bolded Texts
    fuel_re = re.compile(r"Fuel Points Earned Today:.+")
    cumulative_fuel_re = re.compile(r"Total [January|February|March|April|May|June|July|August|September|November|December] Fuel Points:.+")
    last_month_fuel_re = re.compile(r"Remaining [Feb] Fuel Points:.+")
    checkout_time_re = re.compile(r"Time:.+")
    # Get Receipt Image
    receipt = driver.find_element(By.CSS_SELECTOR, 'div.imageContainer')
    i = 0
    bold_nodes = receipt.find_elements(By.CSS_SELECTOR, 'div.imageTextLineCenter.bold') # All Savings, but Also Tax, Balance and Saving Aggregations
    nonbold_nodes = receipt.find_elements(By.CSS_SELECTOR, 'div.imageTextLineCenter')
    metastore_info = receipt.find_elements(By.CSS_SELECTOR, "span[aria-label='StoreHeader'] > div > div")
    # Iterate through nodes get ones who match the re's and assign them the proper name to the return document
    for bn in bold_nodes:
        # TODO: Parse Bold Terms with Selected RegExs
        # TODO: Match Sales w/ Items (Could be Done Via Price Matching w/ Exceptions for Same Prices Since Receipt Names are abbreviations)
        receipt_document.setdefault('bolds', [])
        receipt_document['bolds'].append(bn.text)
    for node in nonbold_nodes:
        if re.match(payment_type_re,node.text) != None:
            receipt_document['payment_type'] = node.text
        elif re.match(full_address_re, node.text) != None:
            receipt_document['address'] = node.text
    
    for row in metastore_info:
        text = row.text.strip()
        if text != "":
            receipt_document['row' + str(i)] = text
        i+=1

    pprint.pprint(receipt_document)
    


    return None


def getCart():
    #web_elem.click()
    time.sleep(2)
    data = []
    items = driver.find_elements(By.CSS_SELECTOR, 'div.PH-ProductCard-productInfo')
    # Find all products as List
    for we in items:
        document = {}
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
            document['item_link'] = we.find_element(By.CSS_SELECTOR, 'span.kds-Text--m.PH-ProductCard-item-description.font-secondary.heading-s.mb-4 > a').get_attribute('href')
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

        data.append(document)
    return data

    

cart = getCart()
pprint.pprint(cart)
time.sleep(2)
driver.get('')
time.sleep(3.5)
cart = getCart()
pprint.pprint(cart)



# getReceipt()

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