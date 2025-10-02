import sys
sys.path.append('D:\\testyd')
sys.path.append('D:\\testyd\\mysql')
from crawler_db_interface import CrawlerDBInterface

db = CrawlerDBInterface(
    platform='tm',
    shops_table='tm_shops',
    tasks_table='tm_tasks',
    database='company'
)

# 检查tm_shops表结构
query = 'DESCRIBE tm_shops'
result = db.execute_custom_sql(query)
print('tm_shops表结构:')
for field in result:
    print(f'  {field["Field"]}: {field["Type"]}')

print('\n' + '='*50 + '\n')

# 检查tm_shops表数据
query = 'SELECT COUNT(*) as count FROM tm_shops'
result = db.execute_custom_sql(query)
print(f'tm_shops表中有 {result[0]["count"]} 条记录')

# 查看前几条记录
query = 'SELECT * FROM tm_shops LIMIT 3'
shops = db.execute_custom_sql(query)
print('\n前3条记录:')
for i, shop in enumerate(shops):
    print(f'记录 {i+1}:')
    for key, value in shop.items():
        if key == 'qncookie' and value:
            print(f'  {key}: {value[:50]}...')
        else:
            print(f'  {key}: {value}')
    print()