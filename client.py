from threading import Thread
from contextlib import suppress
import os
import asyncio
import time
import atexit

from async_timeout import timeout
from poseur import Client
from poseur.constants import MsgEncoding
from mantra import logger
from mantra.service.ttypes import ErrorCode, TalkException
import ujson as json

from se import MantraSE


Client.encoder = MsgEncoding.MESSAGE_PACK
log = logger.get_logger("MantraClient")


def expose(func):
    func.expose = True
    return func


class MantraClient(object):
    def __init__(self, bind, username, password=None, loop=None):
        self.loop = loop or asyncio.new_event_loop()
        self.username = username
        self.password = password
        self.bind = bind
        self.client = {}
        self.stopped = True
        self.connect()

        if not os.path.exists(f"data/{self.username}"):
            os.makedirs(f"data/{self.username}")

        self.local_storage = f"data/{self.username}"

        def cleanup():
            if not self.loop.is_running():
                self.loop.run_until_complete(self.server.unregister(self.username))

        atexit.register(cleanup)

    def start(self):
        self.stopped = False
        t = Thread(name=self.username, target=self.run)
        t.daemon = True
        t.start()
        log.info(f"Mantra-Client started: {self.username} | {self.bind}")

    def stop(self):
        self.stop_all()
        self.stopped = True

    def run(self):
        self.stopped = False
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._poll())
        pending = asyncio.Task.all_tasks()
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(task)

    def connect(self):
        self.server = Client(username=self.username, rpc_registry=self, loop=self.loop)
        self.server.connect(self.bind)

    async def _poll(self):
        # When registering, server will ask for sync_setting
        clients = await self.server.register(self.username, self.password)
        if clients["status"] == "ok":
            log.info(f"Connected to {self.bind} as {self.username}")
            for client in clients["message"]:
                try:
                    await self.start_client(client)
                except Exception as e:
                    log.exception(e)
        else:
            log.warn(f"Cannot connect to {self.bind} : {clients['message']}")

        retires = 0  # start from 1 because of the current logic
        while not self.stopped:
            try:
                async with timeout(5):
                    await self.server.beat(self.username)
            except asyncio.TimeoutError:
                log.warn(f"Server is not responding, reconnecting.. ({retires})")
                self.connect()
                # re-register just in case the server can't keep up
                await self.server.register(self.username, self.password)
                await asyncio.sleep(2 * retires)
                # limit the interval to 10 minutes
                retires = min(retires + 1, 300)
            else:
                await self.sync_setting()
                await asyncio.sleep(2)
                retires = 0  # reset the retries if success

    @expose
    async def start_client(self, data):
        try:
            setting = json.loads(data["setting"])
            if setting["auth"]["token"]:
                # load data received from the server
                se = MantraSE(helper=self)
                se._setting.update(setting)
            else:
                return {"status": "err", "message": "Token is null."}
        except json.decoder.JSONDecodeError:
            return {"status": "err", "message": "No data."}

        # Run client loop on another thread. Running two event-loop on the
        # same thread is not guaranteed to work.
        future = self.loop.run_in_executor(
            None,
            se.loop.run_until_complete,
            se.login(token=se.authToken, clientType="ipad"),
        )

        try:
            await future
        except TalkException as e:
            if e.code in (
                ErrorCode.AUTHENTICATION_FAILED,
                ErrorCode.NOT_AVAILABLE_USER,
                ErrorCode.NOT_AUTHORIZED_DEVICE,
                ErrorCode.INTERNAL_ERROR,
            ):
                se.authToken = None
                await self.save_setting(data["mid"], se._setting)
                se.session._connector.close()
                return

        status = se.start()
        if status == -1:
            se.session._connector.close()
            return {"status": "err", "message": "Cannot start client."}

        self.client[data["mid"]] = se
        return {"status": "ok", "message": f"{data['mid']} started."}

    @expose
    def stop_client(self, mid):
        try:
            cl = self.client[mid]
            cl.stop()
            del self.client[mid]
            return {"status": "ok", "message": cl._setting}
        except KeyError:
            return {"status": "err", "message": "Mid not found."}

    @expose
    def list_client(self):
        return {"status": "ok", "message": self.client.keys()}

    @expose
    def check(self, mid):
        if mid in self.client:
            return {"status": "ok", "message": ""}
        else:
            return {"status": "err", "message": f"{mid} not found."}

    @expose
    async def sync_setting(self):
        cached = os.listdir(self.local_storage)
        for c in cached:
            with open(f"{self.local_storage}/{c}") as file:
                try:
                    data = json.load(file)
                except ValueError:
                    log.warn(f"Incorrect json at {c}, skipping..")
                    continue
            log.info(f"{c} saving..")
            await self.save_setting(c, data)
            os.remove(f"{self.local_storage}/{c}")

    @expose
    async def subclient(self, mid, ms):
        try:
            curr_time = time.time()
            curr_sub = self.client[mid]._setting["subscription"]
            new_sub = curr_sub + ms

            # I lost myself here, please help
            if new_sub > curr_sub:
                if curr_time < curr_sub:
                    self.client[mid]._setting["subscription"] = new_sub
                elif curr_time > curr_sub:
                    self.client[mid]._setting["subscription"] = curr_time + ms
            elif curr_sub > curr_time and new_sub > curr_time:
                self.client[mid]._setting["subscription"] = new_sub
            else:
                return {"status": "err", "message": "EXPIRED"}
        except KeyError:
            return {"status": "err", "message": f"{mid} not found."}
        else:
            await self.save_setting(mid, self.client[mid]._setting)
            res = self.client[mid]._setting["subscription"]
            return {"status": "ok", "message": (res)}

    @expose
    def status(self):
        pass

    @expose
    def stop_all(self):
        for _, client in self.client.items():
            try:
                client.stop()
            except Exception as e:
                log.exception(e)

    @expose
    async def save_all(self):
        pass

    async def save_setting(self, mid, setting):
        # Sync before saving a new one
        try:
            # await asyncio.wait_for(
            #     self.server.save_setting(self.username, mid, setting), 10
            # )
            async with timeout(5):
                res = await self.server.save_setting(self.username, mid, setting)
            if res["status"] == "ok":
                log.info(f"{mid} saved to cloud.")
            elif res["status"] == "err":
                log.warn(f"Error saving {mid}: {res['message']}")
        except asyncio.TimeoutError:
            log.warn("Server is not responding, saving locally.")
            with open(f"{self.local_storage}/{mid}", "w+") as file:
                json.dump(setting, file, ensure_ascii=False)

    async def purge(self, mid):
        try:
            async with timeout(5):
                await self.server.delete_user(mid)
        except asyncio.TimeoutError:
            pass

    def get(self, name):
        func = getattr(self, name)
        if hasattr(func, "expose"):
            return func
        else:
            return None

    @staticmethod
    def reload_processor():
        MantraSE.reload_processor()
