```
1.为我实现两个功能，可以参考D:\testyd\jd_store.py的实现方式，获取cookie直接使用固定的cookie，https://sycm.taobao.com/qos/service/core_monitor/new#/monitor使用D:\testyd\tm\get_cookies_simple.py在这个网址获取cookie，存储到sycm_cookie.txt,文件放到D:\testyd\tm，命名为tm_kpi

2.功能一:获取自制报表数据：
(1)发送获取数据请求：get(获取的data在作为id在2.（2）2.（3）使用)"data":12402688
url：
https://sycm.taobao.com/csp/api/user/customize/async-excel?startDate=20250926(需要动态传入t-4)&endDate=20250926(需要动态传入t-4)&dateType=day&dateRange=cz&reportTemplateId=8257&bizCode=selfMadeReport
head：
accept:application/json, text/plain, */*
accept-language:zh-CN,zh;q=0.9
bx-v:2.5.31
Cookie:cookie（使用保存的）
priority:u=1, i
referer:https://sycm.taobao.com/qos/service/self_made_report
sec-ch-ua:"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-origin
user-agent:

(2)循环发送获取下载状态请求直到message变成下载完成：
url：https://sycm.taobao.com/csp/api/file/task-list.json?pageNo=1&pageSize=10&bizCode=selfMadeReport
head：accept:application/json, text/plain, */*
accept-language:zh-CN,zh;q=0.9
bx-v:2.5.31
Cookie:cookie（使用保存的）
priority:u=1, i
referer:https://sycm.taobao.com/qos/service/self_made_report
sec-ch-ua:"Not=A?Brand";v="24", "Chromium";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-origin
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36


(3)发送获取下载连接请求：get 
url：https://sycm.taobao.com/csp/api/file/url?id=12394144（2.(1)获取的）
head：accept:application/json, text/plain, */*
accept-language:zh-CN,zh;q=0.9
bx-v:2.5.31
Cookie:cookie（使用保存的）
priority:u=1, i
referer:https://sycm.taobao.com/qos/service/self_made_report
sec-ch-ua:"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-origin
user-agent:
(4)参照D:\testyd\jd_store.py实现静默下载，保存到对应日期文件夹D:\yingdao\tm\天猫客服绩效自制报表。
3.功能二:获取售后解决分析数据：
（1）发送获取数据请求：get
url：https://sycm.taobao.com/csp/api/aftsale/cst/list.json?dateRange=cz&endDate=20250925（需要动态传入t-4）&excludeDates=&orderBy=aftSaleRplyUv&pageSize=10&wwGroup=&accountId=&qnGroupId=&dateType=day&page=1&startDate=20250925（需要动态传入t-4）&order=desc
hader：
accept:*/*
accept-language:zh-CN,zh;q=0.9
bx-v:2.5.31
Cookie:cookie（使用保存的）
priority:u=1, i
referer:https://sycm.taobao.com/qos/service/frame/customer/performance/new
sec-ch-ua:"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-origin
sycm-referer:/qos/service/frame/customer/performance/new
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36

（2）把响应解析好保存到保存到对应日期文件夹D:\yingdao\tm\天猫客服绩效解决分析报表，以excel的格式保存。

仔细阅读这两个文件，每天在这里调用任务生成模块，生成当日任务，时间时t-4，任务列分别为kpi_self_status,和kpi_offical_status，然后根据对应的任务，读取mysql中tm_shop表中的sycmcookie和reportTemplateId，reportTemplateId要动态传入reportTemplateId=7798这个id，cookie就是动态传入cookie，不再从txt读取cookie，下载下来的表格以店铺名称命名，合并后传入D:\yingdao\tm\合并文件\天猫客服绩效自制报表，D:\yingdao\tm\合并文件\天猫客服绩效解决分析报表这个请参照的写法，最后将表格传入minio并刷新dremio，minio的路径为warehouse/ods/tm/tm_self_kpi和warehouse/ods/tm/tm_offical_kpi,dremio路径为minio.warehouse.ods.tm."tm_self_kpi"minio.warehouse.ods.tm."tm_offical_kpi"
```

