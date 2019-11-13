#!/usr/bin/env python
# -*- coding: utf-8 -*-

from slack import WebClient
import os

PIZZA_CHANNEL = "CQ249BV7C"

slack_token = os.environ["SLACK_API_TOKEN"]
sc = WebClient(slack_token)

def get_slack_users():
    return sc.api_call("conversations.members",params={"channel":PIZZA_CHANNEL}) 

def get_real_users(channel_members):
    all_users = sc.api_call("users.list")['members']
    members = set(channel_members['members'])
 
    return [u for u in all_users if u['id'] in members and not u['deleted'] and not u['is_bot'] and not u['is_restricted'] and not u['name'] == "slackbot"] # type : list

def send_private_message(user_id, text, attachments=None):
    print("slackutil:send_private_message to", user_id, text)
    try:
        resp = sc.im_open(user=user_id, text=text, attachments=attachments)
        channel_id = resp["channel"]["id"]
        send_channel_message(channel_id, text, attachments)
    except Exception as e:
        print("In send_private_message")
        print(e)

def send_channel_message(channel_id, text, attachments=None):
    print("slackutil:send_channel_message")
    sc.chat_postMessage(channel=channel_id, text=text, username="Meet and eat", icon_url="https://findicons.com/icon/download/37734/pizza_slice/128/png", blocks=attachments)
