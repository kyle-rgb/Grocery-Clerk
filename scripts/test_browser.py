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
driver.execute_script("Object.defineProperty(navigator, 'webdriver', false")
cookie = driver.execute_script(f"document.cookie")
# print(driver.execute_script(f"navigator.plugins"))
# print(driver.execute_script(f"navigator.languages"))
print(cookie)
time.sleep(2)

driver.get("https://www.kroger.com")
cookie = driver.execute_script("document.cookie")
time.sleep(2)
print(cookie)
time.sleep(5)    
driver.get('https://www.kroger.com/mypurchases') 
time.sleep(6)
signInBtn = driver.find_element(By.ID, 'SignIn-submitButton')
signInBtn.click()
time.sleep(3)
driver.quit()







