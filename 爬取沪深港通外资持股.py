# -*- coding: utf-8 -*-
"""
Created on Sat Sep 19 00:23:47 2020

爬取东方财富网沪股通、港股通数据
东方财富网->数据中心->沪深港通->沪深港通持股
可查询个股和机构

@author: Xiaodong, Chen
"""
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import numpy as np
import pandas as pd
import re
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import logging
import PySimpleGUI as sg
import psycopg2
import matplotlib.pyplot as plt
from functools import lru_cache
import requests



def str2num(text):
    if text[-1] == '万':
        return 10e4 * float(text[:-1])
    if text[-1] == '亿':
        return 10e8 * float(text[:-1])
    return float(text)
    

def add_temp_table(driver, content):
    """ 将当前页面的表格追加进content """
    table = driver.find_element_by_tag_name("tbody")
    trs = table.find_elements_by_tag_name("tr")
    for tr in trs:
        tds = tr.find_elements_by_tag_name("td")
        row = [td.text for td in tds]
        content.append(row)


def get_url(name, date):
    """ 某日持仓明细链接 """
    url = "http://data.eastmoney.com/hsgtcg/InstitutionHdDetail.aspx?"
    if name == "JP摩根":
        url += f"jgCode=C00100&date={date}&jgName=JPMORGAN%20CHASE%20BANK%2C%20NATIONAL%20ASSOCIATION"
    if name == "渣打银行":
        url += f"jgCode=C00039&date={date}&jgName=%u6E23%u6253%u94F6%u884C%28%u9999%u6E2F%29%u6709%u9650%u516C%u53F8"
    if name == "汇丰银行":
        url += f"jgCode=C00019&date={date}&jgName=%u9999%u6E2F%u4E0A%u6D77%u6C47%u4E30%u94F6%u884C%u6709%u9650%u516C%u53F8"
    return url


#def login(url):
#    options = Options()
#    options.add_argument("--headless")
#    options.add_experimental_option("excludeSwitches", ["enable-logging"])
#    driver = webdriver.Chrome(
#            r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
#            options=options)
#    driver.maximize_window()
#    driver.get(url)
#    return driver


def to_df(header, content):
    content = pd.DataFrame(content, columns=header) 
    content.drop("相关", axis=1, inplace=True)
    content.replace('-', np.nan, inplace=True)
    # 前三列字符串整理
    content.iloc[:, :3] = content.iloc[:, :3].apply(lambda x: x.str.strip())
    # 第一列（日期列）转为datetime.date
    content.iloc[:, 0] = pd.to_datetime(content.iloc[:, 0]).dt.date
    for col_index in [5, 6, 8, 9, 10]:
        content.iloc[:, col_index] = content.iloc[:, col_index].map(str2num)
    # 剩下的str->float
    content.iloc[:, [3, 4, 7]] = content.iloc[:, [3, 4, 7]].astype(float)
    # 处理列名，不能有小括号和百分号
    content.columns = content.columns.map(
            lambda x: re.sub("[)）]", 
                            "]", 
    re.sub("[(（]", "[", x)).replace("%", "百分数"))
    return content


