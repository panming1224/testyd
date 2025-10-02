http请求：

```python
import requests
import json


headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "anti-content": "0asAfqnygjSgygd9l4e8dO8QdVo7KTwTvty8uJNxxKHBN6_-5entRFsa5DefOoHeOuHjtT64EGCfpd7wEzPxenZg0xbZhwTfzjuG2rgvZltO0kjlTKACIbdIbGXa0mNJMHYDaVBZ4YyI62IcQB0TEy5p88rKGYnSBza4MbBkR2QzbodaAoH0I69z89poXicUYDbVnyZ6W9FR3dHWBWTzJk0vXsoIgv1b4i8Zup2XoAXzl9ZOyZkb6lcTOICgomDuN9JJ2bcrY0SQDAf1R9MYHtjWwcbocNqOH4QbfyzCYD2fI52omGOvIWcnAL9rq4hoXHCZjo2v79nIPBIJ41cCi8fDNQgwrc6cJHXSCRlqhrpL7YAXghxotke0UQffZhIH2yf7AOBRVfKtmRDHKwGKXiS3-xljbPT5KOtdH3tvi4fIWITTlFCxpeN82NTwGhpLw_uCFnycWKgMqWCNo-iQFgXR4lFCAFlRXE21kCdG3B46ODMsvzvAPi0SQEEJtKWnAMEs2dsVi2QPA2jiil4jijG2aj0FzQqYtZ_3YycMNQFKWDwbkMaRendvpPqQ_mMXMSo0k7VkpPoc1s2uisfkvDtt7iG_oeKTqc1TMfgsvPsjEZXeQzbfLLr3yTY3f-X7VZWB9oQ2nxt3lehejDSoJiljvntFMibtt_mjplxckVoWg5PpE_ZPvlm6yasCbRoom0J6VJIcDZlQc9o2Qy2LroIENZTqEHh",
    "cache-control": "max-age=0",
    "content-type": "application/json",
    "etag": "ZMKsB5nx9K69OmMPxs7ZoA1Rh5zy791X",
    "origin": "https://mms.pinduoduo.com",
    "priority": "u=1, i",
    "referer": "https://mms.pinduoduo.com/mms-chat/search?msfrom=mms_sidenav",
    "sec-ch-ua": "\"Not=A?Brand\";v=\"24\", \"Chromium\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}
cookies = {
    "api_uid": "CiDokWjR7OB0rQCRCs1zAg==",
    "_nano_fp": "Xpmyl0dJl0gxlpPJno_5_o4j1sC5SRUOQNMb94iP",
    "rckk": "ZMKsB5nx9K69OmMPxs7ZoA1Rh5zy791X",
    "_bee": "ZMKsB5nx9K69OmMPxs7ZoA1Rh5zy791X",
    "ru1k": "35a113e9-a0c9-4a9c-867b-bd9fd3a13cc1",
    "_f77": "35a113e9-a0c9-4a9c-867b-bd9fd3a13cc1",
    "ru2k": "1683ea6d-5eb0-4485-9ab3-13fff853b6d8",
    "_a42": "1683ea6d-5eb0-4485-9ab3-13fff853b6d8",
    "PASS_ID": "1-IJpazeqwLDdGAe7CJhk5erhTM5sa223hL9f4THT00dctCkt3j+1hQbtj2gTQ3Hg6aIAa9H/t7RniQ0Id0JdW5g_360624906_172053760",
    "windows_app_shop_token_23": "eyJ0IjoiR1dra1NHNTBiNHJuYnlhRGxmK2lYMjliZmh3OEkxVWJ6RFh2bm1Zd1NpMUg3bmZBcUhRc3JmV2pCRHdDNU1tcyIsInYiOjEsInMiOjIzLCJtIjozNjA2MjQ5MDYsInUiOjE3MjA1Mzc2MH0",
    "x-visit-time": "1759378608635",
    "JSESSIONID": "627EB3A27CD8C6A6E341C6F4B75F0E0A",
    "mms_b84d1838": "3616,3523,3660,3614,3678,3599,3601,3603,3658,3605,3621,3622,3669,3588,3254,3531,3559,3474,3475,3477,3479,3497,3482,1202,1203,1204,1205,3417"
}
url = "https://mms.pinduoduo.com/latitude/search/message/getMessagesUsers"
data = {
    "pageNum": 1,
    "pageSize": 25,
    "startTime": 1758816000,
    "endTime": 1759420799,
    "keywords": ""
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, cookies=cookies, data=data)

print(response.text)
print(response)
```

