import os

# 这里填你刚才下载的那个文件名
TS_FILENAME = "test_web_h5e_1280x720.ts"

def analyze_header():
    if not os.path.exists(TS_FILENAME):
        print(f"[!] 找不到文件: {TS_FILENAME}")
        return

    file_size = os.path.getsize(TS_FILENAME)
    print(f"[*] 文件大小: {file_size} 字节 ({file_size/1024/1024:.2f} MB)")

    if file_size < 1024:
        print("[!] 文件太小了！可能下载到了错误页面。")
        with open(TS_FILENAME, 'r', errors='ignore') as f:
            print("--- 文件内容预览 ---")
            print(f.read())
        return

    with open(TS_FILENAME, 'rb') as f:
        # 读取前 128 字节
        header = f.read(128)
        
        print("\n[*] 16进制头信息 (Hex Dump):")
        # 打印 Hex
        print(" ".join(f"{b:02X}" for b in header))
        
        print("\n[*] ASCII 预览:")
        # 尝试打印 ASCII (过滤不可见字符)
        print("".join(chr(b) if 32 <= b <= 126 else '.' for b in header))

        # 分析
        if header.startswith(b'G'): # 0x47
            print("\n[+] 看起来是标准的 TS 文件头 (0x47 ...)")
        elif header.startswith(b'PNG'):
            print("\n[!] 这是一个 PNG 图片头？可能是伪装。")
        elif b'<html>' in header or b'<xml>' in header:
            print("\n[!] 这看起来是个 HTML/XML 文件，不是视频！")
        else:
            print("\n[?] 头信息不标准，可能是被混淆或加密了。")

if __name__ == "__main__":
    analyze_header()
