# Bills-Utils

微信和支付宝导出的账单处理工具。

## 功能特性

- 微信账单导出的 PDF 转 Excel
- 微信账单 Excel, 支付宝 CSV 转 SQL 语句 (MySQL)
- 可视化图表

## 运行环境

- Python >= 3.13
- uv

安装依赖并创建虚拟环境：

```bash
uv sync
```

## 使用方法

文件之间无依赖关系，直接运行即可。

```bash
python utils-file.py # [args...]
```

## 免责声明

请见 [免责声明](doc/disclaimer.md)

## 致谢

- [Gitee:tangx_666/wechat-bills](https://gitee.com/tangx_666/wechat-bills): 提供微信账单 PDF 转换为 Excel 的基础的核心逻辑。
- [DeepSeek](https://www.deepseek.com): 帮助重构程序。
- [Cline](https://github.com/cline/cline): 帮助重构程序。

## LICENSE

[GPL3](./LICENSE)