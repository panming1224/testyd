```
0.创建脚本命名为D:\testyd\erp\erp_purchase_order.py
需要动态获取的参数：
(1)ts___=1759308771842(动态获取)
(2)Cookie:cookie（动态获取）
(3)__VIEWSTATE=/wEPDwUKLTIwOTYzOTkwM2RkyoAQb6bjp9+PhPaoEJ6fF9qHb40=(查询页面元素获取)
(4)__VIEWSTATEGENERATOR=C8154B07(查询页面元素获取)
1.参照D:\testyd\erp\erp_store_order.py，
打开浏览器，导航到https://www.erp321.com/app/scm/purchase/purchasemode.aspx?_c=jst-epaas
2.获取cookie和(3)(4)两个元素的值
3.根据请求案例帮我写http请求
4.根据响应案例的结构获取"PageCount\":6,\"PageIndex\":1,来进行循环获取所有数据,
三个响应解析出的数据，要以po_id为关联，放到同一行，这才是一份完整的数据。
，解析成表格后放到xlsx中
5.保存到D:\yingdao\erp\采购单\{日期}\义务塔智有限公司.xlsx
6.合并文件夹在D:\yingdao\erp\合并表格\采购单\{日期}.xlsx
7.将合并文件上传minio到ods/erp/pruchase_order/dt={日期}/日期.parquet
8.刷新dremio数据集和反射minio.warehouse.ods.erp.purchase_order
```

http请求样例1:

```python
import requests


headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.erp321.com",
    "priority": "u=1, i",
    "referer": "https://www.erp321.com/app/scm/purchase/purchasemode.aspx?_c=jst-epaas",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "_ati": "5108270968404",
    "j_d_3": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_ssi": "",
    "jump_env": "www",
    "isLogin": "true",
    "tmp_gray": "1",
    "jump_isgray": "0",
    "u_shop": "-1",
    "acw_tc": "ac11000117593918225423236e62d64503713247db54fb9fad8c9ea9ccb83a",
    "3AB9D23F7A4B3C9B": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_name": "%e6%bd%98%e6%98%8e",
    "u_lid": "13502065765",
    "_gi": "-302",
    "u_json": "%7b%22t%22%3a%222025-10-2+16%3a01%3a35%22%2c%22co_type%22%3a%22%e6%a0%87%e5%87%86%e5%95%86%e5%ae%b6%22%2c%22proxy%22%3anull%2c%22ug_id%22%3a%22%22%2c%22dbc%22%3a%221753%22%2c%22tt%22%3a%2247%22%2c%22apps%22%3a%221.4.150.152%22%2c%22pwd_valid%22%3a%221%22%2c%22ssi%22%3anull%2c%22sign%22%3a%224509017.A8FEE8ED32B64E8C851E636C09BAA362%2c289a6bfbe7b8b0a6c7feeeed3e251b58%22%7d",
    "u_co_name": "%e4%b9%89%e4%b9%8c%e5%b8%82%e5%a1%94%e6%99%ba%e6%9c%89%e9%99%90%e5%85%ac%e5%8f%b8",
    "u_drp": "-1000000001",
    "v_d_144": "1759392037946_df374e8f90b4fcb4a0772f8c932820e9",
    "u_cid": "134038656957646664",
    "u_r": "12%2c13%2c14%2c15%2c16%2c17%2c18%2c22%2c23%2c27%2c28%2c29%2c30%2c31%2c32%2c33%2c34%2c35%2c36%2c39%2c40%2c41%2c52%2c53%2c54%2c61%2c62%2c63%2c64%2c65%2c66%2c67%2c70%2c71%2c72%2c73%2c76%2c90%2c101%2c102%2c103%2c104%2c105%2c106%2c107%2c108%2c109",
    "u_sso_token": "CS@7909e64a439d4324aefa70122389f960",
    "u_id": "21599824",
    "u_co_id": "12910783",
    "p_50": "603A0D4C11DC5E531A23597A80F4EC43638950176957655711%7c12910783",
    "u_env": "www",
    "u_lastLoginType": "vc",
    "tfstk": "g_Hrw3foxLprRe7XFqeF0x26MCe8EJ81zvaQxDm3Vz4lFT_ngViQRTV3ZjzEoqzo8DK8xy0n8yGWGdi-2JeH5JJ6C0L65oDSUJbIm8ECQlZ3Ydi-2imdLXKHCMl_A4Zu-2VloZq7ogfo-7mcnrELxaqhEno0krXuquqhmSqgY9bn-JxqmrE3Ky03Zno0kk23-bMEqDX4f7xVwszFyQngaPmuu9o-3uVPw04VK9Dqg7zGLrWhKxr-YMHNUORQSfU71P0DhTyEmku41b8NU2onXXVqLaxSSqcE-ohv86zZt0GthSshZmkUz5Dugg-8hJrn-Wlv7OZzFjPZUbKdo00_zf2-AG8S05l46oVcY_2S1cMLsYvPWrNTYqPsaFWrSgkRJoXOLvhP-6VuDoz60nrdPV-2QtwD16CLiRE453Z596FuDoz60n5d9S4Y0Pt7V"
}
url = "https://www.erp321.com/app/scm/purchase/purchasemode.aspx"
params = {
    "_c": "jst-epaas",
    "ts___": "1759392193809",
    "am___": "LoadDataToJSON"
}
data = {
    "__VIEWSTATE": "/wEPDwUKLTM1NjA5NDk2NWRkcHUQ0Db7APYYmrgp3VbC6EbsdUk=",
    "__VIEWSTATEGENERATOR": "1FA1C91A",
    "owner_co_id": "12910783",
    "authorize_co_id": "12910783",
    "remarkOpt": "",
    "labelsOpt": "",
    "priceOptSource": "",
    "queryType": "",
    "poid_type": "po_id",
    "po_id": "",
    "dateRange_temp_id": "po_date",
    "po_date": [
        "",
        ""
    ],
    "status": "待审核,已确认",
    "delivery_status": "",
    "goods_status": "",
    "group": "",
    "supplier_name_id": "",
    "supplier_name": "",
    "filter_sku_id_temp_id": "包含商品",
    "sku_id": "",
    "remark_select": "-1",
    "remark": "",
    "purchaser_name_v": "",
    "purchaser_name": "",
    "lc_id_v": "",
    "lc_id": "",
    "l_id": "",
    "wms_co_id": "",
    "payment_method": "",
    "item_type": "",
    "wmslabels": "",
    "nowmslabels": "",
    "supplier_confirm": "",
    "is_1688_order": "",
    "confirm_name_v": "",
    "confirm_name": "",
    "contract_exist": "",
    "filter_lwh_id_binding_temp_id": "手动锁定",
    "lwh_id_binding": "",
    "manual_lwh_id_binding": "",
    "inpBubyer": [
        "东阳连裤袜厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A诸暨市黛丝韵针织厂D02",
        "A周正标袜厂Z03",
        "A-振鑫袜业Z01",
        "A-柚童针织Y07",
        "A（义乌）杨成林Y01",
        "义乌市友力鞋业有限公司",
        "A温州美梭针织有限公司（陈胜伟）M03",
        "A-（义乌）游冬冬Y05",
        "A-（江都）亿哈健身用品厂",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "A翊品服饰Y08",
        "A（义乌）杨成林Y01",
        "A翊品服饰Y08",
        "A-妙秀品针织M02",
        "A-诸暨市依欣露针织厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A周正标袜厂Z03",
        "A（河南）-亿首艺Y04",
        "A-骏腾体育用品",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司"
    ],
    "_jt_page_count_enabled": "",
    "_jt_page_size": "25",
    "__CALLBACKID": "JTable1",
    "__CALLBACKPARAM": "{\"Method\":\"LoadDataToJSON\",\"Args\":[\"1\",\"[{\\\"k\\\":\\\"poid_type\\\",\\\"v\\\":\\\"po_id\\\",\\\"c\\\":\\\"@=\\\"},{\\\"k\\\":\\\"status\\\",\\\"v\\\":\\\"WaitConfirm,Confirmed\\\",\\\"c\\\":\\\"@=\\\"},{\\\"k\\\":\\\"remark_select\\\",\\\"v\\\":\\\"-1\\\",\\\"c\\\":\\\"@=\\\"},{\\\"k\\\":\\\"contract_exist\\\",\\\"v\\\":\\\"\\\",\\\"c\\\":\\\"@=\\\"}]\",\"{}\"]}"
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)
```

