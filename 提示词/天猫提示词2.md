```
1.网址:https://myseller.taobao.com/home.htm/app-customer-service/toolpage/Message
2.参照D:\testyd\tm\tm_chat.py的登录方式以及签名计算方式，打开这个页面，获取cooike。
3.根据算法帮我写好这个http请求，获取响应。其中t以及sign需要你去根据算法来计算，参照就可以，data需要你去解析。给我返回完整的响应。需要先获取客户列表，再获取聊天信息。你给我返回完整的响应。写好保存为D:\testyd\tm\tm_chat_2.py
3.1获取顾客列表
get请求
url:https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.paas.conversation.list/1.0/?jsv=2.6.2&appKey=12574478&t=1759134274063&sign=a9f2a4054d61fa30950d45c61a06a54a&api=mtop.taobao.wireless.amp2.paas.conversation.list&v=1.0&type=jsonp&dataType=jsonp&callback=mtopjsonp3&data=%7B%22selfWwNick%22%3Anull%2C%22targetWwNick%22%3Anull%2C%22beginDate%22%3A%2220250911%22%2C%22endDate%22%3A%2220250914%22%7Djsv=2.6.1&appKey=12574478&t=1759131696979&sign=a4e5176884e4821b26c298387ba7717c&api=mtop.rm.sellercenter.list.data.pc&type=originaljson&dataType=json

head:accept:*/*
accept-language:zh-CN,zh;q=0.9
Cookie:cookie(动态获取)
referer:https://market.m.taobao.com/
sec-ch-ua:"Not=A?Brand";v="24", "Chromium";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:script
sec-fetch-mode:no-cors
sec-fetch-site:same-site
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36


3.2 获取聊天信息
get请求
url:https://h5api.m.taobao.com/h5/mtop.taobao.wireless.amp2.im.paas.message.list/1.0/?jsv=2.6.2&appKey=12574478&t=1759134274198&sign=b47dd2d7f5d3d9ab5bdfe0cdf08dcf40&api=mtop.taobao.wireless.amp2.im.paas.message.list&v=1.0&type=jsonp&dataType=jsonp&callback=mtopjsonp4&data=%7B%22userNick%22%3A%22cntaobao%E5%9B%9E%E5%8A%9B%E6%A3%89%E5%A8%85%E4%B8%93%E5%8D%96%E5%BA%97%3A%E5%8F%AF%E4%BA%91%22%2C%22cid%22%3A%22797480932.1-2219315280500.1%2311001%22%2C%22userId%22%3A%222219368700744%22%2C%22cursor%22%3A1757520000000%2C%22forward%22%3Atrue%2C%22count%22%3A100%2C%22needRecalledContent%22%3Atrue%7D

head:accept:*/*
accept-language:zh-CN,zh;q=0.9
Cookie:t=1faf25484c52fa7559c3619f6a0cfd40; xlly_s=1; mtop_partitioned_detect=1; _m_h5_tk=07f9b408252d87f99f54c58138640e28_1759139452363; _m_h5_tk_enc=34122950e5fd6516e880a778beede91c; _tb_token_=l3Bjxu4ddtGDhUY5JYUd; _samesite_flag_=true; 3PcFlag=1759134171529; cookie2=146e6c6e4a6dbdb321167c05f262b97a; sgcookie=E100KsBdYAAo4RNAnbI1zoDykDh1tNsFl7VfdZG4tT955UwnPlZICN6xqr0s1sYor1ovqOnxwpHWGw0EW2M6M%2B2TmaOg85rHEkg1s3SvYDELRwIaZUgImGEUPvWy%2FKlb3nSW; unb=2220505165374; sn=%E5%9B%9E%E5%8A%9B%E6%A3%89%E5%A8%85%E4%B8%93%E5%8D%96%E5%BA%97%3A%E5%8F%AF%E4%BA%91; uc1=cookie21=Vq8l%2BKCLiYYu&cookie14=UoYbwhA72U7VWg%3D%3D; csg=dde531a2; _cc_=UIHiLt3xSw%3D%3D; cancelledSubSites=empty; skt=4027ff2e9d190e15; tfstk=gvkEPHfnqppelmb6dVePbtPa_UeLU88XrYa7q0muAy4nABFkzqi0ZWiuP8urz4zQZeeIUVuSqza3O0gwUVaZPDaQP4PoAPWIOBF7zgzi87MWvTGN4m3aFvDr2Troq4KLPHdsvDe8EETjzKiKvk7XNEDFEdViXuzlrCNnbNcb0ETXhdOhj88el41vZ5Ug0o2ux7VuShr7VaXnrWvMbuq5-_XnrcxaWu7ltWV3SNq4xw2uE4mMbuUgx8Vnrcxa2P4oZUnnqOrbth7Mjb5C_HFgoD4NEtSYYWYKb_6V3ArUTYmg7lZsQkPUl7jAvjkn50DIp5dG_8nsg4looF1Q-jrq7SGeu9uqJumzq2JA0PDE4APK1i6qb7zEsvVNqTmmvXNia28F9ycI7SEgsgJYfqaivvcw2Nmnlyy3j59D0cVo1vFxdFXUnjnQdb0D56angujrfaEgA4M-TafutlEalh-a2wg2benR8D5Rw52YbrtQA_C8tlEalh-Nw_FgWlzXAk1..
referer:https://market.m.taobao.com/
sec-ch-ua:"Not=A?Brand";v="24", "Chromium";v="140"
sec-ch-ua-mobile:?0
sec-ch-ua-platform:"Windows"
sec-fetch-dest:script
sec-fetch-mode:no-cors
sec-fetch-site:same-site
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36


```