#def get_data(name, date, timeout=50):
#    """ 
#    获取 date 这一天， 机构名称为name 持仓数据[列表]
#    每一只股票持仓记录构成列表的一个元素 
#    如果失败则返回日期，如果成功则返回表头和数据列表"""
#    
#    content = []
#    url = get_url(name, date)
#    print("\n" + name)
#    print(date + ":")
#    try:
#        driver = login(url)
#        raw_head = WebDriverWait(driver, timeout
#                                 ).until(EC.presence_of_element_located(
#                                 (By.XPATH, "//table[@class='tab1']/following::thead")
#                                 ))
#        # 处理表头
#        raw_head = raw_head.find_elements_by_tag_name("tr")
#        head_1, head_2 = raw_head
#        head_1 = head_1.text.replace('\n', '').split()
#        head_2 = head_2.text.replace('\n', '').split()
#        last_col_name = head_1.pop()
#        head_1.extend([f"{last_col_name}_{day}" for day in head_2])
#    except:
#        print("\t出现错误")
#        return date     # 出现错误返回错误日期
#    else:
#        try:
#            # 获取总页数
#            total_pages = int(driver.find_element_by_xpath("//a[@title='转到最后一页']").text.strip())
#        except: # 非交易日无数据
#            no_content = driver.find_element_by_xpath("//tbody/tr/td").text.strip()
#            print(no_content)
#            if not no_content.startswith("没有相关数据"):
#                return date # 并非没有数据，可能出错
#        else:
#            print("\t爬取第1页") 
#            add_temp_table(driver, content)  # 首页    
#            for page in range(2, total_pages + 1):
#                # 单击下一页
#                driver.find_element_by_xpath("//div[@id='PageCont']/a[text()='下一页']").click()
#                # 直到确认下一页刷新了
#                WebDriverWait(driver, timeout).until(
#                        lambda driver: int(
#                                driver.find_element_by_id(
#                                        "PageContgopage"
#                                        ).get_attribute('value').strip()) == page)
#                print(f"\t爬取第{page}页")
#                add_temp_table(driver, content)
#            print("\t爬取完毕")
#            return head_1, content  # 获取数据成功则返回当日持仓的数据框
#    finally:
#        driver.quit()
#
#           
## ==============================================================================
## 先下载过去的历史数据 ：2020-09-09 至 2020-09-30
#dates = pd.date_range("2020-09-09", "2020-09-30")
#
#jp_history = []
#jp_err_dates = []
#for date in dates:
#    date = date.strftime("%Y-%m-%d")
#    data = get_data("JP摩根", date)
#    if isinstance(data, str):  # 出错的日期
#        jp_err_dates.append(data)
#    if isinstance(data, tuple):
#        header, content = data
#        jp_history.extend(content)
#if not jp_err_dates:
#    jp_history_df = to_df(header, jp_history)
#
#zd_history = []
#zd_err_dates = []
#for date in dates:
#    date = date.strftime("%Y-%m-%d")
#    data = get_data("渣打银行", date)
#    if isinstance(data, str):  # 出错的日期
#        zd_err_dates.append(data)
#    if isinstance(data, tuple):
#        header, content = data
#        zd_history.extend(content)
#if not zd_err_dates:
#    zd_history_df = to_df(header, zd_history)
#
#hf_history = []
#hf_err_dates = []
#for date in dates:
#    date = date.strftime("%Y-%m-%d")
#    data = get_data("汇丰银行", date)
#    if isinstance(data, str):  # 出错的日期
#        hf_err_dates.append(data)
#    if isinstance(data, tuple):
#        header, content = data
#        hf_history.extend(content)
#if not hf_err_dates:
#    hf_history_df = to_df(header, hf_history)
#
## 写入数据库
#user = "postgres"
#password = "123456"
#port = "5433"
#database = "沪深港通"
#engine = create_engine(f'postgresql://{user}:{password}@localhost:{port}/{database}')
#jp_history_df.to_sql('JP摩根', engine, index=False, if_exists='replace')
#del jp_history_df
#zd_history_df.to_sql('渣打银行', engine, index=False, if_exists='replace')
#del zd_history_df
#hf_history_df.to_sql('汇丰银行', engine, index=False, if_exists='replace')
#del hf_history_df
#engine.dispose()
#================================================================================
      
# 以后每天定时执行脚本，将更新数据追加到PostgreSQL

def startup():
    """ 启动浏览器 """
    options = Options()
    options.add_argument("user-agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'")
    options.add_argument("--disable-gpu")  # 谷歌文档提到需要加上这个属性来规避bug,禁用GPU
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument('log-level=3') 
    driver = webdriver.Chrome(
            r"C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe",
            options=options)
    driver.maximize_window()
    return driver


