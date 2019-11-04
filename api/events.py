import datetime

from models import Event, Invitation, InvitationState, Reminder


def get_future_events():
    return (Event
            .select()
            .where(Event.starts_at > datetime.datetime.now()))


def get_events_in_preparation():
    return (Event
            .select()
            .where(
                (Event.starts_at > datetime.datetime.now()) &
                (Event.finalized == False)
            ))


def get_all_invitations(event_id):
    return Event.get(Event.id == event_id).invitations


def get_active_invitations(event_id):
    return (Event
            .get(Event.id == event_id)
            .invitations
            .where(
                (Invitation.state == InvitationState.Invited) |
                (Invitation.state == InvitationState.Accepted)
            ))


def _get_invitation_by_state(event_id, state):
    return (Event
            .get(Event.id == event_id)
            .invitations
            .where(Invitation.state == state))


def get_pending_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Invited)


def get_accepted_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Accepted)


def get_rejected_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Rejected)


def get_norsvp_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.NoResponse)


def get_invitation_reminders(invitation_id):
    return (Reminder
            .select()
            .where(Reminder.invitation == invitation_id)
            .order_by(Reminder.sent_at.desc()))
