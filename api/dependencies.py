import inspect
import traceback
from typing import Optional, Type, List, Any, Callable
from uuid import UUID


from fastapi import Request, HTTPException, Depends, params, Query, Response
from pydantic.class_validators import root_validator
from pydantic.main import create_model

from exceptions import AuthorizationError
from models import Team, Player, AuthSession, Event, Match, Game, Invite, InGameTeam, MapPick, PlayerQueue, Map

# Inherit str to make type serializable by openapi


class UndefinedType(str):
    def __eq__(self, other):
        return type(self) == type(other)

    def __new__(cls, openapi_name='abc'):
        obj = str.__new__(cls, openapi_name)
        return obj

    def __str__(self):
        return "Undefined"


UNDEFINED = UndefinedType(openapi_name='Undefined')


class QueryItem:
    def __init__(self, api_field, db_field, type, required=True, **kwargs):
        self.api_field = api_field.split('.')[0]
        self._loaded_field_path = api_field.split('.')[1:]
        self.db_field = db_field
        self.type = type
        self.required = required

        if 'default' in kwargs:
            self.default = kwargs['default']
        else:
            self.default = UNDEFINED

        if isinstance(type, params.Depends):
            self.type = Any,
            self.default = type

        if 'loc' in kwargs:
            if kwargs['loc'] == 'param':
                default = self.default
                self.default = Query(default=default)

    def get_value(self, value):
        """
            Get value that is used by query. If api_field has value of pool.chain,
            then this method will return value of nested field chain
        """

        if not self._loaded_field_path:
            return value

        field_model = type(value)

        path_to_field = self._loaded_field_path[:-1]
        searched_field = self._loaded_field_path[-1]

        for item in path_to_field:
            field_model = getattr(field_model, item).rel_model
            value = field_model.get_by_id(getattr(value, item))

        return getattr(value, searched_field)

    def __str__(self):
        if inspect.isclass(self.type):
            type_name = self.type.__name__
        else:
            type_name = type(self.type).__name__

        return f"<Query {self.api_field}:{type_name} -> " \
               f"model.{self.db_field} (default={self.default}) {'*' if self.required else ''}>"

    def __repr__(self):
        return str(self)


def get_model(model, values: List[Any], query: List[QueryItem]):
    # NOTE: this restriction does not account for joining same table on different fields
    joined_models = set()

    if not values or all([v == UNDEFINED for v in values]):
        return None

    sql_query = model.objects.all()
    for value, query_item in zip(values, query):

        # value is not required and wasn't passed
        # ignore it
        if value == UNDEFINED:
            continue

        _model = model

        path = query_item.db_field.split(".")

        # make joins for all intermediate tables
        while len(path) > 1:
            field = path.pop(0)

            _model = getattr(_model, field).rel_model

            if _model in joined_models:
                # if field already joined just switch to it,
                # so we can continue joining from there
                sql_query = sql_query.switch(_model)
                continue

            joined_models.add(_model)
            sql_query = sql_query.join(_model)

        # if query uses nested field of loaded model
        # it will be retrieved here
        value = query_item.get_value(value)

        # last item in path is actual field we will be searching by
        filter_by = path.pop(0)
        sql_query = sql_query.filter(**{getattr(_model, filter_by): value})

        # return context back to top-level model
        # to start over for the next field on the next iteration
        sql_query.switch(model)

    return sql_query.get_or_none()


def depends_factory(model, api_field, api_field_type, db_field="id", required=False):
    def inner(**kwargs):
        value = kwargs[api_field]
        if value is None:
            return None
        try:
            instance = model.objects.filter(**{db_field: value})
            if instance.exists():
                return instance.get()
        except Exception:
            traceback.print_exc()
            pass

        raise HTTPException(status_code=404, detail=f"{model.__name__} with {db_field} of {value} not found")

    param = {
        "kind": 1,
        "name": api_field,
        "annotation": api_field_type
    }

    if not required:
        param['default'] = None

    sig = inspect.Signature(
        parameters=[inspect.Parameter(**param)]
    )

    inner.__signature__ = sig
    return Depends(inner)


def RosterDependency(required=True):
    return depends_factory(Team, 'roster', int, 'id', required)


def PlayerDependency(required=True):
    return depends_factory(Player, 'player', UUID, 'uuid', required)


async def get_session(request: Request, response: Response):
    """ Get session from request or create new one """

    session_id = request.headers.get('session_id')

    if session_id:
        session = AuthSession.find_by_key(session_id)
        if session:
            return session

    session = AuthSession.create(None)
    response.headers['session_id'] = session.session_key

    return session


SessionDependency = Depends(get_session)


async def get_player(session: AuthSession = SessionDependency):
    """ Get player from session. If session does not have player, throw an error """

    player = session.player

    if player is None:
        raise AuthorizationError("Player is not found")

    return player


InviteDependency = depends_factory(Invite, 'invite', int, 'id', True)
MatchDependency = depends_factory(Match, 'match', int, 'id', True)

PlayerAuthDependency = Depends(get_player)


async def get_minestrike():
    from services.minestrike import MineStrike
    from main import connection_manager
    transport = connection_manager.get_authorized("bukkit")

    if not transport:
        raise HTTPException(status_code=503, detail="MineStrike is not available")

    return MineStrike(transport)


GetMineStrike = Depends(get_minestrike)
