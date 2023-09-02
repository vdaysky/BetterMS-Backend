import random
from typing import Optional

from fastapi import APIRouter

from dependencies import PlayerAuthDependency, GetMineStrike
from models import Player, Match, Game, InGameTeam, PlayerSession, Round, GamePlayerEvent
from schemas.common import ApiResponse
from schemas.game import CreateGame, JoinGame
from exceptions import PermissionError, BadRequestError
from services.game import find_team_for_player

router = APIRouter()


@router.post('/create')
def create_game(data: CreateGame, player: Player = PlayerAuthDependency):

    if not player.has_perm('api.can_create_game'):
        raise PermissionError

    if len(data.match.games) >= data.match.map_count:
        raise BadRequestError('Match already has all games defined')
    
    return Game.objects.create(match=data.match, map=data.map)


@router.get('/testcreate')
async def test_create(pubs: bool = False):

    if not pubs:
        # get random match with players
        match = Match.objects.filter(team_one__players__isnull=False, team_two__players__isnull=False).order_by("?").first()

        team_a = InGameTeam.objects.create(
            name=match.team_one.full_name,
            starts_as_ct=True,
            is_ct=True,
        )

        team_b = InGameTeam.objects.create(
            name=match.team_two.full_name,
            starts_as_ct=False,
            is_ct=False,
        )

        team_a_players = match.team_one.players.all()
        team_b_players = match.team_two.players.all()

    else:
        match = None
        team_a = InGameTeam.objects.create(
            name=None,
            starts_as_ct=True,
            is_ct=True,
        )

        team_b = InGameTeam.objects.create(
            name=None,
            starts_as_ct=False,
            is_ct=False,
        )
        players = Player.objects.filter(is_active=True).order_by("?")[:10]
        team_a_players = players[:5]
        team_b_players = players[5:]

    # create game
    game = Game.objects.create(
        match=match,
        team_b=team_b,
        team_a=team_a,
        mode=Game.Mode.PUB if pubs else Game.Mode.COMPETITIVE,
        plugins=[],
        map=random.choice(['MIRAGE', 'CACHE', 'INFERNO', 'OVERPASS']),
        status=random.choice([Game.Status.NOT_STARTED, Game.Status.FINISHED, Game.Status.STARTED]),
    )

    # create game sessions for every team member
    for player in team_a_players:
        PlayerSession.objects.create(player=player, game=game, roster=team_a, state=PlayerSession.State.IN_GAME, status=PlayerSession.Status.PARTICIPATING)

    for player in team_b_players:
        PlayerSession.objects.create(player=player, game=game, roster=team_b, state=PlayerSession.State.IN_GAME, status=PlayerSession.Status.PARTICIPATING)

    # generate random number of rounds
    rounds = random.randint(0, 30)
    team_one_won = min(rounds, 16)
    team_two_won = rounds - team_one_won

    for i in range(rounds):

        if random.choice([True, False]):
            if team_one_won:
                Round.objects.create(game=game, winner=team_a, number=i)
            else:
                Round.objects.create(game=game, winner=team_b, number=i)
        else:
            if team_two_won:
                Round.objects.create(game=game, winner=team_b, number=i)
            else:
                Round.objects.create(game=game, winner=team_a, number=i)

    game_rounds = game.rounds.all()

    print(f"sessions: {[player for player in game.team_a.sessions.all()] + [player for player in game.team_b.sessions.all()]}")

    # generate events in eaqch round
    for round in game_rounds:
        for i in range(random.randint(0, 20)):
            e = random.choice(['KILL', 'ASSIST', 'DEATH'])

            hs = None
            if e == 'KILL':
                hs = random.choice([True, False])

            GamePlayerEvent.objects.create(
                round=round,
                game=game,
                player=random.choice([player for player in team_a.sessions.all()] + [player for player in team_b.sessions.all()]).player,
                event=e,
                meta={'hs': hs},
                is_ct=random.choice([True, False])
            )

        if random.random() > 0.4:

            GamePlayerEvent.objects.create(
                round=round,
                game=game,
                player=random.choice([player for player in team_a.sessions.all()] + [player for player in team_b.sessions.all()]).player,
                event='BOMB_PLANT',
                is_ct=random.choice([True, False])
            )

            if random.random() > 0.6:
                GamePlayerEvent.objects.create(
                    round=round,
                    game=game,
                    player=random.choice([player for player in team_a.sessions.all()] + [player for player in team_b.sessions.all()]).player,
                    event='BOMB_DEFUSED',
                    is_ct=random.choice([True, False])
                )

    return game.id


@router.post("/join")
async def join(data: JoinGame, player: Player = PlayerAuthDependency, minestrike=GetMineStrike):

    game = Game.of(data.game)

    roster = find_team_for_player(game, player)

    can_join, reason = player.can_join_game(
            game,
            roster=roster,
            status=PlayerSession.Status.PARTICIPATING
    )
    if not can_join:
        return ApiResponse(
            success=False,
            message=f"You can't join this game: {reason}"
        )

    return await minestrike.join_game(
        game,
        player,
        roster=roster,
        status=PlayerSession.Status.PARTICIPATING
    )
