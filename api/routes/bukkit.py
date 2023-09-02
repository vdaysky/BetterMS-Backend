from blazelink.schemas import IncomingEvent
from fastapi import APIRouter

from events.bukkit import BukkitEventManager
from dependencies import GetMineStrike

router = APIRouter()


@router.post('/event')
async def post_event(event: IncomingEvent, minestrike=GetMineStrike):

    print("received event", event.type, event.data)
    response = await BukkitEventManager.propagate_abstract_event(
        event, minestrike
    )
    print("sending response to event", event.type, response)

    return {
        "response": {
            "payload": response
        }
    }
