import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
import sys
import pathlib
from datetime import datetime

# 设置字体
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "Source Han Sans CN",
    "WenQuanYi Micro Hei",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

def analyze_bills(file_paths, output_file=f"result-{datetime.now().timestamp()}.jpg", single_file_mode=False):
    """
    分析账单数据并生成可视化图表
    
    Args:
        file_paths: Excel文件路径列表
        output_file: 输出图片文件路径
        single_file_mode: 是否为单文件模式（True: 每个文件单独分析，False: 合并分析）
    """
    if single_file_mode:
        # 批量分析模式：每个文件单独分析
        for i, file_path in enumerate(file_paths):
            print(f"\n{'='*60}")
            print(f"分析文件 {i+1}/{len(file_paths)}: {file_path}")
            print(f"{'='*60}")
            
            # 生成输出文件名
            if len(file_paths) == 1:
                # 只有一个文件时使用指定的输出文件名
                file_output = output_file
            else:
                # 多个文件时，为每个文件生成独立的输出文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
                file_output = os.path.join(output_dir, f"{base_name}_analysis.jpg")
            
            # 分析单个文件
            analyze_single_file(file_path, file_output, is_single_file=True)
        
        print(f"\n批量分析完成！共处理 {len(file_paths)} 个文件。")
    else:
        # 合并分析模式：将所有文件数据合并后分析
        print(f"\n{'='*60}")
        print(f"合并分析模式：将 {len(file_paths)} 个文件的数据合并后分析")
        print(f"{'='*60}")
        analyze_merged_files(file_paths, output_file)