def get_data(driver, timeout):
    """ 在当前窗口激活且输入url后，爬取数据 
    如果爬取没有问题，则返回pandas.DataFrame"""
    content = []
    try:
        # 等待出现表头
        raw_head = WebDriverWait(driver, timeout
                                     ).until(EC.presence_of_element_located(
                                     (By.XPATH, "//table[@class='tab1']/following::thead")
                                     ))
        # 处理表头
        raw_head = raw_head.find_elements_by_tag_name("tr")
        head_1, head_2 = raw_head
        head_1 = head_1.text.replace('\n', '').split()
        head_2 = head_2.text.replace('\n', '').split()
        last_col_name = head_1.pop()
        head_1.extend([f"{last_col_name}_{day}" for day in head_2])
    except:
        logging.info("\t出现错误")
    else:
        try:
            # 获取总页数
            total_pages = int(driver.find_element_by_xpath("//a[@title='转到最后一页']").text.strip())
        except: # 非交易日无数据，提示信息
            no_content = driver.find_element_by_xpath("//tbody/tr/td").text.strip()
            logging.info(no_content)
            return no_content
        else:
            logging.info("\t爬取第1页") 
            add_temp_table(driver, content)  # 首页    
            for page in range(2, total_pages + 1):
                # 单击下一页
                driver.find_element_by_xpath("//div[@id='PageCont']/a[text()='下一页']").click()
                # 直到确认下一页刷新了
                WebDriverWait(driver, timeout).until(
                        lambda driver: int(
                                driver.find_element_by_id(
                                        "PageContgopage"
                                        ).get_attribute('value').strip()) == page)
                logging.info(f"\t爬取第{page}页")
                add_temp_table(driver, content)
            logging.info("\t爬取完毕")
            content = to_df(head_1, content)
            return content       # 返回dataframe


def task(names=("JP摩根", "渣打银行", "汇丰银行"), 
         date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), timeout=100):
    logging.info(f"数据日期：{date}")
    #n = len(names)
    driver = startup()
#    for i in range(n - 1):
#        driver.execute_script('window.open()') # 开启新窗口，但活跃的仍是老窗口
        
    user = "postgres"
    password = "123456"
    port = "5433"
    database = "沪深港通"
    engine = create_engine(f'postgresql://{user}:{password}@localhost:{port}/{database}')     
    text = []  # GUI 文本提示信息
    for name in names:
        logging.info("\n" + name)
        line = name + ":"
        url = get_url(name, date)
        driver.get(url)
        try:
            data = get_data(driver, timeout)
        except:
            logging.error("\t提取数据失败")
        else:
            if isinstance(data, str): # 无数据提示（非交易日）
                line += data
            if isinstance(data, pd.DataFrame):
                data.to_sql(name, engine, index=False, if_exists='append')
                logging.info("\t成功写入数据库")
                line += "成功写入数据库"
                text.append(sg.Text(line))
#        if i != (n - 1):  # 不是最后一个（汇丰银行）则激活下一个窗口
#            driver.switch_to.window(driver.window_handles[i + 1])
    driver.quit()       
    engine.dispose()
    
    bt = sg.Button("确认")
    layout = [text, [bt]]
    window = sg.Window(f"数据日期：{date}", layout)
    event, values = window.read()
    if event is None or event == "确认":
        window.close()


def task_supplement(start_date):
    dates = pd.date_range(start_date, datetime.now())
    dates = [date.strftime("%Y-%m-%d") for date in dates]
    for date in dates:
        task(date=date)
        print("\n")
    
        
# 运行
# 日志设置
# print("start...")   # 命令行调试
logging.basicConfig(format='%(message)s',
                    level=logging.INFO,    # 全局设置，避免selenium低级别日志输出
                    filename=r"C:\Users\Administrator\Desktop\沪深港通每日爬取.log",
                    filemode="w")
task()

