import asyncio
import logging
import random
from typing import Optional, Dict

from blazelink.models import ObjectId
from blazelink.transport import Transport, UpdateType
from pydantic import BaseModel
from sqlmodel import select

from adapters.telegram import safe_send
from events.internal import internalHandler
from events.schemas.bukkit import PlayerGameConnectEvent, PlayerLeaveGameEvent, GameTerminatedEvent
from events.schemas.internal import PlayerLeftGame, PlayerJoinGame, PlayerRosterChange, PlayerStatusChange
from models import Game, Player, PlayerSession, Session, Team, InGameTeam, ModelBase


class MineStrike:
    """
        Wrapper on top of WebsocketConnection to provide a
        simplified interface as a way to communicate with
        remote Bukkit plugin.
    """
    _event_queue = []

    def __init__(self, transport: Transport | None):

        self.transport = transport

    async def send_queued(self):
        while self._event_queue:
            await self.safe_send_event(self._event_queue.pop(0))

    def is_connected(self):
        return self.transport is not None

    async def safe_send_event(self, evt: BaseModel) -> None:
        if not self.is_connected():
            self._event_queue.append(evt)
            logging.warning(f"Event {type(evt).__name__} queued")
            return

        return await self.transport.send_message(evt)

    async def model_update(self, model: ModelBase):
        await self.transport.push_update(
            update_type=UpdateType.Update,
            identifier=model.objectId(),
            update_id=int("1000000001" + str(random.randint(111111, 999999))),
            changes={}
        )

    async def update_server(self):
        await self.transport.push_update(
            update_type=UpdateType.Update,
            identifier=ObjectId("Server", 1, dependencies=[
                ObjectId("Game", None)
            ]),
            update_id=int("1000000001" + str(random.randint(111111, 999999))),
            changes={}
        )

    async def leave_active_game(self, player: Player):
        """ Make player leave game they are currently are in"""
        session = player.get_active_session()
        if not session:
            return

        await self.leave_game(player, session.game)

    async def leave_game(self, player: Player, game: Game):

        session = game.get_session(player)

        logging.info(f"Player {player.id} leaving game {session.game.id}...")

        session.state = PlayerSession.State.AWAY
        Session().add(session)
        Session().commit()

        # handle internally
        await internalHandler.propagate_event(event=PlayerLeftGame(session=session), sender=session)

        logging.info(f"Propagate game leave to Bukkit...")

        # explicitly tell Bukkit that player left
        await self.send_leave_game(game=session.game, player=player)

        # update session to make player away
        await self.update_session(session)

        # update roster to mark player as not part of it
        # could be None if player was spectator
        if session.roster is not None:
            await self.update_roster(session.roster)

        player.active_game_id = None
        Session().add(player)
        Session().commit()

        logging.info(f"Player {player.id} left game {session.game.id}")

        safe_send(
            f"Player {player.username} has left game {game.id}"
        )

        # Update database state

        session: PlayerSession = game.get_session(player)

        if game.status == Game.Status.NOT_STARTED and game.get_config_var(Game.ConfigField.AUTO_TEAM_BALANCE):
            # Delete session if player leaves during warm up in game that does not pre-fill teams
            Session().delete(session)
            Session().commit()
        else:
            # mark session as away
            session.state = PlayerSession.State.AWAY

            # update session
            await self.update_session(session)

        if session.roster is not None:
            await self.update_roster(session.roster)

        player.active_game_id = None
        Session().add(player)

        Session().commit()

    async def join_game(self, game: Game, player: Player, status: PlayerSession.Status, roster: InGameTeam | None):
        """
            Make player join given game.

            @param game: Game to join
            @param player: Player to join
            @param status: Status of player in game
            @param roster: Roster to join
        """

        if game.status in (Game.Status.FINISHED, Game.Status.TERMINATED):
            raise ValueError("Game was already finished or terminated")

        logging.info(f"Joining game {game.id} with {player.id} as {status}")

        if status == PlayerSession.Status.SPECTATOR:
            if roster is not None:
                raise ValueError("Player can't spectate and be in a roster")

        active_game: Optional[Game] = player.get_active_game()

        if active_game:
            logging.info(f"Player {player.id} is currently in game {active_game.id}")
            await self.leave_active_game(player)
        else:
            logging.info(f"Player {player.id} does not have active game")

        # player might have idle session already
        stmt = select(PlayerSession).where(
            PlayerSession.player == player,
            PlayerSession.game == game
        )

        session = Session().exec(stmt).first()

        # Player doesn't have a session yet. Just create a new one
        if not session:
            session = PlayerSession(
                game_id=game.id,
                player_id=player.id,
                roster_id=roster.id if roster else None,
                status=status,
                state=PlayerSession.State.IN_GAME
            )

            Session().add(session)
            Session().commit()

        # player had session in this game but in different roster
        else:
            if session.roster != roster:
                old_roster = session.roster
                session.roster = roster
                Session().commit()

                await internalHandler.propagate_event(
                    event=PlayerRosterChange(session=session, old_roster=old_roster, new_roster=roster),
                    sender=session
                )

                if roster is not None:
                    await self.update_roster(roster)

            # player had a session but in different status
            if session.status != status:
                old_status = session.status
                session.status = status
                Session().commit()

                await internalHandler.propagate_event(
                    event=PlayerStatusChange(session=session, old_status=old_status, new_status=status),
                    sender=session
                )

                if roster is not None:
                    await self.update_roster(roster)

        logging.info(f"Player {player.id} now has updated session {session.id}")

        # since we know player wasn't in game, we have to change state
        session.state = PlayerSession.State.IN_GAME
        Session().commit()

        # update model that was indirectly updated
        # after it was updated, we can be sure that
        # plugin is aware that player is now member of
        # inGameTeam via new PlayerSession object
        # await self.update_game(game)
        # await self.update_roster(roster)

        logging.info(f"Propagating internally")

        # handle internally
        await internalHandler.propagate_event(
            event=PlayerJoinGame(session=session),
            sender=session
        )

        logging.info(f"Player {player.id} joining game {game.id}...")

        Session().refresh(game)

        # TODO: Figure out a way to consistently propagate updates
        #   and wait for them to be handled

        # make sure game is up-to-date after session insert
        # it will be synced eventually anyway, but we have to be sure it happened
        # before send_join_game
        await self.model_update(game)

        # Update session object because it might've changed state
        await self.model_update(session)

        # same for roster, update to make sure player is registered as participant
        if roster is not None:
            await self.model_update(roster)

        player.active_game_id = game.id
        Session().add(player)
        Session().commit()

        # explicitly tell Bukkit that player joined
        await self.send_join_game(game=session.game, player=player, team=roster, status=status)

        logging.info(f"Player {player.id} joined game {game.id}")

    async def send_join_game(self, game: Game, player: Player, team: InGameTeam | None, status: PlayerSession.Status):

        return await self.safe_send_event(
            PlayerGameConnectEvent(
                player_id=player.objectId(),
                game_id=game.objectId(),
                team_id=team.objectId() if team else None,
                status=status
            )
        )

    async def send_leave_game(self, game, player):
        await self.safe_send_event(
            PlayerLeaveGameEvent(
                player=player.objectId(),
                game=game.objectId(),
            )
        )

    async def update_roster(self, in_game_team):
        return await self.model_update(in_game_team)

    async def update_game(self, game):
        return await self.model_update(game)

    async def update_session(self, session):
        return await self.model_update(session)

    async def terminate_game(self, game):
        await self.safe_send_event(
            GameTerminatedEvent(
                game=game.objectId()
            )
        )
