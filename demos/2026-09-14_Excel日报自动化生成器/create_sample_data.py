#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成示例数据
运行后会在当前目录创建 sample_data.xlsx，包含50条模拟销售数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# 生成50条模拟销售数据
categories = ['电子产品', '服装鞋帽', '食品饮料', '家居用品', '美妆个护']
products = {
    '电子产品': ['手机', '笔记本', '耳机', '平板', '智能手表'],
    '服装鞋帽': ['T恤', '牛仔裤', '运动鞋', '外套', '帽子'],
    '食品饮料': ['咖啡', '零食大礼包', '茶叶', '果汁', '坚果'],
    '家居用品': ['台灯', '收纳盒', '抱枕', '地毯', '水杯'],
    '美妆个护': ['面膜', '口红', '洗发水', '面霜', '香水']
}
regions = ['华东', '华南', '华北', '西南', '华中']
channels = ['线上商城', '线下门店', '小程序', '第三方平台']

data = []
start_date = datetime(2026, 9, 1)

for i in range(50):
    category = np.random.choice(categories)
    product = np.random.choice(products[category])
    date = start_date + timedelta(days=np.random.randint(0, 14))
    quantity = np.random.randint(1, 20)
    price = round(np.random.uniform(50, 2000), 2)
    amount = round(quantity * price, 2)

    data.append({
        '订单号': f'ORD{2026090000 + i + 1}',
        '日期': date.strftime('%Y-%m-%d'),
        '产品类别': category,
        '产品名称': product,
        '数量': quantity,
        '单价': price,
        '销售额': amount,
        '地区': np.random.choice(regions),
        '销售渠道': np.random.choice(channels),
        '客户类型': np.random.choice(['新客户', '老客户', '会员'])
    })

# 故意加入几条重复数据和空值，测试清洗功能
data.append(data[0].copy())  # 重复行
data.append(data[5].copy())  # 重复行
data[10]['销售额'] = None  # 空值

df = pd.DataFrame(data)

# 写入Excel
output_path = 'sample_data.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='销售数据', index=False)

print(f"✅ 示例数据已生成：{output_path}")
print(f"   共 {len(df)} 行数据（含2条重复、1个空值，用于测试清洗功能）")
print(f"   列名：{', '.join(df.columns.tolist())}")
print(f"   日期范围：2026-09-01 ~ 2026-09-14")
print()
print("   现在可以运行：python3 daily_report_generator.py")
