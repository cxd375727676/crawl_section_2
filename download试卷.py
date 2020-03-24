# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 17:16:22 2020

@author: win 8
"""

from selenium import webdriver
import time
from PIL import Image
import glob
import fpdf


url = "http://www.smartpage.cn/bookcase/hscjzx/xyingyu"

#options = webdriver.FirefoxOptions()
#options.add_argument('-headless')
#driver = webdriver.Firefox(
#        executable_path=r'C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe',
#        firefox_options=options)

driver = webdriver.Firefox(
        executable_path=r'C:\Program Files (x86)\Mozilla Firefox\geckodriver.exe')
driver.maximize_window() 
driver.get(url)
time.sleep(2.5)
driver.find_element_by_xpath(
        "//div[@class='button' and @style='cursor: pointer; left: 814px; top: 8px;']"
        ).click()       # 点击全屏
time.sleep(2)                                     
driver.get_screenshot_as_file('0.png')
for i in range(1, 26):
    driver.find_element_by_class_name("flip_button_right").click() # 翻页
    time.sleep(2)
    driver.get_screenshot_as_file('%d.png' % i)
driver.close()
driver.quit()

for path in glob.glob("*.png"):
    raw_img = Image.open(path)
    #raw_img.show()
    revise_img = raw_img.crop((343,60,4458,2968))
    #revise_img.show()
    revise_img.save(path)

pdf = fpdf.FPDF()
pdf.add_page()
for path in glob.glob("*.png"):
    pdf.image(path, x=0,y=0, w=4000,h=3000)
pdf.output("ttt.pdf")
