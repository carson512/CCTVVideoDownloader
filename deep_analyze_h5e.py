import os

INPUT_FILE = "test_web_h5e_1280x720.ts"

def find_patterns():
    if not os.path.exists(INPUT_FILE): return
    with open(INPUT_FILE, "rb") as f:
        data = f.read(188 * 500) # 读取前500个包

    print(f"[*] 正在分析 h5e 数据流特征...")
    
    # 正常的 TS 包每 188 字节应该有一个 0x47
    sync_errors = 0
    for i in range(0, len(data), 188):
        if data[i] != 0x47:
            sync_errors += 1
    
    if sync_errors == 0:
        print("[+] 同步字节 0x47 完全正常。物理结构未损坏。")
    else:
        print(f"[!] 发现 {sync_errors} 个同步错误。数据可能被整体偏移或异或了。")

    # 尝试寻找 H.264 的起始码 00 00 01 或 00 00 01
    start_code_3 = b'\x00\x00\x01'
    start_code_4 = b'\x00\x00\x00\x01'
    
    found_3 = data.find(start_code_3)
    found_4 = data.find(start_code_4)
    
    print(f"[*] H.264 起始码 (00 00 01) 首次出现位置: {found_3}")
    print(f"[*] H.264 起始码 (00 00 00 01) 首次出现位置: {found_4}")

    # 如果起始码位置不是在正常的 PES 负载起始位置，说明 Payload 被加密了。
    
    # 尝试全文件异或测试 (针对 Payload)
    # 很多私有加密只异或 Payload 的前 128 字节
    
    print("\n[*] 正在尝试寻找 Payload 的解密 Key (基于 0x47 后的数据)...")
    # 如果是简单的异或，数据中应该会出现大量的 0xFF (填充字节)
    # 我们找找数据中出现频率最高的字节
    from collections import Counter
    counts = Counter(data)
    most_common = counts.most_common(5)
    print(f"[*] 出现频率最高的字节: {most_common}")
    # TS 填充字节通常是 0xFF。如果频率最高的是 0xCC，那么 Key 可能就是 0xCC ^ 0xFF = 0x33

if __name__ == "__main__":
    find_patterns()
