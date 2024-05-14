from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from  datetime import datetime

PAGE_TIMEOUT = 10
DEBUG = 1

# from selenium.webdriver.support.select import Select
# from bs4 import BeautifulSoup
## from selenium.webdriver.chrome.options import Options


device_types = [
    ('корректор', 'ЭК270'),
    ('корректор', 'ТК220'),
    ('комплекс', 'СГ-ТКР'),
    ('комплекс', 'СГ-ЭКР'),
]

"""
Produce correct ending for noun of the second declension
"""
def ending(value):

    end = 'ов'
    if value in (11, 12, 13, 14):
        end = 'ов'
    else:
        if value % 10 in (2, 3, 4):
            end = 'а'
        elif value % 10 == 1:
            end = ''

    return end


# WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "css_selector"), "2"))


def wait_for_element(driver, path):
    try:
        element_present = EC.presence_of_element_located((By.XPATH, path))
        element = WebDriverWait(driver, PAGE_TIMEOUT).until(element_present)
    except TimeoutException:
        print("Page download error")
        element = None
    return element

def main():
    # download strategy: none
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'none'

    # get web driver
    driver = webdriver.Chrome(options=options)

    # set timeout for page opening
    driver.set_page_load_timeout(PAGE_TIMEOUT)

    first_page = True

    for device_type in device_types:
        # make URL for each device type
        url = f'https://fgis.gost.ru/fundmetrology/cm/results?filter_mi_mitype={device_type[1]}'

        if DEBUG:
            print(url)

        try:
            driver.get(url)
        except TimeoutException:
            if DEBUG:
                print("Page timeout")
            break

        # Close pop-up window on 1st page
        if first_page:
            # wait for element to download
            wait_for_element(driver, "//button[@class='btn btn-primary']")

            element = driver.find_element(By.XPATH, "//button[@class='btn btn-primary']")
            if element:
                element.click()
        first_page = False

        # wait for element to download
        element = wait_for_element(driver, "//div[@class='col-md-18 col-36 block_pagination_stat']")
        if element is None:
            break
        # Get number of devices
        # element = driver.find_element(By.XPATH, "//div[@class='col-md-18 col-36 block_pagination_stat']")

        answer = []
        answer = element.text.split()

        print(f'{datetime.now().time()}: Поверка: {answer[4]} {device_type[0]}{ending(int(answer[4]))} {device_type[1]} ')

    driver.quit()
    exit()


if __name__ == "__main__":
    main()


