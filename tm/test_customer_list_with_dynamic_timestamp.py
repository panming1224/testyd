import sys
sys.path.append('.')
from tm_chat_2_cleaned import TmallChatManager

def test_customer_list_with_dynamic_timestamp():
    """测试使用动态时间戳的客户列表获取"""
    
    # 创建提取器实例
    extractor = TmallChatManager()
    
    # 读取cookies
    try:
        with open('cookies.txt', 'r', encoding='utf-8') as f:
            cookies_str = f.read().strip()
        print("✅ 成功读取cookies")
    except Exception as e:
        print(f"❌ 读取cookies失败: {e}")
        return
    
    # 测试不同日期的客户列表获取
    test_dates = [
        ("20250925", "20250925"),
        ("20250926", "20250926"), 
        ("20250927", "20250927")
    ]
    
    for begin_date, end_date in test_dates:
        print(f"\n{'='*60}")
        print(f"测试日期范围: {begin_date} - {end_date}")
        print(f"{'='*60}")
        
        try:
            # 调用get_customer_list方法
            result = extractor.get_customer_list(
                cookies_str=cookies_str,
                begin_date=begin_date,
                end_date=end_date,
                page_size=5,  # 减少数量以便测试
                page_index=1
            )
            
            if result:
                print(f"✅ 成功获取客户列表")
                print(f"客户数量: {len(result.get('data', {}).get('result', {}).get('conversationList', []))}")
                
                # 显示前几个客户信息
                conversations = result.get('data', {}).get('result', {}).get('conversationList', [])
                for i, conv in enumerate(conversations[:3]):
                    user_id = conv.get('userID', {})
                    if isinstance(user_id, dict):
                        app_uid = user_id.get('appUid', 'N/A')
                    else:
                        app_uid = user_id
                    print(f"  客户 {i+1}: {conv.get('nick', 'N/A')} (appUid: {app_uid})")
            else:
                print("❌ 获取客户列表失败")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_customer_list_with_dynamic_timestamp()