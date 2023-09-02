from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime
from enum import IntEnum, Enum
from typing import Union, Iterable, Optional, List, TypeVar, Type
from uuid import UUID

from sqlalchemy import DateTime, Column, or_
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlmodel import SQLModel, Field, Relationship, select, create_engine
from sqlmodel.orm.session import Session as SQLModelSession

from events.schemas.bukkit import WinReason
from schemas.game import GamePlugin
from schemas.permission import PType
from settings import settings

from schemas.common import ObjectId as ObjIdSchema

engine = create_engine(
    settings.database_url,
    pool_size=200,
    max_overflow=0,
)
session_maker = sessionmaker(engine, expire_on_commit=False, class_=SQLModelSession)


def scope():
    return id(asyncio.current_task())


def other_scope():
    return id(asyncio.current_task())


# GraphQLSession = scoped_session(session_maker, scopefunc=scope)
Session = scoped_session(session_maker, scopefunc=other_scope)


class Location(IntEnum):
    Europe = 1
    NorthAmerica = 2
    NotSet = 0


T = TypeVar("T", bound="ModelBase")


class ModelBase(SQLModel):

    def objectId(self):

        return ObjIdSchema(
            obj_id=self.id,
            entity=self.__class__.__name__,
            dependencies=[]
        )

    @classmethod
    def of(cls: Type[T], identifier: ObjIdSchema) -> T | None:
        if identifier is None:
            return None
        print(f"{cls.__name__} of ({identifier.obj_id})")
        return Session().exec(select(cls).where(cls.id == identifier.obj_id)).first()


class PlayerPermission(ModelBase, table=True):
    __tablename__ = "player_permission"

    id: int | None = Field(primary_key=True)
    name: str = Field(max_length=100)


class PlayerPermissions(ModelBase, table=True):
    id: int | None = Field(primary_key=True)

    __tablename__ = "player_permissions"

    role_id: int = Field(foreign_key="role.id")
    permission_id: int = Field(foreign_key="player_permission.id")


class Player(ModelBase, table=True):
    """ Player in game / user on website """

    id: int | None = Field(primary_key=True)
    uuid: UUID | None = Field()
    team: Team = Relationship(back_populates="players", sa_relationship_kwargs={"foreign_keys": "Player.team_id"})
    team_id: int | None = Field(foreign_key="team.id", nullable=True)
    role: Role = Relationship()
    role_id: int = Field(foreign_key="role.id")
    elo: int = Field(default=200)
    location: Location = Field(default=Location.NotSet)
    username: str = Field(nullable=False)
    verified_at: datetime = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    last_seen: datetime = Field(default=datetime.now(), sa_column=Column(DateTime(timezone=True)))
    password: str = Field(default=None, nullable=True)
    verification_code: int = Field(default=None, nullable=True)

    in_server: bool = Field(default=False)
    # a Little bit of duplication here, but it helps with performance ig
    active_game: Game = Relationship()
    active_game_id: int | None = Field(foreign_key="game.id", nullable=True)

    def has_perm(self, perm, obj=None):
        return self.role is not None and self.role.has_perm(perm)

    def verify(self):
        self.verified_at = datetime.now()

    def is_verified(self):
        return self.verified_at is not None

    def get_owned_team(self):
        return self.teams.first()

    def get_active_session(self) -> Optional[PlayerSession]:
        stmt = select(PlayerSession).where(
            PlayerSession.state == PlayerSession.State.IN_GAME,
            PlayerSession.player == self
        )
        return Session().exec(stmt).first()

    def get_active_game(self) -> Optional[Game]:
        session = self.get_active_session()
        if not session:
            return

        return session.game

    def can_join_game(self, game: Game, roster: Optional[InGameTeam], status: int) -> tuple[bool, str]:
        """ Check whether this player can join given game """

        if game.status in (Game.Status.FINISHED, Game.Status.TERMINATED):
            return False, "Game was already finished"

        # Player is not whitelisted
        if game.is_whitelisted and self.id not in [x.id for x in game.whitelist]:
            logging.info("Player is not whitelisted")
            return False, "You are not whitelisted for this game"

        print("Blacklist check", self.id , [x.id for x in game.blacklist])

        # Player is blacklisted
        if self.id in [x.id for x in game.blacklist]:
            logging.info("Player is blacklisted")
            return False, "You are blacklisted for this game"

        participants = len(game.get_online_sessions(status=PlayerSession.Status.PARTICIPATING))
        max_participants = 10  # game.get_config_var(Game.ConfigField.MAX_PLAYERS)

        # There are no free slots
        if status == PlayerSession.Status.PARTICIPATING and participants >= max_participants:
            logging.info("No free slots")
            return False, "No free slots"

        # Player can't be a coach in this in-game roster
        if status == PlayerSession.Status.COACH and not self.can_coach(roster):
            logging.info("Can't be a coach")
            return False, "You can't be a coach in this game"

        if roster and self in roster.players:
            session = game.get_session(self)
            if session and session.status == status and session.state == PlayerSession.State.IN_GAME:
                return False, "You are already in this game"

        # todo: do we need additional checks here?
        if status == PlayerSession.Status.SPECTATOR:
            return True, ""

        return True, ""

    def can_coach(self, roster: Optional[InGameTeam]) -> bool:

        if not roster:
            return False

        # Game is not match-based
        if roster.match_team is None:
            return False

        # Player is not a member of MatchTeam
        if not roster.match_team.players.filter(id=self.id).exists():
            return False

        return True