http响应示例1：

```json
0|{"IsSuccess":true,"ExceptionMessage":null,"ReturnValue":"{\"dp\":{\"PageSize\":500,\"PageSizes\":[25,50,100,200,500],\"IsFirst\":true,\"IsLast\":false,\"PageCount\":6,\"PageIndex\":1,\"DataCount\":130,\"SkipCount\":0,\"Action\":0,\"Increament\":null,\"AggregationFields\":null,\"AggregationValues\":null},\"datas\":[{\"rn__\":1,\"checked\":\"\",\"po_id\":145159,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-02 10:33:24\",\"seller\":\"A-（义乌）游冬冬Y05\",\"sellerGroup\":\"百货\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":0.00,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/月结 10.3到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-02 10:33:24\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":11087140,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-02 10:35:22\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:35:22\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"ODbT3jg8x9CRWl_/=-wXkAWb_/=-4Sqn4AJa9ZQEW_/=-opRzLTU=\",\"price_changed\":false},{\"rn__\":2,\"checked\":\"\",\"po_id\":145158,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-02 10:33:24\",\"seller\":\"A-（江都）亿哈健身用品厂\",\"sellerGroup\":\"护膝\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/月结 10.3到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-02 10:33:24\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":10093407,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-02 10:35:22\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:35:22\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"1cvRCIG5VYb1N8iVI8JklokHuiYsCp559k9bun_/=-XRqQ=\",\"price_changed\":false},{\"rn__\":3,\"checked\":\"\",\"po_id\":145157,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-02 10:33:23\",\"seller\":\"A（义乌）酷琦彩印包装\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/月结 10.3到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-02 10:33:24\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":15699748,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-02 10:35:22\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:35:22\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"oSyV1KYgM9/LrXEewpoA7hUBp9KG4v4F69cFDxzNNkg=\",\"price_changed\":false},{\"rn__\":4,\"checked\":\"\",\"po_id\":145128,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 18:50:08\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"待审核\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓10.3必发（加急单）-不贴防伪码\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 18:50:08\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":null,\"confirm_date\":null,\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 18:50:08\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"WaitConfirm\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"v89A7yTIE/HfZN1lY4/8In2uL2ETqyvPdaP315OpHOs=\",\"price_changed\":false},{\"rn__\":5,\"checked\":\"\",\"po_id\":145127,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 18:49:26\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"待审核\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓10.1-不贴防伪码\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 18:49:26\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":null,\"confirm_date\":null,\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 18:49:26\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"WaitConfirm\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"Fh_/=-o3zXderGllnCigkpZ5c39FwMOlXlsBQrevzvw2p8=\",\"price_changed\":false},{\"rn__\":6,\"checked\":\"\",\"po_id\":145126,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 18:48:48\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"待审核\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓10.1-贴防伪码\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 18:48:48\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":null,\"confirm_date\":null,\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 18:48:48\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"WaitConfirm\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"lYs5iLUY1FKVGNpZZwYmkY_/=-hzuIK7riStuv/03gtvS0=\",\"price_changed\":false},{\"rn__\":7,\"checked\":\"\",\"po_id\":145116,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 17:40:40\",\"seller\":\"A诸暨市臻阳袜业有限公司(项钊）\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 17:40:40\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":30271622,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"pNkLrZdOi9GeXRO2QoaLS8/kJOUkm/hjkvsimPileJ4=\",\"price_changed\":false},{\"rn__\":8,\"checked\":\"\",\"po_id\":145115,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 17:38:01\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"未上架\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"部分入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"朱宇强\",\"remark\":\"10.1张杨杨\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 17:38:01\",\"modifier\":20098092,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"向上\",\"confirm_date\":\"2025-10-02 10:28:44\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-02 10:28:44\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"向上\",\"__KeyData\":\"ePSWplZM2T5mORhmAeqLq1rr63XgEvBmFV6smDLUcLE=\",\"price_changed\":false},{\"rn__\":9,\"checked\":\"\",\"po_id\":145109,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 17:22:26\",\"seller\":\"A-柚童针织Y07\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 17:22:26\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":12887560,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"S8RadPd9XiyrQPFIbk1cuLsluMrtueTYbTMUQFXKvNU=\",\"price_changed\":false},{\"rn__\":10,\"checked\":\"\",\"po_id\":145108,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 17:22:26\",\"seller\":\"A翊品服饰Y08\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 17:22:26\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":10093478,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"O/n1FkVrJMjJQ7kQj2wUodfWJth_/=-Vtdl_/=-M7uCx9t9Nw=\",\"price_changed\":false},{\"rn__\":11,\"checked\":\"\",\"po_id\":145107,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 17:22:26\",\"seller\":\"A（义乌）杨成林Y01\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 17:22:26\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":10093277,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"zKozknGZa9f8y1mxMTnnQEeMZN0EjJgR2afpMlygDYU=\",\"price_changed\":false},{\"rn__\":12,\"checked\":\"\",\"po_id\":145088,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 16:45:38\",\"seller\":\"A翊品服饰Y08\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 16:45:38\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":10093478,\"type\":\"po\",\"wms_co_id\":14048088,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩诸暨孵化仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"receiver_name\":\"孵化仓\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"OtmIvqYdw4BB33bvWbbuxB1EHdZBZD626gc1aWikk9g=\",\"price_changed\":false},{\"rn__\":13,\"checked\":\"\",\"po_id\":145087,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 16:45:38\",\"seller\":\"A诸暨魅姿针织\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"term\":\"13967557666 李东平\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 16:45:38\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":30465962,\"type\":\"po\",\"wms_co_id\":14048088,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩诸暨孵化仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"receiver_name\":\"孵化仓\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"bZOqK7IqJRhD8xXUN_/=-wcXuvjOiIeGQ1CDNGhLnuHfDw=\",\"price_changed\":false},{\"rn__\":14,\"checked\":\"\",\"po_id\":145086,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 16:45:38\",\"seller\":\"A-妙秀品针织M02\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 16:45:38\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":11584475,\"type\":\"po\",\"wms_co_id\":14048088,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩诸暨孵化仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"receiver_name\":\"孵化仓\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"FgzKB5k_/=-/yBxC4i2Vz6aDrhiSSR7C/h6/XgA62oUtOY=\",\"price_changed\":false},{\"rn__\":15,\"checked\":\"\",\"po_id\":145084,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 16:45:38\",\"seller\":\"A（义乌）杨成林Y01\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"戴靖\",\"remark\":\"10.2到货\",\"address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 16:45:38\",\"modifier\":21193426,\"co_id\":12910783,\"creator\":21193426,\"seller_id\":10093277,\"type\":\"po\",\"wms_co_id\":14048088,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩诸暨孵化仓\",\"sub_type\":null,\"confirm_name\":\"戴靖\",\"confirm_date\":\"2025-10-02 09:20:14\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"receiver_name\":\"孵化仓\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 09:20:14\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"戴靖\",\"__KeyData\":\"t2226ZBm1ZkQ_/=-vU1PqGrBeNERa8hRWYAcRs_/=-sxfnjPc=\",\"price_changed\":false},{\"rn__\":16,\"checked\":\"\",\"po_id\":145081,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 16:34:10\",\"seller\":\"A-诸暨市依欣露针织厂\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":\"\",\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/现结 10.5到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":\"\",\"accounting_period_days\":0,\"created\":\"2025-10-01 16:35:45\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":31481276,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-02 09:16:27\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:28:45\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"sfufBNrTkyAmLpx1o90BHMXGFrYOk97W79Kmj7lAkJ8=\",\"price_changed\":false},{\"rn__\":17,\"checked\":\"\",\"po_id\":145076,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 15:49:38\",\"seller\":\"A诸暨市臻阳袜业有限公司(项钊）\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"刘宇珂\",\"remark\":\"新品\",\"address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 15:49:38\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":21684661,\"seller_id\":30271622,\"type\":\"po\",\"wms_co_id\":14048088,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩诸暨孵化仓\",\"sub_type\":null,\"confirm_name\":\"刘宇珂\",\"confirm_date\":\"2025-10-01 15:53:39\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 义乌市 圣达南街 浙江省义乌市圣达南街505号，跨境电商物流园S2孵化仓\",\"receiver_name\":\"孵化仓\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-01 15:54:12\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"K2unMyFFAc3Cr7svfNA3L9y8H1GW9fgZ9iBIiYiPuvI=\",\"price_changed\":false},{\"rn__\":18,\"checked\":\"\",\"po_id\":145069,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 14:53:42\",\"seller\":\"A诸暨市黛丝韵针织厂D02\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"朱宇强\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 14:53:42\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":10093369,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 14:53:50\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-01 14:54:49\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"gr0ZOS_/=-UYzVaMk0SsrGm3A5pELXmupHqFrZ9rYlabPU=\",\"price_changed\":false},{\"rn__\":19,\"checked\":\"\",\"po_id\":145068,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 14:53:42\",\"seller\":\"A周正标袜厂Z03\",\"sellerGroup\":\"袜子\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":100.00,\"purchaser_name\":\"朱宇强\",\"remark\":\"10.2到货\",\"address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 14:53:42\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17754648,\"type\":\"po\",\"wms_co_id\":14441134,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"亮彩标杆仓\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 14:53:50\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道义乌跨境物流园（S2）A2栋1单元4楼\",\"receiver_name\":\"李世超\",\"receiver_phone\":\"131****961\",\"member_id\":null,\"modified\":\"2025-10-01 14:53:50\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"LXqEatdyFyXiz8lxssTrb5gEyEnMRno2r5pLND62I74=\",\"price_changed\":false},{\"rn__\":20,\"checked\":\"\",\"po_id\":145046,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 11:52:16\",\"seller\":\"A（河南）-亿首艺Y04\",\"sellerGroup\":\"百货（外采）\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/月结 10.5到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 11:52:16\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":16353270,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-02 09:16:27\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:29:01\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"ogV09HoG1LmmwKJHk2dw1V_/=-ELwkSFNZHZA6UdBKXmnw=\",\"price_changed\":false},{\"rn__\":21,\"checked\":\"\",\"po_id\":145045,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 11:52:16\",\"seller\":\"A-骏腾体育用品\",\"sellerGroup\":\"护膝\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"周俊辉\",\"remark\":\"未结/月结 10.5到\",\"address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"term\":\"\",\"payment_method\":\"账期结算\",\"accounting_period_days\":30,\"created\":\"2025-10-01 11:52:16\",\"modifier\":20098132,\"co_id\":12910783,\"creator\":20098132,\"seller_id\":10093302,\"type\":\"po\",\"wms_co_id\":null,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"\",\"sub_type\":null,\"confirm_name\":\"周俊辉\",\"confirm_date\":\"2025-10-01 11:52:56\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":null,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"浙江省 金华市 义乌市 稠江街道 圣达南街505号 义乌市跨境电商物流园（S2) A2栋一单元6楼\",\"receiver_name\":\"蔡点水\",\"receiver_phone\":\"111****111\",\"member_id\":null,\"modified\":\"2025-10-02 10:29:04\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"周俊辉\",\"__KeyData\":\"NkzQ82uihf3QxyrTzqmQFah7MpFsbOfpouyg8ASyrEc=\",\"price_changed\":false},{\"rn__\":22,\"checked\":\"\",\"po_id\":145032,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 10:48:52\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"待审核\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓9.29-贴防伪码\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 10:48:52\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 10:49:29\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 10:49:52\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"WaitConfirm\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"bMaWelbiG3cNzLgfDasmaBbJAbMO7QSHhox7/F4qhTM=\",\"price_changed\":false},{\"rn__\":23,\"checked\":\"\",\"po_id\":145031,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 10:46:58\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"待审核\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓9.29-不贴防伪码\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 10:46:58\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 10:49:29\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 10:49:52\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"WaitConfirm\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"sykV0dHO6e/6kWTedSxMb0YzsX_/=-sbkrqT7IRvw4By9U=\",\"price_changed\":false},{\"rn__\":24,\"checked\":\"\",\"po_id\":145029,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 10:15:52\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓9.6-不贴防伪码-9.30发货清单-192件\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 10:15:52\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 10:16:15\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 10:16:15\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"0Vy7m4FTknF31UIO7cel/5rZGDaPjtLLamrskd5XhEI=\",\"price_changed\":false},{\"rn__\":25,\"checked\":\"\",\"po_id\":145027,\"merge_po_id\":null,\"op\":\"\",\"po_date\":\"2025-10-01 10:13:26\",\"seller\":\"张杨杨针织有限公司\",\"sellerGroup\":\"\",\"wangwang\":\"\",\"status\":\"已确认\",\"supplier_confirm\":\"待确认\",\"pa\":\"查看\",\"pa_status\":\"\",\"item_type\":\"成品\",\"labels\":null,\"PrintTask\":null,\"print_count\":0,\"qty_count\":\"\",\"sku_amount\":\"\",\"total_in_qty\":\"\",\"total_differences_count\":\"\",\"return_qty\":\"\",\"is_delivery\":\"\",\"qc_qty\":\"\",\"qc_q_qty\":\"\",\"qc_d_qty\":\"\",\"supplier_delivery_qty\":\"\",\"receive_status\":\"未入库\",\"delivery_status\":null,\"logistics_status\":\"\",\"enable_booking_qty\":\"\",\"enable_follow_qty\":\"\",\"delivery_date\":\"\",\"plan_arrive_date\":\"\",\"plan_arrive_qty\":\"\",\"un_arrive_qty\":\"\",\"tax_rate\":null,\"more_rate\":null,\"purchaser_name\":\"朱宇强\",\"remark\":\"亮彩发厦门云仓9.15-不贴防伪码-9.30发货清单-125件\",\"address\":\"\",\"term\":\"\",\"payment_method\":null,\"accounting_period_days\":null,\"created\":\"2025-10-01 10:13:26\",\"modifier\":20890960,\"co_id\":12910783,\"creator\":20890960,\"seller_id\":17147116,\"type\":\"po\",\"wms_co_id\":15001966,\"source_o_id\":null,\"source_o_ids\":\"\",\"source_shop_name\":\"\",\"temp_outer_po_id\":null,\"outer_po_id\":null,\"outer_po_id_1688\":null,\"outer_status_1688\":null,\"type_name\":\"普通采购单\",\"wms_co_name\":\"海能发供应链-亮彩\",\"sub_type\":null,\"confirm_name\":\"朱宇强\",\"confirm_date\":\"2025-10-01 10:13:46\",\"good_status\":\"F\",\"diffQty_status\":\"F\",\"virtual_status\":null,\"lock_warehouse_name\":\"\",\"logistics_company\":null,\"l_id\":null,\"lidcount\":0,\"freight\":0.00,\"lock_lwh_id\":null,\"lock_priority_json\":null,\"prepayments_amount\":\"\",\"contract_file_list\":\"\",\"is_exist_payment\":\"\",\"outer_status\":null,\"send_address\":\"\",\"receiver_name\":\"\",\"receiver_phone\":\"\",\"member_id\":null,\"modified\":\"2025-10-01 10:13:46\",\"finish_time\":null,\"is_archive\":false,\"owner_co_id\":0,\"status_v\":\"Confirmed\",\"modifier_name\":\"朱宇强\",\"__KeyData\":\"sgbL6Kmtmn6X02tJQilUsCuwaDqNSlasOs_/=-Po82C24w=\",\"price_changed\":false}]}","ExceptionText":null,"GotoLogin":false,"ClientScript":null,"Message":null,"LocationUrl":null,"OpenUrl":null,"IsReloadPage":false,"IsReloadData":false,"IsResetData":false,"RequestId":"ac11000117593730723451600e52c2"}

```