def analyze_single_file(file_path, output_file=f"result-{datetime.now().timestamp()}.jpg", is_single_file=True):
    """
    分析单个Excel文件
    
    Args:
        file_path: Excel文件路径
        output_file: 输出图片文件路径
        is_single_file: 是否为单个文件（用于决定年份统计图类型）
    """
    try:
        df = pd.read_excel(file_path)
        print(f"成功读取文件: {file_path} ({len(df)} 条记录)")
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return
    
    # 忽略不需要的列
    cols_to_drop = ["交易单号", "商户单号"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    ### 数据预处理 ###

    # 转换交易时间为 datetime 对象
    df["交易时间"] = pd.to_datetime(df["交易时间"])
    df["金额(元)"] = pd.to_numeric(df["金额(元)"])

    # 提取时间特征
    df["年份"] = df["交易时间"].dt.year
    df["月份"] = df["交易时间"].dt.month
    df["小时"] = df["交易时间"].dt.hour

    ### 统计逻辑实现 ###

    # (2) 划分日内时段
    def get_time_period(hour):
        if 0 <= hour < 6:
            return "凌晨(0-6am)"
        elif 6 <= hour < 12:
            return "上午(6-12am)"
        elif 12 <= hour < 18:
            return "下午(12-18pm)"
        else:
            return "晚上(18-0am)"

    df["时段"] = df["小时"].apply(get_time_period)

    # (6) 金额分组统计
    bins = [0, 50, 100, 300, 1000, float("inf")]
    labels = ["0-50", "50-100", "100-300", "300-1000", "1000+"]
    df["金额区间"] = pd.cut(df["金额(元)"], bins=bins, labels=labels)

    ### 可视化绘图 ###
    fig = plt.figure(figsize=(18, 12))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)

    # 图1: 按自然年分类（根据是否为单个文件决定使用柱状图还是饼图）
    plt.subplot(2, 3, 1)
    year_counts = df["年份"].value_counts().sort_index()
    
    if is_single_file:
        # 单个文件时使用柱状图
        year_counts.plot(kind="bar", color="skyblue")
        plt.title("每年交易笔数统计（柱状图）")
        plt.xlabel("年份")
        plt.ylabel("笔数")
    else:
        # 多个文件合并时使用饼图
        plt.pie(year_counts, labels=year_counts.index, autopct="%1.1f%%")
        plt.title("每年交易笔数统计（饼图）")

    # 图2: 按自然月分类 (饼状图 - 以所有年份汇总为例)
    plt.subplot(2, 3, 2)
    month_counts = df["月份"].value_counts().sort_index()
    plt.pie(
        month_counts, labels=[f"{m}月" for m in month_counts.index], autopct="%1.1f%%"
    )
    plt.title("月度交易分布")

    # 图3: 日内交易时段 (饼状图)
    plt.subplot(2, 3, 3)
    period_counts = df["时段"].value_counts()
    plt.pie(period_counts, labels=period_counts.index, autopct="%1.1f%%")
    plt.title("日内交易时段占比")

    # 图4: 收/支比重 (饼状图 + 金额)
    plt.subplot(2, 3, 4)
    type_sum = df.groupby("收/支/其他")["金额(元)"].sum()
    labels_with_money = [f"{i}\n({v:.2f}元)" for i, v in type_sum.items()]
    plt.pie(
        type_sum,
        labels=labels_with_money,
        autopct="%1.1f%%",
        colors=["#ff9999", "#66b3ff", "#99ff99"],
    )
    plt.title("收/支金额及占比")

    # 图5: 交易对方 (饼状图 - 小于2%的归为其他)
    plt.subplot(2, 3, 5)
    opponent_counts = df["交易对方"].value_counts()
    total_count = opponent_counts.sum()

    # 计算每个交易对方的百分比
    opponent_percentages = opponent_counts / total_count * 100

    # 按百分比筛选交易对方
    percentages_to_hide = 3.0
    significant_opponents = opponent_counts[opponent_percentages >= percentages_to_hide]

    # 将小于指定百分比的合并为"其他"
    other_count = opponent_counts[opponent_percentages < percentages_to_hide].sum()

    # 创建最终的饼图数据
    pie_data = significant_opponents.copy()
    if other_count > 0:
        pie_data["其他"] = other_count

    plt.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%")
    plt.title(f"交易对方分布(≥{percentages_to_hide}%)")

    # 图6: 交易金额区间 (饼状图)
    plt.subplot(2, 3, 6)
    amount_bins = df["金额区间"].value_counts().sort_index()
    plt.pie(amount_bins, labels=amount_bins.index, autopct="%1.1f%%")
    plt.title("交易金额区间分布")

    plt.tight_layout()
    plt.savefig(output_file)
    print(f"可视化图表已保存到: {output_file}")


def analyze_merged_files(file_paths, output_file=f"result-{datetime.now().timestamp()}.jpg"):
    """
    合并多个Excel文件的数据后分析
    
    Args:
        file_paths: Excel文件路径列表
        output_file: 输出图片文件路径
    """
    ### 1. 加载并合并数据 ###
    dfs = []
    
    for file_path in file_paths:
        try:
            df = pd.read_excel(file_path)
            dfs.append(df)
            print(f"成功读取文件: {file_path} ({len(df)} 条记录)")
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            continue
    
    if not dfs:
        print("错误: 没有成功读取任何文件")
        return
    
    # 合并所有数据
    df = pd.concat(dfs, ignore_index=True)
    print(f"合并后总记录数: {len(df)} 条")
    
    # 分析合并后的数据（is_single_file=False 表示多个文件合并，使用饼图）
    analyze_single_file_data(df, output_file, is_single_file=False)


