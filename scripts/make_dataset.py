
import os, sys, math, time, datetime as dt

import pandas as pd, numpy as np, time, json
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# client = MongoClient()
# print(client.database_names())

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
driver.get('https://www.kroger.com/mypurchases')
time.sleep(3.5)
# Sign-In to Profile
elem = driver.find_element(By.ID, 'SignIn-submitButton')
elem.click()
time.sleep(5)
# Get to My Trip Details
elems = driver.find_elements(By.LINK_TEXT, 'See Order Details')
print(elems)
for e in elems:
    print(e.get_attribute('href'))
time.sleep(2)

# Iterate Through Pages, then press <button aria-label='Next page'>


# Go Into Each Trip's Details

# Trip Level:
    # Store Location
    # Purchase Type (pickup, delivery, online, instore etc)
    # Total Spent, Total Aggregate Savings
    # Items: {An Object of Objects}
        # Item:
            # Image
def getCart(web_elem):
    web_elem.click()
    time.sleep(4)
    data = []
    data.append(driver.find_element(By.CSS_SELECTOR, 'img.kds-Image-img').get_attribute('src'))
            # Link to Product :: Link to Item Ends with UPC which Can Help Compare Same Items Across Different Stores for Future Price Watching
    data.append(driver.find_element(By.CSS_SELECTOR, 'a.kds-Link--inherit').get_attribute('href'))
            # Name of Product :: Interestingly there seems to be Brand Information Coded Into the Name, More Data!
    data.append(driver.find_element(By.CSS_SELECTOR, 'a.kds-Link--inherit').text)
            # Item Description Weight or Volume
    data.append(driver.find_element(By.CSS_SELECTOR, 'span.PH-ProductCard-item-description-size').text)
            # Item Quantity and   # Price per Item
    data.append(driver.find_element(By.CSS_SELECTOR, 'span.kds-Text--s').text)
    try:
        # Promotional Price {span class="kds-Price-promotional-dropCaps"}
        data.append(driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text)
        data.append(driver.find_element(By.CSS_SELECTOR, 's.kds-Price-original').text)
    except NoSuchElementException:
        data.append(driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text)
        data.append(driver.find_element(By.CSS_SELECTOR, 'mark.kds-Price-promotional').text)
        
            
            # Regular Price {s class="kds-Price-original"}
    

    time.sleep(2)

    driver.quit()

    return data

cart = getCart(elems[1])
print(cart)


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