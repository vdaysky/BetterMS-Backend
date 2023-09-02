from fastapi import APIRouter

from dependencies import PlayerAuthDependency
from models import PlayerQueue, Player
from schemas.queue import Queue, PickPlayer
from services.queue import join_queue, leave_queue, confirm_queue, pick_player

router = APIRouter()


@router.post("/join")
async def join(data: Queue, player: Player = PlayerAuthDependency):

    queue = PlayerQueue.of(data.queue)

    if queue is None:
        return {
            'success': False,
            'message': 'Queue does not exist'
        }

    return await join_queue(player, queue)


@router.post("/leave")
async def leave(data: Queue, player: Player = PlayerAuthDependency):

    queue = PlayerQueue.of(data.queue)

    if queue is None:
        return {
            'success': False,
            'message': 'Queue does not exist'
        }

    return await leave_queue(player, queue)


@router.post("/confirm")
async def confirm(data: Queue, player: Player = PlayerAuthDependency):

    queue = PlayerQueue.of(data.queue)

    if not queue:
        return {
            'success': False,
            'message': 'Queue does not exist'
        }

    return await confirm_queue(player, queue)


@router.post("/pick")
async def pick(data: PickPlayer, picker: Player = PlayerAuthDependency):

    player = Player.of(data.player)
    queue = PlayerQueue.of(data.queue)

    if not player:
        return {
            'success': False,
            'message': 'Player does not exist'
        }

    if not queue:
        return {
            'success': False,
            'message': 'Queue does not exist'
        }

    return await pick_player(picker, player, queue)

