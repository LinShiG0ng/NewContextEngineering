# 🛡️ 安全测试场景支持

## 概述

AU2压缩算法已扩展支持**渗透测试**和**漏洞挖掘**场景，能够智能识别和压缩安全测试相关的对话内容。

## 🎯 支持的场景

### 1. 渗透测试（Penetration Testing）
- 端口扫描和服务识别
- 漏洞扫描和检测
- 漏洞利用和Exploit
- 权限提升（Privilege Escalation）
- 后渗透（Post-Exploitation）

### 2. Web应用测试
- SQL注入测试
- XSS跨站脚本测试
- CSRF测试
- 文件上传漏洞
- 身份认证绕过

### 3. 网络安全分析
- 数据包分析
- 协议分析
- 流量监控
- 中间人攻击

## 📊 支持的实体类型

### 网络实体
- **IP地址**: IPv4地址（如 192.168.1.100）
- **端口**: 端口号（如 80, 443, 3306）
- **域名**: 目标域名
- **URL**: 完整的URL地址
- **协议**: HTTP, HTTPS, FTP, SSH, TCP, UDP等

### 安全工具
- **扫描工具**: nmap, masscan, nikto, dirb, gobuster
- **漏洞扫描**: nessus, openvas, acunetix
- **Web代理**: burpsuite, zaproxy, mitmproxy
- **SQL注入**: sqlmap
- **密码破解**: hydra, john, hashcat
- **漏洞利用**: metasploit, exploit-db
- **后渗透**: mimikatz, empire, cobalt strike

### 漏洞类型
- **注入**: SQL Injection, Command Injection, LDAP Injection
- **XSS**: Cross-Site Scripting
- **认证**: Broken Authentication, Session Hijacking
- **授权**: Broken Access Control, IDOR, Privilege Escalation
- **加密**: Weak Encryption, Insecure Crypto
- **配置**: Security Misconfiguration
- **其他**: Buffer Overflow, RCE, LFI, RFI, SSRF, XXE

### 其他实体
- **CVE编号**: CVE-2023-1234
- **HTTP方法**: GET, POST, PUT, DELETE
- **状态码**: 200, 404, 500等
- **HTTP头部**: User-Agent, Cookie, Authorization等
- **Payload**: 攻击载荷片段

## 🔧 使用方法

### 方法1: 手动输入

在Web界面中直接输入安全测试相关的对话：

```
用户: 我使用nmap扫描了192.168.1.100，发现开放了80和443端口
助手: 好的，接下来使用burpsuite测试Web应用...
```

### 方法2: 导入JSON（推荐）

使用提供的示例文件快速测试：

```bash
# 1. 启动Web服务
./start_web.sh

# 2. 在浏览器中打开 http://localhost:8000

# 3. 点击"导入对话"按钮

# 4. 使用示例文件
cat examples/security_pentest_example.json
# 复制内容并粘贴到导入对话框

# 5. 选择"自动检测"格式

# 6. 勾选"自动压缩"

# 7. 点击"导入并测试压缩"
```

### 方法3: API调用

```python
import requests
import json

# 读取示例文件
with open('examples/security_pentest_example.json', 'r') as f:
    conversation = json.load(f)

# 导入对话
response = requests.post('http://localhost:8000/api/import', json={
    "json_data": json.dumps(conversation),
    "format_type": "auto",
    "auto_compress": True
})

print(response.json())
```

## 📝 压缩效果展示

### 压缩前（原始对话）

```
用户: 我需要对目标服务器192.168.1.100进行渗透测试
助手: 建议使用nmap进行端口扫描...
用户: nmap扫描结果显示开放了22, 80, 443, 3306, 8080端口...
助手: 发现了Apache 2.4.6和MySQL 5.7.32...
用户: 使用burpsuite发现id参数可能存在SQL注入...
助手: 建议使用sqlmap测试...
用户: sqlmap确认存在SQL注入漏洞...
助手: 尝试提取数据库内容...
用户: 获取到了admin用户的密码哈希...
助手: 尝试破解并登录后台...
用户: 成功上传了webshell...
助手: 获得RCE权限！尝试提权...
用户: 发现SUID文件可以提权...
助手: 成功提权到root!
```

