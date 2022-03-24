from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import InvalidArgumentException
import time



def run_browser_tests():
    options = webdriver.ChromeOptions() 
    options.add_argument("start-maximized")
    options.add_argument("disable-blink-features=AutomationControlled")
    # Load Credentials from Browser Profile
    options.add_argument("user-data-dir=C:\\Users\\Kyle\\AppData\\Local\\Google\\Chrome\\User Data")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome("../../../Python/scraping/chromedriver99.exe", options=options, keep_alive=True)
    time.sleep(2)
    driver.get("https://www.kroger.com")
    time.sleep(7)
    return driver
    



def attach_to_session(executor_url, session_id):
    # REFERNCE: https://web.archive.org/web/20171129014322/http://tarunlalwani.com/post/reusing-existing-browser-session-selenium/
    original_execute = WebDriver.execute
    def new_command_execute(self, command, params=None):
        if command == 'NewSession':
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return original_execute(self, command, params)
    # Patch the function b4 creating the driver object
    WebDriver.execute = new_command_execute
    driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    driver.session_id = session_id
    # Replace the patced function with original function
    WebDriver.execute = original_execute
    return driver.execute_script


try:
    driver = run_browser_tests()
    url = driver.command_executor._url
    session_id = driver.session_id
    driver.get('https://www.kroger.com/mypurchases') 
    time.sleep(6)
    signInBtn = driver.find_element(By.ID, 'SignIn-submitButton')
    signInBtn.click()
    time.sleep(3)
    driver.quit()
except: # Leave Session Open for reconnection if error occurs
    attach_to_session(url, session_id)


