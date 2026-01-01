import os

INPUT_FILE = "test_web_h5e_1280x720.ts"

def try_stripping():
    if not os.path.exists(INPUT_FILE): return
    
    with open(INPUT_FILE, "rb") as f:
        full_data = f.read()

    print(f"[*] 尝试剥离头部字节...")
    
    # 尝试跳过 4, 8, 16, 32 字节
    for offset in [4, 8, 16, 32]:
        new_data = full_data[offset:]
        # 看看新开头是不是 0x47
        if new_data.startswith(b'G'):
            print(f"[!] 发现可能的偏移量: {offset} 字节 (剥离后以 0x47 开头)")
            with open(f"stripped_{offset}.ts", "wb") as out:
                out.write(new_data)
        else:
            # 即便开头不是 0x47，也保存前 100kb 看看播放效果
            with open(f"test_offset_{offset}.ts", "wb") as out:
                out.write(new_data[:1024*100])

if __name__ == "__main__":
    try_stripping()
