from __future__ import annotations

import asyncio
import logging


import uvicorn
from ariadne import Extension
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.types import ContextValue
from blazelink import create_schema
from blazelink.connection import ConnectionManager
from blazelink.models import ObjectId
from blazelink.schemas import AuthorizeEvent
from blazelink.signaling import Signaler
from blazelink.subscription import SubscriptionManager
from blazelink.transport import StarletteTransport, Transport
from blazelink.debugger import Debugger

from sqlmodel import select


from models import (
    PlayerPermission,
    Session,
    session_maker
)

from queries import table_manager
print("Table manager initialized")
from routes import monitoring
from routes.routers import get_v1_router

from fastapi import FastAPI, Depends

from ariadne.asgi import GraphQL

from starlette.websockets import WebSocket
from fastapi.middleware.cors import CORSMiddleware


from exceptions import install_exception_handlers
from settings import settings

# from api.graphql.query import schema

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
]

# Configuring logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def clear_sessions():
    try:
        yield
    finally:
        Session.remove()

app.include_router(prefix="/api", router=get_v1_router(), dependencies=[
    Depends(clear_sessions)
])

app.include_router(prefix="/blazelink-mgmt", router=monitoring.router)


@app.get("/status")
def status():
    return {
        "success": True
    }


@app.on_event("startup")
def ensure_defaults():
    # make sure default permission exists
    stmt = select(PlayerPermission).where(PlayerPermission.name == 'bms.player.any')
    res = Session().exec(stmt)
    res = res.first()
    if res is None:
        perm = PlayerPermission(name='bms.player.any')
        Session().add(perm)
        Session().commit()


# @app.on_event("startup")
# @repeat_every(seconds=60, raise_exceptions=True)
async def keep_open_servers():
    """ A task that runs every minute to keep open servers.
        Ideally servers should be created on events,
        but this is a fallback.
    """
    from api.tasks.game import keep_open_pubs, keep_open_deathmatch, keep_open_duels
    await keep_open_pubs()
    await keep_open_deathmatch()
    await keep_open_duels()


install_exception_handlers(app)


debugger = Debugger()
connection_manager = ConnectionManager()
subs = SubscriptionManager(connection_manager, debugger=debugger)


async def on_sub(session_id: str, object_id: ObjectId):
    """ Add primitive subscriptions for this connection based on this object_id.
     Will only add subscriptions to real database tables / rows. """

    # todo: filter out views, views don't have object ids, but table subscriptions also don't have object ids

    await debugger.add_subscription(session_id, object_id)
    subs.subscribe(session_id, object_id)
    await debugger.sync_subscriptions(session_id, subs._subscriptions[session_id])

    for dependency in object_id.dependencies:
        await on_sub(session_id, dependency)


table_manager.on_subscribe(on_sub)

signaler = Signaler(
    subs,
    db_host=settings.database_host,
    db_port=5432,
    db_name=settings.database_name,
    db_user=settings.database_user,
    db_password=settings.database_password,
    debugger=debugger,
    table_manager=table_manager,
    slot_name="betterms"
)


class SessionExtension(Extension):

    def request_started(self, context: ContextValue) -> None:
        context["database_session"] = session_maker()

    def request_finished(self, context: ContextValue) -> None:
        context["database_session"].close()

print("create schema")

asgi_app = GraphQL(
    create_schema(table_manager),
    debug=True,
    http_handler=GraphQLHTTPHandler(
        extensions=[
            SessionExtension
        ]
    )
)

app.mount(
    "/graphql",
    asgi_app
)


@app.on_event("startup")
async def start_things():
    c = signaler.start()
    asyncio.create_task(c)


@connection_manager.on_authorized("bukkit")
async def bukkit_authorized(transport: Transport):
    from services.minestrike import MineStrike
    await MineStrike(transport).send_queued()


@connection_manager.on_authorized("management")
async def bukkit_authorized(transport: Transport):
    debugger.set_transport(transport)

    for conn_id, sb in subs._subscriptions.items():
        await debugger.sync_subscriptions(conn_id, sb)


@app.websocket("/ws/connect")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    transport = StarletteTransport(websocket, session_id=session_id, debugger=debugger)

    @transport.on_authorize
    def on_authorize(event: AuthorizeEvent):
        connection_manager.authorize(transport, event)

    connection_manager.add_connection(transport)
    print(">>>>>>>>>>> Add connection to manager", transport.get_session_id())

    await transport.run()

    connection_manager.remove_connection(transport)
    print(">>>>>>>>>>> Connection closed.")
    # conn = WsConn(websocket)
    # await conn.run()


