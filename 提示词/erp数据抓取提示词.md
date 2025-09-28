```
1.基于这个D:\testyd\jd_store.py为我新写一个程序就叫erp_store.py放到D:\testyd
需要先打开网页https://www.erp321.com/epaas获取cooike
2.使用这个测试，EXCEL_PATH = r'D:\yingdao\erp\店铺信息 - 副本.xlsx'拉取聚水潭的商品及库存管理及bom表两份数据，状态信息为E，F列，所有日期参数为昨天。
3.商品及库存管理下载方式：需要先发送下载请求，然后轮询检查请求，获取加载进度，直到加载进度变成100且返回url不为none，然后根据下载url下载。
bom表下载方式：点击元素下载，点击后会触发下载，可能需要你监听下载事件。
(1)先点击元素bom标签：<div role="tab" aria-selected="false" id="rc-tabs-0-tab-2342" class="ant-tabs-tab-btn" aria-controls="rc-tabs-0-panel-2342" tabindex="0">BOM维护</div>
(2)再点击元素：<span class="_db_txt _db_pic" style="background-image: url(&quot;/image/menu/import.gif&quot;);">BOM导入导出</span>
(3)再点击元素：<div class="_db_item _db_item_imgbg" title="BOM导出" style="background-image: url(&quot;/image/tool/Excel.gif&quot;);">BOM导出</div>
4.保存到对应日期文件夹D:\yingdao\erp\商品及库存管理，D:\yingdao\erp\bom表
5.合并文件夹为D:\yingdao\erp\合并表格\商品及库存管理，D:\yingdao\erp\合并表格\bom表
6.上传到warehouse/ods/erp/goodscount。warehouse/ods/erp/goodsbom。
7.刷新dremio的minio.warehouse.ods.erp.goodscount，minio.warehouse.ods.erp.goodsbom。
8.下载请求http请求：post
url：https://api.erp321.com/erp/webapi/ItemApi/Export/ItemSkuAndInventory?owner_co_id=owner_co_id(取自店铺信息C列)&authorize_co_id=authorize_co_id(取自店铺信息D列)

header：accept:application/json
accept-language:zh-CN,zh;q=0.9
Content-Type:application/json; charset=utf-8
Cookie:cookie(获取的值)
gwfp:
origin:https://src.erp321.com
priority:u=1, i
sec-ch-ua:
sec-ch-ua-mobile:
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-site
user-agent:

body：{"ip":"","uid":"21599824","coid":"owner_co_id"(取自店铺信息C列),"data":{"type":3,"searchCondition":{"enabled":"1","queryFlds":["pic","i_id","sku_id","name","properties_value","order_lock","qty","orderable","purchase_qty","virtual_qty","sales_qty_3","short_name","sale_price","cost_price","purchase_price","market_price","brand","category","vc_name","labels","sku_code","_sku_codes","supplier_name","purchaseFeature","purchaseQty","weight","l","w","h","volume","unit","enabled","stock_opensync","remark","sku_tag","bin_min_qty","bin_max_qty","overflow_qty","pack_qty","pack_volume","bin","other_price_1","other_price_2","other_price_3","other_1","other_2","other_3","modified","created","creator_name","is_cpfr","cpfr_qty","pic_big"],"sku_type":1,"orderBy":""},"filterType":2},"isOtherStore":false}
查询请求：post
url： https://api.erp321.com/erp/webapi/ItemApi/Export/GetExportData?owner_co_id=owner_co_id(取自店铺信息C列)&authorize_co_id=authorize_co_id(取自店铺信息D列)
header：accept:application/json
accept-language:zh-CN,zh;q=0.9
Content-Type:application/json; charset=utf-8
Cookie:cookie(获取的)
gwfp:
origin:https://src.erp321.com
priority:
sec-ch-ua:
sec-ch-ua-mobile:
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-site
user-agent:

body：{"ip":"","uid":"","coid":"owner_co_id(取自店铺信息C列)","data":data(来自解析商品及库存管理下载请求)}
9.这是解析响应的实例
def data(text):
    raw=json.loads(text)
    data=raw.get("data","")
    return data
    print(data)

def download(result):
    raw=json.loads(result)
    data=raw.get("data","")
    progress=data.get("progress","")
    url=data.get("url","")
    return [progress,url]
    print(progress,url)
```