# 特殊情况忘记任务，手动完成
#start_date = 
#task_supplement(start_date)


# 调试，控制台打印
#logging.basicConfig(format='%(message)s', level=logging.INFO)



# 调取数据
plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei']
# plt.rcParams['figure.dpi'] = 200
plt.rcParams['axes.unicode_minus'] = False

logging.basicConfig(format='%(message)s',
                    level=logging.INFO,
                    #filename=r"C:\Users\Administrator\Desktop\沪深港通每日爬取.log",
                    #filemode="w"
                    )


@lru_cache(maxsize=64)
def get_stock_name(stock_code):
    """ 利用新浪api """
    flag = "sh" if stock_code.startswith(("600", "601", "603")) else "sz"
    url = f"http://hq.sinajs.cn/list={flag}{stock_code}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except:
        print("获取股票名称失败")
    else:
        stock_name = re.search(r'="(.*?),', r.text).group(1).replace(" ", "")
        return stock_name
    
    
#@lru_cache(maxsize=64)
#def get_stock_name(stock_code):
#    """ 利用网易财经api, 0代表sh，1代表sz"""
#    flag = 0 if stock_code.startswith(("600", "601", "603")) else 1
#    url = f"http://img1.money.126.net/data/hs/time/today/{flag}{stock_code}.json"
#    try:
#        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#        r.raise_for_status()
#    except:
#        print("获取股票名称失败")
#    else:
#        data = r.json()
#        stock_name = data.get("name").replace(" ", "")
#        return stock_name
    

def get_stock_info(con, name, stock_code, count):
    """ 获取个股信息 """
    sql = f"""SELECT * FROM "{name}" WHERE (股票代码 = '{stock_code}')
    AND (持股日期 in (
    SELECT DISTINCT 持股日期 FROM "{name}" ORDER BY 持股日期 DESC LIMIT {count})
    )"""
    data = pd.read_sql(sql, con)
    return data


def get_time_series(con, stock_code, col_name, count, name):
    """ 从多个机构就某一特定股票特定指标对比画图 """
    # col_name中有中括号，需要加双引号
    sql = f"""SELECT 持股日期, "{col_name}" FROM "{name}" WHERE (股票代码 = '{stock_code}')
    AND (持股日期 in (
    SELECT DISTINCT 持股日期 FROM "{name}" ORDER BY 持股日期 DESC LIMIT {count})
    )"""
    data = pd.read_sql(sql, con, index_col='持股日期').squeeze().sort_index()
    data.index = pd.to_datetime(data.index)
    data.name = name
    data.index.name = None
    return data
    

    
def extract_data(con, name, *, count=None, date=None):
    """ 最新 count 个交易日 机构名为 name 的持仓数据
    或 指定日期的持仓数据 
    必须指定关键字 """
    
    # 找出最近count个交易日的起点和终点
    if count is not None:
        # 表名要加双引号！！！
        sql = f"""SELECT * FROM "{name}" WHERE 持股日期 in (
        SELECT DISTINCT 持股日期 FROM "{name}" ORDER BY 持股日期 DESC LIMIT {count})"""
    elif date is not None:
        sql = f"""SELECT * FROM "{name}" WHERE 持股日期 = '{date}'"""
    data = pd.read_sql(sql, con)
    return data


def inner_join(col_name, rank):
    """ 
    按某个指标降序排列，取个机构前 rank 只股票求交集
    col_name: '持股市值[元]' , '持股数量占A股百分比[百分比]', '持股数量[股]', ... """
    
    des_sort = lambda df: df.sort_values(by=col_name, ascending=False).iloc[:rank, :]
    jp = jp_data[['持股日期', '股票代码', col_name]].groupby(
            "持股日期", group_keys=False).apply(des_sort)                  
    zd = zd_data[['持股日期', '股票代码', col_name]].groupby(
            "持股日期", group_keys=False).apply(des_sort)
    hf = hf_data[['持股日期', '股票简称', '股票代码', col_name]].groupby(
            "持股日期", group_keys=False).apply(des_sort)
    
    total = jp.merge(
            zd, on=['持股日期', '股票代码'], suffixes=["JP", "ZD"]
            ).merge(hf, on=['持股日期', '股票代码'])
    dates = total['持股日期'].unique()
    intersection = {}  # 每日抱团(交集）字典
    for date in dates:
        stocks = total.loc[total['持股日期'] == date, ['股票简称', '股票代码']]
        intersection[date] = stocks
    return intersection
    
    
