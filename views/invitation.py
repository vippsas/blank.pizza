import logging

from models import InvitationState


class Invitation:
    def __init__(self, user):
        self.user = user
        self.status = InvitationState.Invited
        self.venue = "Hell's Kitchen"
        self.time = "01/11/2019 18:00:00"

    def get_payload(self):
        if self.status == InvitationState.Invited:
            return self.get_invited_blocks()
        elif self.status == InvitationState.Accepted:
            return self.get_accepted_blocks()
        elif self.status == InvitationState.Rejected:
            return self.get_rejected_blocks()
        elif self.status == InvitationState.NoResponse:
            return self.get_norsvp_blocks()
        else:
            logging.error(f"Reached invalid state: {self.status}")
            pass

    def get_event_block(self):
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f":round_pushpin: *Hvor?*\n{self.venue}"
                },
                {
                    "type": "mrkdwn",
                    "text": f":calendar: *Når?*\n{self.time}"
                },
            ]
        }

    def get_invited_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hei <@{self.user}>! :eyes: Du er invitert til :pizza:! Kan du? Svar kjapt! :pray:"
                }
            },
            self.get_event_block(),
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Ja :thumbsup: :star-struck:"
                        },
                        "style": "primary",
                        "value": "accept_invite"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Nei :pizza: :no_entry_sign: :nauseated_face:"
                        },
                        "style": "danger",
                        "value": "reject_invite"
                    }
                ]
            }
        ]
