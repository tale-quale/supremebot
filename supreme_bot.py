import asyncio
import time
from datetime import datetime
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from lxml.html import fromstring

#driver = webdriver.Chrome('/Users/chef/Documents/Develop/Chrdrv/80/chromedriver')  # Optional argument, if not specified will search path.
base_url = 'https://www.supremenewyork.com/'

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

def get_titles(urls):
    titles_list = []
    for url in urls:
        r = requests.get(base_url + url)
        tree = fromstring(r.content)
        title_durty = tree.findtext('.//title')[9:]
        idx = find_all_indexes(title_durty, ' - ')
        if idx:
            title = title_durty[:idx[-1]]
        titles_list.append(title)

    return titles_list

def attack_site():
    #driver.get('https://www.supremenewyork.com/shop/all')
    #soup = BeautifulSoup(driver.page_source, 'lxml')
    r = requests.get('https://www.supremenewyork.com/shop/all')
    soup = BeautifulSoup(r.content, 'lxml')
    #print(soup.prettify())
    goods_urls = []
    articles = soup.find_all('article')
    for article in articles:
        good_url = article.find('a')['href']
        idx = find_all_indexes(good_url, '/')
        good_url = good_url[:idx[-1]]
        if good_url not in goods_urls:
            goods_urls.append(good_url)

    titles_list = get_titles(goods_urls)


    print(len(titles_list))
    print(titles_list[:5])
    print('**************')
    print(titles_list[-5:])

    #driver.quit()

def main():
    attack_site()

if __name__ == '__main__':
    print(datetime.now())
    main()
    print(datetime.now())