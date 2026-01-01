import os

INPUT_FILE = "test_web_h5e_1280x720.ts"

def xor_data(data, key):
    return bytes([b ^ key for b in data])

def try_decrypt():
    if not os.path.exists(INPUT_FILE):
        print(f"找不到文件: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "rb") as f:
        data = f.read(188 * 100) # 只读取前100个包做测试，避免太慢

    print("[*] 开始暴力尝试解密 (测试前 100 个 TS 包)...")

    # 尝试 1: 全局异或 (常见 Key: 0x55, 0xAA, 0xFF, 0xCC)
    # common_keys = [0x55, 0xAA, 0xFF, 0xCC, 0x11, 0x22, 0x33, 0x44]
    # for key in common_keys:
    #     decoded = xor_data(data, key)
    #     # 检查头是否变回 0x47
    #     if decoded[0] == 0x47:
    #         print(f"[!] 发现可能的全局 XOR Key: 0x{key:02X}")
    #         with open(f"decoded_xor_{key:02X}.ts", "wb") as out:
    #             out.write(decoded)

    # 尝试 2: 简单的位移 (很少见)
    
    # 尝试 3: CNTV 特有混淆 - 字节序颠倒? 或者是简单的加法?
    # 您说 "头是 47 40..."，说明头没加密。
    # 那可能是从第 N 个字节开始加密?
    
    # 让我们分析一下花屏的原因。如果头正常，花屏通常意味着 I 帧损坏。
    # 让我们把这个文件仅仅作为 "Raw Data" 来看待。
    
    print("目前头文件正常(0x47)，但播放花屏。说明可能只是 Payload 被加密了。")
    print("我们尝试提取几个 Payload 看看规律。")
    
    # TS 包大小 188 字节。
    # 第 1 字节: 0x47
    # 第 2-4 字节: PID 和 标志位
    # 如果 payload_unit_start_indicator 是 1，后面可能有 PES 头。
    
    for i in range(10):
        packet = data[i*188 : (i+1)*188]
        if len(packet) != 188: break
        
        sync_byte = packet[0]
        if sync_byte != 0x47:
            print(f"包 {i} 同步字节错误: {sync_byte:02X}")
            continue
            
        # 提取 PID
        pid = ((packet[1] & 0x1F) << 8) | packet[2]
        scrambling_control = (packet[3] >> 6) & 0x03
        
        print(f"包 {i}: PID={pid}, 加密位={scrambling_control}")
        
        if scrambling_control != 0:
            print(f"  -> 注意！TS头显示该包被加密了！(Scrambling Control = {scrambling_control})")
            print("  这说明它可能确实是标准的 DVB-CSA 加密，或者 AES 加密，但 KEY 没有通过标准方式传递。")

if __name__ == "__main__":
    try_decrypt()
