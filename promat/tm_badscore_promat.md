
```
1.仔细阅读这个D:\testyd\tm\tm_kpi.py已经完成的文件，仔细理解其中的逻辑。为我修改D:\testyd\tm\tm_badscore.py这个文件。
2.增加在数据库中读取qncookie，替换这个文件中的cookie,删掉现有的cookie获取逻辑。
3.日期改为t-1，执行文件的时候要先生成任务。任务列为badscore_status.
4.生成的excel保存到D:\yingdao\tm\天猫差评表\日期\店铺名称.xlsx。合并后的文件保存到D:\yingdao\tm\合并文件\天猫差评表\日期.xlsx。
5.下载结束后更新任务状态。
5.合并后上传到minio的ods/tm/tm_badscore目录下，文件名格式为dt=日期/日期.parquet。
6.上传后刷新dremio，minio.warehouse.ods.tm.tm_badscore
6.无论是否有下载文件都要执行合并上传刷新动作，

```
```
{
    "userInfo": {
        "userStar": "https://img.alicdn.com/imgextra/i4/O1CN019QZnaG1U1LtUAPn6e_!!6000000002457-2-tps-92-45.png",
        "isReceiver": false,
        "userName": "w**",
        "isForeigner": false,
        "securityuid": "RAzN8BQjir2o7GMWedHbjirBUgdSV"
    },
    "emotionType": {
        "appendRateStatus": "11",
        "status": "11"
    },
    "orderInfo": {
        "userStar": "//img.alicdn.com/newrank/b_blue_3.gif",
        "userName": "w**",
        "mainOrderId": "2951203765016139860",
        "orderId": "2951203765016139860"
    },
    "itemInfo": {
        "link": "//item.taobao.com/item.htm?id=979536801722",
        "itemId": 979536801722,
        "title": "回力抗寒袜子男士冬季加厚中筒袜毛圈袜子加绒防臭抗寒保暖长筒袜",
        "orderId": "2951203765016139860"
    },
    "rateContent": {
        "appendRate": {
            "mediaList": [
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i1/O1CN01mz02Du1uuwInSrIEj_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i1/O1CN01djMbv81uuwInJQLDp_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i3/O1CN01SCUDWl1uuwIm6mkDP_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i4/O1CN01SPOU2U1uuwImXhytp_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i1/O1CN01kdl86M1uuwIoEySE5_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                }
            ],
            "expression": [
                {
                    "content": "不臭脚",
                    "emotion": "11"
                }
            ],
            "feedId": "1284707665461",
            "days": 1,
            "language": "zh_CN",
            "contentTitle": null,
            "content": "袜子穿着舒服而且不臭脚 保暖效果也好 冬天保暖必备啊 价格也挺实惠的"
        },
        "mainRate": {
            "date": 1758897954001,
            "mediaList": [
                {
                    "uiType": "video",
                    "thumbnail": "//img.alicdn.com/imgextra/i2/O1CN01cbDOTC1uuwIoAwYqn_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": "//cloud.video.taobao.com/play/u/null/p/1/d/hd/e/6/t/1/535639949249.mp4"
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i2/O1CN01IGbHsu1uuwInBtQoi_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i3/O1CN01eZdVmj1uuwInXwZZM_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i2/O1CN014csShI1uuwInG7jWR_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i4/O1CN01o9W0LN1uuwImGMYcW_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                },
                {
                    "uiType": "image",
                    "thumbnail": "//img.alicdn.com/i3/O1CN01ZJwoYA1uuwInbKtPp_!!4611686018427383458-0-rate.jpg",
                    "flashUrl": null,
                    "mp4Url": null
                }
            ],
            "expression": [
                {
                    "content": "很厚实",
                    "emotion": "11"
                },
                {
                    "content": "穿着很舒服",
                    "emotion": "11"
                },
                {
                    "content": "价格实惠",
                    "emotion": "11"
                }
            ],
            "feedId": "1284767962779",
            "language": "zh_CN",
            "contentTitle": null,
            "content": "袜子做工蛮不错的 挺厚实的 穿着还挺舒服的 冬天穿这个再也不怕脚冷了 这个价格也挺实惠的"
        }
    },
    "operator": {
        "dataSource": [
            {
                "method": "POST",
                "asyncUrl": "//rate.taobao.com/rateReply.htm",
                "operateType": "reply",
                "params": {
                    "feedbackID": "1284767962779",
                    "explainItemId": 979536801722
                },
                "canAddRecommendItem": false,
                "content": "追评回复",
                "rateType": 3,
                "feedId": 1284767962779,
                "complaintSource": "5",
                "uiType": "reply",
                "addRecommendItemRemainCount": 0,
                "valueRequired": true,
                "beforeTips": "还有27天可回复"
            },
            {
                "rateType": 0,
                "method": "GET",
                "feedId": "1284767962779",
                "asyncUrl": "",
                "complaintSource": "5",
                "uiType": "complaintCro",
                "params": {},
                "content": "投诉评价"
            },
            {
                "rateType": 3,
                "method": "GET",
                "feedId": "1284767962779",
                "asyncUrl": "",
                "complaintSource": "5",
                "uiType": "complaintCro",
                "params": {},
                "content": "投诉追评"
            }
        ]
    }
}
```