http请求样例2：

```
import requests


headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.erp321.com",
    "priority": "u=1, i",
    "referer": "https://www.erp321.com/app/scm/purchase/purchasemode.aspx?_c=jst-epaas",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "purchase_item_height_21599824": "%7B%22foot%22%3A70%2C%22jspliter%22%3A347%7D",
    "_ati": "5108270968404",
    "j_d_3": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_ssi": "",
    "jump_env": "www",
    "isLogin": "true",
    "tmp_gray": "1",
    "jump_isgray": "0",
    "u_shop": "-1",
    "acw_tc": "ac11000117593918225423236e62d64503713247db54fb9fad8c9ea9ccb83a",
    "3AB9D23F7A4B3C9B": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_name": "%e6%bd%98%e6%98%8e",
    "u_lid": "13502065765",
    "_gi": "-302",
    "u_json": "%7b%22t%22%3a%222025-10-2+16%3a01%3a35%22%2c%22co_type%22%3a%22%e6%a0%87%e5%87%86%e5%95%86%e5%ae%b6%22%2c%22proxy%22%3anull%2c%22ug_id%22%3a%22%22%2c%22dbc%22%3a%221753%22%2c%22tt%22%3a%2247%22%2c%22apps%22%3a%221.4.150.152%22%2c%22pwd_valid%22%3a%221%22%2c%22ssi%22%3anull%2c%22sign%22%3a%224509017.A8FEE8ED32B64E8C851E636C09BAA362%2c289a6bfbe7b8b0a6c7feeeed3e251b58%22%7d",
    "u_co_name": "%e4%b9%89%e4%b9%8c%e5%b8%82%e5%a1%94%e6%99%ba%e6%9c%89%e9%99%90%e5%85%ac%e5%8f%b8",
    "u_drp": "-1000000001",
    "v_d_144": "1759392037946_df374e8f90b4fcb4a0772f8c932820e9",
    "u_cid": "134038656957646664",
    "u_r": "12%2c13%2c14%2c15%2c16%2c17%2c18%2c22%2c23%2c27%2c28%2c29%2c30%2c31%2c32%2c33%2c34%2c35%2c36%2c39%2c40%2c41%2c52%2c53%2c54%2c61%2c62%2c63%2c64%2c65%2c66%2c67%2c70%2c71%2c72%2c73%2c76%2c90%2c101%2c102%2c103%2c104%2c105%2c106%2c107%2c108%2c109",
    "u_sso_token": "CS@7909e64a439d4324aefa70122389f960",
    "u_id": "21599824",
    "u_co_id": "12910783",
    "p_50": "603A0D4C11DC5E531A23597A80F4EC43638950176957655711%7c12910783",
    "u_env": "www",
    "u_lastLoginType": "vc",
    "tfstk": "g_Hrw3foxLprRe7XFqeF0x26MCe8EJ81zvaQxDm3Vz4lFT_ngViQRTV3ZjzEoqzo8DK8xy0n8yGWGdi-2JeH5JJ6C0L65oDSUJbIm8ECQlZ3Ydi-2imdLXKHCMl_A4Zu-2VloZq7ogfo-7mcnrELxaqhEno0krXuquqhmSqgY9bn-JxqmrE3Ky03Zno0kk23-bMEqDX4f7xVwszFyQngaPmuu9o-3uVPw04VK9Dqg7zGLrWhKxr-YMHNUORQSfU71P0DhTyEmku41b8NU2onXXVqLaxSSqcE-ohv86zZt0GthSshZmkUz5Dugg-8hJrn-Wlv7OZzFjPZUbKdo00_zf2-AG8S05l46oVcY_2S1cMLsYvPWrNTYqPsaFWrSgkRJoXOLvhP-6VuDoz60nrdPV-2QtwD16CLiRE453Z596FuDoz60n5d9S4Y0Pt7V"
}
url = "https://www.erp321.com/app/scm/purchase/purchasemode.aspx"
params = {
    "_c": "jst-epaas",
    "ts___": "1759392793124",
    "am___": "FillFollowBooking"
}
data = {
    "__VIEWSTATE": "/wEPDwUKLTM1NjA5NDk2NWRkcHUQ0Db7APYYmrgp3VbC6EbsdUk=",
    "__VIEWSTATEGENERATOR": "1FA1C91A",
    "owner_co_id": "12910783",
    "authorize_co_id": "12910783",
    "remarkOpt": "",
    "labelsOpt": "",
    "priceOptSource": "",
    "queryType": "",
    "poid_type": "po_id",
    "po_id": "",
    "dateRange_temp_id": "po_date",
    "po_date": [
        "",
        ""
    ],
    "status": "待审核,已确认",
    "delivery_status": "",
    "goods_status": "",
    "group": "",
    "supplier_name_id": "",
    "supplier_name": "",
    "filter_sku_id_temp_id": "包含商品",
    "sku_id": "",
    "remark_select": "-1",
    "remark": "",
    "purchaser_name_v": "",
    "purchaser_name": "",
    "lc_id_v": "",
    "lc_id": "",
    "l_id": "",
    "wms_co_id": "",
    "payment_method": "",
    "item_type": "",
    "wmslabels": "",
    "nowmslabels": "",
    "supplier_confirm": "",
    "is_1688_order": "",
    "confirm_name_v": "",
    "confirm_name": "",
    "contract_exist": "",
    "filter_lwh_id_binding_temp_id": "手动锁定",
    "lwh_id_binding": "",
    "manual_lwh_id_binding": "",
    "inpBubyer": [
        "东阳连裤袜厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A诸暨市黛丝韵针织厂D02",
        "A周正标袜厂Z03",
        "A-振鑫袜业Z01",
        "A-柚童针织Y07",
        "A（义乌）杨成林Y01",
        "义乌市友力鞋业有限公司",
        "A温州美梭针织有限公司（陈胜伟）M03",
        "A-（义乌）游冬冬Y05",
        "A-（江都）亿哈健身用品厂",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "A翊品服饰Y08",
        "A（义乌）杨成林Y01",
        "A翊品服饰Y08",
        "A-妙秀品针织M02",
        "A-诸暨市依欣露针织厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A周正标袜厂Z03",
        "A（河南）-亿首艺Y04",
        "A-骏腾体育用品",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司"
    ],
    "_jt_page_count_enabled": "",
    "_jt_page_size": "500",
    "__CALLBACKID": "JTable1",
    "__CALLBACKPARAM": "{\"Method\":\"FillFollowBooking\",\"Args\":[\"[{\\\"po_id\\\":145193,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145192,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145191,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145190,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145189,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145188,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145187,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145185,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145174,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145159,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145158,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145128,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145127,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145126,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145108,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145107,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145088,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145086,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145081,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145076,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145068,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":0},{\\\"po_id\\\":145046,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145045,\\\"status_v\\\":\\\"Confirmed\\\",\\\"freight\\\":null},{\\\"po_id\\\":145032,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0},{\\\"po_id\\\":145031,\\\"status_v\\\":\\\"WaitConfirm\\\",\\\"freight\\\":0}]\"],\"CallControl\":\"{page}\"}"
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)
```

