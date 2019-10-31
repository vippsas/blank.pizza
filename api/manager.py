import datetime
import logging
import math

from peewee import SQL, fn

from client import client as slack
from models import Event, Invitation, InvitationState, User, Venue, Reminder

import api.slack
import api.events
import views
import utils


NUM_INVITE_USERS = 3
NUM_REMINDERS = 3


def process_events():
    events = api.events.get_events_in_preparation()

    for e in events:
        # Ensure invitations are reminded of
        send_invitation_reminders(e)

        # Ensure event has invitations
        send_event_invitations(e)


def start_event(channel):
    venue = Venue.select().order_by(fn.Random()).get()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    starts_at = datetime.datetime(
        year=tomorrow.year,
        month=tomorrow.month,
        day=tomorrow.day,
        hour=18
    )

    event = Event(
        channel=channel,
        venue=venue,
        starts_at=starts_at
    )
    event.save()

    send_event_invitations(event)

    return event


def get_event_candidates(event, num_invite, num_candidates):
    num_event_score_limit = math.ceil(num_candidates / num_invite)
    return (User
            .select(User.id, fn.Count(Invitation.state).alias("events_attended"))
            .where(User.channel == event.channel_id)
            .join(Invitation, "LEFT", on=(
                (Invitation.user == User.id) &
                (Invitation.state == InvitationState.Accepted) &
                (Invitation.event.in_((Event
                                       .select(Event.id)
                                       .where(
                                           (Event.finalized == True) &
                                           (Event.starts_at <
                                            datetime.datetime.now())
                                       )
                                       .order_by(Event.starts_at.desc())
                                       .limit(num_event_score_limit)
                                       )
                                      ))))
            .where(~fn.EXISTS(Invitation
                              .select()
                              .where(
                                  (Invitation.event == event.id) &
                                  (Invitation.user == User.id)
                              )
                              ))
            .group_by(User.id)
            .order_by(SQL("events_attended"), fn.Random())
            .limit(num_invite)
            .dicts())


def send_event_invitations(event):
    if event.finalized:
        logging.info(
            f"Event {event.id}: Event finalized, no need for invitations")
        return False

    num_invited = Invitation.select().where(
        (Invitation.event == event.id) & (
            (Invitation.state == InvitationState.Invited) |
            (Invitation.state == InvitationState.Accepted)
        )
    ).count()
    num_invite = NUM_INVITE_USERS - num_invited

    logging.info(
        f"Event {event.id}: Sending {num_invite} invitations for event")

    total_users = (User
                   .select()
                   .where(User.channel == event.channel)
                   .count())
    to_invite = get_event_candidates(event, num_invite, total_users)
    if len(to_invite) < num_invite:
        logging.error(
            f"Event {event.id}: Got fewer candidates ({len(to_invite)}) than requested ({num_invite}). Has everyone been asked?")

    for u in to_invite:
        user = User.get(User.id == u["id"])
        logging.info(
            f"Event {event.id}: Inviting {user.name} (attended {u['events_attended']}) to event")
        send_user_invitation(event, user)

    return num_invite


def send_user_invitation(event, user):
    channel = api.slack.start_im("UCF7RT0HF")  # user.slack_id

    view = views.Invitation(
        user.slack_id,
        InvitationState.Invited,
        event.venue.name,
        event.starts_at
    )

    response = slack.chat_postMessage(
        channel=channel,
        blocks=view.get_payload()
    )
    if not response["ok"]:
        raise "shit"

    invitation = Invitation(
        event=event.id,
        user=user.id,
        state=InvitationState.Invited,
        slack_channel=channel,
        slack_ts=response["ts"]
    )
    invitation.save()

    return invitation


