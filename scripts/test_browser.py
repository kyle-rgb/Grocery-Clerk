from selenium import webdriver
import time

options = webdriver.ChromeOptions() 
options.add_argument("start-maximized")
options.add_argument("disable-blink-features=AutomationControlled")
# Load Credentials from Browser Profile
options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
# Check for Cookies
# TODO: Add Kroger Cookies to Browser When Executing Long Script
driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options)
time.sleep(10)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
cookie = driver.execute_script("document.cookie")
print(cookie)
driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"})
time.sleep(2)