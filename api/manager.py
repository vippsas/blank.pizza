import datetime
import logging

from peewee import fn

from client import client as slack
from models import Event, Invitation, InvitationState, User, Venue, Reminder

import api.slack
import api.events
import views
import utils


NUM_INVITE_USERS = 3
NUM_REMINDERS = 3


def send_reminders():
    events = api.events.get_events_in_preparation()
    for e in events:
        reminded, norsvpd = send_invitation_reminders(e)
        logging.info(
            f"Event {e.id}: {reminded} reminded, {norsvpd} marked no-RSVP")
    logging.info(f"Sent reminders for {len(events)} events")


def _get_last_reminded(event, reminders):
    if len(reminders) == 0:
        return event.created
    # Reminders are passed in in descending order
    # the first element is the more recent
    return reminders[0].sent_at


def send_invitation_reminders(event):
    pending = api.events.get_pending_invitations(event.id)
    created = event.created
    now = datetime.datetime.utcnow()

    reminded, norsvp = 0, 0

    for invitation in pending:
        reminders = api.events.get_invitation_reminders(invitation.id)
        last_reminded = _get_last_reminded(event, reminders)
        time_diff = (now - last_reminded)
        if time_diff > datetime.timedelta(minutes=1):
            logging.info(
                f"Event {event.id}: Invitation {invitation.id} past time threshold, reminding")
            r, n = send_invitation_reminder(invitation, reminders)
            reminded += r
            norsvp += n

    return reminded, norsvp


def send_invitation_reminder(invitation, reminders):
    if len(reminders) >= NUM_REMINDERS:
        logging.info(
            f"Invitation {invitation.id}: Sent reminders reached threshold {NUM_REMINDERS}, marking no-RSVP")
        invitation.state = InvitationState.NoResponse
        invitation.save()
        print(f"{invitation.user.name} taper plassen sin!")
        return 0, 1
    else:
        logging.info(
            f"Invitation {invitation.id}: Sending reminder #{len(reminders+1)}")
        Reminder.create(
            invitation=invitation.id,
            sent_at=datetime.datetime.utcnow()
        )
        print(f"{invitation.user.name} har ikke SVART på mer enn 1 minutter")
        return 1, 0
    return 0, 0


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
        "Event {event.id}: Sending {num_invite} invitations for event")

    to_invite = (User
                 .select()
                 .where(User.channel == event.channel_id)
                 .order_by(fn.Random())
                 .limit(num_invite))

    for u in to_invite:
        send_invitation(event, u)

    return num_invite


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
        slack.chat_postMessage(
            channel=event.channel.id,
            text=f"{mentions} dere skal på pizza da. {event.venue.name} {utils.sane_time(event.starts_at)}"
        )
        return True
    return False


def start_pizza(channel, initiator):
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
        created=datetime.datetime.utcnow(),
        venue=venue,
        starts_at=starts_at
    )
    event.save()

    send_event_invitations(event)

    return event


def send_invitation(event, user, initiator):  # REMOVE INIT
    channel = api.slack.start_im(initiator)  # u

    view = views.Invitation(
        user.slack_id,
        InvitationState.Invited,
        event.venue.name,
        event.starts_at
    )

    response = slack.chat_postMessage(
        channel=channel, blocks=view.get_payload())
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


def update_invitation(invitation, new_state):
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

    return invitation
