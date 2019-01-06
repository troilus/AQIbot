# -*- coding:utf-8 -*-

import telebot
import requests
import json
import time

with open('./config.json', 'r+') as config_file:
    config = json.load(config_file)
    print('Config file load successfully:\n' + str(config))
    bot_token = config['bot_token']
    aqi_token = config['aqi_token']

bot = telebot.TeleBot(bot_token)

"""
location = input()
url = 'https://api.waqi.info/feed/' + location + '/?token=' + aqi_token
aqi = requests.get(url)

text = aqi.json()

print(text)
"""

try:
    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, '欢迎使用AQI_Bot。\n请输入 /help 获得更多帮助。')

    @bot.message_handler(commands=['help'])
    def help(message):
        bot.reply_to(message, '这是一个可以告诉你空气质量的bot。\n请输入 /aqi <location> 来获取空气质量信息。')

    @bot.message_handler(commands=['aqi'])
    def aqi(message):
        location = message.text.split()
        print('acquire location:', location[1])
        aqi_url = 'https://api.waqi.info/feed/' + location[1] + '/?token=' + aqi_token
        aqi_information = requests.get(aqi_url)
        aqi_text = aqi_information.json()
        print('acquire aqi_json_content:', aqi_text)
        if aqi_text['status']=='ok':
        	msg = str(aqi_text['data']['city']['name']) + '\n'
        	msg += 'AQI: ' + str(aqi_text['data']['aqi']) + '\n'
        	for i in aqi_text['data']['iaqi']:
        		msg += str(i) + ': ' + str(aqi_text['data']['iaqi'][i]['v']) + '\n'
        	msg += 'Time: ' + str(aqi_text['data']['time']['s'])
        	bot.reply_to(message, msg)
        else:
        	bot.reply_to(message, str(aqi_text['data']))
    
    while True:
    	if int(time.time())%5 == 0:
    		print("5!")
    
    bot.polling(none_stop=True)
except KeyboardInterrupt:
    quit()
except Exception as e:
    print(str(e))