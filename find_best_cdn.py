import requests
import re
import os

# ================= 配置区域 =================
PID = "ff0d481b6355470ba160519ef25e82a1"

# 模拟 CBox
HEADERS = {
    "User-Agent": "PCCTV/6.0.4.0/Windows11_64Bit",
    "Origin": "https://cboxwin.cctv.com",
    "Referer": "https://cboxwin.cctv.com",
    "Connection": "Keep-Alive"
}

# 候选 CDN 列表
CANDIDATE_DOMAINS = [
    "dhls.cntv.cdn20.com",
    "dhls.cntv.myalicdn.com",
    "dhls.cntv.wscdns.com",
    "dhls1.cntv.myalicdn.com",
    "dhls2.cntv.myalicdn.com",
    "dhls3.cntv.myalicdn.com",
    "dhls2.cntv.cdn20.com",
    "dhls2.cntv.wscdns.com",
    "hls.cntv.myalicdn.com",
    "hls.cntv.cdn20.com",
    "asp.cntv.lxdns.com",
    "dh5.cntv.cdn20.com",
    "dh5.cntv.myalicdn.com",
    "vod.cntv.lxdns.com",
    "vod.cntv.cdn20.com",
    "dhls2.cntv.qcloudcdn.com" # 基准 (已知是 360P)
]
# ===========================================

def get_base_enc2_url():
    url = f"https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={PID}&client=cbox&vn=1035&video_player=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.json().get('manifest', {}).get('hls_enc2_url')
    except:
        return None

def test_cdn(base_url, domain):
    # 替换域名
    test_url = re.sub(r"https?://[^/]+/", f"https://{domain}/", base_url)
    
    try:
        # 1. 下载主 M3U8
        r = requests.get(test_url, headers=HEADERS, timeout=5)
        if r.status_code != 200: return None, 0
        
        # 2. 解析 2000 码率
        content = r.text
        sub_path = None
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "BANDWIDTH=2048000" in line:
                sub_path = lines[i+1].strip()
                break
        
        if not sub_path: return None, 0
        
        # 3. 下载子 M3U8
        if sub_path.startswith("/"):
            sub_url = f"https://{domain}{sub_path}"
        else:
            sub_url = test_url.rsplit('/', 1)[0] + "/" + sub_path
            
        r = requests.get(sub_url, headers=HEADERS, timeout=5)
        if r.status_code != 200: return None, 0
        
        # 4. 找到 TS
        ts_list = [l for l in r.text.split('\n') if l.endswith('.ts')]
        if not ts_list: return None, 0
        
        # 取中间一个分片
        target_ts = ts_list[len(ts_list)//2]
        
        if target_ts.startswith("/"):
            ts_url = f"https://{domain}{target_ts}"
        else:
            ts_url = sub_url.rsplit('/', 1)[0] + "/" + target_ts
            
        # 5. 下载并测速/测大小
        r = requests.get(ts_url, headers=HEADERS, stream=True, timeout=10)
        if r.status_code != 200: return None, 0
        
        size = 0
        # 下载前 2MB 或者下完
        content = b""
        for chunk in r.iter_content(8192):
            content += chunk
            size += len(chunk)
            if size > 5 * 1024 * 1024: break # 最多下 5MB
            
        return target_ts, size

    except Exception as e:
        # print(f"  [x] {domain} 错误: {e}")
        return None, 0

def main():
    base_url = get_base_enc2_url()
    if not base_url:
        print("[!] 无法获取基础 URL")
        return

    print(f"[*] 基础 URL: {base_url}")
    print("[*] 开始轮询 CDN 寻找真·720P...")
    print(f"{ 'CDN 域名':<30} | { 'TS 文件名':<10} | { '文件大小 (字节)':<15} | {'状态'}")
    print("-" * 70)

    results = []

    for domain in CANDIDATE_DOMAINS:
        ts_name, size = test_cdn(base_url, domain)
        if size > 0:
            status = "可能高清!" if size > 1500000 else "低清?" # 假设 360P 分片约 1MB，720P 约 2MB+
            print(f"{domain:<30} | {ts_name[:10]:<10} | {size:<15} | {status}")
            results.append((domain, size))
            
            # 如果是疑似高清，保存下来给你看
            if size > 1800000: # 阈值设高点
                print(f"  [!] 发现大文件！正在保存 test_{domain}.ts ...")
                # 重新下载完整的
                # ... (略，直接用刚才的 content 保存也可以，但刚才只下了部分)
                # 简单起见，我们只打印，你自己用 test_quality.py 去验证
        else:
            print(f"{domain:<30} | {'-':<10} | {'-':<15} | 失败/404")

    print("\n[*] 测试结束。请关注文件大小显著较大的域名。")

if __name__ == "__main__":
    main()
