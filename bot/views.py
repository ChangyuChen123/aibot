from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, ImageSendMessage
from bs4 import BeautifulSoup
import requests

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parse = WebhookParser(settings.LINE_CHANNEL_SECRET)


def get_weather(msg_county='台北市'):
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWB-A50AC47B-3657-4F08-91AD-567C72A4F450&locationName='
    res = requests.get(url)   # 取得 JSON 檔案的內容為文字
    data_json = res.json()    # 轉換成 JSON 格式
    locations = data_json['records']['location']

    datas = {}
    for location in locations:  # 取得所有資料
        for j in range(1):
            county = location['locationName'].replace("臺", "台")
            startTime = location['weatherElement'][0]['time'][j]['startTime']
            endTime = location['weatherElement'][0]['time'][j]['endTime']
            Wx = location['weatherElement'][0]['time'][j]['parameter']['parameterName']
            PoP = location['weatherElement'][1]['time'][j]['parameter']['parameterName']
            MinT = location['weatherElement'][2]['time'][j]['parameter']['parameterName']
            CI = location['weatherElement'][3]['time'][j]['parameter']['parameterName']
            MaxT = location['weatherElement'][4]['time'][j]['parameter']['parameterName']
            # print(county,startTime,endTime,Wx,PoP,MinT,CI,MaxT)
            datas[county] = [startTime, endTime, Wx, PoP, MinT, MaxT, CI]
    message = ''
    # columns=['startTime','endTime','天氣現象','降雨機率','最低溫','最高溫','舒適度']
    for data in datas:
        if msg_county == data:
            message += '【天氣小助手】\n'
            message += f'今天{data}的天氣:{datas[data][2]}\n'
            message += f'溫度:{datas[data][4]}°C - {datas[data][5]}°C\n'
            message += f'降雨機率:{datas[data][3]}%\n'
            message += f'舒適度:{datas[data][6]}\n'
            message += f'時間:{datas[data][0]} ~ {datas[data][1]}\n'
            if int(datas[data][3]) > 70:
                message += "**提醒您，今天很有可能會下雨，出門記得帶把傘哦!"
            elif int(datas[data][5]) > 33:
                message += "**提醒您，今天很熱，外出要小心中暑哦~"
            elif int(datas[data][4]) < 10:
                message += "**提醒您，今天很冷，記得穿暖一點再出門哦~"
    return message


def get_biglottery():
    try:
        url = 'https://www.taiwanlottery.com.tw/lotto/lotto649/history.aspx'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        trs = soup.find('table', class_="table_org td_hm").find_all('tr')
        data1 = [td.text.strip() for td in trs[0].find_all('td')]
        data2 = [td.text.strip() for td in trs[1].find_all('td')]
        numbers = [td.text.strip() for td in trs[4].find_all('td')[1:]]
        data = ''
        for i in range(len(data1)):
            # print(f'{data1[i]}:{data2[i]}')
            data += f'{data1[i]}:{data2[i]}\n'
        data += ','.join(numbers[:-1])+'特別號:'+numbers[-1]
        print(data)
        return data
    except Exception as e:
        print(e)
        return '取得大樂透號碼，請稍後再試...'


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parse.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        for event in events:
            if isinstance(event, MessageEvent):
                text = event.message.text
                message = None
                if text == "早安":
                    message = f"{text},你好!"
                elif text == "1":
                    message = "早安"
                elif '早安' in text:
                    message = '早安你好!'
                elif '樂透' in text:
                    message = get_biglottery()

                elif '天氣' in text:
                    countys = ['台東縣', '嘉義縣', '新北市', '屏東縣', '台中市', '花蓮縣', '苗栗縣', '金門縣', '新竹市', '台南市',
                               '彰化縣', '新竹縣', '宜蘭縣', '基隆市', '嘉義市', '桃園市', '台北市', '澎湖縣', '高雄市', '雲林縣', '連江縣', '南投縣']
                    for county in countys:
                        if county in text:
                            message = get_weather(county)

                elif '捷運' in text:
                    print(text)
                    mrts = {
                        '台北': 'https://www.travelking.com.tw/tourguide/mrt/images/map.png',
                        '台中': 'https://jrhouse.net/wp-content/uploads/2021/04/2016%E5%B9%B4%E5%BA%95%E9%80%9A%E8%BB%8A%E7%9A%84%E5%8F%B0%E4%B8%AD%E5%B1%B1%E7%B7%9A%E9%90%B5%E8%B7%AF%E9%AB%98%E6%9E%B6%E6%8D%B7%E9%81%8B%E5%8C%96.png',
                        '高雄': 'https://upload.wikimedia.org/wikipedia/commons/5/56/%E9%AB%98%E9%9B%84%E6%8D%B7%E9%81%8B%E8%B7%AF%E7%B6%B2%E5%9C%96_%282020%29.png'
                    }

                    image_url = 'https://www.travelking.com.tw/tourguide/mrt/images/map.png'
                    for mrt in mrts:
                        print(mrt)
                        if mrt in text:
                            image_url = mrts[mrt]
                            print(image_url)
                            break
                    #image_url = 'https://www.travelking.com.tw/tourguide/mrt/images/map.png'

                else:
                    message = '抱歉，我不知道你說什麼?'

                if message is None:
                    message_obj = ImageSendMessage(image_url, image_url)
                else:
                    message_obj = TextSendMessage(text=message)
                # if event.message.text=='hello':
                line_bot_api.reply_message(event.reply_token, message_obj)
                #TextSendMessage(text='hello world')
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def index(request):
    return HttpResponse("<h1>你好，我是AI機器人</h1>")

def get_biglottery():
    try:
        url = 'https://www.taiwanlottery.com.tw/lotto/lotto649/history.aspx'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        trs = soup.find('table', class_="table_org td_hm").find_all('tr')
        data1 = [td.text.strip() for td in trs[0].find_all('td')]
        data2 = [td.text.strip() for td in trs[1].find_all('td')]
        numbers = [td.text.strip() for td in trs[4].find_all('td')[1:]]
        data = ''
        for i in range(len(data1)):
            # print(f'{data1[i]}:{data2[i]}')
            data += f'{data1[i]}:{data2[i]}\n'
        data += ','.join(numbers[:-1])+'特別號:'+numbers[-1]
        print(data)
        return data
    except Exception as e:
        print(e)
        return '取得大樂透號碼，請稍後再試...'

def lottery(request):
    text = get_biglottery().replace('\n', '<br>')
    return HttpResponse(f'<h1>{text}</h1>')
        
    
