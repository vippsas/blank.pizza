#!/usr/bin/env python
# -*- coding: utf-8 -*-

import api
import os
import requests
import base64

import slackutil
from slack import RTMClient
from time import sleep

pizza_channel_id = 'CQ249BV7C'

slack_token = os.environ["SLACK_API_TOKEN"]
rtmclient = RTMClient(token=slack_token)



def is_dm(message):
    return message['channel'][0] == 'D'


@RTMClient.run_on(event='message')
def respond(**payload):
    try:
        print("responding")
        print("payload is", payload)
        message = payload["data"]
        if(message['channel'] == pizza_channel_id):
            if 'files' in message:
                web_client = payload["web_client"]
                user = message["user"]
                web_client.chat_postMessage(channel=message["channel"], text=f"Hi <@{user}>! Sorry I can't handle images yet :(")

                return
                """
 |  def say_hello(**payload):  |      data = payload['data']  |      web_client = payload['web_client']  |      if 'Hello' in data['text']:  |          channel_id = data['channel']  |          thread_ts = data['ts']  |          user = data['user']  |  |          web_client.chat_postMessage(  |              channel=channel_id,  |              text=f"Hi <@{user}>!",  |              thread_ts=thread_ts  |          )

                api.send_slack_message(
                    message['channel'], u'Takk for fil! 🤙')
                headers = {u'Authorization': u'Bearer %s' % slack_token}
                for file in message['files']:
                    r = requests.get(
                        file['url_private'], headers=headers)
                    b64 = base64.b64encode(r.content).decode('utf-8')
                    payload = {'file': 'data:image;base64,%s' % b64,
                               'upload_preset': 'blank.pizza'}
                    r2 = requests.post(
                        'https://api.cloudinary.com/v1_1/blank/image/upload', data=payload)
                    api.save_image(
                        r2.json()['public_id'], file['user'], file['title'])
                """
        elif(is_dm(message) and 'user' in message):
            web_client = payload["web_client"]
            web_client.chat_postMessage(channel=message["channel"], text="Thanks for your message", username="Meet and eat", icon_url="https://findicons.com/icon/download/37734/pizza_slice/128/png")
            if message['user'] in api.get_invited_users():
                if message['text'].lower() == 'ja':
                    api.rsvp(message['user'], 'attending')
                    slackutil.send_slack_message(
                        message['channel'], u'Sweet! 🤙')
                    api.finalize_event_if_complete()
                elif message['text'].lower() == 'nei':
                    api.rsvp(message['user'], 'not attending')
                    web_client.chat_postMessage(channel=message["channel"], text=f'Ok 😏', username="Meet and eat", icon_url="https://findicons.com/icon/download/37734/pizza_slice/128/png")

                    api.invite_if_needed()
                else:
                    api.send_slack_message(
                        message['channel'], u'Hehe jeg er litt dum, jeg. Skjønner jeg ikke helt hva du mener 😳. Kan du være med? (ja/nei)')
    except Exception as e:
        print("exception", e)

print("starting rtmclient listener")
rtmclient.start()
