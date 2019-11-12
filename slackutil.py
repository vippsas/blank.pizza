#!/usr/bin/env python
# -*- coding: utf-8 -*-

from slack import WebClient
import os

slack_token = os.environ["SLACK_API_TOKEN"]
sc = WebClient(slack_token)

def get_slack_users():
    return sc.api_call("conversations.members",params={"channel":"CQ249BV7C"}) 

def get_real_users(channel_members):
    all_users = sc.api_call("users.list")['members']
    members = set(channel_members['members'])
 
    return [u for u in all_users if u['id'] in members and not u['deleted'] and not u['is_bot'] and not u['is_restricted'] and not u['name'] == "slackbot"] # type : list

def send_slack_message(channel_id, text, attachments=None):
    sc.api_call(
        "chat.postMessage",
        channel=channel_id,
        as_user=True,
        text=text,
        attachments=attachments)
