import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
import sys
import pathlib
import csv
from datetime import datetime

# 设置字体
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "Source Han Sans CN",
    "WenQuanYi Micro Hei",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False

def detect_header(csv_file_path):
    """
    检测CSV文件的表头位置
    
    Args:
        csv_file_path: CSV文件路径
        
    Returns:
        tuple: (表头所在行号（0-based）, 使用的编码)，如果找不到返回(-1, None)
    """
    # 尝试的编码列表（按优先级排序）
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    
    for encoding in encodings_to_try:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                
                # 先检查第25行（索引24，0-based）
                for i, row in enumerate(reader):
                    if i == 24:  # 第25行
                        # 检查这一行是否包含预期的表头关键词
                        header_keywords = ['交易时间', '交易分类', '交易对方', '收/支', '金额', '收/付款方式']
                        row_text = ''.join(row)
                        if any(keyword in row_text for keyword in header_keywords):
                            print(f"使用编码 {encoding} 检测到表头在第 {i + 1} 行")
                            return i, encoding
                        break
                
                # 如果第25行不是表头，从第一行开始查找
                f.seek(0)
                for i, row in enumerate(reader):
                    row_text = ''.join(row)
                    header_keywords = ['交易时间', '交易分类', '交易对方', '收/支', '金额', '收/付款方式']
                    if any(keyword in row_text for keyword in header_keywords):
                        print(f"使用编码 {encoding} 检测到表头在第 {i + 1} 行")
                        return i, encoding
                    
                    # 最多检查前50行
                    if i >= 49:
                        break
                        
        except UnicodeDecodeError:
            # 编码不匹配，尝试下一个编码
            continue
        except Exception as e:
            print(f"使用编码 {encoding} 检测表头时出错: {e}")
            continue
    
    print(f"错误: 无法使用任何支持的编码读取文件: {csv_file_path}")
    print(f"尝试的编码: {encodings_to_try}")
    return -1, None

