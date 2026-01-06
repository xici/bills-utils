import pandas as pd
import os
import glob

SOURCE_DIR = "/data/bills"  # CSV 账单所在目录
OUTPUT_SQL = "alipay_bills_all.sql" # 生成的 SQL 语句文件名
TABLE_NAME = "alipay_bills" # 数据库表名

def process_alipay_csv(file_path):
    """专门解析支付宝CSV格式：寻找表头并清洗数据"""
    try:
        # 支付宝CSV通常是 GB18030 编码
        with open(file_path, "r", encoding="gb18030") as f:
            lines = f.readlines()

        # 1. 寻找表头行索引
        header_index = -1
        for i, line in enumerate(lines):
            if "交易时间" in line and "交易订单号" in line:
                header_index = i
                break

        if header_index == -1:
            print(f"跳过：文件 {file_path} 未找到支付宝标准表头")
            return None

        # 2. 从表头行开始重新读取数据
        # 支付宝CSV末尾常有多余逗号，这里手动指定列名防止错位
        df = pd.read_csv(
            file_path,
            encoding="gb18030",
            skiprows=header_index,
            on_bad_lines="skip",  # 忽略可能存在的坏行
        )

        # 3. 字段清洗
        # 去除列名的空格（支付宝导出的CSV列名常带空格）
        df.columns = [c.strip() for c in df.columns]

        # 只保留我们数据库需要的列，并进行重命名以匹配
        # 注意：支付宝CSV最后一列通常是空列，我们只取需要的字段
        mapping = {
            "交易时间": "transaction_time",
            "交易分类": "category",
            "交易对方": "counterparty",
            "对方账号": "counterparty_account",
            "商品说明": "product_name",
            "收/支": "direction",
            "金额": "amount",
            "收/付款方式": "payment_method",
            "交易状态": "status",
            "交易订单号": "transaction_id",
            "商家订单号": "merchant_id",
            "备注": "remark",
        }

        # 筛选存在的列
        df = df[list(mapping.keys())].copy()
        df.columns = [mapping[c] for c in df.columns]

        # 4. 数据预处理
        # 去除单号前后的空格（支付宝单号常有 \t 或空格后缀）
        df["transaction_id"] = df["transaction_id"].astype(str).str.strip()
        df["merchant_id"] = df["merchant_id"].astype(str).str.strip()

        # 金额转数值
        df["amount"] = pd.to_numeric(
            df["amount"].astype(str).str.replace(",", ""), errors="coerce"
        )

        # 剔除无效行（如单号为空或金额为空的行）
        df = df.dropna(subset=["transaction_id", "amount"])

        return df

    except Exception as e:
        print(f"解析文件 {file_path} 出错: {e}")
        return None


def run_batch():
    all_files = glob.glob(os.path.join(SOURCE_DIR, "*.csv"))
    print(f"找到 {len(all_files)} 个支付宝 CSV 文件待处理...")

    with open(OUTPUT_SQL, "w", encoding="utf-8") as f_out:
        for file_path in all_files:
            print(f"正在处理: {os.path.basename(file_path)}...")
            df = process_alipay_csv(file_path)

            if df is not None and not df.empty:
                for _, row in df.iterrows():

                    def clean(val):
                        if pd.isna(val):
                            return ""
                        # 处理单引号，防止SQL注入/错误
                        return str(val).replace("'", "''").strip()

                    sql = (
                        f"INSERT INTO {TABLE_NAME} (transaction_time, category, counterparty, "
                        f"counterparty_account, product_name, direction, amount, payment_method, "
                        f"status, transaction_id, merchant_id, remark) VALUES ("
                        f"'{clean(row['transaction_time'])}', '{clean(row['category'])}', '{clean(row['counterparty'])}', "
                        f"'{clean(row['counterparty_account'])}', '{clean(row['product_name'])}', '{clean(row['direction'])}', "
                        f"{row['amount']}, '{clean(row['payment_method'])}', '{clean(row['status'])}', "
                        f"'{clean(row['transaction_id'])}', '{clean(row['merchant_id'])}', '{clean(row['remark'])}');\n"
                    )
                    f_out.write(sql)

    print(f"\n全部完成！生成的 SQL 文件：{OUTPUT_SQL}")


if __name__ == "__main__":
    run_batch()
