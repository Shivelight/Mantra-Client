# -*- coding: utf-8 -*-
import time
import asyncio
from contextlib import suppress
from threading import Thread
from importlib import reload

from mantra import mantra
from mantra.logger import get_logger
from mantra.service.ttypes import ErrorCode, TalkException

import processor

log = get_logger("MantraSE")


async def noop(*args, **kwargs):
    pass


class MantraSE(mantra.Mantra):
    version = "0.1"
    grace_period = 259200
    operation = {}
    _procs = []

    def __init__(self, key="Mantra", subs=30, helper=None, loop=None):
        super().__init__(loop)
        self._polling = False
        # self.key = key.lower()
        self.stopped = True
        self.helper = helper
        self.logged_in = False

        initial_subs = time.time() + (float(subs) * 86400)

        self._var = {"debug": False, "lurk": {}, "mimic": "", "coin": set()}

        self._state = {
            "broadcast": False,
            "fancyname": False,
            "mayhem": False,
            "purgeblocked": False,
            "wait": {"type": set(), "queue": asyncio.Queue(loop=self.loop)},
        }

        self._setting.update(
            {
                "autoadd": False,
                "autojoin": {"state": "0", "minmem": 0},
                "automsg": "",
                "autoread": {
                    "chat": False,
                    "group": False,
                    "room": False,
                    "behavior": "1",
                },
                "disguise": {},
                "key": key.lower(),
                "fancyname": [],
                "subscription": initial_subs,
                "whitelist": [],
            }
        )

    @property
    def key(self):
        return self._setting["key"]

    def debug(self):
        self._var["debug"] = not self._var["debug"]
        log.info("Debug {}".format(self._var["debug"]))

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._poll())
        self.stopped = True

        # Copy to avoid set being changed while iterating
        pending = asyncio.Task.all_tasks(loop=self.loop).copy()
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(task)
        self.loop.run_until_complete(self.close())
        self.helper.stop_client(self.mid)
        log.info(f"{self.mid} stopped.")

    def saveSetting(self):
        if self.mid is None:
            log.warn("Client must be logged in!")
            return
        if self.helper is not None:
            coro = self.helper.save_setting(self.mid, self._setting)
            asyncio.run_coroutine_threadsafe(coro, self.helper.loop)
            # setting = fut.result(10)
            # if setting["result"] == "err":
            #     # TODO: save on-disk
            #     pass
            # else:
            #     log.info(f"{self.mid} saved to cloud.")

    def start(self):
        if self.authToken is None:
            log.warn("({}) Not logged in!".format(self.key.title()))
            return -1
        if self.stopped:
            self.stopped = False
            t = Thread(target=self.run)
            t.daemon = True
            t.start()
            log.info(f"{self.mid} started!")
        else:
            log.info(f"{self.mid} already started!")

    def stop(self):
        self._polling = False

    def sync_login(
        self,
        identity=None,
        password=None,
        cert=None,
        token=None,
        qr=False,
        key=None,
        callback=print,
        clientType="ipad",
        protocol="binary",
        sns=None,
        ssl=True,
    ):
        self.loop.run_until_complete(
            self.login(
                identity,
                password,
                cert,
                token,
                qr,
                key,
                callback,
                clientType,
                protocol,
                sns,
                ssl,
            )
        )

    async def _poll(self):
        self._polling = True

        while self._polling:
            try:
                ops = await self.stream()
                for op in ops:
                    if self._var["debug"]:
                        print("")
                        log.debug(op)
                        print("")
                    asyncio.ensure_future(self.operation.get(op.type, noop)(self, op))
            except EOFError:
                pass
            except asyncio.TimeoutError:
                pass
            except TalkException as e:
                if e.code in (
                    ErrorCode.AUTHENTICATION_FAILED,
                    ErrorCode.NOT_AVAILABLE_USER,
                    ErrorCode.NOT_AUTHORIZED_DEVICE,
                    ErrorCode.INTERNAL_ERROR,
                ):
                    self.authToken = None
                    self._polling = False
            except Exception as e:
                log.exception(e)

        if not hasattr(self, "purged"):
            self.saveSetting()

    @staticmethod
    def load_processor(proc):
        proc.setup(MantraSE)
        MantraSE._procs.append(proc)

    @staticmethod
    def reload_processor():
        for proc in MantraSE._procs:
            p = reload(proc)
            p.setup(MantraSE)


MantraSE.load_processor(processor)