def read_alipay_csv(file_path):
    """
    读取支付宝CSV文件
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        pd.DataFrame: 包含账单数据的DataFrame，失败时返回None
    """
    try:
        # 检测表头位置和编码
        header_row, file_encoding = detect_header(file_path)
        
        if header_row == -1 or file_encoding is None:
            print(f"错误: 无法在文件中找到表头或确定编码: {file_path}")
            return None
        
        print(f"检测到表头在第 {header_row + 1} 行，使用编码: {file_encoding}")
        
        # 读取CSV文件，跳过表头之前的所有行，使用检测到的编码
        df = pd.read_csv(file_path, encoding=file_encoding, skiprows=header_row)
        
        # 检查必要的列是否存在
        required_columns = ['交易时间', '交易分类', '交易对方', '收/支', '金额', '收/付款方式']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"错误: CSV文件缺少必要的列: {missing_columns}")
            print(f"找到的列: {list(df.columns)}")
            return None
        
        print(f"成功读取文件: {file_path} ({len(df)} 条记录)")
        return df
        
    except Exception as e:
        print(f"读取CSV文件失败 {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_alipay_bills(file_paths, output_file="alipay_result.jpg", single_file_mode=False):
    """
    分析支付宝账单数据并生成可视化图表
    
    Args:
        file_paths: CSV文件路径列表
        output_file: 输出图片文件路径或目录
        single_file_mode: 是否为单文件模式（True: 每个文件单独分析，False: 合并分析）
    """
    if single_file_mode:
        # 批量分析模式：每个文件单独分析
        for i, file_path in enumerate(file_paths):
            print(f"\n{'='*60}")
            print(f"分析文件 {i+1}/{len(file_paths)}: {file_path}")
            print(f"{'='*60}")
            
            # 生成输出文件名
            if len(file_paths) == 1 and not os.path.isdir(output_file):
                # 只有一个文件且输出不是目录时，使用指定的输出文件名
                file_output = output_file
            else:
                # 多个文件或输出是目录时，为每个文件生成独立的输出文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 确定输出目录
                if os.path.isdir(output_file):
                    output_dir = output_file
                else:
                    output_dir = os.path.dirname(output_file) if os.path.dirname(output_file) else "."
                
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成输出文件名
                file_output = os.path.join(output_dir, f"{base_name}_analysis.jpg")
            
            # 分析单个文件
            analyze_single_alipay_file(file_path, file_output, is_single_file=True)
        
        print(f"\n批量分析完成！共处理 {len(file_paths)} 个文件。")
    else:
        # 合并分析模式：将所有文件数据合并后分析
        print(f"\n{'='*60}")
        print(f"合并分析模式：将 {len(file_paths)} 个文件的数据合并后分析")
        print(f"{'='*60}")
        analyze_merged_alipay_files(file_paths, output_file)

def analyze_single_alipay_file(file_path, output_file="alipay_result.jpg", is_single_file=True):
    """
    分析单个支付宝CSV文件
    
    Args:
        file_path: CSV文件路径
        output_file: 输出图片文件路径
        is_single_file: 是否为单个文件（用于决定年份统计图类型）
    """
    # 读取数据
    df = read_alipay_csv(file_path)
    
    if df is None:
        print(f"无法分析文件: {file_path}")
        return
    
    # 分析数据
    analyze_alipay_data(df, output_file, is_single_file)

def analyze_merged_alipay_files(file_paths, output_file="alipay_result.jpg"):
    """
    合并多个支付宝CSV文件的数据后分析
    
    Args:
        file_paths: CSV文件路径列表
        output_file: 输出图片文件路径
    """
    ### 1. 加载并合并数据 ###
    dfs = []
    
    for file_path in file_paths:
        df = read_alipay_csv(file_path)
        if df is not None:
            dfs.append(df)
            print(f"成功读取文件: {file_path} ({len(df)} 条记录)")
    
    if not dfs:
        print("错误: 没有成功读取任何文件")
        return
    
    # 合并所有数据
    df = pd.concat(dfs, ignore_index=True)
    print(f"合并后总记录数: {len(df)} 条")
    
    # 分析合并后的数据（is_single_file=False 表示多个文件合并，使用饼图）
    analyze_alipay_data(df, output_file, is_single_file=False)

def analyze_alipay_data(df, output_file="alipay_result.jpg", is_single_file=True):
    """
    分析支付宝账单数据
    
    Args:
        df: 包含支付宝账单数据的DataFrame
        output_file: 输出图片文件路径
        is_single_file: 是否为单个文件（用于决定年份统计图类型）
    """
    ### 数据预处理 ###
    
    # 转换交易时间为 datetime 对象
    df["交易时间"] = pd.to_datetime(df["交易时间"])
    
    # 转换金额为数值类型
    df["金额"] = pd.to_numeric(df["金额"], errors='coerce')
    
    # 提取时间特征
    df["年份"] = df["交易时间"].dt.year
    df["月份"] = df["交易时间"].dt.month
    df["小时"] = df["交易时间"].dt.hour
    
    # 清理交易分类数据
    df["交易分类"] = df["交易分类"].fillna("未知分类")
    
    # 清理收/付款方式数据
    df["收/付款方式"] = df["收/付款方式"].fillna("未知方式")
    
    ### 统计逻辑实现 ###
    
    # (1) 划分日内时段
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
    
    # (2) 金额分组统计
    bins = [0, 50, 100, 300, 1000, float("inf")]
    labels = ["0-50", "50-100", "100-300", "300-1000", "1000+"]
    df["金额区间"] = pd.cut(df["金额"], bins=bins, labels=labels)
    
    ### 可视化绘图 ###
    fig = plt.figure(figsize=(20, 15))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    
    # 图1: 按自然年分类（根据是否为单个文件决定使用柱状图还是饼图）
    plt.subplot(3, 3, 1)
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
    
    # 图2: 按自然月分类 (饼状图)
    plt.subplot(3, 3, 2)
    month_counts = df["月份"].value_counts().sort_index()
    plt.pie(
        month_counts, labels=[f"{m}月" for m in month_counts.index], autopct="%1.1f%%"
    )
    plt.title("月度交易分布")
    
    # 图3: 日内交易时段 (饼状图)
    plt.subplot(3, 3, 3)
    period_counts = df["时段"].value_counts()
    plt.pie(period_counts, labels=period_counts.index, autopct="%1.1f%%")
    plt.title("日内交易时段占比")
    
    # 图4: 收/支比重 (饼状图 + 金额)
    plt.subplot(3, 3, 4)
    type_sum = df.groupby("收/支")["金额"].sum()
    labels_with_money = [f"{i}\n({v:.2f}元)" for i, v in type_sum.items()]
    plt.pie(
        type_sum,
        labels=labels_with_money,
        autopct="%1.1f%%",
        colors=["#ff9999", "#66b3ff", "#99ff99"],
    )
    plt.title("收/支金额及占比")
    
    # 图5: 交易对方 (饼状图 - 小于3%的归为其他)
    plt.subplot(3, 3, 5)
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
    plt.subplot(3, 3, 6)
    amount_bins = df["金额区间"].value_counts().sort_index()
    plt.pie(amount_bins, labels=amount_bins.index, autopct="%1.1f%%")
    plt.title("交易金额区间分布")
    
    # 图7: 收/付款方式统计 (饼状图 - 合并收款和付款方式)
    plt.subplot(3, 3, 7)
    # 统计所有交易记录中的收/付款方式
    payment_method_counts = df["收/付款方式"].value_counts()
    
    if not payment_method_counts.empty:
        # 计算百分比
        total_count = payment_method_counts.sum()
        payment_percentages = payment_method_counts / total_count * 100
        
        # 按百分比筛选支付方式
        payment_percentages_to_hide = 2.0
        significant_payments = payment_method_counts[payment_percentages >= payment_percentages_to_hide]
        
        # 将小于指定百分比的合并为"其他"
        other_payment_count = payment_method_counts[payment_percentages < payment_percentages_to_hide].sum()
        
        # 创建最终的饼图数据
        payment_pie_data = significant_payments.copy()
        if other_payment_count > 0:
            payment_pie_data["其他"] = other_payment_count
        
        plt.pie(payment_pie_data, labels=payment_pie_data.index, autopct="%1.1f%%")
        plt.title(f"收/付款方式分布(≥{payment_percentages_to_hide}%)")
    else:
        plt.text(0.5, 0.5, "无支付方式数据", ha='center', va='center')
        plt.title("收/付款方式分布")
    
    # 图8: 交易分类统计 (饼状图 - 小于2%的归为其他)
    plt.subplot(3, 3, 8)
    category_counts = df["交易分类"].value_counts()
    total_category_count = category_counts.sum()
    
    # 计算每个交易分类的百分比
    category_percentages = category_counts / total_category_count * 100
    
    # 按百分比筛选交易分类
    category_percentages_to_hide = 2.0
    significant_categories = category_counts[category_percentages >= category_percentages_to_hide]
    
    # 将小于指定百分比的合并为"其他"
    other_category_count = category_counts[category_percentages < category_percentages_to_hide].sum()
    
    # 创建最终的饼图数据
    category_pie_data = significant_categories.copy()
    if other_category_count > 0:
        category_pie_data["其他"] = other_category_count
    
    plt.pie(category_pie_data, labels=category_pie_data.index, autopct="%1.1f%%")
    plt.title(f"交易分类分布(≥{category_percentages_to_hide}%)")
    
    # 图9: 交易状态统计 (饼状图)
    plt.subplot(3, 3, 9)
    # 检查是否有交易状态列
    if "交易状态" in df.columns:
        status_counts = df["交易状态"].value_counts()
        if not status_counts.empty:
            plt.pie(status_counts, labels=status_counts.index, autopct="%1.1f%%")
            plt.title("交易状态分布")
        else:
            plt.text(0.5, 0.5, "无交易状态数据", ha='center', va='center')
            plt.title("交易状态分布")
    else:
        plt.text(0.5, 0.5, "无交易状态列", ha='center', va='center')
        plt.title("交易状态分布")
    
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"支付宝账单可视化图表已保存到: {output_file}")

