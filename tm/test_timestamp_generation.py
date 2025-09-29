from datetime import datetime

def test_timestamp_generation():
    """测试时间戳生成逻辑"""
    
    # 测试不同的日期
    test_dates = ["20250925", "20250926", "20250927", "20250928"]
    
    for begin_date in test_dates:
        # 基于begin_date的00:00:00生成时间戳
        begin_datetime = datetime.strptime(begin_date, "%Y%m%d")
        timestamp = str(int(begin_datetime.timestamp() * 1000))
        
        print(f"日期: {begin_date}")
        print(f"对应的datetime: {begin_datetime}")
        print(f"生成的时间戳: {timestamp}")
        
        # 验证时间戳转换回日期时间
        verify_datetime = datetime.fromtimestamp(int(timestamp) / 1000)
        print(f"验证转换回的时间: {verify_datetime}")
        print("-" * 50)

if __name__ == "__main__":
    test_timestamp_generation()