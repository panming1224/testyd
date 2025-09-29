import datetime

# 时间戳转换
timestamp_ms = 1758729600000
print(f"时间戳: {timestamp_ms}")

# 转换为秒
timestamp_s = timestamp_ms / 1000
print(f"时间戳(秒): {timestamp_s}")

# 转换为日期时间
dt = datetime.datetime.fromtimestamp(timestamp_s)
print(f"对应时间: {dt}")
print(f"格式化时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

# 显示星期几
weekday_names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
weekday = weekday_names[dt.weekday()]
print(f"星期: {weekday}")