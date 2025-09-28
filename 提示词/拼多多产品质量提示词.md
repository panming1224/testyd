```
1.基于这个D:\testyd\pdd_kpi_copy.py为我新写一个程序就叫pdd_quality.py放到D:\testyd
2.使用这个测试，EXCEL_PATH = r'D:\pdd\拼多多店铺汇总表\拼多多店铺汇总表-副本.xlsx'拉取拼多多差评，状态信息为K列，所有日期参数为今天。
3.这个不需要下载，而是把http请求返回的内容以这种格式写入excel文件，提取的信息格式参照这个文件D:\pdd\产品质量体验存档\2025-09-26\回力运动袜旗舰店.xlsx。
保存和上传的表头使用这个[['商品id','商品名称','商品主图链接 ','商品质量体验排名','近30天异常订单数 ','异常订单占比',' 权益状态','商品质量等级','近30天品质求助平台率','近30天商品评价分排名','老客订单占比']]
对应关系为json在的['goods_id','goods_name','img_url','rank_percent','abnormal_order_num','abnormal_order_ratio','right_status','quality_level','quality_help_rate_last30_days','goods_rating_rank','repeat_purchase_ratio']
4.保存到对应日期文件夹D:\pdd\产品质量体验存档。
5.合并文件夹为D:\pdd\合并文件\产品质量体验存档。
6.上传到warehouse/ods/pdd/pdd_quality。
7.刷新dremio的minio.warehouse.ods.pdd."pdd_quality"。
8.http请求：post
url：https://mms.pinduoduo.com/api/price/mariana/quality_experience/goods_list
header：accept:*/*
accept-language:zh-CN,zh;q=0.9
anti-content:
cache-control:
Content-Type:application/json
Cookie:cookie(替换)
etag:
origin:https://mms.pinduoduo.com
priority:
referer:https://mms.pinduoduo.com/mms-marketing-mixin/quality-experience?msfrom=mms_globalsearch
sec-ch-ua:
sec-ch-ua-mobile:
sec-ch-ua-platform:"Windows"
sec-fetch-dest:
sec-fetch-mode:
sec-fetch-site:
user-agent:
body：{"sort_field":1,"sort_type":"ASC","page_size":40,"page_no":1}
9.先根据返回的响应里面的total数量判断多少条数据，再改页数循环。
10.这是解析响应的实例
def to_list(response,cols):
    data=json.loads(response)
    result=data.get("result",[])
    total=result.get("total",[])
    goods_list=result.get("goods_list",[])

    matrix = [[row.get(c, '') for c in cols] for row in goods_list]
    test=[total,matrix]
    return test
    print(test)
```

