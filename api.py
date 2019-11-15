#!/usr/bin/env python
# -*- coding: utf-8 -*-

import slackutil
import db
import locale
import pytz
from datetime import datetime, timedelta

#locale.setlocale(locale.LC_ALL, "nb_NO.utf8")

PEOPLE_PER_EVENT = 3
REPLY_DEADLINE_IN_HOURS = 24
DAYS_IN_ADVANCE_TO_INVITE = 10
HOURS_BETWEEN_REMINDERS = 4


BUTTONS_ATTACHMENT = [
    {
        "type": "actions",
        "elements": [
            {
                "text": {
                    "type": "plain_text", 
                    "text": "Hells yesss!!! 🍕🍕🍕",
                },
                "type": "button",
                "value": "attending"
            },
            {
                "text": {
                    "type": "plain_text", 
                    "text": "Nah ☹️",
                },
                "type": "button",
                "value": "attending"
            }
        ]
    }
]
BUTTONS_ATTACHMENT = None

def invite_if_needed():
    print("api:invite_if_needed")
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
        slackutil.send_private_message(user_id, "Hey <@%s>! You are invited to 🍕 at %s, %s. Please answer within %s hours 🙏. Are you able to join?" %
                (user_id, place, timestamp.strftime("%A %d. %B at %H:%M"), REPLY_DEADLINE_IN_HOURS), BUTTONS_ATTACHMENT)
        print("%s was invited to event on %s" % (user_id, timestamp))

def send_reminders():
    print("api:send_reminders")
    inviations = db.get_unanswered_invitations()

    for invitation in inviations:
        slack_id, invited_at, reminded_at = invitation
        actual_dude = slack_id
        remind_timestamp = datetime.now() + timedelta(hours=-HOURS_BETWEEN_REMINDERS)
        if(reminded_at < remind_timestamp):
            slackutil.send_private_message(slack_id, "Hey you <@%s>! I didn't hear anything from you? Are you pumped? 💪 🍕 (yes/no)" % actual_dude, BUTTONS_ATTACHMENT)
            db.update_reminded_at(slack_id)
            print("%s was reminded about an event." % slack_id)

def finalize_event_if_complete():
    print("api:finalize_event_if_complete")
    event = db.get_event_ready_to_finalize(PEOPLE_PER_EVENT)
    if event is None:
        print("No events ready to finalize")
    else:
        event_id, timestamp, place = event
        sync_db_with_slack_and_return_count()
        slack_ids = ['<@%s>' % user for user in db.get_attending_users(event_id)]
        db.mark_event_as_finalized(event_id)
        ids_string = ", ".join(slack_ids)
        slackutil.send_channel_message(slackutil.PIZZA_CHANNEL, "Hi 👏 %s! You will eat 🍕 at %s, %s. %s book a table, and %s cover the food. Vipps is paying 🤗 !" % (ids_string, place, timestamp.strftime("%A %d. %B kl %H:%M"), slack_ids[0], slack_ids[1]))

def auto_reply():
    print("api:auto_reply")
    users_that_did_not_reply = db.auto_reply_after_deadline(REPLY_DEADLINE_IN_HOURS)
    if users_that_did_not_reply is None:
       return

    for user_id in users_that_did_not_reply:
        slackutil.send_private_message(user_id, "I guess you are not available today - I will ask someone else instead 😉 Next time 😘")
        print("%s didn't answer. Setting RSVP to not attending.")

def save_image(cloudinary_id, slack_id, title):
    db.save_image(cloudinary_id, slack_id, title)

def rsvp(slack_id, answer):
    db.rsvp(slack_id, answer)

def get_invited_users():
    return db.get_invited_users()

def sync_db_with_slack_and_return_count():
  slack_users = slackutil.get_real_users(slackutil.get_slack_users())
  db.update_slack_users(slack_users)
  return len(slack_users)