def analyze_single_file_data(df, output_file=f"result-{datetime.now().timestamp()}.jpg", is_single_file=True):
    """
    分析单个DataFrame数据
    
    Args:
        df: 包含账单数据的DataFrame
        output_file: 输出图片文件路径
        is_single_file: 是否为单个文件（用于决定年份统计图类型）
    """
    # 忽略不需要的列
    cols_to_drop = ["交易单号", "商户单号"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    ### 数据预处理 ###

    # 转换交易时间为 datetime 对象
    df["交易时间"] = pd.to_datetime(df["交易时间"])
    df["金额(元)"] = pd.to_numeric(df["金额(元)"])

    # 提取时间特征
    df["年份"] = df["交易时间"].dt.year
    df["月份"] = df["交易时间"].dt.month
    df["小时"] = df["交易时间"].dt.hour

    ### 统计逻辑实现 ###

    # (2) 划分日内时段
    def get_time_period(hour):
        if 0 <= hour < 6:
            return "凌晨(0-6am)"
        elif 6 <= hour < 12:
            return "上午(6-12am)"
        elif 12 <= hour < 18:
            return "下午(12-18pm)"
        else:
            return "晚上(18-0am)"

    df["时段"] = df["小时"].apply(get_time_period)

    # (6) 金额分组统计
    bins = [0, 50, 100, 300, 1000, float("inf")]
    labels = ["0-50", "50-100", "100-300", "300-1000", "1000+"]
    df["金额区间"] = pd.cut(df["金额(元)"], bins=bins, labels=labels)

    ### 可视化绘图 ###
    fig = plt.figure(figsize=(18, 12))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)

    # 图1: 按自然年分类（根据是否为单个文件决定使用柱状图还是饼图）
    plt.subplot(2, 3, 1)
    year_counts = df["年份"].value_counts().sort_index()
    
    if is_single_file:
        # 单个文件时使用柱状图
        year_counts.plot(kind="bar", color="skyblue")
        plt.title("每年交易笔数统计（柱状图）")
        plt.xlabel("年份")
        plt.ylabel("笔数")
    else:
        # 多个文件合并时使用饼图
        plt.pie(year_counts, labels=year_counts.index, autopct="%1.1f%%")
        plt.title("每年交易笔数统计（饼图）")

    # 图2: 按自然月分类 (饼状图 - 以所有年份汇总为例)
    plt.subplot(2, 3, 2)
    month_counts = df["月份"].value_counts().sort_index()
    plt.pie(
        month_counts, labels=[f"{m}月" for m in month_counts.index], autopct="%1.1f%%"
    )
    plt.title("月度交易分布")

    # 图3: 日内交易时段 (饼状图)
    plt.subplot(2, 3, 3)
    period_counts = df["时段"].value_counts()
    plt.pie(period_counts, labels=period_counts.index, autopct="%1.1f%%")
    plt.title("日内交易时段占比")

    # 图4: 收/支比重 (饼状图 + 金额)
    plt.subplot(2, 3, 4)
    type_sum = df.groupby("收/支/其他")["金额(元)"].sum()
    labels_with_money = [f"{i}\n({v:.2f}元)" for i, v in type_sum.items()]
    plt.pie(
        type_sum,
        labels=labels_with_money,
        autopct="%1.1f%%",
        colors=["#ff9999", "#66b3ff", "#99ff99"],
    )
    plt.title("收/支金额及占比")

    # 图5: 交易对方 (饼状图 - 小于2%的归为其他)
    plt.subplot(2, 3, 5)
    opponent_counts = df["交易对方"].value_counts()
    total_count = opponent_counts.sum()

    # 计算每个交易对方的百分比
    opponent_percentages = opponent_counts / total_count * 100

    # 按百分比筛选交易对方
    percentages_to_hide = 3.0
    significant_opponents = opponent_counts[opponent_percentages >= percentages_to_hide]

    # 将小于指定百分比的合并为"其他"
    other_count = opponent_counts[opponent_percentages < percentages_to_hide].sum()

    # 创建最终的饼图数据
    pie_data = significant_opponents.copy()
    if other_count > 0:
        pie_data["其他"] = other_count

    plt.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%")
    plt.title(f"交易对方分布(≥{percentages_to_hide}%)")

    # 图6: 交易金额区间 (饼状图)
    plt.subplot(2, 3, 6)
    amount_bins = df["金额区间"].value_counts().sort_index()
    plt.pie(amount_bins, labels=amount_bins.index, autopct="%1.1f%%")
    plt.title("交易金额区间分布")

    plt.tight_layout()
    plt.savefig(output_file)
    print(f"可视化图表已保存到: {output_file}")


