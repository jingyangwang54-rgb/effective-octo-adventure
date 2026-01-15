import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# 中文和负号的问题解决
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
# 保证图表的显示
plt.switch_backend('TkAgg')


def read_fortune500_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'fortune500.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 错误：未找到数据库文件！路径：{db_path}")
        print("   请先运行爬虫代码生成fortune500.db文件")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        # 读取全部数据
        sql = """
        SELECT rank, company, revenue, profit, country, company_url 
        FROM company_info 
        WHERE company != '无数据' -- 过滤无效数据
        """
        df = pd.read_sql(sql, conn)
        conn.close()
        
        # 数据格式转换：处理非数字字符，转为数值型
        df['revenue'] = pd.to_numeric(
            df['revenue'].replace(['无数据', '--', '—'], '0').str.replace(',', ''),
            errors='coerce'
        ).fillna(0)
        
        df['profit'] = pd.to_numeric(
            df['profit'].replace(['无数据', '--', '—'], '0').str.replace(',', ''),
            errors='coerce'
        ).fillna(0)
        
        print(f"✅ 成功读取 {len(df)} 条有效数据")
        print("📊 数据预览：")
        print(df[['rank', 'company', 'revenue', 'profit', 'country']].head(5))
        
        return df
    except Exception as e:
        print(f"❌ 读取数据库失败：{str(e)}")
        return None

def generate_visualizations(df):
    # 创建可视化文件夹，避免文件杂乱
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '可视化结果')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 导出完整数据到Excel
    excel_path = os.path.join(output_dir, '财富500强完整数据.xlsx')
    df.to_excel(excel_path, index=False)
    print(f"📄 数据表格已保存：{excel_path}")
    
    def clean_company_name(name):
        """彻底移除括号及内部的英文名，只保留中文主体"""
        # 处理半角括号 (xxx)
        if '(' in name:
            name = name.split('(')[0].strip()
        # 处理全角括号 （xxx）
        if '（' in name:
            name = name.split('（')[0].strip()
        # 移除多余符号，保证名称简洁
        return name.replace(' ', '').replace('-', '').replace('_', '')
    
    # 第一步，去掉英文名
    df['clean_name'] = df['company'].apply(clean_company_name)
    
    # 第二步：名称去重，保留营收最高的记录
    df_unique = df.sort_values('revenue', ascending=False).drop_duplicates(
        subset='clean_name',
        keep='first'
    )
    
    # 第三步，筛选前10家
    top10 = df_unique.sort_values('revenue', ascending=False).head(10)
    top10['short_name'] = top10['clean_name']
    
    # 打印验证：确认名称已清洗
    print("✅ 清洗后（无英文名）的前10家公司：")
    print(top10['short_name'].tolist())
    print(f"✅ 前10家公司数量：{len(top10)}")
    
    # 绘制营收/利润对比图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(22, 14))
    
    # 营收柱状图
    ax1.barh(top10['short_name'], top10['revenue'], color='#2E86AB', height=0.7)
    ax1.set_title('2025财富500强前10家公司营收排行', fontsize=14, pad=20)
    ax1.set_xlabel('营收（百万美元）', fontsize=12)
    ax1.grid(axis='x', alpha=0.3)
    ax1.tick_params(axis='y', labelsize=11)
    ax1.invert_yaxis()
    
    # 利润柱状图
    ax2.barh(top10['short_name'], top10['profit'], color='#A23B72', height=0.7)
    ax2.set_title('2025财富500强前10家公司利润对比', fontsize=14, pad=20)
    ax2.set_xlabel('利润（百万美元）', fontsize=12)
    ax2.grid(axis='x', alpha=0.3)
    ax2.tick_params(axis='y', labelsize=11)
    ax2.invert_yaxis()
    
    plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15, wspace=0.4)
    
    chart_path = os.path.join(output_dir, '前10家公司营收利润对比.png')
    #plt.tight_layout()
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"📈 对比图表已保存：{chart_path}")
    
    # 各国分布饼图
    country_count = df['country'].value_counts().head(10)
    fig2, ax3 = plt.subplots(figsize=(12, 8))
    ax3.pie(
        country_count.values, 
        labels=country_count.index,  
        autopct='%1.1f%%',
        startangle=90,
        colors=plt.cm.Set3.colors
    )
    ax3.set_title('2025财富500强前10大上榜国家分布', fontsize=14, pad=20)
    pie_path = os.path.join(output_dir, '各国企业数量分布.png')
    plt.tight_layout()
    plt.savefig(pie_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"🥧 饼图已保存：{pie_path}")


if __name__ == '__main__':
    # 读取数据
    data_df = read_fortune500_data()
    
    # 生成可视化
    if data_df is not None and len(data_df) > 0:
        generate_visualizations(data_df)
        print("\n🎉 所有可视化文件已生成完成！")
    else:
        print("\n❌ 可视化失败：无有效数据，请检查爬虫是否正常入库！")
