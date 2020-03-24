# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 14:42:35 2020

@author: win 8
"""

from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time


url = "https://wenku.baidu.com/view/656e7fccae45b307e87101f69e3143323968f5a2.html"
options = webdriver.FirefoxOptions()
options.add_argument('-headless')
browser = webdriver.Firefox(
        executable_path=r'C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe',
        firefox_options=options)
browser.get(url)

#将滚动条移动到按钮位置
js = "var q=document.documentElement.scrollTop=4000"  
browser.execute_script(js)
time.sleep(2)
# 点击继续阅读
browser.find_element_by_class_name("moreBtn").click()
time.sleep(2)

def get_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    ps = soup.find_all('p')
    res = ''
    for p in ps:
        string = p.string
        if string and '\u2002' not in string:
            res += string
    return res

# 回到顶部(第一部分)
js_top = "var q=document.documentElement.scrollTop=0"
browser.execute_script(js_top)
time.sleep(2)
part1 = get_info(browser.page_source)

# 拉到底部(第二部分)
js_bottom = "var q=document.documentElement.scrollTop=10000"
browser.execute_script(js_bottom)
time.sleep(2)
part2 = get_info(browser.page_source)

res = part1 + part2
# 字符串清洗
start = '学前教育教研的工作计划'
end = '优秀教育随笔评比'
res = res[res.index(start):res.index(end)]
with open("zkl.txt", "w") as f:
    f.write(res)