def find_excel_files(input_path):
    """
    查找Excel文件
    
    Args:
        input_path: 文件路径或目录路径
        
    Returns:
        list: Excel文件路径列表
    """
    excel_files = []
    
    if os.path.isfile(input_path):
        # 单个文件
        if input_path.lower().endswith(('.xlsx', '.xls')):
            excel_files.append(input_path)
        else:
            print(f"警告: 文件不是Excel格式: {input_path}")
    else:
        # 目录
        if not os.path.isdir(input_path):
            print(f"错误: 路径不存在: {input_path}")
            return []
        
        # 查找目录中的所有Excel文件（递归查找，避免重复）
        for ext in ['.xlsx', '.xls']:
            # 使用递归查找，但避免重复匹配
            files = list(pathlib.Path(input_path).rglob(f"*{ext}"))
            # 过滤掉隐藏文件
            files = [f for f in files if not any(part.startswith('.') for part in f.parts)]
            excel_files.extend(files)
    
    # 去重并排序
    excel_files = list(set(excel_files))
    excel_files.sort()
    
    return excel_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="微信账单Excel可视化分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 分析单个Excel文件
  python %(prog)s bill.xlsx
  
  # 分析单个Excel文件并指定输出文件
  python %(prog)s bill.xlsx -o ./output/chart.jpg
  
  # 分析目录中的所有Excel文件（合并分析模式）
  python %(prog)s ./excel_files
  
  # 分析目录中的所有Excel文件并指定输出文件（合并分析模式）
  python %(prog)s ./excel_files -o ./output/merged_chart.jpg
  
  # 批量分析目录中的所有Excel文件
  python %(prog)s ./excel_files -b
  
  # 批量分析目录中的所有Excel文件并指定输出目录
  python %(prog)s ./excel_files -b -o ./output/
        """,
    )

    parser.add_argument("input", help="Excel文件路径或包含Excel文件的目录")

    parser.add_argument(
        "-o", "--output",
        help="输出图片文件路径或目录（可选，默认为result-时间戳.jpg）",
        default=f"result-{datetime.now().timestamp()}.jpg"
    )

    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="批量分析模式：每个文件单独分析并生成独立的图表文件",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="显示程序版本并退出",
        version="微信账单 Excel 可视化分析工具 v1.0",
    )

    args = parser.parse_args()

    input_path = args.input
    output_file = args.output
    batch_mode = args.batch

    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"错误: 输入路径不存在: {input_path}")
        return 1

    # 查找Excel文件
    excel_files = find_excel_files(input_path)

    if not excel_files:
        print(f"错误: 未找到Excel文件: {input_path}")
        return 1

    print(f"找到 {len(excel_files)} 个Excel文件:")
    for file in excel_files:
        print(f"  - {file}")

    # 处理输出路径
    if batch_mode:
        # 批量分析模式
        if os.path.isdir(output_file) or output_file.endswith('/') or output_file.endswith('\\'):
            # 如果输出路径是目录，确保目录存在
            os.makedirs(output_file, exist_ok=True)
            print(f"批量分析模式：每个文件的分析结果将保存到目录: {output_file}")
        else:
            # 如果输出路径是文件，使用其所在目录
            output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
            os.makedirs(output_dir, exist_ok=True)
            print(f"批量分析模式：每个文件的分析结果将保存到目录: {output_dir}")
    else:
        # 合并分析模式
        output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
        os.makedirs(output_dir, exist_ok=True)
        print(f"合并分析模式：所有文件的数据将合并分析，结果保存到: {output_file}")

    # 分析数据并生成图表
    analyze_bills(excel_files, output_file, single_file_mode=batch_mode)

    return 0


if __name__ == "__main__":
    sys.exit(main())
