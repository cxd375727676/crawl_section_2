# -*- coding: utf-8 -*-
"""
企查查，两种版本查经营范围
版本一： requests同步爬取 + BeautifulSoup解析
版本二： aiohttp异步爬取 + BeautifulSoup解析[python 3.7异步版本]

"""
import logging
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import pandas as pd
import asyncio
import aiohttp



def log_config(log_fname, log_level):
    """ 日志设置：日志文件记录 + 控制台输出 """
    logger = logging.getLogger()  # root logger
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if log_fname is not None:
        fh = logging.FileHandler(log_fname, mode='w')
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def launch_driver_and_login():
    options = webdriver.ChromeOptions()
    # log-level: INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3; default is 0
    options.add_argument('log-level=3') 
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(executable_path="C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
    driver.maximize_window()
    driver.get("https://www.qcc.com/")
    button = WebDriverWait(
            driver, 10).until(
                    EC.element_to_be_clickable(
                            (By.XPATH, "//div[@class='modal-content']/button")))
    button.click()   # 点击红包
    driver.find_element_by_class_name("navi-btn").click()  # 准备登录
    print("请用企查查APP扫码登录...")
    WebDriverWait(
            driver, 200).until_not(
                    EC.presence_of_element_located(
                            (By.CLASS_NAME, "login-sao-panel")))
    driver.minimize_window()
    return driver


def get_detail_urls(input_firms):
    """ 获取查询企业 与 对应详情超链接， 返回字典 """
    res = {}
    try:
        driver = launch_driver_and_login()
    except:
        logging.error("登陆企查查失败")
    else:
        logging.info("开始获取企业详情链接...")
        for input_firm in input_firms:
            try:
                driver.find_element_by_id("searchkey").send_keys(input_firm)
                driver.find_element_by_class_name("index-searchbtn").click()
                first_info = (driver
                              .find_element_by_id("search-result")
                              .find_element_by_tag_name("a")
                              )                                # 首个搜索内容
                output_firm = (re
                               .search(
                                       "内容名称':'(.+)','内容链接", 
                                       first_info.get_attribute("onclick"))
                               .group(1)
                               .replace(" ", "")
                               )
                detail_url = first_info.get_attribute("href")
                if input_firm != output_firm:
                    logging.warning(f"查询不一致。原始查询：{input_firm}， 查询结果：{output_firm}")
                res.update({output_firm: detail_url})
            except:
                logging.error(f"{input_firm} 详情url获取失败")
            else:
                logging.info(f"{input_firm} 详情url获取成功")
            finally:
                driver.back()
        driver.quit()
    finally:
        return res


def get_input_firms():   # 可定制
    data = pd.read_excel("test.xlsx", usecols=['公司名称'])
    return data['公司名称'].str.strip().tolist()


def save_result(data):  # 可定制
    data = pd.Series(data)
    data.index.name = '公司名称'
    data.name = '经营范围'
    data.to_excel('scope.xlsx')
    print("数据已保存")
    

def parse_scope(html):
    """ 从源代码提取经营范围 """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("section", attrs={'id': 'Cominfo'}).find("table") # 基本信息标签
    rows = table.find_all("tr")
    key, value = rows[-1].find_all("td")    # 经营范围（最后一行）
    assert key.text == '经营范围'
    return value.text.strip()
    

# ***************************   获取网页源代码 *********************************     
# 版本一：requests库
def get_html_1(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


# 版本二：aiohttp库
async def get_html_2(url):
    async with aiohttp.ClientSession() as session:
         async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
            assert response.status == 200
            return await response.text()


async def write_scope(dict_, firm, url):  
    try:
        html = await get_html_2(url)
        scope = parse_scope(html)
        dict_.update({firm: scope})
    except:
        logging.error(f"{firm} 信息获取失败")
    else:
        logging.info(f"{firm} 信息获取成功")

# *****************************************************************************
        
def main_1():  # 版本一 
    res = {}
    input_firms = get_input_firms()
    detail_urls = get_detail_urls(input_firms)
    logging.info("开始获取企业信息...")
    for firm, href in detail_urls.items():
        try:
            html = get_html_1(href)
            scope = parse_scope(html)
            res.update({firm: scope})
        except:
            logging.error(f"{firm} 信息获取失败")
        else:
            logging.info(f"{firm} 信息获取成功")
    save_result(res)


async def main_2():  # 版本二
    res = {}
    input_firms = get_input_firms()
    detail_urls = get_detail_urls(input_firms)
    logging.info("开始异步获取企业信息...")
    tasks = [asyncio.create_task(write_scope(res, firm, href)) for firm, href in detail_urls.items()]
    await asyncio.gather(*tasks)
    save_result(res)
            
        
        
if __name__ == '__main__':
    log_config('test.log', logging.INFO)
#    main_1()   # 版本一
    asyncio.run(main_2())   # 版本二