def find_csv_files(input_path):
    """
    查找CSV文件
    
    Args:
        input_path: 文件路径或目录路径
        
    Returns:
        list: CSV文件路径列表
    """
    csv_files = []
    
    if os.path.isfile(input_path):
        # 单个文件
        if input_path.lower().endswith('.csv'):
            csv_files.append(input_path)
        else:
            print(f"警告: 文件不是CSV格式: {input_path}")
    else:
        # 目录
        if not os.path.isdir(input_path):
            print(f"错误: 路径不存在: {input_path}")
            return []
        
        # 查找目录中的所有CSV文件（递归查找，避免重复）
        files = list(pathlib.Path(input_path).rglob("*.csv"))
        # 过滤掉隐藏文件
        files = [f for f in files if not any(part.startswith('.') for part in f.parts)]
        csv_files.extend(files)
    
    # 去重并排序
    csv_files = list(set(csv_files))
    csv_files.sort()
    
    return csv_files

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="支付宝账单CSV可视化分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 分析单个CSV文件（合并分析模式）
  python %(prog)s bill.csv
  
  # 分析单个CSV文件并指定输出文件（合并分析模式）
  python %(prog)s bill.csv -o ./output/alipay_chart.jpg
  
  # 分析目录中的所有CSV文件（合并分析模式）
  python %(prog)s ./csv_files
  
  # 分析目录中的所有CSV文件并指定输出文件（合并分析模式）
  python %(prog)s ./csv_files -o ./output/merged_alipay_chart.jpg
  
  # 批量分析目录中的所有CSV文件（每个文件单独分析）
  python %(prog)s ./csv_files -b
  
  # 批量分析目录中的所有CSV文件并指定输出目录
  python %(prog)s ./csv_files -b -o ./output/
        """,
    )
    
    parser.add_argument("input", help="CSV文件路径或包含CSV文件的目录")
    
    parser.add_argument(
        "-o", "--output",
        help="输出图片文件路径或目录（可选，默认为alipay_result.jpg）",
        default="alipay_result.jpg"
    )
    
    parser.add_argument(
        "-b", "--batch",
        action="store_true",
        help="批量分析模式：每个文件单独分析并生成独立的图表文件",
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="支付宝账单 CSV 可视化分析工具 v1.0",
    )
    
    args = parser.parse_args()
    
    input_path = args.input
    output_file = args.output
    batch_mode = args.batch
    
    # 检查输入路径是否存在
    if not os.path.exists(input_path):
        print(f"错误: 输入路径不存在: {input_path}")
        return 1
    
    # 查找CSV文件
    csv_files = find_csv_files(input_path)
    
    if not csv_files:
        print(f"错误: 未找到CSV文件: {input_path}")
        return 1
    
    print(f"找到 {len(csv_files)} 个CSV文件:")
    for file in csv_files:
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
    analyze_alipay_bills(csv_files, output_file, single_file_mode=batch_mode)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