class Team(ModelBase, table=True):
    """ Competitive roster of players """

    __tablename__ = "team"

    id: int = Field(primary_key=True)
    short_name: str = Field(max_length=10, unique=True)
    full_name: str = Field(max_length=10, unique=True)
    active: bool = Field(default=True)
    location: Location = Field(default=Location.NotSet)
    elo: int = Field(default=200)
    owner: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "Team.owner_id"})
    owner_id: int = Field(foreign_key="player.id")
    players: List[Player] = Relationship(back_populates="team",
                                         sa_relationship_kwargs={"foreign_keys": "Player.team_id"})


class Invite(ModelBase, table=True):
    """ Invite sent to player to join a team """

    class Status(IntEnum):
        Pending = 0
        Accepted = 1
        Declined = 2

    id: int = Field(primary_key=True)

    player: Player = Relationship()
    player_id: int = Field(foreign_key="player.id")

    team: Team = Relationship()
    team_id: int = Field(foreign_key="team.id")

    status: int = Field(default=Status.Pending)

    @property
    def declined(self):
        return self.status == 0

    @property
    def accepted(self):
        return self.status == 1

    @declined.setter
    def declined(self, v):
        self.status = 0 if v is True else None

    @accepted.setter
    def accepted(self, v):
        self.status = 1 if v is True else None


class PlayerSession(ModelBase, table=True):
    """ Player inside a game """

    class Status(IntEnum):
        """
            Player's status in this game.
            Player can be a coach, can spectate
            or can participate in a game.
        """
        PARTICIPATING = 0
        SPECTATOR = 1
        COACH = 2

    class State(IntEnum):
        """
            Player game session state.
            Even after quitting the game itself player still might be in-game,
            which ensures that player is going to get in that game automatically after rejoin
        """
        IN_GAME = 0  # player is associated with this game
        AWAY = 1  # player once was in the game but left

    id: int | None = Field(primary_key=True)

    player: Player = Relationship()
    player_id: int = Field(foreign_key="player.id")

    game: Game = Relationship(back_populates="sessions")
    game_id: int = Field(foreign_key="game.id")

    roster: InGameTeam = Relationship(back_populates="sessions")
    roster_id: int = Field(foreign_key="in_game_team.id", nullable=True)

    status: PlayerSession.Status = Field()
    state: PlayerSession.State = Field()

    @classmethod
    def get(cls, game, player):
        return PlayerSession.objects.filter(game=game, player=player).first()


