import requests
from bs4 import BeautifulSoup
import re

#获得网页“汤”
def get_soup(url):
    r=requests.get(url)
    r.encoding=r.apparent_encoding
    soup=BeautifulSoup(r.text,"html.parser")
    return soup

#获得淘股吧热门股
def get_hot_stocks_tgb(url):
    soup=get_soup(url)
    input_tags=soup.find_all("input")
    
    hot_stocks=[]
    for input in input_tags:
        try:
            value=input.attrs["value"]
            hot_stocks.append(re.findall(r"s[hz]\d{6}", value)[0])
        except:
            continue
    
    return hot_stocks


#获得新浪股吧热门股
def get_hot_stocks_sina(url):
    soup=get_soup(url)
    div_tags=soup.find_all("div",{"class":"b_cont"})
    a_tags=[]
    for div in div_tags:
        try:
            div.find_all("a")
            a_tags+=div.find_all("a")
        except:
            continue
    
    hot_stocks=[]
    for a in a_tags:
        try:
            href=a.attrs["href"]     
            hot_stocks.append(re.findall(r"s[hz]\d{6}", href)[0])
        except:
            continue
    
    return hot_stocks


url_tgb="https://www.taoguba.com.cn/moreHotStock"
url_sina="http://guba.sina.com.cn/?s=bar&bid=14247"
hot_stocks_tgb=get_hot_stocks_tgb(url_tgb)
hot_stocks_sina=get_hot_stocks_sina(url_sina)
print(hot_stocks_tgb)
print(hot_stocks_sina)