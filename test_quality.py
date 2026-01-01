import requests
import re
import os
import json

# ================= 配置区域 =================
# 1. 视频的 GUID
PID = "ff0d481b6355470ba160519ef25e82a1"

# 2. 模拟 Web 端 Headers (Chrome 143)
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://tv.cctv.com",
    "Pragma": "no-cache",
    "Referer": "https://tv.cctv.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}
# ===========================================

def get_video_info(pid):
    print(f"[*] 步骤 1: 获取视频信息 (PID: {pid})")
    url = f"https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={pid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        m3u8_url = data.get('manifest', {}).get('hls_enc2_url')
        if not m3u8_url:
            print("[!] 无法从接口获取 hls_enc2_url")
            return None
        return m3u8_url
    except Exception as e:
        print(f"[!] 获取视频信息失败: {e}")
        return None

def run_test():
    # 1. 获取原始 M3U8 URL
    original_m3u8_url = get_video_info(PID)
    if not original_m3u8_url: return

    print(f"[*] 原始主 M3U8: {original_m3u8_url}")

    # 2. 构造 Web 端 URL (魔改逻辑)
    # 规则: 替换域名为 dh5wswx02.v.cntv.cn，替换 /asp/enc2/ 为 /asp/h5e/
    test_url = original_m3u8_url.replace("/asp/enc2/", "/asp/h5e/")
    test_url = re.sub(r"https?://[^/]+/", "https://dh5wswx02.v.cntv.cn/", test_url)
    
    print(f"[*] 构造的 Web 端 M3U8: {test_url}")
    
    # 提取域名用于后续拼接
    global TARGET_DOMAIN
    TARGET_DOMAIN = "dh5wswx02.v.cntv.cn"

    # 3. 下载主 M3U8
    print(f"\n[*] 步骤 2: 下载主 M3U8...")
    try:
        r = requests.get(test_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        master_content = r.text
        print("--- 主 M3U8 内容 ---")
        print(master_content.strip())
        print("--------------------")
    except Exception as e:
        print(f"[!] 下载主 M3U8 失败: {e}")
        return

    # 4. 解析最高质量流
    print("\n[*] 步骤 3: 解析清晰度列表...")
    lines = master_content.split('\n')
    streams = []
    for i, line in enumerate(lines):
        if "#EXT-X-STREAM-INF" in line:
            bw = re.search(r"BANDWIDTH=(\d+)", line).group(1)
            res = re.search(r"RESOLUTION=([x\d]+)", line)
            res_str = res.group(1) if res else "Unknown"
            url = lines[i+1].strip()
            streams.append({'bw': int(bw), 'res': res_str, 'url': url})
            print(f"    - 发现: {res_str} (带宽: {bw}) -> {url}")

    if not streams:
        print("[!] 未解析到任何视频流")
        return

    # 选带宽最大的
    best = max(streams, key=lambda x: x['bw'])
    print(f"[*] 选中最高质量: {best['res']} (带宽: {best['bw']})")

    # 5. 下载子 M3U8 (获取 TS 列表)
    # 注意：Web 端 M3U8 的子链接可能也是 /asp/h5e/...
    if best['url'].startswith("/"):
        sub_m3u8_url = f"https://{TARGET_DOMAIN}{best['url']}"
    else:
        # 相对路径
        base = test_url.rsplit('?', 1)[0].rsplit('/', 1)[0]
        sub_m3u8_url = f"{base}/{best['url']}"

    print(f"\n[*] 步骤 4: 下载视频分片列表 (URL: {sub_m3u8_url})")
    try:
        r = requests.get(sub_m3u8_url, headers=HEADERS, timeout=10)
        sub_content = r.text
        ts_files = [l.strip() for l in sub_content.split('\n') if l.strip().endswith('.ts')]
        print(f"[*] 找到 {len(ts_files)} 个 TS 分片")
    except Exception as e:
        print(f"[!] 下载子 M3U8 失败: {e}")
        return

    # 6. 下载其中一个 TS 分片进行测试
    if not ts_files: return
    test_ts = ts_files[len(ts_files)//2] # 取中间的
    
    # 构造 TS URL
    if test_ts.startswith("http"):
        ts_url = test_ts
    elif test_ts.startswith("/"):
        ts_url = f"https://{TARGET_DOMAIN}{test_ts}"
    else:
        base_path = sub_m3u8_url.rsplit('/', 1)[0]
        ts_url = f"{base_path}/{test_ts}"
    
    print(f"\n[*] 步骤 5: 下载测试分片 (URL: {ts_url})")
    try:
        r = requests.get(ts_url, headers=HEADERS, timeout=20, stream=True)
        r.raise_for_status()
        
        save_name = f"test_web_h5e_{best['res']}.ts"
        with open(save_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\n[SUCCESS] 下载完成！已保存为: {save_name}")
        print(f"[*] 请检查该文件的实际分辨率是否为 {best['res']}")
    except Exception as e:
        print(f"[!] 下载 TS 失败: {e}")

if __name__ == "__main__":
    run_test()