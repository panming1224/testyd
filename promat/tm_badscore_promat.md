```
1.网址:https://myseller.taobao.com/home.htm/comment-manage/list
2.参照D:\testyd\pdd_chat.py的登录方式，打开这个页面，获取cooike。
3.根据算法帮我写好这个http请求，获取响应。其中t以及sign需要你去根据算法来计算
post请求
url:https://h5api.m.taobao.com/h5/mtop.rm.sellercenter.list.data.pc/1.0/?jsv=2.6.1&appKey=12574478&t=1759131696979&sign=a4e5176884e4821b26c298387ba7717c&api=mtop.rm.sellercenter.list.data.pc&type=originaljson&dataType=json

head:accept:application/json
accept-language:zh-CN,zh;q=0.9
Content-Type:application/x-www-form-urlencoded
Cookie:cooike(动态获取)
origin:https://myseller.taobao.com
priority:u=1, i
referer:https://myseller.taobao.com/home.htm/comment-manage/list/rateWait4PC?current=1&pageSize=20&dateRange=20250926%2C20251027
sec-ch-ua:"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:empty
sec-fetch-mode:cors
sec-fetch-site:same-site
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36

data={"jsonBody":"{\"pageType\":\"rateWait4PC\",\"pagination\":{\"current\":1,\"pageSize\":20},\"dateRange\":[\"20250926\",\"20251027\"]}"}


```

