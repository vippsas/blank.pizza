#!/usr/bin/env python
# -*- coding: utf-8 -*-

import slackutil
import db
import locale
import pytz
from datetime import datetime, timedelta

#locale.setlocale(locale.LC_ALL, "nb_NO.utf8")

PEOPLE_PER_EVENT = 5
REPLY_DEADLINE_IN_HOURS = 24
DAYS_IN_ADVANCE_TO_INVITE = 10
HOURS_BETWEEN_REMINDERS = 4

BUTTONS_ATTACHMENT = [
    {
        "fallback": "Det funket ikke å svare :/",
        "callback_id": "rsvp",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "actions": [
            {
                "name": "option",
                "text": "Hells yesss!!! 🍕🍕🍕",
                "type": "button",
                "value": "attending"
            },
            {
                "name": "option",
                "text": "Nah ☹️",
                "type": "button",
                "value": "not attending"
            }]
    }]


def invite_if_needed():
    event = db.get_event_in_need_of_invitations(
        DAYS_IN_ADVANCE_TO_INVITE, PEOPLE_PER_EVENT)
    if event is None:
        print("No users were invited")
        return

    event_id, timestamp, place, number_of_already_invited = event
    number_of_employees = sync_db_with_slack_and_return_count()
    number_to_invite = PEOPLE_PER_EVENT - number_of_already_invited
    users_to_invite = db.get_users_to_invite(number_to_invite, event_id, number_of_employees, PEOPLE_PER_EVENT)

    if len(users_to_invite) == 0:
        print("Event in need of users, but noone to invite") # TODO: needs to be handled
        return

    db.save_invitations(users_to_invite, event_id)

    for user_id in users_to_invite:
        slackutil.send_slack_message(user_id, "Du er invitert til 🍕 på %s, %s. Pls svar innen %d timer 🙏. Kan du?" %
                                 (place, timestamp.strftime("%A %d. %B kl %H:%M"), REPLY_DEADLINE_IN_HOURS), BUTTONS_ATTACHMENT)
        print("%s was invited to event on %s" % (user_id, timestamp))

def send_reminders():
    inviations = db.get_unanswered_invitations()

    for invitation in inviations:
        slack_id, invited_at, reminded_at = invitation
        actual_dude = slack_id
        slack_id = "UNBJ9NVK4" # todo fix, always andreas
        remind_timestamp = datetime.now() + timedelta(hours=-HOURS_BETWEEN_REMINDERS)
        if(reminded_at < remind_timestamp):
            slackutil.send_slack_message(slack_id, "Hei du <@%s>! Jeg hørte ikke noe mer? Er du gira? (ja/nei)" % actual_dude)
            db.update_reminded_at(slack_id)
            print("%s was reminded about an event." % slack_id)

def finalize_event_if_complete():
    event = db.get_event_ready_to_finalize(PEOPLE_PER_EVENT)
    if event is None:
        print("No events ready to finalize")
    else:
        event_id, timestamp, place = event
        sync_db_with_slack_and_return_count()
        slack_ids = ['<@%s>' % user for user in db.get_attending_users(event_id)]
        db.mark_event_as_finalized(event_id)
        ids_string = ", ".join(slack_ids)
        slackutil.send_slack_message('#pizza', "Halloi! %s! Dere skal spise 🍕 på %s, %s. %s booker bord, og %s legger ut for maten. Vipps betaler!" % (ids_string, place, timestamp.strftime("%A %d. %B kl %H:%M"), slack_ids[0], slack_ids[1]))

def auto_reply():
    users_that_did_not_reply = db.auto_reply_after_deadline(REPLY_DEADLINE_IN_HOURS)
    if users_that_did_not_reply is None:
       return

    for user_id in users_that_did_not_reply:
        slackutil.send_slack_message(user_id, "Neivel, da antar jeg du ikke kan/gidder. Håper du blir med neste gang! 🤞")
        print("%s didn't answer. Setting RSVP to not attending.")

def save_image(cloudinary_id, slack_id, title):
    db.save_image(cloudinary_id, slack_id, title)

def rsvp(slack_id, answer):
    db.rsvp(slack_id, answer)


def send_slack_message(rtmclient, channel_id, text, attachments=None):
    rtmclient.send_slack_message(channel_id, text, attachments)


def get_invited_users():
    return db.get_invited_users()

def sync_db_with_slack_and_return_count():
  slack_users = slackutil.get_real_users(slackutil.get_slack_users())
  db.update_slack_users(slack_users)
  return len(slack_users)
