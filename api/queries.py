from __future__ import annotations


from typing import Any

from blazelink import TableManager
from blazelink.models import BlazeConfig, DataAccessor, BlazeContext, ScalarQuery, ListQuery, Table, computed, ObjectId, \
    Struct, VirtualTable, BlazeField, Page
from sqlalchemy import func, case, and_
from sqlalchemy.orm import aliased
from sqlmodel import select, col

from models import *


class SqlalchemyAccessor(DataAccessor):

    async def get_by_pk(self, context: BlazeContext, model, pk):
        q = select(model).where(model.id == pk)
        res = context.session.exec(q)
        res = res.first()
        return res

    async def execute_query(self, context: BlazeContext, query) -> Any:
        if isinstance(query, ScalarQuery):
            res = context.session.exec(query.query)
            return res.scalar()
        elif isinstance(query, ListQuery):
            return (context.session.exec(query.query)).all()
        else:
            assert False


def context_factory(__info):
    db = __info.context["database_session"]

    request = __info.context.get("request")
    sess_id = request.headers.get('session_id')
    auth_id = request.headers.get('Authorization')
    session = select(AuthSession).where(AuthSession.session_key == auth_id)
    session = db.exec(session).first()

    return BlazeContext(
        user=session.player if session else None,
        request=request,
        session_id=sess_id,
        session=db
    )


table_manager = TableManager(BlazeConfig(orm_class=float, data_accessor=SqlalchemyAccessor(), context_factory=context_factory))


@table_manager.table
class TeamTable(Table[Team]):
    id: int
    full_name: str
    short_name: str
    active: bool
    location: int
    elo: int
    owner: PlayerTable
    players: list[PlayerTable]


@table_manager.table
class PlayerPermissionTable(Table[PlayerPermission]):
    id: int
    name: str


@table_manager.table
class RoleTable(Table[Role]):
    id: int
    name: str
    tab_prefix: str
    tab_color: str
    chat_prefix: str
    chat_suffix: str
    chat_color: str
    chat_message_color: str
    team_override_color: bool
    permissions: list[PlayerPermissionTable]


@table_manager.table
class PlayerTable(Table[Player]):
    id: int
    uuid: str
    team: TeamTable
    role: RoleTable
    elo: int
    location: int
    verified_at: datetime
    username: str
    last_seen: str

    in_server: bool
    active_game: GameTable
    permissions: list[PlayerPermissionTable]

    @computed
    def games_played(self) -> int:

        stmt = select(func.count(PlayerSession.id)).where(PlayerSession.player_id == self.get_model().id)
        res = self.context.session.exec(stmt)
        return res.first()

    @computed
    def winrate(self) -> int:
        stmt = select(func.count(PlayerSession.id)).where(PlayerSession.player_id == self.get_model().id)
        res = self.context.session.exec(stmt)
        total_games = res.first()

        stmt = (
                select(func.count(Game.id))
                .join(PlayerSession)
                .where(PlayerSession.roster_id == Game.winner_id)
                .where(PlayerSession.player_id == self.get_model().id)
        )

        res = self.context.session.exec(stmt)
        wins = res.first()

        return int(wins / (total_games or 1) * 10000)


@table_manager.table
class MapTable(Table[Map]):
    id: int
    display_name: str
    name: str


@table_manager.table
class EventTable(Table[Event]):
    id: int
    name: str


@table_manager.table
class InGameTeamTable(Table[InGameTeam]):
    id: int
    name: str
    players: list[PlayerTable]
    starts_as_ct: bool
    is_ct: bool


@table_manager.table
class MatchTeamTable(Table[MatchTeam]):
    id: int
    name: str
    team: TeamTable
    players: list[PlayerTable]

    def __dependencies__(self):
        return [
            ObjectId(
                entity="MatchPlayers",
                obj_id=None,
            )
        ]


@table_manager.table
class MapPIckTable(Table[MapPick]):

    id: int
    map: MapTable
    selected_by: MatchTeamTable
    picked: bool


@table_manager.table
class MapPickProcessTable(Table[MapPickProcess]):
    id: int
    finished: bool
    next_action: MapPickProcess.Action
    picker_a: PlayerTable
    picker_b: PlayerTable
    turn: PlayerTable
    maps: list[MapPIckTable]
    match: MatchTable

    def __dependencies__(self):
        return [
            ObjectId(
                entity="MapPick",
                obj_id=None
            )
        ]


