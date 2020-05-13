from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import re, os, time, zipfile, sys

import util

errHandle = util.ErrHandle()

url = r'https://ru.idm.oclc.org/login?url=http://www.nexisuni.com'
searchTerms = r'corona'
root = r'd:/etc/LexisNexis'
path_to_chromedriver = root + r'/chromedriver/chromedriver.exe'
download_folder = root + r'/download'
dead_time = 300

try:
    chromeOptions = webdriver.ChromeOptions()
    prefs = {"download.default_directory" : download_folder}
    chromeOptions.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(executable_path = path_to_chromedriver, options=chromeOptions)
    browser.set_window_size(1800, 1000)

    # Go to the NexisUni url
    browser.get(url)
    # Get Page Info
    browser.find_element_by_xpath('//*[@id="searchTerms"]').send_keys(searchTerms)
    browser.find_element_by_xpath('//*[@id="mainSearch"]').click()
    N_temp = browser.find_element_by_xpath('//*[@id="content"]/header/h2/span').text
    time.sleep(5)
    total_number = int(''.join(re.findall(r'[0-9]', N_temp)))
    total_page = int(np.ceil(total_number/10))
    file_digit = len(str(total_page)) * 2 + 1
    # Sort by Date
    start_time = time.time()
    while True:
        if time.time() - start_time > dead_time:
            raise Exception()
        try:        
            browser.find_element_by_xpath('//*[@id="results-list-delivery-toolbar"]/div/ul[2]/li/div/button').click()
            break
        except WebDriverException: 
            pass             
    browser.find_element_by_xpath('//*[@id="results-list-delivery-toolbar"]/div/ul[2]/li/div/div/button[4]').click()
except:
    msg = errHandle.get_error_message()
    errHandle.DoError("main")


