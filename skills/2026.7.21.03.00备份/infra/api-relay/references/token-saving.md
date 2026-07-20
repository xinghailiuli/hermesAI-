# Token 节省工具

## RTK Compressor

**来源**: `Efficiency97/rtk-compressor` — Python CLI 输出压缩工具，降低 token 消耗 60-90%。

安装:

```bash
pip install --break-system-packages /tmp/rtk-compressor/
```

用法:

```bash
# 管道压缩（自动检测内容类型）
长命令输出 | rtk-compress

# 指定模式: auto | code | list | json | log | generic
cat large_file.py | rtk-compress --mode code

# 显示压缩统计
command | rtk-compress --stats
```

压缩效果:

| 类型 | 节省 |
|------|------|
| ls/tree | ~80% |
| cat/read 代码 | ~70% |
| 测试输出 | ~90% |

工作原理:
- 移除注释 (`#`, `//`, `/* */`)
- 移除空行，合并连续空行
- 压缩多余空白
- 列表去重 + 限制 50 条
- JSON 压缩为紧凑格式（截断 5000 字符）
- 日志只保留 ERROR/WARN/FAIL 行
- 通用输出截断至 10000 字符

⚠️ `--break-system-packages` 是 Ubuntu 24.04 PEP 668 的要求。
