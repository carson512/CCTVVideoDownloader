import requests
import re
import os
import json

# ================= 配置区域 =================
PID = "ff0d481b6355470ba160519ef25e82a1"

# 模拟 CBox PC 客户端 Headers
HEADERS = {
    "User-Agent": "PCCTV/6.0.4.0/Windows11_64Bit",
    "Origin": "https://cboxwin.cctv.com",
    "Referer": "https://cboxwin.cctv.com",
    "Connection": "Keep-Alive"
}
# ===========================================

def run_test():
    print(f"[*] 正在尝试: 原始 enc2 URL + CBox Headers...")
    
    # 1. 获取视频信息，提取原始 hls_enc2_url
    url = f"https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={PID}&client=cbox&vn=1035&video_player=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        test_url = data.get('manifest', {}).get('hls_enc2_url')
    except:
        test_url = None

    if not test_url:
        print("[!] 无法获取 enc2 地址")
        return

    print(f"[*] 目标 URL: {test_url}")

    # 2. 下载主 M3U8
    try:
        r = requests.get(test_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        content = r.text
        
        # 3. 解析最高码率 (2048000)
        streams = re.findall(r"BANDWIDTH=(\d+).*\n(.*\.m3u8)", content)
        if not streams:
            print("[!] 未找到码率列表")
            return
            
        streams.sort(key=lambda x: int(x[0]), reverse=True)
        bw, sub_path = streams[0]
        print(f"[+] 选中流带宽: {bw}")
        
        # 构造子 M3U8 URL
        match = re.search(r"https?://([^/]+)/", test_url)
        domain = match.group(1)
        if sub_path.startswith("/"):
            sub_url = f"https://{domain}{sub_path}"
        else:
            sub_url = test_url.rsplit('/', 1)[0] + "/" + sub_path
            
        # 4. 下载子 M3U8 并取 TS
        r = requests.get(sub_url, headers=HEADERS, timeout=10)
        ts_list = [l for l in r.text.split('\n') if l.endswith('.ts')]
        if not ts_list:
            print("[!] 未找到 TS")
            return
            
        test_ts = ts_list[len(ts_list)//2]
        if test_ts.startswith("/"):
            ts_url = f"https://{domain}{test_ts}"
        else:
            ts_url = sub_url.rsplit('/', 1)[0] + "/" + test_ts
            
        print(f"[*] 尝试下载测试分片: {ts_url}")
        
        # 5. 下载并保存
        r = requests.get(ts_url, headers=HEADERS, stream=True, timeout=20)
        if r.status_code == 200:
            fname = f"test_original_enc2_cbox_headers.ts"
            with open(fname, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    if f.tell() > 1024 * 1024: break
            print(f"\n[SUCCESS] 下载完成: {fname}")
            print("[*] 请检查分辨率是否为 720P。")
        else:
            print(f"[!] TS 下载失败: {r.status_code}")

    except Exception as e:
        print(f"[!] 发生错误: {e}")

if __name__ == "__main__":
    run_test()
