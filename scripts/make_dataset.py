
import os, sys, math, time, datetime as dt

import pandas as pd, numpy as np, time
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By

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
driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
driver.get('https://www.kroger.com/mypurchases')
time.sleep(10)
# Sign-In to Profile
elem = driver.find_element(By.ID, 'SignIn-submitButton')
elem.click()
time.sleep(4)
# Get to My Trip Details
elems = driver.find_elements(By.LINK_TEXT, 'See Order Details')
driver.quit()

# Go Into Each Trip's Details

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