import logging
import random
from enum import Enum
from typing import Optional

from sqlalchemy import func
from sqlmodel import select

from events.schemas.internal import PlayerLeftGame, PlayerRosterChange, PlayerStatusChange, PlayerJoinGame
from models import Match, InGameTeam, PlayerSession, Game, Player, MatchTeam, Map, Session
from events.internal import internalHandler
from schemas.game import GamePlugin
from services.minestrike import MineStrike


PluginMap = {
    Game.Mode.PUB: [GamePlugin.DefusalPlugin, GamePlugin.WarmUpPlugin],
    Game.Mode.COMPETITIVE: [GamePlugin.DefusalPlugin, GamePlugin.WarmUpPlugin, GamePlugin.WhitelistPlugin, GamePlugin.CompetitivePlugin],
    Game.Mode.DUEL: [GamePlugin.DuelPlugin, GamePlugin.WarmUpPlugin],
    Game.Mode.RANKED: [GamePlugin.DefusalPlugin, GamePlugin.RankedPlugin, GamePlugin.WarmUpPlugin, GamePlugin.WhitelistPlugin, GamePlugin.CompetitivePlugin],
    Game.Mode.PRACTICE: [GamePlugin.TargetPracticePlugin],
    Game.Mode.DEATHMATCH: [GamePlugin.DeathmatchPlugin, GamePlugin.WarmUpPlugin],
    Game.Mode.GUNGAME: [GamePlugin.WarmUpPlugin, GamePlugin.GunGamePlugin],
}


@internalHandler.on("MapPickDone")
async def on_map_pick_done(match: Match, payload):

    print("Map pick done")

    game_meta = match.game_meta

    # create games with maps from map pick
    for map_pick in sorted(match.map_pick_process.picked, key=lambda pick: pick.id):

        print(f"Create game for map_pick {map_pick.id}")

        if match.team_one:
            igt_a = InGameTeam.from_match_team(match.team_one, is_ct=True)
        else:
            # Ranked games don't have teams but still use map picks.
            # TODO: perhaps I should do ranked magic here?
            #  it doesn't look right to create team for comp games here
            #  but for ranked separately
            igt_a = InGameTeam(starts_as_ct=True, is_ct=True)
            Session.add(igt_a)
            Session.commit()
            Session.refresh(igt_a)

        if match.team_two:
            igt_b = InGameTeam.from_match_team(match.team_two, is_ct=False)
        else:
            igt_b = InGameTeam(starts_as_ct=False, is_ct=False)
            Session.add(igt_b)
            Session.commit()
            Session.refresh(igt_b)

        game = Game(
            map_id=map_pick.map.id,
            team_a_id=igt_a.id,
            team_b_id=igt_b.id,
            plugins=PluginMap[game_meta['mode']],
            mode=game_meta['mode'],
            is_whitelisted=True
        )

        game.config_overrides = {**game.config_overrides, **game_meta.get('config_overrides', {})}

        Session.add(game)
        Session.commit()

        match.games.append(game)

        # add players to in-game team
        for player in match.team_one.players:
            sess = PlayerSession(
                player_id=player.id,
                game_id=game.id,
                roster_id=igt_a.id,
                state=PlayerSession.State.AWAY,
                status=PlayerSession.Status.PARTICIPATING,
            )
            Session.add(sess)
            Session.commit()

        for player in match.team_two.players:
            sess = PlayerSession(
                player_id=player.id,
                game_id=game.id,
                roster_id=igt_b.id,
                state=PlayerSession.State.AWAY,
                status=PlayerSession.Status.PARTICIPATING,
            )
            Session.add(sess)
            Session.commit()

        # only participants are allowed
        game.whitelist.extend([*match.team_one.players, *match.team_two.players])
        Session.commit()


def find_team_for_player(game: Game, player: Player) -> InGameTeam:
    """
    Find team for player in given game. Doesn't check if player can join the game,
    only tries its best to find a better option. Does consider game options, like
    team auto balance option.
    """

    match: Match = game.match

    roster = None

    # If player is supposed to participate in match, respect team choice
    if match:
        match_team: Optional[MatchTeam] = match.get_player_team(player)

        if match_team == match.team_one:
            roster = game.team_a
        elif match_team == match.team_two:
            roster = game.team_b

    # If roster wasn't found, see if player already was on team
    # roster = roster or game.get_player_team(player)

    if not roster:
        # if still no luck, just put player on team with less players
        roster = game.get_emptier_team(player)
    else:
        # if roster was found, but it is overfilled,
        # put player on team with fewer players, unless config says otherwise
        team_overpopulated = len(roster.active_sessions()) > len(game.get_emptier_team().active_sessions()) + 1
        if game.get_config_var(Game.ConfigField.AUTO_TEAM_BALANCE) and team_overpopulated:
            roster = game.get_emptier_team(player)

    return roster


def team_auto_balance(game: Game) -> bool:

    team_a = game.team_a
    team_b = game.team_b

    if team_a.players.count() > team_b.players.count() + 1:
        # take random player from team A and put them to team B
        player = random.choice(team_a.players.all())
        team_a.players.remove(player)
        team_b.players.add(player)
        return True

    elif team_b.players.count() > team_a.players.count() + 1:
        # take random player from team B and put them to team A
        player = random.choice(team_b.players.all())
        team_b.players.remove(player)
        team_a.players.add(player)
        return True

    return False


async def create_game(game_map: Map | None, mode: Game.Mode, player: Player = None):
    """
        Create game with given map and mode.
    """
    team_a = InGameTeam(starts_as_ct=True, is_ct=True)
    team_b = InGameTeam(starts_as_ct=False, is_ct=False)

    Session().add(team_a)
    Session().add(team_b)
    Session().commit()

    if game_map is None:
        map_count = select(Map.id)

        ids = Session().exec(map_count).all()

        if not ids:
            return

        map_id = random.choice(ids)
        stmt = select(Map).where(Map.id == map_id)
        game_map = Session().exec(stmt).first()

    plugins = PluginMap[mode]

    is_whitelisted = GamePlugin.WhitelistPlugin in plugins

    game = Game(
        map_id=game_map.id,
        mode=mode,
        plugins=plugins,
        is_whitelisted=is_whitelisted,
        status=Game.Status.NOT_STARTED,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
    )

    Session().add(game)
    Session().commit()

    if player is not None and is_whitelisted:
        game.whitelist.append(player)

    Session().commit()

    return game
