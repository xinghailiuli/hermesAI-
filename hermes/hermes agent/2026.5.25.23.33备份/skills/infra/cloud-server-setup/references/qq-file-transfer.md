# QQ 传文件到服务器：模式与坑

## QQ 文件到达模式

QQ 转发文件到 Linux 服务器时，文件会出现在 `/tmp/` 下，但命名和行为不规律：

### 模式1：原始文件名保留在子目录
文件出现在 `/tmp/<dirname>/<original_name>`，如：
- `/tmp/dscode_install/deepseek.tar.gz`（tar.gz 保持原样）
- 目录名可能是之前解压残留的

### 模式2：随机临时文件名
文件以临时名出现在 `/tmp/` 顶层：
- `/tmp/tmpvb5d5um0`（17MB）
- `/tmp/tmpgvgne_e9`（1.2MB）
- 临时文件可能被 QQ 进程清理，不持久

### 模式3：QQ 包装（非标准 zip）
QQ 有时会把二进制文件包进一个非标准 zip 容器：
- `file` 命令显示 `Zip archive data`
- `unzip` 报 `End-of-central-directory signature not found` 或 `BadZipFile`
- 解法：跳过 QQ 包装，用 `grep -aboP '\x7fELF' <file>` 找原始 ELF 头，或 `tail -c +N` 截取
- 或者直接用 `tar xf` 试（有时 zip 伪装实际是 tar）

## 大文件截断

QQ 传输大文件（>~10MB）时可能静默截断：
- CodeWhale 18MB → 到达时仅 3.4MB，`file` 显示 `missing section headers`
- **无错误提示**，文件看起来正常只是变小了

### 解法：分割传输

```bash
# 发送端（WSL/本地）
split -b 9M codewhale-linux-x64 codewhale_part_

# 生成 codewhale_part_aa (~9MB), codewhale_part_ab (~8MB)
# 分别通过 QQ 发送

# 接收端（服务器）
cat codewhale_part_* > codewhale-linux-x64
chmod +x codewhale-linux-x64
```

## 查找 QQ 附件

### 首选：Hermes 缓存目录（最可靠）

QQ 发送的文件被 Hermes QQ Bot 适配器缓存到：

```bash
ls -lht /home/admin/.hermes/cache/documents/
# 文件名格式: doc_<hash>_qqdownloadftnv5
# 最新到达的在最前面
```

**示例输出**：
```
-rw-rw-r-- 1 admin admin 9.0M May 25 22:29 doc_dadf6f1be5c1_qqdownloadftnv5
-rw-rw-r-- 1 admin admin 9.0M May 25 22:28 doc_0909165ac4eb_qqdownloadftnv5
```

> ⚠️ 注意：文件名不含原始名，按修改时间区分。多个分片的 MD5 相同 = 用户重复发了同一分片。

### 备用：/tmp 搜索

```bash
# 按时间查找最近到达的非系统文件
find /tmp -maxdepth 1 -type f -mmin -5 ! -name "pip-*" ! -name "hermes-*" -exec ls -lht {} \;

# 按文件名搜索
find /tmp /home/admin -maxdepth 4 -name "*关键词*" 2>/dev/null

# 搜索 ELF 二进制（找可执行文件）
find /tmp -type f -exec file {} \; 2>/dev/null | grep ELF
```

### 验证分片完整性

```bash
# 合并前确认分片不是同一文件重复发送
md5sum /home/admin/.hermes/cache/documents/doc_*

# 合并分片
cat /home/admin/.hermes/cache/documents/doc_<hash1> \
    /home/admin/.hermes/cache/documents/doc_<hash2> > /tmp/output_file
```

## 最佳实践

| 文件大小 | 建议 |
|---------|------|
| <5MB | QQ 直接发，一般没问题 |
| 5-10MB | QQ 可试，检查文件完整性 |
| >10MB | `split -b 9M` 分割，或 scp 直传 |
| 超大 | scp 或网盘中转（蓝奏云/奶牛快传） |
