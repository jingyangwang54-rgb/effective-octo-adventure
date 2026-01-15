# 1.Flask核心工具
from flask import Flask, render_template, redirect, url_for, request, flash
import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  #  非交互式后端（Web服务不能弹出图表窗口，用这个后端生成图片）
import matplotlib.pyplot as plt # 绘制网页端图表
from io import BytesIO # 内存缓冲区（临时存图表，不写入本地文件）
import base64 # 把图表转为Base64字符串（网页能直接显示）

# 2.配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
DB_PATH = os.path.join(BASE_DIR, 'fortune500.db')

# 3.初始化Flask
app = Flask(__name__, template_folder=TEMPLATE_DIR)         # __name__：当前模块名，template_folder：指定模板文件夹
app.config['SECRET_KEY'] = 'test-key-2025'                  # 密钥（用于Flash消息、会话等，随便填一个字符串即可）

# 4.测试账号
test_users = {"admin": "admin123", "user": "user123"}

# 5.核心工具函数
def clean_company_name(name):
    """清洗公司名称"""
    if pd.isna(name) or name == "无数据":
        return "无数据"
    # 处理半角括号 (xxx)
    if '(' in name:
        name = name.split('(')[0].strip()
    # 处理全角括号 （xxx）
    if '（' in name:
        name = name.split('（')[0].strip()
    # 移除多余符号
    return name.replace(' ', '').replace('-', '').replace('_', '')

def read_fortune500_data(query=None):
    """读取数据库数据，支持搜索过滤"""
    if not os.path.exists(DB_PATH):
        flash(f"❌ 错误：未找到数据库文件！路径：{DB_PATH}")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row      # 让查询结果能按列名访问（如data['company']）
        
        # 基础SQL
        base_sql = """
        SELECT rank, company, revenue, profit, country, company_url 
        FROM company_info 
        WHERE company != '无数据'
        """
        
        # ++++++++搜索逻辑：如果用户输入了查询关键词，就过滤数据
        if query and query.strip() != "":
            sql = base_sql + " AND (company LIKE ? OR country LIKE ?)"
            df = pd.read_sql(sql, conn, params=(f'%{query}%', f'%{query}%'))
        else:
            df = pd.read_sql(base_sql, conn)
        conn.close()
        
        # 数据格式转换（和你的本地代码完全一致）
        df['revenue'] = pd.to_numeric(
            df['revenue'].replace(['无数据', '--', '—'], '0').str.replace(',', ''),
            errors='coerce'
        ).fillna(0)
        
        df['profit'] = pd.to_numeric(
            df['profit'].replace(['无数据', '--', '—'], '0').str.replace(',', ''),
            errors='coerce'
        ).fillna(0)
        
        # 清洗公司名称（和你的代码一致）
        df['clean_name'] = df['company'].apply(clean_company_name)
        
        # 名称去重，保留营收最高的记录（和你的代码一致）
        df_unique = df.sort_values('revenue', ascending=False).drop_duplicates(
            subset='clean_name',
            keep='first'
        )
        
        return df_unique
    except Exception as e:
        flash(f"❌ 读取数据库失败：{str(e)}")
        return None

# 6. 网页端图表生成函数（和本地可视化类似，但输出Base64字符串）
def generate_revenue_chart(df):
    """生成营收前十柱状图（和你的本地代码样式一致）"""
    try:
        # 中文显示（和你的代码一致）
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 取营收前10（和你的代码一致）
        top10 = df.sort_values('revenue', ascending=False).head(10)
        top10['short_name'] = top10['clean_name']
        
        # 绘制营收柱状图（配色/样式和你的代码一致）
        fig, ax = plt.subplots(figsize=(11, 14))
        ax.barh(top10['short_name'], top10['revenue'], color='#2E86AB', height=0.7)
        ax.set_title('2025财富500强前10家公司营收排行', fontsize=14, pad=20)
        ax.set_xlabel('营收（百万美元）', fontsize=12)
        ax.grid(axis='x', alpha=0.3)
        ax.tick_params(axis='y', labelsize=11)
        ax.invert_yaxis()
        
        # 保存为Base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    except Exception as e:
        flash(f"❌ 营收图表生成失败：{str(e)}")
        return ""

