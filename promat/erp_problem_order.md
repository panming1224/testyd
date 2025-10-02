```
需要动态获取的：1.ts___=1759308771842(动态获取)
2.Cookie:cookie（动态获取）
3.__VIEWSTATE=/wEPDwUKLTIwOTYzOTkwM2RkyoAQb6bjp9+PhPaoEJ6fF9qHb40=(查询页面元素获取)
4.__VIEWSTATEGENERATOR=C8154B07(查询页面元素获取)
1.参照D:\testyd\erp_store.py，打开浏览器，导航到https://www.erp321.com/epaas
2.获取cookie和3.4两个元素的值
3.帮我写http请求：post
url：https://www.erp321.com/app/order/order/list.aspx?_c=jst-epaas&ts___=1759308771842(动态获取)&am___=LoadDataToJSON
head：
accept:*/*
accept-language:zh-CN,zh;q=0.9
Content-Type:application/x-www-form-urlencoded; charset=UTF-8
Cookie:cookie（动态获取）
origin:https://www.erp321.com
priority:u=1, i
referer:https://www.erp321.com/app/order/order/list.aspx?_c=jst-epaas
sec-ch-ua:"Not=A?Brand";v="24", "Chromium";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-origin
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
x-requested-with:XMLHttpRequest

body:
__VIEWSTATE=/wEPDwUKLTIwOTYzOTkwM2RkyoAQb6bjp9+PhPaoEJ6fF9qHb40=(查询页面元素获取)
&__VIEWSTATEGENERATOR=C8154B07(查询页面元素获取)
&insurePrice=
&_jt_page_count_enabled=true
&_jt_page_increament_enabled=true
&_jt_page_increament_page_mode=
&_jt_page_increament_key_value=
&_jt_page_increament_business_values=
&_jt_page_increament_key_name=o_id
&_jt_page_size=2000
&_jt_page_action=2
&fe_node_desc=
&receiver_state=
&receiver_city=
&receiver_district=
&receiver_address=
&receiver_name=
&receiver_phone=
&receiver_mobile=
&check_name=
&check_address=
&fe_remark_type=single
&node_type=
&fe_flag=
&fe_is_append_remark=
&feedback=
&__CALLBACKID=JTable1
&__CALLBACKPARAM={"Method":"LoadDataToJSON"
,"Args":["1","[{\"k\":\"status\",\"v\":\"question\",\"c\":\"@=\"}
,{\"k\":\"question_type\",\"v\":\"亏钱订单,商品编码缺失,没有任何可发货商品\",\"c\":\"@=\"}
,{\"k\":\"order_date\",\"v\":\"今天\",\"c\":\">=\",\"t\":\"date\"}
,{\"k\":\"order_date\",\"v\":\"今天 23:59:59.998\",\"c\":\"<=\",\"t\":\"date\"}]"
,"{}"]}
根据响应内容的"PageCount\\":0,\\"PageIndex\\":1来进行循环获取所有数据，解析成表格后放到xlsx中
​```
(status_code=200, content_type='text/html', content_encoding='', content='0|{
    "IsSuccess": true,
    "ExceptionMessage": null,
    "ReturnValue": "{\\"dp\\":{\\"PageSize\\":2000,\\"PageSizes\\":[20,50,100,200,500,1000,1500,2000],\\"IsFirst\\":true,\\"IsLast\\":true,\\"PageCount\\":0,\\"PageIndex\\":1,\\"DataCount\\":-1,\\"SkipCount\\":0,\\"Action\\":1,\\"Increament\\":{\\"PageMode\\":null,\\"KeyName\\":\\"o_id\\",\\"BusinessValues\\":null,\\"KeyValue\\":\\"70176597\\"},\\"AggregationFields\\":null,\\"AggregationValues\\":null},\\"datas\\":[{\\"checked\\":\\"\\",\\"o_id\\":70210627,\\"labels\\":\\"拼团中,退货包运费\\",\\"shop_id\\":19161543,\\"its\\":\\"\\",\\"orderFreight\\":\\"\\",\\"multiWaybillLid\\":\\"\\",\\"process_infos\\":\\"\\",\\"package\\":null,\\"so_id\\":\\"251001-260109780600895\\",\\"purchase_id\\":\\"\\",\\"purchase_lid\\":\\"\\",\\"outer_so_id\\":null,\\"order_date\\":\\"2025-10-01 17: 16: 50\\",\\"pay_date\\":\\"2025-10-01 17: 16: 50\\",\\"shop_buyer_id\\":\\"开*_***********\\",\\"pay_amount\\":29.80,\\"paid_amount\\":29.80,\\"amount_list\\":\\"\\",\\"status\\":\\"异常\\",\\"question_suggest\\":\\"\\",\\"buyer_message\\":null,\\"remark\\":null,\\"drp_remark\\":\\"\\",\\"ext_datas\\":null,\\"glasses_setting\\":\\"\\",\\"promise_time\\":\\"\\",\\"lastCollect_time\\":\\"\\",\\"node\\":null,\\"logistics_company\\":null,\\"second_logistics\\":\\"\\",
​```
5.保存到D:\yingdao\erp\异常订单\{日期}\义务塔智有限公司.xlsx
6.合并文件夹在D:\yingdao\erp\合并表格\异常订单\{日期}.xlsx
7.将合并文件上传minio到warehouse/ods/erp/problem_order/dt={日期}/日期.parquet
8.刷新dremio数据集和反射minio.warehouse.ods.erp.problem_order
```

