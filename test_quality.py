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

# 目标测试域名
TARGET_DOMAIN = "drm.cntv.vod.dnsv1.com"
# ===========================================

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_video_info(pid):
    print(f"[*] 步骤 1: 获取视频信息 (PID: {pid})")
    url = f"https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={pid}&client=cbox&vn=1035&video_player=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        original_m3u8_url = data.get('manifest', {}).get('hls_enc2_url')
        return original_m3u8_url
    except Exception as e:
        print(f"[!] 获取视频信息失败: {e}")
        return None

def run_test():
    print(f"[*] 正在尝试特定 DRM CDN: {TARGET_DOMAIN} ...")
    
    # 1. 获取视频信息
    original_m3u8_url = get_video_info(PID)
    if not original_m3u8_url:
        return

    # 2. 构造测试 URL
    test_url = re.sub(r"https?://[^/]+/", f"https://{TARGET_DOMAIN}/", original_m3u8_url)
    print(f"[*] 构造的测试 URL: {test_url}")

    # 3. 下载主 M3U8
    try:
        r = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
        r.raise_for_status()
        content = r.text
        
        # 4. 解析最高码率 (2048000)
        streams = re.findall(r"BANDWIDTH=(\d+).*\n(.*\.m3u8)", content)
        if not streams:
            print("[!] 未找到码率列表")
            return
            
        streams.sort(key=lambda x: int(x[0]), reverse=True)
        bw, sub_path = streams[0]
        print(f"[+] 选中流带宽: {bw}")
        
        # 构造子 M3U8 URL
        if sub_path.startswith("/"):
            sub_url = f"https://{TARGET_DOMAIN}{sub_path}"
        else:
            sub_url = test_url.rsplit('/', 1)[0] + "/" + sub_path
            
        # 5. 下载子 M3U8 并取 TS
        r = requests.get(sub_url, headers=HEADERS, timeout=10, verify=False)
        ts_list = [l for l in r.text.split('\n') if l.strip().endswith('.ts')]
        if not ts_list:
            print("[!] 未找到 TS")
            return
            
        test_ts = ts_list[len(ts_list)//2]
        if test_ts.startswith("/"):
            ts_url = f"https://{TARGET_DOMAIN}{test_ts}"
        else:
            ts_url = sub_url.rsplit('/', 1)[0] + "/" + test_ts
            
        print(f"[*] 尝试下载测试分片: {ts_url}")
        
        # 6. 下载并保存
        r = requests.get(ts_url, headers=HEADERS, stream=True, timeout=20, verify=False)
        if r.status_code == 200:
            fname = f"test_drm_cdn_enc2.ts"
            with open(fname, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    if f.tell() > 2 * 1024 * 1024: break # 下 2MB 足够看画质了
            
            actual_size = os.path.getsize(fname)
            print(f"\n[SUCCESS] 下载完成: {fname}, 大小: {actual_size} 字节")
            if actual_size > 1500000:
                print("[!!!] 注意：文件体积较大，极有可能是真 720P！")
            else:
                print("[?] 文件体积较小，可能仍是 360P。")
        else:
            print(f"[!] TS 下载失败: {r.status_code}")

    except Exception as e:
        print(f"[!] 发生错误: {e}")

if __name__ == "__main__":
    run_test()