# 2 instances per game
class InGameTeam(ModelBase, table=True):
    """
        Group of players inside particular game playing on the same side.
        Can contain AWAY players.
    """

    __tablename__ = "in_game_team"

    id: int | None = Field(primary_key=True)

    # only for team-ish entities (produced from Team or MatchTeam)
    name: str = Field(nullable=True, max_length=32, default=None)

    # reference to MatchTeam that created this InGameTeam, if exists
    # for Ranked/Competitive games (ones having Match) there are usually
    # MatchTeam objects that define who can get into this match.
    match_team: MatchTeam = Relationship()
    match_team_id: int = Field(foreign_key="match_team.id", nullable=True, default=None)

    starts_as_ct: bool = Field()
    is_ct: bool = Field()

    sessions: List[PlayerSession] = Relationship()

    players: List[Player] = Relationship(link_model=PlayerSession)

    def get_current_team(self):
        if self.is_ct:
            return "CT"
        else:
            return "T"

    def active_sessions(self):
        return [
            session for session in self.sessions
            if session.state == PlayerSession.State.IN_GAME
        ]

    def get_players(self):
        return [x.player for x in self.sessions]

    def award_elo(self, elo):
        for player in self.get_players():
            player.elo = player.elo + elo
        Session.commit()

    def deduct_elo(self, elo):
        for player in self.get_players():
            player.elo = max(0, player.elo - elo)
        Session.commit()

    @property
    def game(self):
        statement = select(Game).where(or_(Game.team_a_id == self.id, Game.team_b_id == self.id))
        return Session.execute(statement).scalar_one()

    @classmethod
    def from_match_team(cls, team: MatchTeam, is_ct: bool):
        team_1 = InGameTeam(
            name=team.name,
            starts_as_ct=is_ct,
            is_ct=is_ct,
            match_team=team
        )
        Session.add(team_1)
        Session.commit()
        Session.refresh(team_1)

        # keep in mind that I can't fill this team yet

        return team_1


class MatchPlayers(ModelBase, table=True):
    """ Many-to-many relationship between MatchTeam and Player """

    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    match_id: int = Field(foreign_key="match_team.id")


class MatchTeam(ModelBase, table=True):
    """
        Player set that can join in-game team.
    """

    __tablename__ = "match_team"

    # NOTE:
    # match is accessible through `match` reverse relation
    # in-game team is accessible through `in_game_team`

    id: int | None = Field(primary_key=True)

    # display name
    name: str = Field(max_length=32, nullable=True, default=None)

    # Real team this match team is based on
    team: Team | None = Relationship()
    team_id: int | None = Field(foreign_key="team.id", nullable=True)

    players: List[Player] = Relationship(link_model=MatchPlayers)

    @classmethod
    def from_team(cls, team: Team):
        return MatchTeam.objects.create(
            name=team.short_name,
            team=team,
        )

    @property
    def match(self) -> Match:
        stmt = select(Match).where(or_(Match.team_one_id == self.id, Match.team_two_id == self.id))
        return Session.execute(stmt).scalar_one()


class MapTag(ModelBase, table=True):
    __tablename__ = "map_tag"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=32, unique=True)


class MapTags(ModelBase, table=True):
    __tablename__ = "map_tags"

    id: int = Field(primary_key=True)
    map_id: int = Field(foreign_key="map.id")
    tag_id: int = Field(foreign_key="map_tag.id")


class Map(ModelBase, table=True):

    class Tag:
        Competitive = "competitive"
        GunGame = "gungame"
        Duel = "duel"

    id: int = Field(primary_key=True)
    display_name: str = Field(max_length=32)
    name: str = Field(max_length=32)

    tags: List[MapTag] = Relationship(link_model=MapTags)

    @classmethod
    def with_tag(cls, *tags: Map.Tag):
        stmt = select(cls).where(
            cls.tags.any(MapTag.name.in_(tags))
        )
        return Session().exec(stmt).all()

    @classmethod
    def random(cls, tags=None):
        stmt = select(cls)
        if tags:
            stmt = stmt.where(
                cls.tags.any(MapTag.name.in_(tags))
            )

        maps = Session().exec(stmt).all()
        return random.choice(maps)


