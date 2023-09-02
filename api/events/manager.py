import asyncio
import functools
import traceback
from collections import defaultdict
from dataclasses import dataclass
from typing import Type, Any

from blazelink.schemas import IncomingEvent
from pydantic import BaseModel

from events.event import IntentResponse
from events.schemas.bukkit import IntentEvent


class WaitObject:

    def __init__(self, registerer):
        self.registerer = registerer

    def on(self, model) -> asyncio.Future:
        return self.registerer(model, 'on')

    def pre(self, model) -> asyncio.Future:
        return self.registerer(model, 'pre')

    def post(self, model) -> asyncio.Future:
        return self.registerer(model, 'post')


@dataclass
class Waiter:
    # name of event we are waiting for
    # or class of event we are waiting for
    event: str
    # entity of the event
    model: Any
    # type of waiter (on/pre/post)
    type: str
    # future that will be resolved when waiter is completed
    future: asyncio.Future


class EventManager:

    def __init__(self):
        self.handlers = defaultdict(list)
        self.waiters: list[Waiter] = []

    def _execute_waiters(self, event, model, waiter_type):

        waiters_to_remove = []
        for waiter in self.waiters:

            if model != waiter.model and (
                    (not hasattr(model, 'id') or not hasattr(waiter.model, 'id'))
                    or not isinstance(model, type(waiter.model))
                    or model.id != waiter.model.id
            ):
                continue

            if waiter_type != waiter.type:
                continue

            if isinstance(event, IncomingEvent):
                if event.type != waiter.event:
                    continue

            elif event != waiter.event:
                continue

            waiters_to_remove.append(waiter)

            if waiter.future.done():
                print("[WARN] waiter already completed")
                continue

            waiter.future.set_result(event)

        for waiter in waiters_to_remove:
            self.waiters.remove(waiter)

    def on(self, event: Type[BaseModel]):
        def inner(func):

            if isinstance(event, IntentEvent):

                @functools.wraps(func)
                async def safeguarded_func(entity, payload):
                    r = func(entity, payload)
                    if asyncio.iscoroutine(r):
                        r = await r

                    if not isinstance(r, IntentResponse):
                        raise TypeError(f'IntentEvent handler {func} did not return IntentEvent')

                func = safeguarded_func

            if isinstance(event, str):
                self.handlers[event].append(func)
            else:
                def parse_and_trigger(sender, evt_payload):
                    return func(
                        sender,
                        event.parse_obj(evt_payload)
                    )

                self.handlers[event.__name__].append(parse_and_trigger)

        return inner

    async def propagate_event(self, sender: Any, event: BaseModel):
        """
            Propagate arbitrary pydantic schema as event
        """
        abs_event = IncomingEvent(
            type=type(event).__name__,
            data=event.dict()
        )

        return await self.propagate_abstract_event(abs_event, sender)

    async def propagate_abstract_event(self, event: IncomingEvent, entity, blocking=True):
        """
            Propagate generic event with strict schema
        """

        print(f">>> >>> Propagate event {event.type}")

        self._execute_waiters(event, entity, 'pre')
        self._execute_waiters(event, entity, 'on')

        awaited_response = None

        for handler in self.handlers[event.type]:
            try:
                response = handler(entity, event.data)
                if asyncio.iscoroutine(response):
                    if not blocking:
                        asyncio.create_task(response)
                    else:
                        awaited_response = await response
                else:
                    awaited_response = response
            except Exception:
                traceback.print_exc()

        self._execute_waiters(event, entity, 'post')

        return awaited_response

    def wait(self, event: str | Type[BaseModel], timeout=None) -> WaitObject:

        if isinstance(event, type) and issubclass(event, BaseModel):
            event = event.__name__

        async def fail_task_if_did_not_succeed(future: asyncio.Future):
            await asyncio.sleep(timeout)
            if not future.done():
                future.set_exception(TimeoutError(f'Event Waiter timed out after {timeout} seconds'))

        def register_waiter(model, waiter_type):
            future = asyncio.Future()

            if timeout:
                asyncio.create_task(fail_task_if_did_not_succeed(future))

            self.waiters.append(Waiter(event, model, waiter_type, future))
            return future

        return WaitObject(register_waiter)