def update_user_invitation(invitation, new_state):
    logging.info(
        f"Invitation {invitation.id}: Received invitation response. Updating.")
    invitation.state = new_state

    # Update view
    view = views.Invitation(
        invitation.user.slack_id,
        invitation.state,
        invitation.event.venue.name,
        invitation.event.starts_at
    )
    response = slack.chat_update(
        channel=invitation.slack_channel,
        ts=invitation.slack_ts,
        blocks=view.get_payload()
    )
    if not response["ok"]:
        raise "shit"

    # Update database record
    invitation.slack_ts = response["ts"]
    invitation.save()

    # Send acknowledgement
    reply = {
        InvitationState.Accepted: "Du har takket JA :thumbsup: til :pizza:. Merk kalenderen!",
        InvitationState.Rejected: "Du har takket NEI :thumbsdown: til :pizza:. Håper å se deg neste gang!",
        InvitationState.NoResponse: "Du ignorerte meg! :blushing_robot: Nå går plassen din til noen andre og du går glipp av :pizza:. Sees neste gang?",
    }.get(new_state, ":scream:")

    response = slack.chat_postMessage(
        channel=invitation.slack_channel,
        text=reply
    )
    if not response["ok"]:
        raise "shit"

    if invitation.state == InvitationState.Rejected:
        logging.info(
            "Event {invitiation.event_id}: Sending new invitations as invitation {invitation.id} was rejected")
        send_event_invitations(invitation.event)

    if invitation.state == InvitationState.Accepted:
        logging.info(
            f"Event {invitation.event_id}: Checking if event can be finalized as {invitation.id} was accepted")
        finalize_event(invitation.event)

    return invitation


def _get_last_reminded(event, reminders):
    if len(reminders) == 0:
        return event.created
    # Reminders are passed in in descending order
    # the first element is the more recent
    return reminders[0].sent_at


def send_invitation_reminders(event):
    pending = api.events.get_pending_invitations(event.id)

    reminded, norsvp = 0, 0

    for invitation in pending:
        reminders = api.events.get_invitation_reminders(invitation.id)
        last_reminded = _get_last_reminded(event, reminders)
        time_diff = (datetime.datetime.now() - last_reminded)
        if time_diff > datetime.timedelta(minutes=1):
            logging.info(
                f"Event {event.id}: Invitation {invitation.id} past time threshold, reminding")
            r, n = send_invitation_reminder(invitation, reminders)
            reminded += r
            norsvp += n
    logging.info(
        f"Event {event.id}: Sent {reminded} reminders and marked {norsvp} no-RSVP on {len(pending)} invitations")
    return reminded, norsvp


def send_invitation_reminder(invitation, reminders):
    if len(reminders) >= NUM_REMINDERS:
        logging.info(
            f"Invitation {invitation.id}: Sent reminders reached threshold {NUM_REMINDERS}, marking no-RSVP")
        update_user_invitation(invitation, InvitationState.NoResponse)

        return 0, 1
    else:
        logging.info(
            f"Invitation {invitation.id}: Sending reminder #{len(reminders)+1}")
        Reminder.create(
            invitation=invitation.id,
        )

        channel = api.slack.start_im("UCF7RT0HF")  # invitation.user.slack_id
        num_reminded = len(reminders)
        level_of_anger = "!?" * (num_reminded + 1)
        slack.chat_postMessage(
            channel=channel,
            text=f"Hei! Har ikke hørt noe fra deg på en stund ang. denne pizzakvelden. Kan du plz svare{level_of_anger}"
        )

        return 1, 0

    return 0, 0


def finalize_events():
    events = api.events.get_events_in_preparation()
    finalized = 0
    for e in events:
        did_finalize = finalize_event(e)
        if did_finalize:
            finalized += 1
    return finalized


def finalize_event(event):
    accepted = api.events.get_accepted_invitations(event.id)
    if len(accepted) == NUM_INVITE_USERS:
        logging.info(
            f"Event {event.id}: Accepted invitations reached threshold, finalizing event")
        # Sanity check: Ensure there are no pending invites
        pending = api.events.get_pending_invitations(event.id)
        if len(pending) > 0:
            logging.error(
                f"{event.id} has enough accepted members, yet there are {len(pending)} pending invites. Marking as rejections.")
            for i in pending:
                i.update(state=InvitationState.Rejected)

        event.finalized = True
        event.save()

        users = list(map(lambda inv: inv.user.slack_id, accepted))
        mentions = utils.create_mentions(users)
        # TODO: REMOVE
        channel = api.slack.start_im("UCF7RT0HF")
        slack.chat_postMessage(
            channel=channel,  # event.channel.id
            text=f"{mentions} dere skal på pizza da. {event.venue.name} {utils.sane_time(event.starts_at)}"
        )
        return True
    return False
