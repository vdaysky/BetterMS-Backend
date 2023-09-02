import asyncio
from datetime import datetime

from blazelink.schemas import IncomingEvent

from models import Player, PlayerQueue, Match, MapPickProcess, Game, PlayerSession, MatchTeam, Session, MapPick, Map
from events.internal import internalHandler


async def join_queue(player: Player, queue: PlayerQueue):
    if queue.locked:
        return {
            'success': False,
            'message': 'Queue is locked'
        }

    if not queue.join(player):
        return {
            'success': False,
            'message': 'Player already in queue'
        }

    await internalHandler.propagate_abstract_event(
        IncomingEvent(type='PlayerJoinQueue', data={'player': player}),
        queue,
        blocking=False
    )

    return {
        'success': True,
        'message': 'Player joined queue'
    }


async def leave_queue(player: Player, queue: PlayerQueue):
    if queue.locked:
        return {
            'success': False,
            'message': 'Queue is locked'
        }

    if not queue.leave(player):
        return {
            'success': False,
            'message': 'Player not in queue'
        }

    await internalHandler.propagate_abstract_event(IncomingEvent(type='PlayerLeaveQueue', data={'player': player}), queue)

    return {
        'success': True,
    }


async def confirm_queue(player: Player, queue: PlayerQueue):
    # can only confirm game once queue is locked
    if not queue.locked:
        return {
            'success': False,
            'message': 'Queue is not locked'
        }

    if not queue.confirm(player):
        return {
            'success': False,
            'message': 'Player already confirmed'
        }

    await internalHandler.propagate_abstract_event(
        IncomingEvent(type='PlayerConfirmQueue', data={'player': player}),
        queue
    )

    return {
        'success': True,
        'message': 'Player confirmed queue'
    }


async def pick_player(captain: Player, player: Player, queue: PlayerQueue):

    # player is not a captain
    if not queue.captain_a == captain and not queue.captain_b == captain:
        return {
            'success': False,
            'message': 'Player is not a captain'
        }

    captain_is_a = queue.captain_a == captain

    match = queue.match

    a_players = len(match.team_one.players)
    b_players = len(match.team_two.players)

    # not your turn
    if captain_is_a and a_players != b_players:
        return {
            'success': False,
            'message': 'Not your turn'
        }

    if not captain_is_a and a_players - b_players != 1:
        return {
            'success': False,
            'message': 'Not your turn'
        }

    # queue wasn't confirmed yet (how did we get captains then?)
    if not queue.confirmed:
        return {
            'success': False,
            'message': 'Queue not confirmed'
        }

    # player already picked
    if player in [*match.team_two.players, *match.team_one.players]:
        return {
            'success': False,
            'message': 'Player already picked'
        }

    # add player to captain's match team
    if queue.captain_a == captain:
        match.team_one.players.append(player)
    else:
        match.team_two.players.append(player)

    Session.commit()

    await internalHandler.propagate_abstract_event(IncomingEvent(type='PlayerPicked', data={'player': player}), queue)

    return {
        'success': True,
        'message': 'Player picked'
    }


@internalHandler.on("PlayerConfirmQueue")
async def on_queue_confirmation(queue: PlayerQueue, payload):
    # check if all players accepted
    if len(queue.confirmed_players) == queue.size:
        queue.confirmed = True
        Session.commit()
        await internalHandler.propagate_abstract_event(IncomingEvent(type='QueueConfirmed', data={}), queue)
        return


@internalHandler.on("PlayerJoinQueue")
async def on_player_join_queue(queue: PlayerQueue, payload):

    queue = Session().merge(queue)

    print(f"Player Joined Queue. Players in queue: {len(queue.players)}")
    # check if queue is full
    if len(queue.players) != queue.size:
        return

    # lock queue
    queue.lock()

    # queue is locked, meaning match confirmation started
    # make sure that in 30 seconds QueueConfirmed event will be fired
    try:
        await internalHandler.wait("QueueConfirmed", timeout=60).on(queue)
    except TimeoutError:
        # Timed out: did not receive enough confirmations

        # get players who didn't accept
        not_confirmed = [player for player in queue.players if player not in queue.confirmed_players]

        print(f"QueueConfirmed was never received. Unlocking queue. Not confirmed: {len(not_confirmed)}")

        for player in not_confirmed:
            # remove players who didn't accept from queue
            queue.players.remove(player)

        # unlock queue, let new players in
        queue.unlock()

        # delete all player confirmations
        queue.unconfirm()


@internalHandler.on("QueueConfirmed")
async def on_queue_confirmed(queue: PlayerQueue, payload):
    # select two captains with highest elo
    captain_a, captain_b = sorted(queue.players, key=lambda p: p.elo)[-2:]

    team_one = MatchTeam(name=f"Team_{captain_a.username}")
    team_two = MatchTeam(name=f"Team_{captain_b.username}")

    Session.add(team_one)
    Session.add(team_two)
    Session.commit()
    Session.refresh(team_one)
    Session.refresh(team_two)

    # by default captain_a is picking first
    map_pick_process = MapPickProcess(
        next_action=MapPickProcess.Action.BAN,
        picker_a_id=captain_a.id,
        picker_b_id=captain_b.id,
        turn_id=captain_a.id,
    )

    Session.add(map_pick_process)
    Session.commit()

    maps = Map.with_tag(Map.Tag.Competitive)

    picks = [MapPick(map_id=map.id, process_id=map_pick_process.id) for map in maps]

    for pick in picks:
        Session.add(pick)

    map_pick_process.maps.extend(picks)

    Session.commit()

    # create match
    match = Match(
        team_one_id=team_one.id,
        team_two_id=team_two.id,
        name=f'Team_{captain_a.username} vs Team_{captain_b.username}',
        start_date=datetime.now(),
        map_count=1,
        game_meta={
            'mode': Game.Mode.RANKED,
            'config_overrides': {
                'min_players': queue.size,
                'max_players': queue.size,
                'block_b_site': 1 if queue.size <= 4 else 0,  # small queues play on one site
            }
        },
        map_pick_process_id=map_pick_process.id,
    )

    Session.add(match)
    Session.commit()

    # Captains belong to their team instantly
    match.team_one.players.append(captain_a)
    match.team_two.players.append(captain_b)

    queue.match = match
    queue.captain_a = captain_a
    queue.captain_b = captain_b

    Session.commit()

    # We need to create a new empty queue
    new_queue = PlayerQueue(
        type=queue.type,
        size=queue.size,
    )

    Session.add(new_queue)
    Session.commit()

    # wait for map pick to finish
    # await internalHandler.wait("MapPickDone").post(match)

    # # manage players inside game
    # # note: in-game teams are not filled here.
    # for game in match.games:
    #     # register whitelist
    #     game.whitelist.extend(queue.players)

    # Session.commit()
