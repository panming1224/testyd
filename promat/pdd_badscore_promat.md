```
1.基于这个D:\testyd\pdd_kpi_copy.py为我新写一个程序就叫pdd_badscore.py放到D:\testyd
2.使用这个测试，EXCEL_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表-副本.xlsx'拉取拼多多差评，状态信息为N列，所有日期参数为昨天。
3.这个不需要下载，而是把http请求返回的内容以这种格式写入excel文件，提取的信息格式参照这个文件D:\pdd\评价文件存档\2025-09-26\回力运动袜旗舰店.xlsx。
4.保存到对应日期文件夹D:\pdd\评价文件存档。
5.合并文件夹为D:\pdd\合并文件\评价文件存档。
6.上传到warehouse/ods/pdd/pdd_badscore。
7.刷新dremio的minio.warehouse.ods.pdd."pdd_badscore"。
8.http请求：post
url：https://mms.pinduoduo.com/saturn/reviews/list
header：accept:
accept-language:zh-CN,zh;q=0.9
anti-content:
cache-control:
Content-Type:application/json
Cookie:cookie(进行替换)
etag:
origin:https://mms.pinduoduo.com
priority:
referer:https://mms.pinduoduo.com/goods/evaluation/index?msfrom=mms_globalsearch
sec-ch-ua:
sec-ch-ua-mobile:
sec-ch-ua-platform:
sec-fetch-dest:
sec-fetch-mode:
sec-fetch-site:
user-agent:
body：{"startTime":timestart(昨天00：00：00秒级时间戳),"endTime":timeend(昨天23：59：59秒级时间戳),"pageNo":1(需要根据页数循环),"pageSize":40,"descScore":["1","2","3"],"mainReviewContentStatus":"1","orderSn":""}
9.先根据返回的响应里面的total数量判断多少条数据，再改页数循环。
10.这是解析响应的实例def main(text):
    row_data = json.loads(text)
    totalRows=row_data .get('result').get('totalRows')
    data=row_data .get('result',{}).get('data',[])
    keys = [
    'descScore',           # 用户评价分
    'comment',             # 用户评论
    'orderSn',             # 订单编号
    'name',                # 卖家昵称（在 orderSnapshotInfo 里）
    'goodsId',             # 商品 ID
    # 'pictures_link',       # 自定义：所有用户图片 URL 合并
    'goodsInfoUrl'         # 页返回链接（商品页）
]
    table = [keys]

    max_pictures = 0  # 用于记录最大图片数量

    for item in data:
        row = []
        current_pictures = 0  # 当前条目中的图片数量

        # 遍历每个字段
        for k in keys:
            row.append(item.get(k, ''))

        # 处理图片链接，每个图片单独一列
        pics = item.get('pictures', []) or []
        current_pictures = len(pics)
        if current_pictures > max_pictures:
            max_pictures = current_pictures
        for pic in pics:
            row.append(pic.get('url', ''))

        # 如果当前图片数量少于最大值，填充空字符串以对齐
        if current_pictures < max_pictures:
            row.extend([''] * (max_pictures - current_pictures))

        table.append(row)

    # 更新表头以包含图片列
    table[0].extend([f'Picture_{i+1}' for i in range(max_pictures)])
    # return totalRows
    return [totalRows, table]
    # return row_data
```

