from blazelink.schemas import IncomingEvent

from exceptions import BadRequestError
from models import MapPick, Player, MapPickProcess, Session
from events.internal import internalHandler


async def select_map(map: MapPick, player: Player):
    process = map.process
    match = process.match
    is_picked = process.next_action == MapPickProcess.Action.PICK

    # look up pick process
    map_pick_process = match.map_pick_process

    if map_pick_process.turn is None:
        raise BadRequestError("You are not allowed to pick yet")

    # count some stats prior to picking
    maps_banned = len(map_pick_process.banned)
    maps_picked = len(map_pick_process.picked)
    map_count = match.map_count
    selected_maps = maps_banned + maps_picked

    if map_pick_process.finished:
        raise BadRequestError

    if map_pick_process.turn != player:
        raise BadRequestError("Wait for your turn")

    if map.was_selected():
        raise BadRequestError('Map was already selected')

    # mark map as selected
    map.picked = is_picked
    map.selected_by_id = match.get_team_of(player).id

    print("map selected", map.id, map.picked, map.selected_by_id)
    Session.add(map)
    Session.commit()
    Session.refresh(map)

    # update count after last action
    maps_banned += not is_picked
    maps_picked += is_picked

    selected_maps += 1

    # Now that validation is done we have to determine next action
    next_action = None

    picks_finished = False

    # first two are always ban
    if maps_banned < 2:
        next_action = MapPickProcess.Action.BAN

    # after initial bans we pick one less than actual map count
    elif maps_picked < map_count - 1:
        next_action = MapPickProcess.Action.PICK

    # Last is always picked by default
    elif selected_maps == 6:
        next_action = MapPickProcess.Action.NULL

        picks_finished = True

        not_picked = map_pick_process.not_picked
        assert len(not_picked) == 1
        map_left = not_picked[0]
        map_left.picked = True
        map_left.selected_by = None
        Session.commit()

    # after that we ban until decider is found
    else:
        next_action = MapPickProcess.Action.BAN

    # save next action
    map_pick_process.next_action = next_action

    if not picks_finished:
        map_pick_process.turn = map_pick_process.other_picker(player)
    else:
        map_pick_process.turn = None
        map_pick_process.finished = True

    Session.commit()

    if map_pick_process.finished:
        await internalHandler.propagate_abstract_event(IncomingEvent(type='MapPickDone', data={}), match)


async def finish_mp(match):
    await internalHandler.propagate_abstract_event(IncomingEvent(type='MapPickDone', data={}), match)