class WhitelistedPlayer(ModelBase, table=True):
    __tablename__ = "whitelisted_player"

    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    game_id: int = Field(foreign_key="game.id")


class BlacklistedPlayer(ModelBase, table=True):
    __tablename__ = "blacklisted_player"

    id: int = Field(primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    game_id: int = Field(foreign_key="game.id")


class Game(ModelBase, table=True):
    class Status(IntEnum):
        NOT_STARTED = 0
        STARTED = 1
        FINISHED = 2
        TERMINATED = 3

    class Mode(IntEnum):
        COMPETITIVE = 0
        PUB = 1
        DEATHMATCH = 2
        DUEL = 3
        PRACTICE = 4
        RANKED = 5
        GUNGAME = 6

        @staticmethod
        def to_code(name):
            return getattr(Game.Mode, name.upper(), None)

    class ConfigField:
        MAX_PLAYERS = "MAX_PLAYERS"
        AUTO_TEAM_BALANCE = "AUTO_TEAM_BALANCE"

    id: int | None = Field(primary_key=True)

    map: Map = Relationship()
    map_id: int = Field(foreign_key="map.id")

    # Game status
    status: Game.Status = Field(default=Status.NOT_STARTED)

    # Match
    match: Match = Relationship(back_populates="games")
    match_id: int = Field(foreign_key="match.id", nullable=True, default=None)

    # Teams
    team_a: InGameTeam = Relationship(sa_relationship_kwargs={"foreign_keys": "Game.team_a_id"})
    team_a_id: int = Field(foreign_key="in_game_team.id")

    team_b: InGameTeam = Relationship(sa_relationship_kwargs={"foreign_keys": "Game.team_b_id"})
    team_b_id: int = Field(foreign_key="in_game_team.id")

    winner: InGameTeam = Relationship(sa_relationship_kwargs={"foreign_keys": "Game.winner_id"})
    winner_id: int = Field(foreign_key="in_game_team.id", nullable=True, default=None)

    # Plugins
    plugins: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    mode: Game.Mode = Field()

    config_overrides: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Whitelist
    whitelist: List[Player] = Relationship(link_model=WhitelistedPlayer)
    blacklist: List[Player] = Relationship(link_model=BlacklistedPlayer)

    # Whether whitelist is enabled or not
    is_whitelisted: bool = Field(default=False)

    sessions: List[PlayerSession] = Relationship(back_populates="game")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime = Field(default=None, nullable=True)

    async def has_plugin(self, plugin: GamePlugin):
        return str(plugin) in self.plugins

    def get_default_config(self):
        return {
            Game.Mode.PUB: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: True,
            },
            Game.Mode.RANKED: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: False,
            },
            Game.Mode.DUEL: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: True,
            },
            Game.Mode.DEATHMATCH: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: False,
            },
            Game.Mode.COMPETITIVE: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: False,
            },
            Game.Mode.PRACTICE: {
                Game.ConfigField.MAX_PLAYERS: 10,
                Game.ConfigField.AUTO_TEAM_BALANCE: False,
            },
            Game.Mode.GUNGAME: {
                Game.ConfigField.AUTO_TEAM_BALANCE: True,
                Game.ConfigField.MAX_PLAYERS: 16
            }
        }[self.mode]

    def set_config_var(self, name: ConfigField, value: int):
        self.config_overrides[name] = value

    def get_config_var(self, name) -> int:
        if name in self.config_overrides:
            return self.config_overrides[name]

        return self.get_default_config()[name]

    def get_online_sessions(self, status: int = None) -> List[PlayerSession]:
        q = [
            session for session in self.sessions
            if session.state == PlayerSession.State.IN_GAME
        ]

        if status:
            q = [session for session in q if session.status == status]
        return q

    def get_player_team(self, player: Player):
        for team in [self.team_a, self.team_b]:
            if player in team.get_players():
                return team

    @property
    def is_started(self):
        return self.status == self.Status.STARTED

    @property
    def is_finished(self):
        return self.status == self.Status.FINISHED

    def get_emptier_team(self, for_player=None):

        team_a_sessions = [
            session for session in self.team_a.sessions if session.player != for_player
        ]

        team_b_sessions = [
            session for session in self.team_b.sessions if session.player != for_player
        ]

        if len(team_a_sessions) == len(team_b_sessions):
            return random.choice([self.team_a, self.team_b])

        if len(team_a_sessions) < len(team_b_sessions):
            return self.team_a

        return self.team_b

    def get_team(self, short_name):
        """ Get team by short name (T/CT) """

        if self.team_a.get_current_team() == short_name:
            return self.team_a

        return self.team_b

    def get_session(self, player) -> PlayerSession:
        stmt = select(PlayerSession).where(
            PlayerSession.game_id == self.id,
            PlayerSession.player_id == player.id
        )
        return Session().exec(stmt).first()

    def has_plugin(self, plugin):
        return self.plugins and plugin in self.plugins

    @property
    def score_a(self):
        return Round.objects.filter(game=self, winner=self.team_a).count()

    @property
    def score_b(self):
        return Round.objects.filter(game=self, winner=self.team_b).count()


