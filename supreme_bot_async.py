import asyncio
from concurrent.futures import ProcessPoolExecutor

import re
import time
import json
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

import requests
from bs4 import BeautifulSoup
from lxml.html import fromstring

# get settings
with open('/Users/chef/Documents/Develop/Python/resell_bots/info.txt', 'r') as f:
    info = json.loads(f.read().replace('\n', ''))

driver = webdriver.Chrome('/Users/chef/Documents/Develop/Chrdrv/80/chromedriver')  # Optional argument, if not specified will search path.
base_url = 'https://www.supremenewyork.com/'
hot_filename = '/Users/chef/Documents/Develop/Python/resell_bots/hot.txt'
bad_urls_filename = '/Users/chef/Documents/Develop/Python/resell_bots/bad_urls.txt'
hot = [tuple(line.rstrip('\n').split(';')) for line in open(hot_filename, 'r')]
hot_db = {}
for e in hot:
    hot_db[e[0]] = (e[1], e[2])

try:
    with open(bad_urls_filename, 'r') as f:
        bad_urls = []
        for line in f:
            bad_urls.append(line.strip())
except IOError:
    bad_urls = []

new_bads = []

def browser_select_size(element_id, label):
    select = Select(driver.find_element_by_id(element_id))
    select.select_by_visible_text(label)

'''time.sleep(3) # Let the user actually see something!
assert False
search_box = driver.find_element_by_name('q')
search_box.send_keys('ChromeDriver')
search_box.submit()
time.sleep(5) # Let the user actually see something!
driver.quit()'''

def find_all_indexes(input_str, search_str):
    l1 = []
    length = len(input_str)
    index = 0
    while index < length:
        i = input_str.find(search_str, index)
        if i == -1:
            return l1
        l1.append(i)
        index = i + 1
    return l1

def get_hot_urls(urls):
    #print('get_hot_urls() urls count: ', len(urls))
    hot_urls = []
    for url in urls:
        r = requests.get(base_url + url)
        tree = fromstring(r.content)
        title_durty = tree.findtext('.//title')[9:] # cut 'Supreme:' in the start of the title
        idx = find_all_indexes(title_durty, ' - ')
        if idx:
            title = title_durty[:idx[-1]].strip()
        if title in hot_db:
            hot_one = hot_db.get(title)
            soup = BeautifulSoup(r.content, 'lxml')
            colors_tags = soup.find_all('a', {'data-style-name' : re.compile(hot_one[0])})
            hot_urls.append(colors_tags[0]['href'])
        else:
            bad_urls.append(url)

    return hot_urls

def get_urls_from_soup(soup):
    goods_urls = []
    for el in soup:
        url = el.find('a')['href']
        # cut the color parametr in url (last)
        idx = find_all_indexes(url, '/')
        url = url[:idx[-1]]
        if url in bad_urls:
            #print('catch')
            continue
        if url not in goods_urls:
            goods_urls.append(url)

    return goods_urls

def prepare_browser_windows():
    # one windows was opened by deafualt then browser was started
    # and one additional window for checkout process
    if len(driver.window_handles) < len(hot):
        for _ in range(len(hot)-len(driver.window_handles)+1):
            driver.execute_script("window.open('');")

def prepare_to_checkout(hot_urls):
    for i, url in enumerate(hot_urls):
        driver.switch_to.window(driver.window_handles[i])
        driver.get(base_url + url)
        soup = BeautifulSoup(driver.page_source, 'lxml')

        title = soup.find('h1', {'itemprop': 'name'})
        if title:
            good_entity = hot_db.get(title.text.strip())

        if len(good_entity[1]) > 1: # symbol * in sizes tells us what any kind of size can be bought, 'Black' and etc have len() > 1
            size_select = soup.find('select', {'name': 'size'})
            if size_select:
                select = Select(driver.find_element_by_name('size'))
                select.select_by_visible_text(good_entity[1]) # select size option

        try:
            add_to_basket_btn = driver.find_element_by_name('commit')
            add_to_basket_btn.click()
        except NoSuchElementException:
            print(title.text, good_entity[0], good_entity[1], 'is sold out (no button found)!')

def process_select_option(id, text):
    select = Select(driver.find_element_by_id(id))
    select.select_by_visible_text(text)

def fill_checkout_form(data_dict):
    driver.switch_to.window(driver.window_handles[-1])
    driver.get('https://www.supremenewyork.com/checkout')

    # get elements
    full_name = driver.find_element_by_id('order_billing_name')
    email = driver.find_element_by_id('order_email')
    tel = driver.find_element_by_id('order_tel')
    address = driver.find_element_by_id('bo')
    address2 = driver.find_element_by_id('oba3')
    address3 = driver.find_element_by_id('order_billing_address_3')
    city = driver.find_element_by_id('order_billing_city')
    postcode = driver.find_element_by_id('order_billing_zip')

    number = driver.find_element_by_id('cnb')
    cvv = driver.find_element_by_id('vval')

    # fill elements
    full_name.send_keys(data_dict['bill_shipp_info']['full name'])
    email.send_keys(data_dict['bill_shipp_info']['email'])
    tel.send_keys(data_dict['bill_shipp_info']['tel'])
    address.send_keys(data_dict['bill_shipp_info']['address'])
    address2.send_keys(data_dict['bill_shipp_info']['address2'])
    city.send_keys(data_dict['bill_shipp_info']['city'])
    postcode.send_keys(data_dict['bill_shipp_info']['postcode'])
    process_select_option('order_billing_country', data_dict['bill_shipp_info']['country']) # select

    process_select_option('credit_card_type', data_dict['card_info']['card_type']) # select
    number.send_keys(data_dict['card_info']['number'])
    process_select_option('credit_card_month', data_dict['card_info']['month']) # select
    process_select_option('credit_card_year', data_dict['card_info']['year']) # select
    cvv.send_keys(data_dict['card_info']['cvv'])

    ''' captcha is bad thing
    # click i_have_read_and_agree_checkbox 
    actions = ActionChains(driver) 
    actions.send_keys(Keys.TAB) # checkbox is next element on the page after cvv field
    actions.send_keys(Keys.SPACE) # activate it
    actions.perform()

    # and go next
    process_payment_btn = driver.find_element_by_name('commit')
    process_payment_btn.click()
    '''




def attack_site():
    r = requests.get('https://www.supremenewyork.com/shop/all')
    soup = BeautifulSoup(r.content, 'lxml')
    new_goods_urls = []
    articles = soup.find_all('article')
    new_goods_urls = get_urls_from_soup(articles)
    hot_urls = get_hot_urls(new_goods_urls)

    prepare_browser_windows()
    prepare_to_checkout(hot_urls)

    time.sleep(0.2) # time for server accept last add to cart

    fill_checkout_form(info)

    time.sleep(150)
    driver.quit()

def main():
    attack_site()
    # save bad_urls in file for farther using
    #with open(bad_urls_filename, 'w') as f:
        #f.writelines('%s\n' % url for url in bad_urls)

if __name__ == '__main__':
    print(datetime.now())
    main()
    print(datetime.now())