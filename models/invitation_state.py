from enum import Enum


class InvitationState(str, Enum):
    Invited = "invited"
    Accepted = "accepted"
    Rejected = "rejected"
    NoResponse = "norsvp"
