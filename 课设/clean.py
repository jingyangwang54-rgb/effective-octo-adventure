import sqlite3
import pandas as pd
import os

def clean_fortune500_db():
    """
    """
    #1. 定位数据库（绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'fortune500.db')
    
    print("="*50)
    print(f"数据库路径：{db_path}")
    print(f"数据库是否存在：{os.path.exists(db_path)}")
    if not os.path.exists(db_path):
        print("❌ 未找到数据库文件！")
        return

    # 2. 连接数据库并读取数据
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM company_info", conn)        #存为DataFrame
    original_count = len(df)
    print(f"\n【清洗前】总数据量：{original_count}")
    print(f"【清洗前】唯一公司数：{df['company'].nunique()}")

    # 3. 清洗公司名称
    def clean_company_name(name):
        """清洗公司名：去掉括号/英文名/空格，只保留中文主体"""
        if pd.isna(name) or name == "无数据":
            return "无数据"
        if '(' in name:
            name = name.split('(')[0].strip()
        if '（' in name:
            name = name.split('（')[0].strip()
        name = name.replace(' ', '').strip()
        return name

    df['clean_company'] = df['company'].apply(clean_company_name)
    
    # 4.检查重复公司
    duplicate_companies = df['clean_company'].value_counts()[df['clean_company'].value_counts() > 1]
    print(f"\n【清洗后】重复公司数量：{len(duplicate_companies)}")
    if len(duplicate_companies) > 0:
        print("前5个重复公司：")
        print(duplicate_companies.head())

    # 5. 标准化营收/利润为数值类型
    def convert_to_numeric(val):
        """转换营收/利润为数值：去掉逗号、替换无数据/0为0.0"""
        if pd.isna(val) or val in ["无数据", "0", "", "--", "—"]:
            return 0.0
        # 去掉逗号（爬虫爬取的revenue含逗号，如"1,234"）
        val = str(val).replace(',', '').strip()
        try:
            return float(val)
        except:
            return 0.0

    df['revenue_num'] = df['revenue'].apply(convert_to_numeric)
    df['profit_num'] = df['profit'].apply(convert_to_numeric)
    
    print(f"\n【数值转换】营收最大值：{df['revenue_num'].max():,.2f}")
    print(f"【数值转换】利润最大值：{df['profit_num'].max():,.2f}")

    # 6. 去重：保留同一公司营收最高的记录
    # 按营收降序排序
    df_sorted = df.sort_values('revenue_num', ascending=False)
    df_clean = df_sorted.drop_duplicates(subset='clean_company', keep='first')
    clean_count = len(df_clean)
    
    print(f"\n【去重后】总数据量：{clean_count}")
    print(f"【去重后】删除重复数据：{original_count - clean_count} 条")

    # 7. 覆盖原表
    # 去掉临时清洗列，只保留原表字段
    df_clean_final = df_clean[['rank', 'company', 'company_url', 'revenue', 'profit', 'country']]
    # 清空原表并插入清洗后的数据
    conn.execute("DELETE FROM company_info")
    df_clean_final.to_sql('company_info', conn, if_exists='append', index=False)
    conn.commit()

    # 8. 最终验证
    df_final = pd.read_sql("SELECT * FROM company_info", conn)
    df_final['clean_company'] = df_final['company'].apply(clean_company_name)
    final_duplicates = df_final['clean_company'].value_counts()[df_final['clean_company'].value_counts() > 1]
    
    print(f"\n【最终验证】数据总量：{len(df_final)}")
    print(f"【最终验证】重复公司数：{len(final_duplicates)}")
    print(f"【最终验证】唯一公司数：{df_final['clean_company'].nunique()}")

    # 9. 关闭连接
    conn.close()
    print("\n✅ 数据库清洗完成！")

if __name__ == "__main__":
    clean_fortune500_db()