@table_manager.table
class MatchTable(Table[Match]):
    id: int

    team_one: MatchTeamTable
    team_two: MatchTeamTable

    map_pick_process: MapPickProcessTable
    name: str
    event: EventTable
    map_count: int
    games: list[GameTable]

    def __dependencies__(self):
        return [
            ObjectId(
                entity="Game",
                obj_id=None,
            )
        ]


@table_manager.type
class Config(Struct):

    overrides: str

    def __init__(self, overrides: str):
        self.overrides = overrides


@table_manager.table
class PlayerSessionTable(Table[PlayerSession]):
    id: int
    player: PlayerTable
    player_id: int
    game: GameTable
    game_id: int
    roster: InGameTeamTable
    roster_id: int
    status: int
    state: int


@table_manager.table
class GameTable(Table[Game]):

    id: int
    map: MapTable

    # Game status
    status: Game.Status

    # Match
    match: MatchTable

    # Teams
    team_a: InGameTeamTable

    team_b: InGameTeamTable

    winner: InGameTeamTable

    mode: Game.Mode

    whitelist: list[PlayerTable]
    blacklist: list[PlayerTable]

    plugins: list[str]

    sessions: list[PlayerSessionTable]

    created_at: str
    started_at: str

    @computed
    def config(self) -> Config:
        return Config(json.dumps(self.get_model().config_overrides))

    @computed
    def score_a(self) -> int:
        game_model = self.get_model()
        stmt = select(func.count(Round.id)).where(Round.game_id == game_model.id, Round.winner_id == game_model.team_a_id)
        return self.context.session.execute(stmt).scalar()

    @computed
    def score_b(self) -> int:
        game_model = self.get_model()
        stmt = select(func.count(Round.id)).where(Round.game_id == game_model.id, Round.winner_id == game_model.team_b_id)
        return self.context.session.execute(stmt).scalar()


@table_manager.type
class PlayerStat(Struct):
    kills: int
    deaths: int
    assists: int
    hs: int
    player: PlayerTable

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self._values = kwargs


@table_manager.table
class GameStatsView(VirtualTable):

    def __init__(self, identifier: ObjectId, context: BlazeContext):
        game_team_obj = identifier.find_dependency('InGameTeam')
        self.game_team_id = game_team_obj.obj_id
        game_team = select(InGameTeam).where(InGameTeam.id == self.game_team_id)
        game_team = context.session.exec(game_team).first()
        self.game = game_team.game

    @computed
    def stats(self) -> list[PlayerStat]:
        kill_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.KILL, 1),
                (GamePlayerEvent.event != GamePlayerEvent.Type.KILL, 0)
            ]
        )
        death_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.DEATH, 1),
                (GamePlayerEvent.event != GamePlayerEvent.Type.DEATH, 0)
            ]
        )

        assists_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.ASSIST, 1),
                (GamePlayerEvent.event != GamePlayerEvent.Type.ASSIST, 0)
            ]
        )

        hs_counter = case(
            [
                (GamePlayerEvent.meta['modifiers']['headshot'].astext == "true", 1),
                (GamePlayerEvent.meta['modifiers']['headshot'].astext != "true", 0)
            ]
        )

        stmt = (
            select(
                func.coalesce(func.sum(kill_counter), 0).label('kills'),
                func.coalesce(func.sum(death_counter), 0).label('deaths'),
                func.coalesce(func.sum(assists_counter), 0).label('assists'),
                func.coalesce(func.sum(hs_counter), 0).label('hs'),
                PlayerSession.player_id.label('player_id')
            )
            .select_from(InGameTeam)
            .join(
                PlayerSession,
                onclause=PlayerSession.roster_id == InGameTeam.id
            )
            .join(
                GamePlayerEvent,
                isouter=True,
                onclause=(
                    and_(
                        GamePlayerEvent.game_id == self.game.id,
                        GamePlayerEvent.player_id == PlayerSession.player_id
                    )
                )
            )
            .where(
                InGameTeam.id == self.game_team_id,
                or_(
                    GamePlayerEvent.game_id == self.game.id,
                    GamePlayerEvent.game_id == None,
                )
            )
            .join(
                Player,
                onclause=Player.id == PlayerSession.player_id
            )
            .group_by(
                PlayerSession.player_id
            )
        )

        stats = self.context.session.execute(stmt).all()

        stat_structs = []
        for stat in stats:
            player = self.context.session.get(Player, stat.player_id)
            stat = PlayerStat(
                kills=stat.kills,
                deaths=stat.deaths,
                assists=stat.assists,
                hs=stat.hs,
                player=player
            )
            stat.context = self.context
            stat_structs.append(stat)

        return stat_structs


