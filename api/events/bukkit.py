import asyncio
import logging
import random
from datetime import datetime

from sqlalchemy import delete
from sqlmodel import select

from adapters.telegram import bot, safe_send
from events.event import IntentResponse
from events.schemas.bukkit import ServerStartEvent, CreateGameIntentEvent, PlayerJoinGameIntentEvent, \
    PlayerLeaveGameEvent, PlayerTeamChangeIntentEvent, PreGameEndEvent, GameStartedEvent, PlayerJoinServerEvent, \
    PlayerLeaveServerEvent, PlayerDeathEvent, PlayerLeaveGameIntentEvent, GameDeleteIntentEvent, \
    ChangePlayerWhitelistStatusAtGameIntent, ChangePlayerBlacklistStatusAtGameIntent, RoundWinEvent, \
    PlayerGenerateCodeIntent
from schemas.permission import Permission
from services.game import find_team_for_player, PluginMap, create_game
from services.minestrike import MineStrike
from events.manager import EventManager
from models import InGameTeam, Game, Player, PlayerSession, Map, GamePlayerEvent, Round, Session
from services.permission import has_permission
from services.ranked import compute_elo
from settings import settings

BukkitEventManager = EventManager()


@BukkitEventManager.on(ServerStartEvent)
async def on_plugin_start(minestrike: MineStrike, event: ServerStartEvent):
    print("server started")

    stmt = Session().exec(
        select(PlayerSession).join(Player).where(Player.uuid == None)
    ).all()

    print("Delete temp player sessions", stmt)

    d = delete(PlayerSession).where(PlayerSession.id.in_([x.id for x in stmt]))
    Session().execute(d)
    Session().commit()


@BukkitEventManager.on(PlayerLeaveGameIntentEvent)
async def on_game_leave_request(minestrike: MineStrike, event: PlayerLeaveGameIntentEvent):
    game = Game.of(event.game)
    player = Player.of(event.player)

    await minestrike.leave_game(
        player,
        game,
    )


@BukkitEventManager.on(GameDeleteIntentEvent)
async def on_game_delete_request(minestrike: MineStrike, event: GameDeleteIntentEvent):
    game = Game.of(event.game)

    if game is None:
        return IntentResponse.failure(
            f"Game {event.game.obj_id} not found on backend"
        )

    game.status = Game.Status.TERMINATED
    Session().commit()

    # let server know that game is terminated
    await minestrike.terminate_game(game)

    # make sure game is deleted from server list
    await minestrike.update_server()

    return IntentResponse.success("Game deleted")


@BukkitEventManager.on(ChangePlayerBlacklistStatusAtGameIntent)
async def on_blacklist_request(minestrike: MineStrike, event: ChangePlayerBlacklistStatusAtGameIntent):

    manager = Player.of(event.manager)
    player = Player.of(event.player)
    game = Game.of(event.game)

    if None in [manager, player, game]:
        return IntentResponse.failure("Invalid intent request")

    if not manager.has_perm(Permission.BMS.Games.Manager.Blacklist):
        return IntentResponse.failure("You don't have permission to manage game blacklist")

    dry_run = False

    if event.isBlacklisted:
        if player not in game.blacklist:
            game.blacklist.append(player)
        else:
            dry_run = True
    else:
        try:
            game.blacklist.remove(player)
        except ValueError:
            dry_run = True

    Session().commit()

    # propagate whitelist change
    await minestrike.update_game(game)

    if dry_run:
        if event.isBlacklisted:
            return IntentResponse.success("Player already blacklisted")
        else:
            return IntentResponse.success("Player already not on blacklist")
    else:
        if event.isBlacklisted:
            return IntentResponse.success("Player blacklisted")
        else:
            return IntentResponse.success("Player removed from blacklist")


@BukkitEventManager.on(ChangePlayerWhitelistStatusAtGameIntent)
async def on_whitelist_request(minestrike: MineStrike, event: ChangePlayerWhitelistStatusAtGameIntent):

    manager = Player.of(event.manager)
    player = Player.of(event.player)
    game = Game.of(event.game)

    if None in [manager, player, game]:
        return IntentResponse.failure("Invalid intent request")

    if not manager.has_perm(Permission.BMS.Games.Manager.Whitelist):
        return IntentResponse.failure("You don't have permission to manage game whitelist")

    dry_run = False

    if event.isWhitelisted:
        if player not in game.whitelist:
            game.whitelist.append(player)
        else:
            dry_run = True
    else:
        try:
            game.whitelist.remove(player)
        except ValueError:
            dry_run = True

    Session().commit()

    # propagate whitelist change
    await minestrike.update_game(game)

    if dry_run:
        if event.isWhitelisted:
            return IntentResponse.success("Player already whitelisted")
        else:
            return IntentResponse.success("Player already not on whitelist")
    else:
        if event.isWhitelisted:
            return IntentResponse.success("Player whitelisted")
        else:
            return IntentResponse.success("Player removed from whitelist")


