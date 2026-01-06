## 使用说明

基本用法：

```bash
# 转换单个 PDF 文件
python wx_conversion.py bill.pdf

# 转换单个 PDF 文件并指定输出目录
python wx_conversion.py bill.pdf ./output

# 转换目录中的所有 PDF 文件
python wx_conversion.py ./pdf_files

# 转换目录中的所有 PDF 文件并指定输出目录
python wx_conversion.py ./pdf_files ./output
```

查看帮助：

```bash
python wx_conversion.py -h
```

## 输出说明

- 转换后的 Excel 文件将保存在指定输出目录（默认为输入文件所在目录）
- 文件名格式：`原文件名_converted_时间戳。xlsx`
- Excel 文件包含"账单"工作表，包含原始 PDF 中的所有交易记录
- 日期和金额格式已自动处理

## 错误处理

- 文件不存在或格式错误时中断程序
- 批量处理时，单个文件失败不影响其他文件