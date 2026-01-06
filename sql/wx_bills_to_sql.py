import pandas as pd
import os
import glob

SOURCE_DIR = "/data/bills"  # Excel 账单文件目录
OUTPUT_SQL = "wechat_bills_all.sql"  # 生成的 SQL 语句文件名
TABLE_NAME = "wechat_bills" # 数据库表名

def process_file(file_path):
    """鲁棒性读取并定位真实数据起始行"""
    try:
        # 1. 尝试读取，不设表头(header=None)，方便我们手动寻找“交易单号”所在行
        df_raw = pd.read_excel(file_path, engine="openpyxl", header=None)
    except Exception:
        try:
            df_raw = pd.read_csv(file_path, header=None, encoding="utf-8")
        except:
            df_raw = pd.read_csv(file_path, header=None, encoding="gb18030")

    # 2. 自动寻找表头所在的行索引
    header_row_index = None
    for i, row in df_raw.iterrows():
        if "交易单号" in str(row.values):
            header_row_index = i
            break

    if header_row_index is None:
        print(f"跳过：文件 {file_path} 未能识别到交易记录表头")
        return None

    # 3. 重新以发现的表头行读取数据
    df = df_raw.iloc[header_row_index + 1 :].copy()
    # 强制手动设置列名，确保对应
    df.columns = [
        "transaction_id",
        "transaction_time",
        "transaction_type",
        "direction",
        "payment_method",
        "amount",
        "counterparty",
        "merchant_id",
    ]

    # 4. 数据清理：处理金额
    # 先强制转为字符串，再替换符号，最后转回 float 以便写入 SQL
    # 这样无论 Excel 里存的是 "¥30.00" 还是数字 30.00 都能处理
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace("¥", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    # 过滤掉金额转换后可能产生的空值，并确保它是数值类型
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    # 去除无效行（如末尾的空行）
    df = df.dropna(subset=["transaction_id"])
    return df


def run_batch():
    # 获取所有真正的 xlsx 文件，排除以 .~ 开头的临时文件
    all_files = [
        f
        for f in glob.glob(os.path.join(SOURCE_DIR, "*.xlsx"))
        if not os.path.basename(f).startswith(".~")
    ]

    print(f"找到 {len(all_files)} 个有效文件待处理...")

    with open(OUTPUT_SQL, "w", encoding="utf-8") as f_out:
        for file_path in all_files:
            print(f"正在处理: {os.path.basename(file_path)}...")
            df = process_file(file_path)

            if df is not None and not df.empty:
                for _, row in df.iterrows():

                    def clean(val):
                        # 处理单引号并转为字符串
                        return str(val).replace("'", "''") if pd.notna(val) else ""

                    sql = (
                        f"INSERT INTO {TABLE_NAME} (transaction_id, transaction_time, transaction_type, "
                        f"direction, payment_method, amount, counterparty, merchant_id) VALUES ("
                        f"'{clean(row['transaction_id'])}', '{clean(row['transaction_time'])}', "
                        f"'{clean(row['transaction_type'])}', '{clean(row['direction'])}', "
                        f"'{clean(row['payment_method'])}', {row['amount']}, "
                        f"'{clean(row['counterparty'])}', '{clean(row['merchant_id'])}');\n"
                    )
                    f_out.write(sql)

    print(f"\n全部完成！生成的 SQL 文件：{OUTPUT_SQL}")


if __name__ == "__main__":
    run_batch()
