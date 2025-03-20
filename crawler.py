from selenium import webdriver
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

def open_facebook():
    driver = setup_driver()
    driver.get("https://www.facebook.com")
    time.sleep(5)
    print("Facebook Page Open Ho Gaya!")
    driver.quit()

if __name__ == "__main__":
    open_facebook()