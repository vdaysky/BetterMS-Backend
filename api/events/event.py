import random

from pydantic import BaseModel


class EventOut:
    """ Event that will be sent via websocket to frontend. Usually represents change in the database """

    def __init__(self, type, payload=None):
        self.type = type
        self.data = payload
        self.msg_id = random.randint(0, 1_000_000)

    def dict(self):
        return {
            'type': self.type,
            'data': self.data,
            'msg_id': self.msg_id
        }

    def __str__(self):
        return f"EventOut<{self.type}>"

    class Type:
        """ Event types to send. Websocket should ideally be used only to send events.
        Everything else should be done via HTTP. """

        # internal workings
        MODEL_UPDATE = "ModelUpdateEvent"
        MODEL_CREATE = "ModelCreateEvent"


class EventResponse(BaseModel):
    payload: dict


class IntentResponse(BaseModel):
    payload: dict
    intent_success: bool
    intent_message: str

    @classmethod
    def success(cls, message: str, **kwargs):
        return cls(intent_success=True, intent_message=message, payload=kwargs)

    @classmethod
    def failure(cls, message: str, **kwargs):
        return cls(intent_success=False, intent_message=message, payload=kwargs)