@BukkitEventManager.on(PlayerGenerateCodeIntent)
async def on_player_generated_code(minestrike: MineStrike, event: PlayerGenerateCodeIntent):
    print("on_player_generated_code", event)

    player = Player.of(event.player)

    if player is None:
        return

    code = random.randint(100000, 999999)

    player.verification_code = code
    Session().commit()

    return IntentResponse.success(
        f"Your verification code is {code}"
    )


@BukkitEventManager.on(CreateGameIntentEvent)
async def on_game_create_request(minestrike: MineStrike, event: CreateGameIntentEvent):

    print("on_game_create_request")

    player = Player.of(event.player)

    if player is not None and not has_permission(player, Permission.BMS.Games.Create):
        return IntentResponse.failure(
            "You don't have permission to create games"
        )

    mode = Game.Mode.to_code(event.mode)

    if mode is None:
        return IntentResponse.failure(
            f"Unknown game mode {event.mode}"
        )

    if event.mapName is None:
        mode_tags = {
            Game.Mode.PUB: [Map.Tag.Competitive],
            Game.Mode.GUNGAME: [Map.Tag.GunGame],
            Game.Mode.DEATHMATCH: [Map.Tag.Competitive],
            Game.Mode.DUEL: [Map.Tag.Duel],
        }
        game_map = Map.random(tags=mode_tags.get(mode))
    else:
        stmt = select(Map).where(Map.name == event.mapName)
        game_map = Session().exec(stmt).one_or_none()

    print("game_map", game_map)

    if not game_map:
        return IntentResponse.failure(
            f"Unknown map {event.mapName}"
        )

    game = await create_game(
        game_map=game_map,
        mode=mode,
        player=player,
    )
    print("created game", game)

    # update server object effectively updating list of games
    await minestrike.update_server()

    return IntentResponse.success(
        f"Game created, it's ID is {game.id}",
        game_id=game.id,
    )


@BukkitEventManager.on(PlayerJoinGameIntentEvent)
async def on_player_request_join_game(minestrike: MineStrike, event: PlayerJoinGameIntentEvent):

    print("player join game intent:", event.game.obj_id)

    game: Game = Game.of(event.game)

    player: Player = Player.of(event.player)

    safe_send(
        f"Player {player.username} has requested to join game {game.id} "
        f"(team {event.team}), spectates: {event.spectate}"
    )

    team = event.team

    print("game", game.id, "player", player.id, "team", team)

    # TODO: optionally save player join game event?

    roster = None

    if not event.spectate:
        # adhere to match teams
        if game.match is not None:
            match_team = game.match.get_player_team(player)
            if match_team is not None:
                if match_team == game.match.team_one:
                    roster = game.team_a
                elif match_team == game.match.team_two:
                    roster = game.team_b
                else:
                    print("match team does not match")

        # rejoin same team
        if not game.get_config_var(Game.ConfigField.AUTO_TEAM_BALANCE):
            roster = game.get_player_team(player)
            if roster:
                print("joining pre-defined roster", roster.name)

        if not roster:
            if team is not None:
                roster = game.get_team(team)
                print("joining requested team", team)
            else:
                roster = find_team_for_player(game, player)
                print("found best match for player: ", roster.name)

    join_with_status = PlayerSession.Status.PARTICIPATING

    if event.spectate:
        join_with_status = PlayerSession.Status.SPECTATOR

    can_join, error_msg = player.can_join_game(
            game=game,
            roster=roster,
            status=join_with_status,
    )

    if not can_join:
        print(f"player can't join game: {error_msg}")

        safe_send(
            f"Player {player.username} denied join: {error_msg}"
        )

        return IntentResponse.failure(
            f"Cannot join game {game.id}: {error_msg}"
        )

    print("player can join game")

    await minestrike.join_game(
        game=game,
        player=player,
        status=join_with_status,
        roster=roster
    )

    print("player joined game")

    return IntentResponse.success(
        "You joined the game"
    )


@BukkitEventManager.on(PlayerTeamChangeIntentEvent)
async def on_player_request_team_change(minestrike: MineStrike, event: PlayerTeamChangeIntentEvent):

    game = Game.of(event.game)
    player = Player.of(event.player)
    team = event.team  # T / CT
    other_team = "T" if team == "CT" else "CT"

    roster = game.get_team(team)

    session = game.get_session(player)
    session.roster = roster

    # todo: just an idea, i could modify save method to return a coroutine
    #  that is resolved when bukkit confirms handling
    Session().commit()

    await minestrike.update_session(session)
    await minestrike.update_roster(roster)
    await minestrike.update_roster(game.get_team(other_team))


