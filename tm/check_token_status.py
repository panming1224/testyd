# -*- coding: utf-8 -*-
import time
from datetime import datetime

def check_token_status():
    """检查token状态"""
    # 从cookies.txt读取
    with open("d:/testyd/tm/cookies.txt", 'r', encoding='utf-8') as f:
        cookies_str = f.read().strip()
    
    # 查找_m_h5_tk cookie
    for cookie in cookies_str.split(';'):
        cookie = cookie.strip()
        if '_m_h5_tk=' in cookie:
            token_value = cookie.split('_m_h5_tk=')[1].strip()
            print(f"完整token值: {token_value}")
            
            # token格式为: token_expireTime
            if '_' in token_value:
                token_part = token_value.split('_')[0]
                expire_time = token_value.split('_')[1] if len(token_value.split('_')) > 1 else None
                
                print(f"Token部分: {token_part}")
                print(f"过期时间戳: {expire_time}")
                
                if expire_time:
                    try:
                        expire_timestamp = int(expire_time)
                        current_timestamp = int(time.time() * 1000)
                        
                        # 转换为可读时间
                        expire_datetime = datetime.fromtimestamp(expire_timestamp / 1000)
                        current_datetime = datetime.fromtimestamp(current_timestamp / 1000)
                        
                        print(f"当前时间: {current_datetime}")
                        print(f"Token过期时间: {expire_datetime}")
                        
                        if current_timestamp > expire_timestamp:
                            print("❌ Token已过期！")
                            time_diff = (current_timestamp - expire_timestamp) / 1000 / 60  # 分钟
                            print(f"已过期 {time_diff:.1f} 分钟")
                        else:
                            print("✅ Token仍然有效")
                            time_diff = (expire_timestamp - current_timestamp) / 1000 / 60  # 分钟
                            print(f"还有 {time_diff:.1f} 分钟过期")
                            
                    except ValueError:
                        print("❌ 无法解析过期时间戳")
            break
    else:
        print("❌ 未找到_m_h5_tk cookie")

if __name__ == "__main__":
    check_token_status()