"""
安全测试场景扩展模块

为AU2压缩算法添加渗透测试和漏洞挖掘场景的支持
包括：
- 工具调用识别（nmap, sqlmap, burpsuite等）
- 网络数据包分析
- 漏洞类型识别
- Payload提取
- 安全测试流程压缩
"""

import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class SecurityEntityExtractor:
    """安全测试实体提取器"""

    # 常见渗透测试工具
    PENTEST_TOOLS = {
        # 扫描工具
        'nmap', 'masscan', 'zmap', 'unicornscan',
        # Web扫描
        'nikto', 'dirb', 'dirbuster', 'gobuster', 'ffuf', 'wfuzz',
        # 漏洞扫描
        'nessus', 'openvas', 'nexpose', 'acunetix', 'appscan',
        # SQL注入
        'sqlmap', 'havij', 'pangolin',
        # XSS
        'xsser', 'xsstrike', 'beef',
        # 密码破解
        'hydra', 'medusa', 'john', 'hashcat', 'crunch',
        # 抓包工具
        'wireshark', 'tcpdump', 'tshark', 'ettercap',
        # 代理工具
        'burpsuite', 'burp', 'zaproxy', 'zap', 'mitmproxy', 'fiddler',
        # 漏洞利用
        'metasploit', 'msf', 'msfconsole', 'msfvenom',
        # 后渗透
        'cobalt strike', 'empire', 'powersploit', 'mimikatz',
        # 其他
        'searchsploit', 'exploit-db', 'nuclei', 'subfinder'
    }

    # 漏洞类型
    VULNERABILITY_TYPES = {
        # Web漏洞
        'sql injection', 'sqli', 'xss', 'cross-site scripting',
        'csrf', 'cross-site request forgery', 'ssrf', 'xxe',
        'rce', 'remote code execution', 'lfi', 'local file inclusion',
        'rfi', 'remote file inclusion', 'path traversal', 'directory traversal',
        'command injection', 'code injection', 'ldap injection',
        'xml injection', 'xpath injection', 'ssti', 'template injection',
        # 认证授权
        'broken authentication', 'broken access control', 'idor',
        'privilege escalation', 'session fixation', 'session hijacking',
        # 配置问题
        'security misconfiguration', 'cors', 'clickjacking',
        'information disclosure', 'sensitive data exposure',
        # 加密问题
        'weak encryption', 'insecure crypto', 'hard-coded credentials',
        # 业务逻辑
        'business logic flaw', 'race condition', 'dos', 'denial of service',
        # 其他
        'buffer overflow', 'heap overflow', 'stack overflow',
        'use after free', 'format string', 'integer overflow'
    }

    # HTTP方法
    HTTP_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'}

    # 常见Payload关键词
    PAYLOAD_KEYWORDS = {
        "' or '1'='1", "1' or '1'='1'--", "admin'--", "' union select",
        "<script>", "alert(", "onerror=", "onload=", "javascript:",
        "../", "..\\", "/etc/passwd", "c:\\windows\\",
        "${", "{{", "<%", "<?php",
        "sleep(", "waitfor delay", "benchmark(",
        "nc ", "netcat", "bash -i", "/bin/sh", "cmd.exe",
        "base64", "eval(", "exec(", "system(", "passthru("
    }

    def extract_security_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取安全测试相关的实体

        Args:
            text: 要分析的文本

        Returns:
            实体字典
        """
        entities = {
            "ip_addresses": [],
            "ports": [],
            "domains": [],
            "urls": [],
            "tools": [],
            "vulnerabilities": [],
            "payloads": [],
            "http_methods": [],
            "status_codes": [],
            "headers": [],
            "cve_ids": [],
            "protocols": []
        }

        # IP地址（IPv4）
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        entities["ip_addresses"] = list(set(re.findall(ip_pattern, text)))

        # 端口号
        port_pattern = r':(\d{1,5})\b'
        ports = [p for p in re.findall(port_pattern, text) if 0 < int(p) <= 65535]
        entities["ports"] = list(set(ports))

        # 域名
        domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'
        entities["domains"] = list(set(re.findall(domain_pattern, text.lower())))

        # URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        entities["urls"] = list(set(re.findall(url_pattern, text)))

        # 工具名称
        text_lower = text.lower()
        for tool in self.PENTEST_TOOLS:
            if tool in text_lower:
                entities["tools"].append(tool)
        entities["tools"] = list(set(entities["tools"]))

        # 漏洞类型
        for vuln in self.VULNERABILITY_TYPES:
            if vuln in text_lower:
                entities["vulnerabilities"].append(vuln)
        entities["vulnerabilities"] = list(set(entities["vulnerabilities"]))

        # HTTP方法
        for method in self.HTTP_METHODS:
            if method in text.upper():
                entities["http_methods"].append(method)
        entities["http_methods"] = list(set(entities["http_methods"]))

        # HTTP状态码
        status_pattern = r'\b(1\d{2}|2\d{2}|3\d{2}|4\d{2}|5\d{2})\b'
        entities["status_codes"] = list(set(re.findall(status_pattern, text)))

        # CVE编号
        cve_pattern = r'CVE-\d{4}-\d{4,}'
        entities["cve_ids"] = list(set(re.findall(cve_pattern, text, re.IGNORECASE)))

        # 常见协议
        protocols = ['http', 'https', 'ftp', 'ssh', 'telnet', 'smtp', 'dns',
                    'tcp', 'udp', 'icmp', 'ssl', 'tls', 'rdp', 'smb']
        for protocol in protocols:
            if protocol in text_lower:
                entities["protocols"].append(protocol)
        entities["protocols"] = list(set(entities["protocols"]))

        # Payload片段
        for keyword in self.PAYLOAD_KEYWORDS:
            if keyword.lower() in text_lower:
                entities["payloads"].append(keyword)
        entities["payloads"] = list(set(entities["payloads"]))[:10]  # 限制数量

        # HTTP头部
        header_pattern = r'^([A-Z][a-zA-Z-]+):\s*(.+)$'
        headers = re.findall(header_pattern, text, re.MULTILINE)
        entities["headers"] = [h[0] for h in headers[:10]]

        return entities

    def extract_packet_data(self, text: str) -> List[Dict]:
        """
        提取网络数据包信息

        Args:
            text: 包含数据包的文本

        Returns:
            数据包列表
        """
        packets = []

        # 识别HTTP请求/响应
        http_request_pattern = r'(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^\s]+)\s+HTTP/[\d\.]+.*?(?=\n\n|\Z)'
        for match in re.finditer(http_request_pattern, text, re.DOTALL):
            packets.append({
                "type": "http_request",
                "method": match.group(1),
                "path": match.group(2),
                "content": match.group(0)[:500]  # 限制长度
            })

        # 识别HTTP响应
        http_response_pattern = r'HTTP/[\d\.]+\s+(\d{3})\s+.*?(?=\n\n|\Z)'
        for match in re.finditer(http_response_pattern, text, re.DOTALL):
            packets.append({
                "type": "http_response",
                "status_code": match.group(1),
                "content": match.group(0)[:500]
            })

        return packets

    def identify_tool_output(self, text: str) -> Dict[str, any]:
        """
        识别工具输出并提取关键信息

        Args:
            text: 工具输出文本

        Returns:
            工具信息字典
        """
        tool_info = {
            "tool": None,
            "target": None,
            "findings": []
        }

        text_lower = text.lower()

        # 识别Nmap输出
        if 'nmap' in text_lower or 'starting nmap' in text_lower:
            tool_info["tool"] = "nmap"
            # 提取开放端口
            port_pattern = r'(\d+)/tcp\s+open\s+(\w+)'
            ports = re.findall(port_pattern, text)
            tool_info["findings"] = [f"Port {p[0]}: {p[1]}" for p in ports[:10]]

        # 识别SQLMap输出
        elif 'sqlmap' in text_lower:
            tool_info["tool"] = "sqlmap"
            if 'vulnerable' in text_lower or 'injectable' in text_lower:
                tool_info["findings"].append("SQL Injection vulnerability found")

        # 识别Burp Suite输出
        elif 'burp' in text_lower or 'burp suite' in text_lower:
            tool_info["tool"] = "burpsuite"

        # 识别Metasploit输出
        elif 'metasploit' in text_lower or 'msf' in text_lower:
            tool_info["tool"] = "metasploit"
            if 'exploit completed' in text_lower:
                tool_info["findings"].append("Exploit successful")

        # 识别Nikto输出
        elif 'nikto' in text_lower:
            tool_info["tool"] = "nikto"
            vuln_pattern = r'\+\s+([^\n]+)'
            findings = re.findall(vuln_pattern, text)
            tool_info["findings"] = findings[:10]

        return tool_info


class SecurityScenarioClassifier:
    """安全测试场景分类器"""

    def classify_security_message(self, message: str) -> str:
        """
        判断消息的安全测试重要性

        Args:
            message: 消息内容

        Returns:
            重要性级别: critical/important/contextual
        """
        msg_lower = message.lower()

        # Critical: 发现漏洞或成功利用
        critical_keywords = [
            'vulnerable', 'exploitable', 'exploit successful',
            'vulnerability found', 'injection point',
            'authentication bypass', 'remote code execution',
            'privilege escalation successful', 'shell obtained',
            'password found', 'credential leaked',
            'critical', 'high severity'
        ]

        if any(kw in msg_lower for kw in critical_keywords):
            return "critical"

        # Important: 工具执行和重要发现
        important_keywords = [
            'scan complete', 'testing', 'attempting',
            'sending payload', 'analyzing response',
            'port open', 'service detected',
            'potential vulnerability', 'suspicious',
            'warning', 'medium severity'
        ]

        if any(kw in msg_lower for kw in important_keywords):
            return "important"

        # 默认为contextual
        return "contextual"

    def is_tool_output(self, message: str) -> bool:
        """判断是否为工具输出"""
        # 工具输出通常包含特定格式或大量技术信息
        indicators = [
            re.search(r'\d+/tcp\s+open', message),  # nmap
            re.search(r'Starting Nmap', message),
            re.search(r'sqlmap/', message),
            re.search(r'\[\*\]|\[+\]|\[-\]', message),  # metasploit
            re.search(r'HTTP/\d\.\d\s+\d{3}', message),  # HTTP响应
        ]

        return any(indicators)

    def is_packet_data(self, message: str) -> bool:
        """判断是否为数据包数据"""
        packet_indicators = [
            'GET ' in message or 'POST ' in message,
            'HTTP/' in message,
            'Host:' in message,
            'User-Agent:' in message,
            'Content-Type:' in message
        ]

        return sum(packet_indicators) >= 2


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("安全测试实体提取测试")
    print("=" * 60)

    extractor = SecurityEntityExtractor()
    classifier = SecurityScenarioClassifier()

    # 测试文本
    test_text = """
    我使用nmap扫描了目标服务器192.168.1.100:

    PORT     STATE SERVICE
    22/tcp   open  ssh
    80/tcp   open  http
    443/tcp  open  https
    3306/tcp open  mysql

    接着我使用sqlmap测试了http://example.com/page.php?id=1，
    发现存在SQL注入漏洞(CVE-2023-1234)。

    我尝试了payload: 1' OR '1'='1'--
    服务器返回了200状态码，并且User-Agent头部显示了内部信息。

    使用burpsuite拦截请求后，发现存在XSS漏洞。
    """

    print("\n【提取安全实体】")
    entities = extractor.extract_security_entities(test_text)
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"  • {entity_type}: {entity_list}")

    print("\n【消息分类】")
    messages = [
        "扫描完成，发现开放端口22, 80, 443",
        "发现SQL注入漏洞！系统vulnerable",
        "正在尝试payload...",
        "利用成功，获得shell权限！"
    ]

    for msg in messages:
        importance = classifier.classify_security_message(msg)
        print(f"  [{importance}] {msg}")

    print("\n【工具输出识别】")
    nmap_output = """
    Starting Nmap 7.91
    PORT     STATE SERVICE
    22/tcp   open  ssh
    80/tcp   open  http
    """

    tool_info = extractor.identify_tool_output(nmap_output)
    print(f"  工具: {tool_info['tool']}")
    print(f"  发现: {tool_info['findings']}")

    print("\n" + "=" * 60)
