import datetime

from peewee import fn

from client import client as slack
from models import Event, Invitation, InvitationState, User, Venue

import api.slack
import api.events
import views
import utils

NUM_INVITE_USERS = 3
NUM_REMINDERS = 3


def send_reminders(event):
    invitations = Invitation.select().where((Invitation.event_id == event.id) &
                                            (Invitation.state == InvitationState.Invited))
    pass


def finalize_events():
    events = api.events.get_events_in_preparation()
    for e in events:
        accepted = api.events.get_accepted_invitations(e.id)
        if len(accepted) == NUM_INVITE_USERS:
            e.finalized = True
            e.save()

            users = list(map(lambda inv: inv.user.slack_id, accepted))
            mentions = utils.create_mentions(users)
            slack.chat_postMessage(
                channel=e.channel.id, text=f"{mentions} dere skal på pizza da. {e.venue.name} kl {utils.sane_time(e.starts_at)}")


def start_pizza(channel, initiator):
    venue = Venue.select().order_by(fn.Random()).get()
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    starts_at = datetime.datetime(
        year=tomorrow.year, month=tomorrow.month, day=tomorrow.day, hour=18)

    event = Event(channel=channel, venue=venue, starts_at=starts_at)
    event.save()

    to_invite = User.select().order_by(fn.Random()).limit(NUM_INVITE_USERS)
    for u in to_invite:
        send_invitation(event, u, initiator)


def send_invitation(event, user, initiator):  # REMOVE INIT
    channel = api.slack.start_im(initiator)  # u

    view = views.Invitation(user.slack_id, InvitationState.Invited,
                            event.venue.name, event.starts_at)

    response = slack.chat_postMessage(
        channel=channel, blocks=view.get_payload())
    if not response["ok"]:
        raise "shit"

    invitation = Invitation(
        event=event.id, user=user.id, state=InvitationState.Invited, slack_channel=channel, slack_ts=response["ts"])
    invitation.save()


def update_invitation(invitation, new_state):
    # Update view
    view = views.Invitation(invitation.user.slack_id, new_state,
                            invitation.event.venue.name, invitation.event.starts_at)
    response = slack.chat_update(
        channel=invitation.slack_channel, ts=invitation.slack_ts, blocks=view.get_payload())
    if not response["ok"]:
        raise "shit"

    # Update database record
    invitation.state = new_state
    invitation.slack_ts = response["ts"]
    invitation.save()

    # Send acknowledgement
    reply = {
        InvitationState.Accepted: "Du har takket JA :thumbsup: til :pizza:. Merk kalenderen!",
        InvitationState.Rejected: "Du har takket NEI :thumbsdown: til :pizza:. Håper å se deg neste gang!",
        InvitationState.NoResponse: "Du ignorerte meg! :blushing_robot: Nå går plassen din til noen andre og du går glipp av :pizza:. Sees neste gang?",
    }.get(new_state, ":scream:")

    response = slack.chat_postMessage(
        channel=invitation.slack_channel, text=reply)
    if not response["ok"]:
        raise "shit"