class Round(ModelBase, table=True):
    """
        Represents a round in a game.
        Has context of absolute round number.
        If we want to rebuild score at halftime we
        have to rely on round number assuming half is 15 rounds.
    """

    id: int | None = Field(default=None, primary_key=True)
    game: Game = Relationship()
    game_id: int = Field(foreign_key="game.id")
    number: int = Field()
    winner: InGameTeam = Relationship()
    win_reason: WinReason = Field(nullable=True, default=None)
    winner_id: int = Field(foreign_key="in_game_team.id", nullable=True, default=None)


class GamePlayerEvent(ModelBase, table=True):
    """
        Represents a player event in game, like kill,
        death, bomb plant, defuse or anything else.
        This table can be used in many ways to analyze player activity
    """

    class Type(str, Enum):
        KILL = "KILL"
        DEATH = "DEATH"
        ASSIST = "ASSIST"
        BOMB_PLANT = "BOMB_PLANT"
        BOMB_DEFUSE = "BOMB_DEFUSE"

    id: int | None = Field(primary_key=True)

    # Event name
    event: GamePlayerEvent.Type = Field()

    # Game
    game: Game = Relationship()
    game_id: int = Field(foreign_key="game.id")

    # Player
    player: Player = Relationship()
    player_id: int = Field(foreign_key="player.id")

    # Round
    round: Round = Relationship()
    round_id: int = Field(foreign_key="round.id")

    # Meta
    meta: dict = Field(sa_column=Column(JSON), default_factory=dict)

    # Is player CT
    is_ct: bool = Field()

    # Timestamp
    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime(timezone=True)))


class MapPick(ModelBase, table=True):
    """ Represents game map that was either picked, banned, or just present waiting to be picked or banned.
     Map pick process is initialized with 7 maps by default. """

    id: int | None = Field(primary_key=True)
    process: MapPickProcess = Relationship(back_populates="maps")
    process_id: int = Field(foreign_key="map_pick_process.id")

    map: Map = Relationship()
    map_id: int = Field(foreign_key="map.id")

    selected_by: MatchTeam = Relationship()
    selected_by_id: int = Field(foreign_key="match_team.id", nullable=True, default=None)

    picked: bool = Field(nullable=True, default=None)

    def was_selected(self):
        return self.selected_by is not None