@BukkitEventManager.on(PreGameEndEvent)
async def on_game_end(minestrike: MineStrike, event: PreGameEndEvent):

    game = Game.of(event.game)

    if None not in (event.looser, event.winner):
        winner = InGameTeam.of(event.winner)
        looser = InGameTeam.of(event.looser)

        game.winner = winner

        if game.has_plugin("RankedPlugin"):
            win, loose = compute_elo(winner, looser)

            winner.award_elo(win)

            win, loose = compute_elo(looser, winner)

            looser.deduct_elo(loose)

    game.status = Game.Status.FINISHED
    Session().commit()


@BukkitEventManager.on(GameStartedEvent)
async def on_game_start(minestrike: MineStrike, event: GameStartedEvent):
    game = Game.of(event.game)
    game.status = Game.Status.STARTED
    game.started_at = datetime.now()

    # delete all sessions with AWAY status from the game
    for session in game.sessions:
        if session.state == PlayerSession.State.AWAY:
            Session().delete(session)

    Session().commit()


@BukkitEventManager.on(PlayerJoinServerEvent)
async def on_player_join_server(minestrike: MineStrike, event: PlayerJoinServerEvent):
    print("Player", event.player, "joined server")
    player = Player.of(event.player)

    player.in_server = True
    Session.commit()

    safe_send(
        f"Player {player.username} has joined the server"
    )


@BukkitEventManager.on(PlayerLeaveServerEvent)
async def on_player_leave_server(minestrike: MineStrike, event: PlayerLeaveServerEvent):
    player: Player = Player.of(event.player)

    player.in_server = False
    player.last_seen = datetime.now()

    session = player.get_active_session()

    # if player was in game, leave it
    if session:
        session.state = PlayerSession.State.AWAY

    Session().commit()

    safe_send(
        f"Player {player.username} has left the server"
    )


@BukkitEventManager.on(RoundWinEvent)
async def on_round_win(minestrike: MineStrike, event: RoundWinEvent):

    game = Game.of(event.game)
    winner = InGameTeam.of(event.winner)
    looser = InGameTeam.of(event.looser)

    stmt = select(Round).where(
        Round.game_id == game.id,
        Round.number == event.roundNumber
    )

    game_round = Session().exec(stmt).one_or_none()

    if game_round is None:
        game_round = Round(
            game_id=game.id,
            number=event.roundNumber,
            winner=winner,
            win_reason=event.reason
        )
        Session().add(game_round)
        Session().commit()
        Session().refresh(game_round)
    else:
        game_round.winner = winner
        Session().commit()


@BukkitEventManager.on(PlayerDeathEvent)
async def on_player_death(minestrike: MineStrike, event: PlayerDeathEvent):

    game = Game.of(event.game)
    damagee = Player.of(event.damagee)
    damager = Player.of(event.damager)

    if event.round == -1:
        print("Warmup", event)
        return

    stmt = select(Round).where(
        Round.game_id == game.id,
        Round.number == event.round
    )

    game_round = Session().exec(stmt).one_or_none()

    if game_round is None:

        game_round = Round(
            game_id=game.id,
            number=event.round,
        )
        Session().add(game_round)
        Session().commit()
        Session().refresh(game_round)

    game_event = GamePlayerEvent(
        game_id=game.id,
        player_id=damagee.id,
        event=GamePlayerEvent.Type.DEATH,
        round_id=game_round.id,
        is_ct=game.get_player_team(damagee).is_ct,
        meta={
            "damage_source": event.damageSource,  # weapon name / grenade name
            "damage_type": event.reason,  # fire, grenade, gun, etc
            "modifiers": event.modifiers,  # headshot, blinded, wallbangPenalty, etc
        }
    )

    Session().add(game_event)
    Session().commit()

    if damager:
        game_event = GamePlayerEvent(
            game_id=game.id,
            player_id=damager.id,
            event=GamePlayerEvent.Type.KILL,
            round_id=game_round.id,
            is_ct=game.get_player_team(damager).is_ct,
            meta={
                "damage_source": event.damageSource,  # weapon name / grenade name
                "damage_type": event.reason,  # fire, grenade, gun, etc
                "modifiers": event.modifiers,  # headshot, blinded, wallbangPenalty, etc
            }
        )

        Session().add(game_event)
        Session().commit()