http响应样例2：

```
0|{"IsSuccess":true,"ExceptionMessage":null,"ReturnValue":[{"po_id":145193,"status_v":"Confirmed","freight":null,"enable_booking_qty":1670.0000,"enable_follow_qty":1670.0000,"booking_count":0,"qty_count":1670.0000,"item_count":8,"total_in_qty":0.0000,"total_differences_count":1670.0000,"supplier_delivery_qty":0,"sku_amount":13256.30,"sku_sale_amount":0.00,"currency_amounts":0},{"po_id":145192,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":600.0000,"enable_follow_qty":600.0000,"booking_count":0,"qty_count":600.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":600.0000,"supplier_delivery_qty":0,"sku_amount":1932.00,"sku_sale_amount":2318.40,"currency_amounts":0},{"po_id":145191,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":250.0000,"enable_follow_qty":250.0000,"booking_count":0,"qty_count":250.0000,"item_count":2,"total_in_qty":0.0000,"total_differences_count":250.0000,"supplier_delivery_qty":0,"sku_amount":462.50,"sku_sale_amount":555.00,"currency_amounts":0},{"po_id":145190,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":200.0000,"enable_follow_qty":200.0000,"booking_count":0,"qty_count":200.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":200.0000,"supplier_delivery_qty":0,"sku_amount":596.00,"sku_sale_amount":715.20,"currency_amounts":0},{"po_id":145189,"status_v":"Confirmed","freight":0,"enable_booking_qty":200.0000,"enable_follow_qty":200.0000,"booking_count":0,"qty_count":200.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":200.0000,"supplier_delivery_qty":0,"sku_amount":804.00,"sku_sale_amount":962.40,"currency_amounts":0.00},{"po_id":145188,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":200.0000,"enable_follow_qty":200.0000,"booking_count":0,"delivery_date":"2025-10-02 15:00:24","qty_count":200.0000,"item_count":2,"total_in_qty":0.0000,"total_differences_count":200.0000,"supplier_delivery_qty":0,"sku_amount":850.00,"sku_sale_amount":1020.00,"currency_amounts":0},{"po_id":145187,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":550.0000,"enable_follow_qty":550.0000,"booking_count":0,"delivery_date":"2025-10-02 15:00:24","qty_count":550.0000,"item_count":6,"total_in_qty":0.0000,"total_differences_count":550.0000,"supplier_delivery_qty":0,"sku_amount":1792.50,"sku_sale_amount":2151.00,"currency_amounts":0},{"po_id":145185,"status_v":"Confirmed","freight":null,"enable_booking_qty":0.0000,"enable_follow_qty":0.0000,"booking_count":0,"qty_count":1720.0000,"item_count":13,"total_in_qty":1720.0000,"total_differences_count":0.0000,"supplier_delivery_qty":0,"sku_amount":11180.19,"sku_sale_amount":16340.00,"currency_amounts":0},{"po_id":145174,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":500.0000,"enable_follow_qty":500.0000,"booking_count":0,"qty_count":500.0000,"item_count":3,"total_in_qty":0.0000,"total_differences_count":500.0000,"supplier_delivery_qty":0,"sku_amount":1800.00,"sku_sale_amount":1800.00,"currency_amounts":0},{"po_id":145159,"status_v":"Confirmed","freight":null,"enable_booking_qty":200.0000,"enable_follow_qty":200.0000,"booking_count":0,"qty_count":200.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":200.0000,"supplier_delivery_qty":0,"sku_amount":1100.00,"sku_sale_amount":1320.00,"currency_amounts":0},{"po_id":145158,"status_v":"Confirmed","freight":null,"enable_booking_qty":300.0000,"enable_follow_qty":300.0000,"booking_count":0,"qty_count":300.0000,"item_count":2,"total_in_qty":0.0000,"total_differences_count":300.0000,"supplier_delivery_qty":0,"sku_amount":2100.00,"sku_sale_amount":2475.00,"currency_amounts":0},{"po_id":145128,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":11000.0000,"enable_follow_qty":11000.0000,"booking_count":0,"qty_count":11000.0000,"item_count":30,"total_in_qty":0.0000,"total_differences_count":11000.0000,"supplier_delivery_qty":0,"sku_amount":71172.32,"sku_sale_amount":83651.68,"currency_amounts":0},{"po_id":145127,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":38500.0000,"enable_follow_qty":38500.0000,"booking_count":0,"qty_count":38500.0000,"item_count":8,"total_in_qty":0.0000,"total_differences_count":38500.0000,"supplier_delivery_qty":0,"sku_amount":298425.10,"sku_sale_amount":353863.22,"currency_amounts":0},{"po_id":145126,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":1400.0000,"enable_follow_qty":1400.0000,"booking_count":0,"delivery_date":"2025-10-01 18:48:48","qty_count":1400.0000,"item_count":4,"total_in_qty":0.0000,"total_differences_count":1400.0000,"supplier_delivery_qty":0,"sku_amount":5971.10,"sku_sale_amount":7165.31,"currency_amounts":0},{"po_id":145108,"status_v":"Confirmed","freight":0,"enable_booking_qty":100.0000,"enable_follow_qty":100.0000,"booking_count":0,"qty_count":100.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":100.0000,"supplier_delivery_qty":0,"sku_amount":787.00,"sku_sale_amount":905.05,"currency_amounts":0},{"po_id":145107,"status_v":"Confirmed","freight":0,"enable_booking_qty":150.0000,"enable_follow_qty":150.0000,"booking_count":0,"qty_count":150.0000,"item_count":2,"total_in_qty":0.0000,"total_differences_count":150.0000,"supplier_delivery_qty":0,"sku_amount":342.50,"sku_sale_amount":411.00,"currency_amounts":0},{"po_id":145088,"status_v":"Confirmed","freight":0,"enable_booking_qty":150.0000,"enable_follow_qty":150.0000,"booking_count":0,"qty_count":150.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":150.0000,"supplier_delivery_qty":0,"sku_amount":225.00,"sku_sale_amount":225.00,"currency_amounts":0},{"po_id":145086,"status_v":"Confirmed","freight":0,"enable_booking_qty":400.0000,"enable_follow_qty":400.0000,"booking_count":0,"qty_count":400.0000,"item_count":4,"total_in_qty":0.0000,"total_differences_count":400.0000,"supplier_delivery_qty":0,"sku_amount":420.00,"sku_sale_amount":420.00,"currency_amounts":0},{"po_id":145081,"status_v":"Confirmed","freight":null,"enable_booking_qty":600.0000,"enable_follow_qty":600.0000,"booking_count":0,"qty_count":600.0000,"item_count":12,"total_in_qty":0.0000,"total_differences_count":600.0000,"supplier_delivery_qty":0,"sku_amount":5610.00,"sku_sale_amount":0,"currency_amounts":0},{"po_id":145076,"status_v":"Confirmed","freight":0,"enable_booking_qty":60000.0000,"enable_follow_qty":60000.0000,"booking_count":0,"qty_count":60000.0000,"item_count":6,"total_in_qty":0.0000,"total_differences_count":60000.0000,"supplier_delivery_qty":0,"sku_amount":108000.00,"sku_sale_amount":0.00,"currency_amounts":0.00},{"po_id":145068,"status_v":"Confirmed","freight":0,"enable_booking_qty":200.0000,"enable_follow_qty":200.0000,"booking_count":0,"qty_count":200.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":200.0000,"supplier_delivery_qty":0,"sku_amount":1624.00,"sku_sale_amount":1867.60,"currency_amounts":0},{"po_id":145046,"status_v":"Confirmed","freight":null,"enable_booking_qty":950.0000,"enable_follow_qty":950.0000,"booking_count":0,"qty_count":950.0000,"item_count":3,"total_in_qty":0.0000,"total_differences_count":950.0000,"supplier_delivery_qty":0,"sku_amount":5680.00,"sku_sale_amount":6847.20,"currency_amounts":0.00},{"po_id":145045,"status_v":"Confirmed","freight":null,"enable_booking_qty":1200.0000,"enable_follow_qty":1200.0000,"booking_count":0,"qty_count":1200.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":1200.0000,"supplier_delivery_qty":0,"sku_amount":5520.00,"sku_sale_amount":6624.00,"currency_amounts":0},{"po_id":145032,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":400.0000,"enable_follow_qty":400.0000,"booking_count":0,"qty_count":400.0000,"item_count":1,"total_in_qty":0.0000,"total_differences_count":400.0000,"supplier_delivery_qty":0,"sku_amount":4121.60,"sku_sale_amount":4739.84,"currency_amounts":0},{"po_id":145031,"status_v":"WaitConfirm","freight":0,"enable_booking_qty":68100.0000,"enable_follow_qty":68100.0000,"booking_count":0,"qty_count":68100.0000,"item_count":17,"total_in_qty":0.0000,"total_differences_count":68100.0000,"supplier_delivery_qty":0,"sku_amount":575322.79,"sku_sale_amount":673183.78,"currency_amounts":0}],"ExceptionText":null,"GotoLogin":false,"ClientScript":null,"Message":null,"LocationUrl":null,"OpenUrl":null,"IsReloadPage":false,"IsReloadData":false,"IsResetData":false,"RequestId":"ac11000117593927926622973e8e01"}

```

