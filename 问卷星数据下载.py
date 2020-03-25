# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 23:38:24 2020

@author: win 8
"""

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time


url = "https://www.wjx.cn/login.aspx"
options = webdriver.ChromeOptions()
options.add_argument('--headless') 
prefs = {"download.default_directory":"C:\\"}
options.add_experimental_option("prefs", prefs)
options.add_argument('log-level=3')
##		INFO = 0, 
##              WARNING = 1, 
##              LOG_ERROR = 2, 
##              LOG_FATAL = 3
##              default is 0
# driver = webdriver.Firefox(executable_path=r'C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe')
driver = webdriver.Chrome(chrome_options=options,
                          executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe')
driver.maximize_window() 
driver.get(url)
time.sleep(3)
driver.find_element_by_id("UserName").send_keys("此处键入账号")
driver.find_element_by_id("Password").send_keys("此处键入密码")
driver.find_element_by_id("LoginButton").click()
time.sleep(3)

#dd = driver.find_element_by_xpath(
#        "//a[@title='问卷名']/../../following-sibling::dd[1]/div[1]/dl[3]/dd")

a1 = driver.find_element_by_xpath(
        "//a[@title='问卷名']/../../following-sibling::dd[1]/div[1]/dl[3]/dd/a[@title='答卷统计分析']")
a2 = driver.find_element_by_xpath(
        "//a[@title='问卷名']/../../following-sibling::dd[1]/div[1]/dl[3]/dd/ul/li[2]/a[text()='查看下载答卷']")
ActionChains(driver).move_to_element(a1).move_to_element(a2).click().perform()
try:
    driver.find_element_by_xpath("//*[text()='此问卷暂时还没有答卷，请先回收答卷']")
except:
    # 答卷非空,下载数据
   span = driver.find_element_by_xpath("//span[text()='下载答卷数据']")
   a = driver.find_element_by_xpath("//a[text()='按选项文本下载']")
   ActionChains(driver).move_to_element(span).move_to_element(a).click().perform()
   
    
else:
    print("无人填写")
    
    
