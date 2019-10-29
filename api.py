from models import Event, Invitation, InvitationState


def get_all_invitations(event_id):
    return Event.get(Event.id == event_id).invitations


def _get_invitation_by_state(event_id, state):
    return Event.get(Event.id == event_id).invitations.where(
        Invitation.state == state)


def get_pending_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Invited)


def get_accepted_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Accepted)


def get_rejected_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.Rejected)


def get_norsvp_invitations(event_id):
    return _get_invitation_by_state(event_id, InvitationState.NoResponse)
