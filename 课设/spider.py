import requests
import sqlite3
from lxml import etree
from urllib.parse import urljoin

headers = {
    'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0'
}


#定义工具函数：提取列表中第一个元素并去除空格（处理网页解析结果）
# 通俗解释：网页解析可能拿到空数据，这个函数避免程序报错
def get_first_text(list):
    try:
        return list[0].strip()
    except:
        return ""


url = "https://www.fortunechina.com/fortune500/c/2025-07/29/content_467206.htm"
base_url = "https://www.fortunechina.com"   #网页根域名

# 关键：绝对路径生成数据库
import os
current_dir = os.path.dirname(os.path.abspath(__file__))     #获取文件路径
db_path = os.path.join(current_dir, 'fortune500.db')         #获取数据库路径
conn = sqlite3.connect(db_path)                              #连接（创建数据库）
cursor = conn.cursor()#*

# 数据表
cursor.execute('''
CREATE TABLE IF NOT EXISTS company_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank TEXT,
    company TEXT,
    company_url TEXT,
    revenue TEXT,
    profit TEXT,
    country TEXT
)
''')
conn.commit()

res = requests.get(url=url, headers=headers)            
res.encoding = res.apparent_encoding                #自动识别网页编码，防止中文乱码
print("请求状态码：", res.status_code)
if res.status_code != 200:
    print("网页请求失败！")
else:
    html = etree.HTML(res.text)                        #把网页源码转化为可解析的形式
    tr_list = html.xpath('//*[@id="table1"]//tr')       #tr是行标签，提取表格所有行
    print(f"共解析到 {len(tr_list)} 行数据（含表头）")

    insert_data = []                                    #批量存储数据进入数据库
    
    for tr in tr_list[1:]:
        rank = get_first_text(tr.xpath('./td[1]//text()'))        
        company = get_first_text(tr.xpath('./td[2]//text()'))     
        revenue = get_first_text(tr.xpath('./td[3]//text()'))     
        profit = get_first_text(tr.xpath('./td[4]//text()'))       
        country = get_first_text(tr.xpath('./td[5]//text()'))    
        
        # 超链接
        company_url_relative = get_first_text(tr.xpath('./td[2]//a/@href'))
        if company_url_relative:
            if company_url_relative.startswith('http'):
                company_url = company_url_relative
            else:
                company_url = urljoin(base_url, company_url_relative)
        else:
            company_url = ""

        # 数据清洗
        rank = rank if rank else "无数据"
        company = company if company else "无数据"
        revenue = revenue if revenue else "0"
        profit = profit if profit else "0"
        country = country if country else "无数据"

        # 加入批量列表，不立即提交
        insert_data.append((rank, company, company_url, revenue, profit, country))
        
        # 打印
        print(f"排名：{rank} | 公司：{company} | 链接：{company_url} | 营收：{revenue} | 利润：{profit} | 国家：{country}")

    # 提交
    if insert_data:
        cursor.executemany('''
        INSERT INTO company_info (rank, company, company_url, revenue, profit, country)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', insert_data)
        conn.commit()
        print(f"✅ 共插入 {len(insert_data)} 条数据到数据库")

# 关闭连接
cursor.close()                      #关闭游标
conn.close()                        #关闭数据库连接
print("爬虫数据提取完成！")