class MapPickProcess(ModelBase, table=True):
    class Action(IntEnum):
        PICK = 2
        DEFAULT = 3
        BAN = 1
        NULL = 0

    __tablename__ = "map_pick_process"

    id: int | None = Field(primary_key=True)

    finished: bool = Field(default=False)

    next_action: MapPickProcess.Action = Field()

    picker_a: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "MapPickProcess.picker_a_id"})
    picker_b: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "MapPickProcess.picker_b_id"})

    picker_a_id: int = Field(foreign_key="player.id")
    picker_b_id: int = Field(foreign_key="player.id")

    # player that has to make a decision
    turn: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "MapPickProcess.turn_id"})
    turn_id: int = Field(foreign_key="player.id", nullable=True)

    maps: List[MapPick] = Relationship(back_populates="process")

    match: Match = Relationship(back_populates="map_pick_process", sa_relationship_kwargs={"uselist": False})

    def other_picker(self, picker):
        if picker == self.picker_a:
            return self.picker_b
        elif picker == self.picker_b:
            return self.picker_a
        raise ValueError(f"Picker is not in match")

    @property
    def not_picked(self):
        Session.refresh(self)
        return [m for m in self.maps if m.selected_by is None]

    @property
    def last_action(self):
        return sorted(self.maps, key=lambda m: m.id)[-1]

    @property
    def picked(self):
        return [m for m in self.maps if m.picked is True]

    @property
    def banned(self):
        return [m for m in self.maps if m.picked is False]


def new_map_pick_process():
    return MapPickProcess.objects.create()


class Match(ModelBase, table=True):

    def other_team(self, team):
        if team == self.team_one:
            return self.team_two
        elif team == self.team_two:
            return self.team_one
        raise ValueError(f"<team {team.short_name}/> is not in <match id={self.id} />")

    def get_random_team(self):
        return random.choice([self.team_one, self.team_two])

    def get_player_team(self, player: Player) -> Optional[MatchTeam]:
        if self.team_one and player in self.team_one.players:
            return self.team_one

        if self.team_two and player in self.team_two.players:
            return self.team_two

        return None

    id: int | None = Field(primary_key=True)

    team_one: MatchTeam = Relationship(sa_relationship_kwargs={"foreign_keys": "Match.team_one_id"})
    team_two: MatchTeam = Relationship(sa_relationship_kwargs={"foreign_keys": "Match.team_two_id"})

    team_one_id: int = Field(foreign_key="match_team.id", nullable=True, default=None)
    team_two_id: int = Field(foreign_key="match_team.id", nullable=True, default=None)

    name: str = Field(max_length=100, nullable=True, default=None)
    start_date: datetime = Field(sa_column=Column(DateTime(timezone=True)), nullable=True, default=None)

    actual_start_date: datetime = Field(sa_column=Column(DateTime(timezone=True)), nullable=True, default=None)
    actual_end_date: datetime = Field(sa_column=Column(DateTime(timezone=True)), nullable=True, default=None)

    event: Event = Relationship()
    event_id: int = Field(foreign_key="event.id", nullable=True, default=None)

    map_count: int = Field()

    # data that helps to construct game instances
    game_meta: dict = Field(sa_column=Column(JSON), default_factory=dict)

    map_pick_process: MapPickProcess = Relationship(back_populates="match")
    map_pick_process_id: int = Field(foreign_key="map_pick_process.id", nullable=True, unique=True, default=None)

    games: List[Game] = Relationship(back_populates="match")

    def get_team_of(self, player):
        if player in self.team_one.players:
            return self.team_one

        if player in self.team_two.players:
            return self.team_two

        return None




class Event(ModelBase, table=True):
    """ Competitive event / tournament """
    id: int = Field(primary_key=True)
    name: str = Field(max_length=100)


class Role(ModelBase, table=True):
    id: int | None = Field(primary_key=True)

    name: str = Field(max_length=100)
    tab_prefix: str = Field(max_length=100)
    tab_color: str = Field(max_length=100)
    chat_prefix: str = Field(max_length=100)
    chat_suffix: str = Field(max_length=100)
    chat_color: str = Field(max_length=100)
    chat_message_color: str = Field(max_length=100)
    team_override_color: bool = Field()
    permissions: List[PlayerPermission] = Relationship(link_model=PlayerPermissions)

    def has_perm(self, perm: PType):
        perm = perm.str()

        for has_perm in self.permissions:
            parts_present = has_perm.name.lower().split(".")
            parts_required = perm.lower().split(".")
            print(f"present: {parts_present}, required: {parts_required}")

            # present permission is more specific than required
            if len(parts_present) > len(parts_required):
                continue

            # iterate both lists and check if they match
            for pres, req in zip(parts_present, parts_required):
                if pres != req:
                    if pres == "*":
                        return True
                    break
            else:
                return True

        return False


