import importlib
import sys
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pyquery import PyQuery as pq
from config import *
importlib.reload(sys)
import pymongo
import pymysql

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)


def search():
    try:

        browser.get('https://www.taobao.com/')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mq"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        "#J_PopSearch > div.sb-search > div > form > input[type=\"submit\"]:nth-child(2)"))
        )
        input.send_keys('美食')
        submit.click()
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            "#mainsrp-pager > div > div > div > div.total"))
        )
        products()
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit"))
        )
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR,
                                              '#mainsrp-pager > div > div > div > ul > li.item.active > span'),
                                             str(page_number))
        )
        products()
    except TimeoutException:
        return next_page(page_number)


def products():
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'location': item.find('.location').text(),
            'shop': item.find('.shop').text()
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('save to db successfully !',result)
    except Exception:
        print('save to db failed !')


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    print(total)
    for i in range(2, total + 1):
        next_page(i)


if __name__ == '__main__':
    main()