http请求样例3：

```
import requests


headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.erp321.com",
    "priority": "u=1, i",
    "referer": "https://www.erp321.com/app/scm/purchase/purchasemode.aspx?_c=jst-epaas",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "purchase_item_height_21599824": "%7B%22foot%22%3A70%2C%22jspliter%22%3A347%7D",
    "_ati": "5108270968404",
    "j_d_3": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_ssi": "",
    "jump_env": "www",
    "isLogin": "true",
    "tmp_gray": "1",
    "jump_isgray": "0",
    "u_shop": "-1",
    "acw_tc": "ac11000117593918225423236e62d64503713247db54fb9fad8c9ea9ccb83a",
    "3AB9D23F7A4B3C9B": "2VYIWTSJBM47LJHDMGMNPZ7VHKA4MVVWELZFTXTUU4OWQDTYMAELVD24NTWEYJJ355QYZ3OO4OSERJUWUUUSDBGZZU",
    "u_name": "%e6%bd%98%e6%98%8e",
    "u_lid": "13502065765",
    "_gi": "-302",
    "u_json": "%7b%22t%22%3a%222025-10-2+16%3a01%3a35%22%2c%22co_type%22%3a%22%e6%a0%87%e5%87%86%e5%95%86%e5%ae%b6%22%2c%22proxy%22%3anull%2c%22ug_id%22%3a%22%22%2c%22dbc%22%3a%221753%22%2c%22tt%22%3a%2247%22%2c%22apps%22%3a%221.4.150.152%22%2c%22pwd_valid%22%3a%221%22%2c%22ssi%22%3anull%2c%22sign%22%3a%224509017.A8FEE8ED32B64E8C851E636C09BAA362%2c289a6bfbe7b8b0a6c7feeeed3e251b58%22%7d",
    "u_co_name": "%e4%b9%89%e4%b9%8c%e5%b8%82%e5%a1%94%e6%99%ba%e6%9c%89%e9%99%90%e5%85%ac%e5%8f%b8",
    "u_drp": "-1000000001",
    "v_d_144": "1759392037946_df374e8f90b4fcb4a0772f8c932820e9",
    "u_cid": "134038656957646664",
    "u_r": "12%2c13%2c14%2c15%2c16%2c17%2c18%2c22%2c23%2c27%2c28%2c29%2c30%2c31%2c32%2c33%2c34%2c35%2c36%2c39%2c40%2c41%2c52%2c53%2c54%2c61%2c62%2c63%2c64%2c65%2c66%2c67%2c70%2c71%2c72%2c73%2c76%2c90%2c101%2c102%2c103%2c104%2c105%2c106%2c107%2c108%2c109",
    "u_sso_token": "CS@7909e64a439d4324aefa70122389f960",
    "u_id": "21599824",
    "u_co_id": "12910783",
    "p_50": "603A0D4C11DC5E531A23597A80F4EC43638950176957655711%7c12910783",
    "u_env": "www",
    "u_lastLoginType": "vc",
    "tfstk": "g_Hrw3foxLprRe7XFqeF0x26MCe8EJ81zvaQxDm3Vz4lFT_ngViQRTV3ZjzEoqzo8DK8xy0n8yGWGdi-2JeH5JJ6C0L65oDSUJbIm8ECQlZ3Ydi-2imdLXKHCMl_A4Zu-2VloZq7ogfo-7mcnrELxaqhEno0krXuquqhmSqgY9bn-JxqmrE3Ky03Zno0kk23-bMEqDX4f7xVwszFyQngaPmuu9o-3uVPw04VK9Dqg7zGLrWhKxr-YMHNUORQSfU71P0DhTyEmku41b8NU2onXXVqLaxSSqcE-ohv86zZt0GthSshZmkUz5Dugg-8hJrn-Wlv7OZzFjPZUbKdo00_zf2-AG8S05l46oVcY_2S1cMLsYvPWrNTYqPsaFWrSgkRJoXOLvhP-6VuDoz60nrdPV-2QtwD16CLiRE453Z596FuDoz60n5d9S4Y0Pt7V"
}
url = "https://www.erp321.com/app/scm/purchase/purchasemode.aspx"
params = {
    "_c": "jst-epaas",
    "ts___": "1759392793126",
    "am___": "FillOtherData"
}
data = {
    "__VIEWSTATE": "/wEPDwUKLTM1NjA5NDk2NWRkcHUQ0Db7APYYmrgp3VbC6EbsdUk=",
    "__VIEWSTATEGENERATOR": "1FA1C91A",
    "owner_co_id": "12910783",
    "authorize_co_id": "12910783",
    "remarkOpt": "",
    "labelsOpt": "",
    "priceOptSource": "",
    "queryType": "",
    "poid_type": "po_id",
    "po_id": "",
    "dateRange_temp_id": "po_date",
    "po_date": [
        "",
        ""
    ],
    "status": "待审核,已确认",
    "delivery_status": "",
    "goods_status": "",
    "group": "",
    "supplier_name_id": "",
    "supplier_name": "",
    "filter_sku_id_temp_id": "包含商品",
    "sku_id": "",
    "remark_select": "-1",
    "remark": "",
    "purchaser_name_v": "",
    "purchaser_name": "",
    "lc_id_v": "",
    "lc_id": "",
    "l_id": "",
    "wms_co_id": "",
    "payment_method": "",
    "item_type": "",
    "wmslabels": "",
    "nowmslabels": "",
    "supplier_confirm": "",
    "is_1688_order": "",
    "confirm_name_v": "",
    "confirm_name": "",
    "contract_exist": "",
    "filter_lwh_id_binding_temp_id": "手动锁定",
    "lwh_id_binding": "",
    "manual_lwh_id_binding": "",
    "inpBubyer": [
        "东阳连裤袜厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A诸暨市黛丝韵针织厂D02",
        "A周正标袜厂Z03",
        "A-振鑫袜业Z01",
        "A-柚童针织Y07",
        "A（义乌）杨成林Y01",
        "义乌市友力鞋业有限公司",
        "A温州美梭针织有限公司（陈胜伟）M03",
        "A-（义乌）游冬冬Y05",
        "A-（江都）亿哈健身用品厂",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司",
        "A翊品服饰Y08",
        "A（义乌）杨成林Y01",
        "A翊品服饰Y08",
        "A-妙秀品针织M02",
        "A-诸暨市依欣露针织厂",
        "A诸暨市臻阳袜业有限公司(项钊）",
        "A周正标袜厂Z03",
        "A（河南）-亿首艺Y04",
        "A-骏腾体育用品",
        "张杨杨针织有限公司",
        "张杨杨针织有限公司"
    ],
    "_jt_page_count_enabled": "",
    "_jt_page_size": "500",
    "__CALLBACKID": "JTable1",
    "__CALLBACKPARAM": "{\"Method\":\"FillOtherData\",\"Args\":[\"[{\\\"po_id\\\":145193,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145192,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145191,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145190,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145189,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145188,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145187,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145185,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145174,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145159,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145158,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145128,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145127,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145126,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145108,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145107,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145088,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145086,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145081,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145076,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145068,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145046,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145045,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145032,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null},{\\\"po_id\\\":145031,\\\"member_id\\\":null,\\\"lock_lwh_id\\\":null,\\\"lock_priority_json\\\":null,\\\"l_id\\\":null}]\"],\"CallControl\":\"{page}\"}"
}
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)
```

http响应样例3：

```
0|{"IsSuccess":true,"ExceptionMessage":null,"ReturnValue":[{"po_id":145193,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145192,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145191,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145190,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145189,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145188,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145187,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145185,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145174,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145159,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145158,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145128,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145127,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145126,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145108,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145107,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145088,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145086,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145081,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145076,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145068,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145046,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145045,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145032,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false},{"po_id":145031,"member_id":null,"lock_lwh_id":null,"lock_priority_json":null,"l_id":null,"is_exist_payment":false}],"ExceptionText":null,"GotoLogin":false,"ClientScript":null,"Message":null,"LocationUrl":null,"OpenUrl":null,"IsReloadPage":false,"IsReloadData":false,"IsResetData":false,"RequestId":"ac11000117593927926632974e8e01"}

```