@table_manager.table
class Server(VirtualTable):

    def __init__(self, identifier: ObjectId, context: BlazeContext):
        self.identifier = identifier

    @computed
    async def games(self) -> list[GameTable]:
        stmt = select(Game).where(col(Game.status).not_in([Game.Status.FINISHED, Game.Status.TERMINATED]))
        return (self.context.session.exec(stmt)).all()


@table_manager.table
class TopTeamView(VirtualTable):

    id: int
    full_name: str
    short_name: str
    active: bool
    location: int
    elo: int
    owner: PlayerTable
    players: list[PlayerTable]

    def __init__(self, identifier: ObjectId):
        self.identifier = identifier

    @classmethod
    async def resolve(cls, __parent, __field: Optional[BlazeField], __context: BlazeContext, __config: BlazeConfig, **extra_args):
        stmt = select(Team).order_by(col(Team.elo).desc()).limit(1).where(Team.active == True)
        res = __context.session.exec(stmt).first()
        return TeamTable(res, __context)


@table_manager.table
class TopPlayersView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    async def players(self) -> Page[PlayerTable]:
        stmt = select(Player).order_by(col(Player.elo).desc()).limit(10)
        res = self.context.session.exec(stmt).all()
        return res


@table_manager.table
class GameModeStatsView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def ranked_online(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.RANKED, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()

    @computed
    def pubs_online(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.PUB, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()

    @computed
    def duels_online(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.DUEL, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()

    @computed
    def deathmatch_online(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.DEATHMATCH, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()

    @computed
    def gungame_online(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.GUNGAME, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()

    @computed
    def ranked_games(self) -> int:
        stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.RANKED, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).first()

    @computed
    def pubs_games(self) -> int:
        stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.PUB, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).first()

    @computed
    def duels_games(self) -> int:
        stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.DUEL, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).first()

    @computed
    def deathmatch_games(self) -> int:
        stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.DEATHMATCH, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).first()

    @computed
    def gungame_games(self) -> int:
        stmt = select(func.count(Game.id)).where(Game.mode == Game.Mode.GUNGAME, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).first()


@table_manager.table
class QueueTable(Table[PlayerQueue]):
    id: int

    type: PlayerQueue.Type
    size: int

    locked: bool
    confirmed: bool

    captain_a: PlayerTable
    captain_b: PlayerTable

    match: MatchTable

    players: list[PlayerTable]
    confirmed_players: list[PlayerTable]

    @computed
    def confirmed_by_me(self) -> bool:
        queue: PlayerQueue = self.get_model()
        return self.context.user in queue.confirmed_players


@table_manager.table
class RankedView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def queues(self) -> list[QueueTable]:
        stmt = select(PlayerQueue).where(PlayerQueue.type == PlayerQueue.Type.RANKED).order_by(PlayerQueue.locked == True, col(PlayerQueue.id).desc()).limit(10)
        return self.context.session.exec(stmt).all()

    @computed
    def my_queue(self) -> QueueTable:
        stmt = select(PlayerQueue).where(PlayerQueue.type == PlayerQueue.Type.RANKED, PlayerQueue.players.any(id=self.context.user.id))
        return self.context.session.exec(stmt).first()


@table_manager.table
class PubsView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def games(self) -> list[GameTable]:
        stmt = select(Game).where(Game.mode == Game.Mode.PUB, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).all()

    @computed
    def online_player_count(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.PUB, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()


@table_manager.table
class GunGameView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def games(self) -> list[GameTable]:
        stmt = select(Game).where(Game.mode == Game.Mode.GUNGAME, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).all()

    @computed
    def online_player_count(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.GUNGAME, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()


@table_manager.table
class DeathMatchView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def games(self) -> list[GameTable]:
        stmt = select(Game).where(Game.mode == Game.Mode.DEATHMATCH, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).all()

    @computed
    def online_player_count(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.DEATHMATCH, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()


@table_manager.table
class DuelsView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    def games(self) -> list[GameTable]:
        stmt = select(Game).where(Game.mode == Game.Mode.DUEL, Game.status.in_([Game.Status.NOT_STARTED, Game.Status.STARTED]))
        return self.context.session.exec(stmt).all()

    @computed
    def online_player_count(self) -> int:
        stmt = select(func.count(PlayerSession.id)).join(Game).where(Game.mode == Game.Mode.DUEL, PlayerSession.state == PlayerSession.State.IN_GAME)
        return self.context.session.exec(stmt).first()


@table_manager.table
class PlayersView(VirtualTable):

    def __init__(self, identifier, context):
        pass

    @computed
    async def players(self, elo: int = None, games_played: int = None, winrate: int = None, query: str = None) -> Page[PlayerTable]:

        stmt = select(Player)

        if winrate is not None:
            if winrate == -1:
                stmt = stmt.group_by(Player.id).join(
                    PlayerSession,
                    isouter=True,
                    onclause=PlayerSession.player_id == Player.id
                ).join(
                    Game,
                    isouter=True,
                ).order_by(
                    func.coalesce(
                        func.sum(
                            case(
                                [(Game.winner_id == PlayerSession.roster_id, 1)],
                                else_=0
                            ) * 100
                        )
                        /
                        func.nullif(
                            func.sum(
                                case(
                                    [(PlayerSession.roster_id != None, 1), ],
                                    else_=0
                                )
                            ),
                            0
                        ),
                        0
                    ).desc()
                )
            elif winrate == 1:
                stmt = stmt.group_by(Player.id).join(
                    PlayerSession,
                    isouter=True,
                    onclause=PlayerSession.player_id == Player.id
                ).join(
                    Game,
                    isouter=True,
                ).order_by(
                    func.coalesce(
                        func.sum(
                            case(
                                [(Game.winner_id == PlayerSession.roster_id, 1)],
                                else_=0
                            ) * 100
                        )
                        /
                        func.nullif(
                            func.sum(
                                case(
                                    [(PlayerSession.roster_id != None, 1), ],
                                    else_=0
                                )
                            ),
                            0
                        ),
                        0
                    ).asc()
                )

        if games_played is not None:

            if not winrate:
                stmt = stmt.group_by(Player.id).join(PlayerSession, isouter=True, onclause=PlayerSession.player_id == Player.id)

            if games_played == 1:
                stmt = stmt.order_by(
                    func.sum(
                        case(
                            [
                                (PlayerSession.id != None, 1),
                            ],
                            else_=0
                        )
                    ).desc()
                )
            elif games_played == -1:
                stmt = stmt.order_by(
                    func.sum(
                        case(
                            [
                                (PlayerSession.id != None, 1),
                            ],
                            else_=0
                        )
                    ).asc()
                )

        if elo == 1:
            stmt = stmt.order_by(col(Player.elo).desc())
        elif elo == -1:
            stmt = stmt.order_by(col(Player.elo).asc())

        if query:
            stmt = stmt.where(
                or_(
                    col(Player.username).ilike(f'%{query}%'),
                )
            )

        return self.context.session.exec(stmt).all()


@table_manager.table
class PlayerPerformanceAggregatedView(VirtualTable):

    def __init__(self, identifier: ObjectId, context: BlazeContext):
        player_obj = identifier.find_dependency('Player')
        self.player_id = player_obj.obj_id

        kill_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.KILL, 1),
            ],
            else_=0
        )
        death_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.DEATH, 1),
            ],
            else_=0
        )

        assists_counter = case(
            [
                (GamePlayerEvent.event == GamePlayerEvent.Type.ASSIST, 1),
            ],
            else_=0
        )

        hs_counter = case(
            [
                (
                    and_(
                        GamePlayerEvent.event == GamePlayerEvent.Type.KILL,
                        GamePlayerEvent.meta['modifiers']['headshot'].astext == "true"
                    ), 1
                ),
            ],
            else_=0
        )

        stmt = (
            select(
                func.sum(kill_counter).label('kills'),
                func.sum(death_counter).label('deaths'),
                func.sum(assists_counter).label('assists'),
                func.sum(hs_counter).label('hs'),
            )
            .select_from(GamePlayerEvent)
            .where(
                GamePlayerEvent.player_id == self.player_id,
            )
        )

        self.stats = context.session.execute(stmt).first()

    @computed
    async def kills(self) -> int:
        return self.stats.kills or 0

    @computed
    async def deaths(self) -> int:
        return self.stats.deaths or 0

    @computed
    async def assists(self) -> int:
        return self.stats.assists or 0

    @computed
    async def hs(self) -> int:
        return self.stats.hs or 0

    @computed
    async def games_played(self) -> int:
        stmt = select(func.count(InGameTeam.id)).join(PlayerSession).where(
            PlayerSession.player_id == self.player_id
        )
        return self.context.session.execute(stmt).scalar()

    @computed
    async def games_won(self) -> int:
        stmt = (
            select(func.count(InGameTeam.id)).join(PlayerSession)
            .join(
                Game,
                onclause=or_(
                    Game.team_a_id == InGameTeam.id,
                    Game.team_b_id == InGameTeam.id,
                )
            )
            .where(
                Game.winner_id == InGameTeam.id,
                PlayerSession.player_id == self.player_id,
            )
        )
        return self.context.session.execute(stmt).scalar()

    @computed
    async def ranked_games_played(self) -> int:
        stmt = (
            select(func.count(InGameTeam.id)).join(PlayerSession)
            .join(
                Game,
                onclause=or_(
                    Game.team_a_id == InGameTeam.id,
                    Game.team_b_id == InGameTeam.id,
                )
            )
            .where(
                PlayerSession.player_id == self.player_id,
                Game.mode == Game.Mode.RANKED,
            )
        )
        return self.context.session.execute(stmt).scalar()

    @computed
    async def ranked_games_won(self) -> int:
        stmt = (
            select(func.count(InGameTeam.id)).join(PlayerSession)
            .join(
                Game,
                onclause=or_(
                    Game.team_a_id == InGameTeam.id,
                    Game.team_b_id == InGameTeam.id,
                )
            )
            .where(
                PlayerSession.player_id == self.player_id,
                Game.mode == Game.Mode.RANKED,
                Game.winner_id == InGameTeam.id,
            )
        )
        return self.context.session.execute(stmt).scalar()

    @computed
    async def player(self) -> PlayerTable:
        stmt = select(Player).where(Player.id == self.player_id).limit(1)
        player = self.context.session.execute(stmt).one_or_none()[0]
        return player

    @computed
    async def recent_games(self) -> Page[GameTable]:
        team_a = aliased(InGameTeam)
        team_b = aliased(InGameTeam)

        stmt = (
            select(Game)
            .join(team_a, onclause=(team_a.id == Game.team_a_id))
            .join(team_b, onclause=(team_b.id == Game.team_b_id))
            .join(
                PlayerSession, onclause=(
                    and_(
                        PlayerSession.game_id == Game.id,
                        or_(
                            PlayerSession.roster_id == team_a.id,
                            PlayerSession.roster_id == team_b.id
                        )
                    )
                )
            )
            .where(PlayerSession.player_id == self.player_id)
            .order_by(col(Game.created_at).desc())
        )

        return self.context.session.exec(stmt).all()

    @computed
    async def games(self, mode: str = None, won: bool = None) -> Page[GameTable]:
        team_a = aliased(InGameTeam)
        team_b = aliased(InGameTeam)

        stmt = (
            select(Game)
            .join(team_a, onclause=(team_a.id == Game.team_a_id))
            .join(team_b, onclause=(team_b.id == Game.team_b_id))
            .join(
                PlayerSession, onclause=(
                    and_(
                        PlayerSession.game_id == Game.id,
                        or_(
                            PlayerSession.roster_id == team_a.id,
                            PlayerSession.roster_id == team_b.id
                        )
                    )
                )
            )
            .where(PlayerSession.player_id == self.player_id)
            .order_by(col(Game.created_at).desc())
        )

        if mode:
            stmt = stmt.where(Game.mode == Game.Mode[mode.upper()])

        if won is not None:
            if won:
                stmt = stmt.where(Game.winner_id == PlayerSession.roster_id)
            else:
                stmt = stmt.where(Game.winner_id != PlayerSession.roster_id)

        return self.context.session.exec(stmt).all()


@table_manager.table
class GamesView(VirtualTable):

    def __init__(self, *args, **kwargs):
        pass

    @computed
    async def games(self) -> Page[GameTable]:
        # query all games newest to latest
        stmt = (
            select(Game)
            .order_by(col(Game.started_at).is_(None), col(Game.started_at).desc(), col(Game.created_at).desc())
        )

        return self.context.session.exec(stmt).all()
