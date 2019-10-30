import logging

from models import InvitationState


class Invitation:
    def __init__(self, user, state, venue, starts_at):
        self.user = user
        self.state = state
        self.venue = venue
        self.starts_at = starts_at

    def get_payload(self):
        if self.state == InvitationState.Invited:
            return [
                self._get_greeting_block(),
                self._get_event_block(),
                self._get_actions_block(),
            ]
        else:
            return [
                self._get_greeting_block(),
                self._get_event_block(),
            ]

    def _get_greeting_block(self):
        return {
            "type": "section",
            "text": {
                    "type": "mrkdwn",
                    "text": f"Hei <@{self.user}>! :eyes: Du er invitert til :pizza:! Kan du? Svar kjapt! :pray:"
            }
        }

    def _get_event_block(self):
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f":round_pushpin: *Hvor?*\n{self.venue}"
                },
                {
                    "type": "mrkdwn",
                    "text": f":calendar: *Når?*\n{self.starts_at.strftime('%d/%m %H:%M')}"
                },
            ]
        }

    def _get_actions_block(self):
        return {
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
                        "value": InvitationState.Accepted
                    },
                {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Nei :pizza: :no_entry_sign: :nauseated_face:"
                        },
                        "style": "danger",
                        "value": InvitationState.Rejected
                    }
            ]
        }