class QueuePlayers(ModelBase, table=True):
    id: int = Field(primary_key=True)

    queue_id: int = Field(foreign_key="player_queue.id")
    player_id: int = Field(foreign_key="player.id")


class ConfirmedPlayers(ModelBase, table=True):
    id: int = Field(primary_key=True)

    queue_id: int = Field(foreign_key="player_queue.id")
    player_id: int = Field(foreign_key="player.id")


class PlayerQueue(ModelBase, table=True):
    __tablename__ = "player_queue"

    class Type(IntEnum):
        RANKED = 1

    id: int | None = Field(primary_key=True)

    type: PlayerQueue.Type = Field()
    size: int = Field(default=10)
    meta: dict = Field(sa_column=Column(JSON), default_factory=dict)

    locked: bool = Field(default=False)
    locked_at: datetime = Field(nullable=True, default=None)

    confirmed: bool = Field(default=False)

    # once queue is full, map picking will start
    captain_a: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "PlayerQueue.captain_a_id"})
    captain_b: Player = Relationship(sa_relationship_kwargs={"foreign_keys": "PlayerQueue.captain_b_id"})

    captain_a_id: int = Field(foreign_key="player.id", nullable=True, default=None)
    captain_b_id: int = Field(foreign_key="player.id", nullable=True, default=None)

    # once queue is full, it will be associated with a match.
    # usually Bo1 will be played, but still match is preferred because it has all map pick features
    match: Match = Relationship()
    match_id: int = Field(foreign_key="match.id", nullable=True, default=None)

    players: List[Player] = Relationship(link_model=QueuePlayers)
    confirmed_players: List[Player] = Relationship(link_model=ConfirmedPlayers)

    def join(self, player: Player) -> bool:
        if self.has(player):
            return False

        self.players.append(player)
        Session.commit()
        return True

    def has(self, player: Player):
        """ Checks if player is in THIS queue already """
        return player in self.players

    def leave(self, player: Player) -> bool:
        if not self.has(player):
            return False

        self.players.remove(player)
        Session.commit()

        return True

    def has_confirmed(self, player: Player):
        return player in self.confirmed_players

    def unlock(self):
        print(f"Unlocking queue {self.id}")
        self.locked = False
        self.locked_at = None
        Session.commit()
        print(f"Queue unlocked {self.id}")

    def lock(self):
        print(f"Locking queue {self.id}")
        self.locked = True
        self.locked_at = datetime.now()
        Session.commit()
        Session.refresh(self)
        print(f"Queue {self.id} locked: {self.locked}")

    def confirm(self, player: Player):
        if self.has_confirmed(player):
            return False

        self.confirmed_players.append(player)
        Session.commit()
        return True

    def unconfirm(self):
        self.confirmed_players.clear()
        Session.commit()


class AuthSession(ModelBase, table=True):
    id: int | None = Field(primary_key=True)

    player: Player = Relationship()
    player_id: int = Field(foreign_key="player.id", nullable=True, default=None)

    session_key: str = Field(max_length=64)
    data: dict = Field(sa_column=Column(JSON), default_factory=dict)

    # def set_data(self, **data):
    #     self.data = {**self.data, **data}
    #     self.save()
    #
    # def get_data(self, key):
    #     return self.data.get(key)

    @classmethod
    def find_by_key(cls, key: str) -> Optional[AuthSession]:
        stmt = select(cls).where(cls.session_key == key)
        res = Session().execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    def create(cls, player: Optional[Player]):
        auth_sess = AuthSession(
            player=player,
            session_key="".join(
                [
                    random.choice(
                        list("qwertyuiopasdfghjklzxcvbnm1234567890")
                    )
                    for _ in range(64)
                ]
            )
        )
        Session().add(auth_sess)
        Session().commit()
        return auth_sess

    @classmethod
    def log_out(cls, player):
        AuthSession.objects.filter(player=player).delete()
        return