**统计**: 14条消息，约3500 tokens

### 压缩后（摘要）

```markdown
📝 渗透测试过程摘要

🎯 目标信息:
  • IP地址: 192.168.1.100
  • 开放端口: 22(SSH), 80(HTTP), 443(HTTPS), 3306(MySQL), 8080(Tomcat)
  • 服务版本: Apache 2.4.6, MySQL 5.7.32, Tomcat 8.5.50

🔧 使用工具:
  • nmap: 端口扫描和服务识别
  • burpsuite: HTTP请求拦截和分析
  • sqlmap: SQL注入自动化测试
  • hashcat: 密码哈希破解

🔴 发现漏洞:
  1. [critical] SQL Injection - /admin/user.php?id=参数
     - 类型: Boolean-based blind + Time-based blind
     - 数据库: MySQL (testdb)
     - 影响表: users, admin, products

  2. [critical] Credential Leak - 通过SQL注入获取
     - admin: password (MD5: 5f4dcc3b5aa765d61d8327deb882cf99)
     - test: test (MD5: 098f6bcd4621d373cade4e832627b4f6)

  3. [critical] File Upload Vulnerability
     - 上传路径: /uploads/
     - 上传文件: shell.php (webshell)

  4. [critical] Remote Code Execution (RCE)
     - 访问: http://192.168.1.100/uploads/shell.php?cmd=
     - 当前用户: www-data

  5. [critical] Privilege Escalation via SUID
     - SUID程序: /usr/bin/find
     - 提权成功: root权限

💣 关键Payload:
  • SQL: id=1' OR '1'='1'--
  • SQL: id=1' AND SLEEP(5)--
  • Shell: <?php system($_GET['cmd']); ?>
  • Privesc: /usr/bin/find . -exec /bin/sh -p \; -quit

🔗 攻击链:
Port Scan → SQL Injection → Database Dump → Password Cracking →
Authentication Bypass → File Upload → RCE → SUID Exploitation →
Privilege Escalation → Root Access

⚠️ 风险评估:
  • 综合评分: Critical (10/10)
  • 可远程利用: Yes
  • 需要认证: No (SQL注入绕过)
  • 复杂度: Low
  • 影响: Complete System Compromise
```

**统计**: 1条压缩消息，约800 tokens

**压缩率**: 77.1% (节省2700 tokens)

## 🎨 实体提取示例

### 输入文本

```
我使用nmap扫描了192.168.1.100，发现开放端口：
22/tcp   open  ssh
80/tcp   open  http
3306/tcp open  mysql

接着用sqlmap测试了http://target.com/page.php?id=1
发现存在SQL注入漏洞(CVE-2023-1234)。

使用payload: 1' OR '1'='1'--
服务器返回200状态码。

通过burpsuite拦截请求，User-Agent头部包含敏感信息。
```

### 提取结果

```json
{
  "ip_addresses": ["192.168.1.100"],
  "ports": ["22", "80", "3306"],
  "domains": ["target.com"],
  "urls": ["http://target.com/page.php?id=1"],
  "tools": ["nmap", "sqlmap", "burpsuite"],
  "vulnerabilities": ["sql injection"],
  "cve_ids": ["CVE-2023-1234"],
  "payloads": ["1' OR '1'='1'--"],
  "http_methods": ["GET"],
  "status_codes": ["200"],
  "headers": ["User-Agent"],
  "protocols": ["tcp", "ssh", "http"]
}
```

## 🔍 消息分类规则

