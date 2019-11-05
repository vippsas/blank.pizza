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

# use this to prevent spamming poor slack users while debugging bot
DEBUG_SLACK_USER_ID = ''


def process_events():
    events = api.events.get_events_in_preparation()

    for e in events:
        process_event(e)


def process_event(event):
    logging.info(f"Event {event.id}: Processing upcoming event")
    if event.finalized:
        logging.info(f"Event {event.id}: Event is finalized, skipping")
        return

    channel = event.channel

    time_until_event = datetime.datetime.now() - event.starts_at
    if time_until_event > utils.seconds_to_timedelta(channel.start_preparation):
        logging.info(
            f"Event {event.id}: Event is too far in the future, skipping")
        return

    """
    if time_until_event <= datetime.timedelta(hours=EVENT_URGENT):
        logging.info(f"Event {event.id}: Event is in URGENT mode")
    """

    if trigger_finalization(event):
        return
    trigger_reminders(event)
    trigger_invitations(event)


def trigger_reminders(event):
    channel = event.channel
    pending_invitations = api.events.get_pending_invitations(event.id)
    if len(pending_invitations) > 0:
        reminded, norsvpd = 0, 0
        for invitation in pending_invitations:
            reminders = api.events.get_invitation_reminders(invitation.id)
            last_reminded = _get_last_reminded(event, reminders)
            time_diff = (datetime.datetime.now() - last_reminded)
            if time_diff > utils.seconds_to_timedelta(channel.reminder_interval):
                # Check if invitation reminder has expired
                if len(reminders) >= channel.reminders:
                    # Check if invitation has reached threshold for amount of reminders
                    logging.info(
                        f"Event {event.id}: Invitation {invitation.id} expired without response, marking no-RSVP")
                    update_user_invitation(
                        invitation, InvitationState.NoResponse)
                    norsvpd += 1
                else:
                    # If not, send a new reminder
                    logging.info(
                        f"Event {event.id}: Sending reminder  # {len(reminders)+1} for invitation {invitation.id}")
                    send_invitation_reminder(invitation)
                    reminded += 1
        logging.info(
            f"Event {event.id}: Sent {reminded} invitation reminders and marked {norsvpd} invitations no-RSVP")


def trigger_finalization(event):
    channel = event.channel
    num_accepted_invitations = (api.events
                                .get_accepted_invitations(event.id)
                                .count())
    if num_accepted_invitations == channel.participants:
        logging.info(
            f"Event {event.id}: Event has enough participants, finalizing")

        # Sanity check: If event has enough participants, it should not have any pending invites
        pending_invitations = api.events.get_pending_invitations(event.id)
        if len(pending_invitations) > 0:
            logging.warning(
                f"Event {event.id}: Event has enough participants, yet has pending invites. This should not happen. Rescinding invitations.")
            for invitation in pending_invitations:
                update_user_invitation(
                    invitation, InvitationState.Rescinded)

        finalize_event(event)
        return True
    return False


def trigger_invitations(event):
    channel = event.channel
    num_accepted_invitations = (api.events
                                .get_accepted_invitations(event.id)
                                .count())
    num_pending_invitations = (api.events
                               .get_pending_invitations(event.id)
                               .count())
    num_active_invitations = num_accepted_invitations + num_pending_invitations
    num_to_invite = channel.participants - num_active_invitations
    if num_to_invite > 0:
        new_invitations = get_event_candidates(
            event,
            num_to_invite,
            event.channel.users.count()
        )

        # Check if channel is exhausted for invitations
        if len(new_invitations) == 0:
            logging.info(
                f"Event {event.id}: Event needs {num_to_invite} more participants, but there are no more candidates")
            if num_pending_invitations == 0 and num_accepted_invitations < channel.participants:
                logging.info(
                    f"Event {event.id}: Finalizing event with {num_accepted_invitations} participants as there are no more candidates to invite")
                finalize_event(event)
                return
        elif len(new_invitations) < num_to_invite:
            logging.info(
                f"Event {event.id}: Needed {num_to_invite} new candidates, but found only {len(new_invitations)}")

        for candidate in new_invitations:
            user = User.get(User.id == candidate["id"])
            logging.info(
                f"Event {event.id}: Inviting {user.name} (attended {candidate['events_attended']}) to event")
            send_user_invitation(event, user)


def create_event(channel):
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


def send_user_invitation(event, user):
    channel = api.slack.start_im(DEBUG_SLACK_USER_ID)  # user.slack_id

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
        InvitationState.Rescinded: "Utvikleren av Pizzabot har gjort noe dumt, og som en konsekvens av dette må din invitasjon til pizzakveld trekkes. Beklager :("
    }.get(new_state, ":scream:")

    response = slack.chat_postMessage(
        channel=invitation.slack_channel,
        text=reply
    )
    if not response["ok"]:
        raise "shit"

    if new_state == InvitationState.Accepted:
        trigger_finalization(invitation.event)
    if new_state == InvitationState.Rejected:
        trigger_invitations(invitation.event)


def _get_last_reminded(event, reminders):
    if len(reminders) == 0:
        return event.created
    # Reminders are passed in in descending order
    # the first element is the more recent
    return reminders[0].sent_at


def send_invitation_reminder(invitation):
    Reminder.create(
        invitation=invitation.id,
    )

    # invitation.user.slack_id
    channel = api.slack.start_im(DEBUG_SLACK_USER_ID)
    slack.chat_postMessage(
        channel=channel,
        text=f"Hei! Har ikke hørt noe fra deg på en stund ang. denne pizzakvelden. Kan du plz svare!?"
    )


def finalize_event(event):
    event.finalized = True
    event.save()
    accepted = api.events.get_accepted_invitations(event.id)
    users = list(map(lambda inv: inv.user.slack_id, accepted))
    mentions = utils.create_mentions(users)
    # TODO: REMOVE
    channel = api.slack.start_im(DEBUG_SLACK_USER_ID)
    slack.chat_postMessage(
        channel=channel,  # event.channel.id
        text=f"{mentions} dere skal på pizza da. {event.venue.name} {utils.sane_time(event.starts_at)}"
    )