def generate_profit_chart(df):
    """生成利润前十柱状图（和你的本地代码样式一致）"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 取营收前10的企业（保证和营收图企业一致）
        top10 = df.sort_values('revenue', ascending=False).head(10)
        top10['short_name'] = top10['clean_name']
        
        # 绘制利润柱状图（配色/样式和你的代码一致）
        fig, ax = plt.subplots(figsize=(11, 14))
        ax.barh(top10['short_name'], top10['profit'], color='#A23B72', height=0.7)
        ax.set_title('2025财富500强前10家公司利润对比', fontsize=14, pad=20)
        ax.set_xlabel('利润（百万美元）', fontsize=12)
        ax.grid(axis='x', alpha=0.3)
        ax.tick_params(axis='y', labelsize=11)
        ax.invert_yaxis()
        
        # 保存为Base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    except Exception as e:
        flash(f"❌ 利润图表生成失败：{str(e)}")
        return ""

def generate_country_pie_chart(df):
    """生成各国企业数量饼状图（和你的本地代码样式一致）"""
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 取前10个国家（和你的代码一致）
        country_count = df['country'].value_counts().head(10)
        
        # 绘制饼状图（样式/配色和你的代码一致）
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.pie(
            country_count.values, 
            labels=country_count.index,  
            autopct='%1.1f%%',
            startangle=90,
            colors=plt.cm.Set3.colors
        )
        ax.set_title('2025财富500强前10大上榜国家分布', fontsize=14, pad=20)
        
        # 保存为Base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    except Exception as e:
        flash(f"❌ 饼状图生成失败：{str(e)}")
        return ""

# ++++7. 路由函数（Web服务的核心，定义网页访问路径）
@app.route('/', methods=['GET', 'POST'])            # 根路径（http://127.0.0.1:5000），支持GET（访问）和POST（提交数据）
@app.route('/login', methods=['GET', 'POST'])       # 登录路径（http://127.0.0.1:5000/login），和根路径共用函数
def login():
    if request.method == 'POST':                    # 如果是POST请求（用户点击登录按钮提交数据）
        username = request.form.get('username')     # 从表单获取“username”输入框的值
        password = request.form.get('password')
        # 验证账号密码
        if username not in test_users:
            flash('❌ 用户名不存在！')
            return redirect(url_for('login'))
        if test_users[username] != password:
            flash('❌ 密码错误！')
            return redirect(url_for('login'))
        
        return redirect(url_for('dashboard'))       # 登录成功，跳转到查询页（dashboard）
    
    return render_template('login.html')            # 如果是GET请求（用户直接访问登录页），返回登录模板

@app.route('/dashboard', methods=['GET', 'POST'])   # 查询页路径
def dashboard():
    # 获取搜索关键词（用户提交搜索表单时，POST请求传递的“query”值）
    query = request.form.get('query', '').strip() if request.method == 'POST' else ''
    
    # 读取数据
    df = read_fortune500_data(query)
    # 数据转为字典列表（前端模板能识别的格式）
    companies = df.to_dict('records') if df is not None and len(df) > 0 else []
    
    # 生成3个图表
    revenue_chart = generate_revenue_chart(df) if df is not None else ""
    profit_chart = generate_profit_chart(df) if df is not None else ""
    pie_chart = generate_country_pie_chart(df) if df is not None else ""
    
    return render_template(
        'dashboard.html',
        companies=companies,
        revenue_chart=revenue_chart,  # 营收图
        profit_chart=profit_chart,    # 利润图
        pie_chart=pie_chart,          # 饼状图
        query=query
    )

# 8. 启动Web服务
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')