from multiprocessing import Process
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys





options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome("./chromedriver/chromedriver", chrome_options=options)
url = "https://web.telegram.org"
driver.get(url)
sleep(1)
phone_country = driver.find_element_by_name("phone_country")
phone_country.send_keys(Keys.CONTROL + "a")
phone_country.send_keys("+7")
phone_number = driver.find_element_by_name("phone_number")
phone_number.send_keys("9778486184")
phone_number.send_keys(Keys.ENTER)

driver.find_element_by_class_name("btn-md-primary").send_keys(Keys.ENTER)