### Critical（关键）
- 发现漏洞: "vulnerable", "vulnerability found"
- 成功利用: "exploit successful", "shell obtained"
- 凭证泄露: "password found", "credential leaked"
- 严重程度: "critical", "high severity"

### Important（重要）
- 工具执行: "scan complete", "testing"
- 端口开放: "port open"
- 服务检测: "service detected"
- 可疑发现: "potential vulnerability", "suspicious"

### Contextual（上下文）
- 一般说明和解释
- 工具使用指导
- 背景信息

## 📦 示例文件

### 渗透测试完整流程
文件: `examples/security_pentest_example.json`

内容:
- 信息收集（nmap扫描）
- 漏洞发现（SQL注入）
- 数据提取（数据库dump）
- 权限获取（webshell上传）
- 权限提升（SUID利用）

### 使用方法

```bash
# 导入示例
# 1. 复制 examples/security_pentest_example.json 的内容
# 2. 在Web界面点击"导入对话"
# 3. 粘贴内容
# 4. 选择"通用格式"或"自动检测"
# 5. 点击"导入并测试压缩"

# 观察压缩效果
# 1. 查看Token使用率变化
# 2. 点击"查看完整内容"查看压缩摘要
# 3. 检查关键信息是否保留（IP、端口、漏洞、工具等）
```

## ⚙️ 技术实现

### 实体提取

```python
from security_extensions import SecurityEntityExtractor

extractor = SecurityEntityExtractor()
entities = extractor.extract_security_entities(text)

# 返回的实体字典包含：
# - ip_addresses: IP地址列表
# - ports: 端口列表
# - tools: 工具名称列表
# - vulnerabilities: 漏洞类型列表
# - payloads: Payload列表
# - cve_ids: CVE编号列表
# 等等...
```

### 场景分类

```python
from security_extensions import SecurityScenarioClassifier

classifier = SecurityScenarioClassifier()

# 判断消息重要性
importance = classifier.classify_security_message(message)
# 返回: "critical" / "important" / "contextual"

# 判断是否为工具输出
is_tool = classifier.is_tool_output(message)

# 判断是否为数据包
is_packet = classifier.is_packet_data(message)
```

### 集成到压缩流程

AU2Compressor自动检测安全测试内容：

1. **消息分类**: 识别漏洞发现、工具执行等关键消息
2. **实体提取**: 提取IP、端口、漏洞、工具、CVE等
3. **知识图谱**: 构建攻击链关系图
4. **摘要生成**: 保留完整的攻击路径和关键发现

## 🎯 最佳实践

### 1. 记录完整的测试流程

包含：
- 目标信息
- 使用的工具和命令
- 发现的漏洞
- 使用的Payload
- 测试结果

### 2. 标注关键发现

使用明确的关键词：
- "发现漏洞"、"vulnerable"
- "利用成功"、"exploit successful"
- "获取权限"、"shell obtained"

### 3. 包含技术细节

- CVE编号
- 完整的命令
- HTTP请求/响应
- 错误信息

### 4. 导出和分享

```bash
# 导出压缩后的报告
curl http://localhost:8000/api/context/full?format=markdown > report.md
```

## ⚠️ 安全提醒

1. **仅用于授权测试**: 只在获得明确授权的系统上进行测试
2. **保护敏感信息**: 导出的内容可能包含敏感信息，注意保密
3. **合规性**: 遵守相关法律法规和安全测试规范
4. **伦理准则**: 遵循负责任的漏洞披露原则

## 📚 参考资料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PTES渗透测试标准](http://www.pentest-standard.org/)
- [CVE数据库](https://cve.mitre.org/)
- [Exploit Database](https://www.exploit-db.com/)

## 🤝 贡献

欢迎贡献更多安全测试场景的支持！

可以添加：
- 更多工具识别
- 更多漏洞类型
- 更完善的Payload提取
- 自动化报告生成

---

**🛡️ 让上下文压缩支持你的安全测试工作流！**