def show_gather(intersection):    
    """ 抱团信息 """
    days = len(intersection)
    logging.info(f"近{days}日抱团信息==============")
    for date in sorted(intersection.keys()):
        logging.info(str(date) + ":")
        stocks = intersection[date][['股票简称', '股票代码']]
        for _, row in stocks.iterrows():
            logging.info("\t{}({})".format(row.loc['股票简称'], row.loc['股票代码']))
    

def show_change(intersection):    
    """ 变动信息（少一天）"""
    days = len(intersection)
    logging.info(f"\n近{days}日变动信息==============")
    dates = sorted(intersection.keys())
    for prev_date, date in zip(dates, dates[1:]):
        logging.info(str(date) + ":")
        new = set(intersection[date]['股票简称'].values)
        old = set(intersection[prev_date]['股票简称'].values)
        add = new - old
        if add:
            logging.info("  新增:")
            for stock in (new - old):
                logging.info("\t" + stock)
        sub = old - new
        if sub:
            logging.info("  减少:")
            for stock in (old - new):
                logging.info("\t" + stock)
    
# 连接 ************************************************************************
con = psycopg2.connect(database="沪深港通", user='postgres', 
                            password='123456', host='localhost', port='5433')
# 全局数据
count = 3   # 最近 count 天
rank = 100  # 前 rank 筛选

jp_data = extract_data(con, "JP摩根", count=count)
zd_data = extract_data(con, "渣打银行", count=count)
hf_data = extract_data(con, "汇丰银行", count=count)


# 从市值看
logging.info("\n从持有市值看===================================================")
intersection = inner_join('持股市值[元]', rank)
# show_gather(intersection)
show_change(intersection)


# 从数量占比看
logging.info("\n从持股占A股比例看===============================================")
intersection = inner_join('持股数量占A股百分比[百分数]', rank)
#show_gather(intersection)
show_change(intersection)
# =============================================================================


# 从单一指标看三家机构的时间序列
stock_code = "002648" # 卫星石化
stock_code = "600036" # 招商银行
stock_code = "002230" # 科大讯飞
stock_code = "600536" # 中国软件
stock_code = "000977" # 浪潮信息
stock_code = "000063" # 中兴通讯
stock_code = "600276" # 恒瑞医药
stock_code = "600872" # 中炬高新
stock_code = "603489" # 八方股份
stock_code = "601318" # 中国平安

count = 30
col_name = '持股数量[股]'
con = psycopg2.connect(database="沪深港通", user='postgres', 
                            password='123456', host='localhost', port='5433')
ts_jp = get_time_series(con, stock_code, col_name, count, name="JP摩根")
ts_zd = get_time_series(con, stock_code, col_name, count, name="渣打银行") 
ts_hf = get_time_series(con, stock_code, col_name, count, name="汇丰银行")
# 可视化
fig, axes = plt.subplots(2, 2, figsize=(15, 12), sharex=True)
ts_jp.plot(title=ts_jp.name, ax=axes[0][0])
ts_zd.plot(title=ts_zd.name, ax=axes[1][0])
ts_hf.plot(title=ts_hf.name, ax=axes[1][1])
fig.delaxes(axes[0][1])
stock_name = get_stock_name(stock_code)
fig.suptitle("{}:{}".format(stock_name, col_name), fontsize=30);

con.close()
