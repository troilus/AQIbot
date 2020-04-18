#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import telebot
import requests
import json
import time
import re
import os
from xpinyin import Pinyin
import threading

with open('./config.json', 'r+') as config_file:
    config = json.load(config_file)
    bot_token = config['bot_token']
    aqi_token = config['aqi_token']
    channel_id = int(config['channel_id'])
    admin_list = config['admin_list']
    print('Config file load successfully:\n' + str(config))
    print(admin_list)

bot = telebot.TeleBot(bot_token)

try:
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, '欢迎使用AQI_Bot。\n请输入 /help 获得更多帮助。')

    @bot.message_handler(commands=['help'])
    def help(message):
        bot.reply_to(
            message, '这是一个可以告诉你空气质量的bot。\n请输入 /aqi <location> 来获取空气质量信息。')

    def checkAPI(location):
        aqi_url = 'https://api.waqi.info/feed/' + location + '/?token=' + aqi_token
        aqi_information = requests.get(aqi_url)
        aqi_text = aqi_information.json()
        print('acquired aqi_json_content:', aqi_text)
        return aqi_text

    def formatPol(pollution):
        if pollution == 'pm25':
            return 'PM2.5'
        elif pollution == 'pm10':
            return 'PM10'
        elif pollution == 'co':
            return '一氧化碳'
        elif pollution == 'no2':
            return '二氧化氮'
        elif pollution == 'o3':
            return '臭氧'
        elif pollution == 'so2':
            return '二氧化硫'
        elif pollution == 'p':
            return '大气压强'
        elif pollution == 'w':
            return '风速'
        elif pollution == 'wd':
            return '风向'
        elif pollution == 't':
            return '气温'
        elif pollution == 'h':
            return '湿度'
        else:
            return pollution

    def formatData(aqi_text):
        if aqi_text['status'] == 'ok':
            msg = '{city}的AQI：'.format(city=str(aqi_text['data']['city']['name']))

            aqi_temp = aqi_text['data']['aqi']

            if isinstance(aqi_temp, int):
                msg += str(aqi_temp) + ' '
                if 0 <= aqi_temp <= 50:
                    msg += '优 ⭕️⭕️\n'
                elif 51 <= aqi_temp <= 100:
                    msg += '良 ⭕️\n'
                elif 101 <= aqi_temp <= 150:
                    msg += '轻度污染 ❗️\n'
                elif 151 <= aqi_temp <= 200:
                    msg += '中度污染 ❗️❗️\n'
                elif 201 <= aqi_temp <= 300:
                    msg += '重度污染 ❗️❗️❗️\n'
                elif 301 <= aqi_temp:
                    msg += '严重污染 ❗️❗️❗️❗️\n'
                elif aqi_temp == 824:
                    msg += '\n\n数据源疑似发生错误，小熊表示无能为力\n\n'
            else:
                msg += '未获取到数据\n'

            aqi_temp = aqi_text['data']['dominentpol']
            if aqi_temp == "" or not(isinstance(aqi_temp, str)):
                msg += '主要污染物：未获取到数据\n'
            else:
                msg += '主要污染物：{dominentpol}\n'.format(dominentpol=str(formatPol(aqi_temp)))

            for i in aqi_text['data']['iaqi']:
                aqi_temp = aqi_text['data']['iaqi'][i]['v']
                if not(aqi_temp, int):
                    msg += '{pol}：未获取到数据\n'.format(pol=str(formatPol(str(i))))
                else:
                    msg += '{pol}：\t{data}\n'.format(pol=str(formatPol(str(i))), data=str(aqi_temp))

            aqi_temp = aqi_text['data']['time']['s']
            if aqi_temp == "" or not(isinstance(aqi_temp, str)):
                msg += '数据更新时间：未获取到数据\n'
            else:
                msg += '数据更新时间：{update_time}\n'.format(update_time=str(aqi_temp))

            return msg
        else:
            if str(aqi_text['data']) == 'Unknown station':
                return '未获取到该城市的空气质量信息。'
            elif str(aqi_text['data']) == 'Invalid key':
                return 'API_KEY错误，请联系开发者 @LittleBear0729 解决问题。'
            else:
                return '{error}\n请联系开发者解决问题，或者使用 /help 获取帮助。'.format(error=str(aqi_text['data']))

    @bot.message_handler(commands=['aqi'])
    def aqi(message):
        location = message.text.split()
        if len(location) == 1:
            bot.reply_to(message, "你想知道哪个城市的空气质量？请使用 /help 获取帮助。")
        else:
            p = Pinyin()
            location[1] = p.get_pinyin(location[1], "").lower()
            print('-----User requests-----')
            print('acquire location:', location[1])
            pattern = re.compile('^[a-z]+$')
            if pattern.search(location[1]) == None:
                bot.reply_to(message, '输入不合法，请检查输入内容。')
            else:
                bot.reply_to(message, formatData(checkAPI(location[1])))

    def channel_broadcast(bot, channel_id):
        last_data = checkAPI('beijing')
        time.sleep(60)
        while 1:
            print('-----1min auto check-----')
            curr_data = checkAPI('beijing')
            if curr_data['status'] == 'ok':
                if last_data['data']['time']['v'] < curr_data['data']['time']['v']:
                    print('-----auto push-----')
                    bot.send_message(channel_id, formatData(curr_data))
                    last_data = curr_data
            else:
                bot.send_message(
                    channel_id, 'API_KEY错误，请联系开发者 @LittleBear0729 解决问题。')
            time.sleep(60)
        print('*-*-*-*Thread Exited*-*-*-*')
    broadcast = threading.Thread(
        target=channel_broadcast, args=(bot, channel_id))
    broadcast.start()

    @bot.message_handler(commands=['restart'])
    def restart_bot(message):
        if str(message.from_user.id) in admin_list:
            print('-----received restart signal-----')
            bot.reply_to(message, 'Bot is now restarting...')
            os.system('systemctl restart china-aqi-bot.service')
        else:
            bot.reply_to(message, 'No permission!')

    bot.polling(none_stop=True)
except KeyboardInterrupt:
    quit()
except Exception as e:
    print(str(e))
