from threading import Thread
from contextlib import suppress
import os
import asyncio
import logging

from colorlog import ColoredFormatter
from poseur import Client
import ujson as json

from se import MantraSE

LOG_LEVEL = logging.DEBUG
LOGFORMAT = (
    "[%(log_color)s%(levelname)s%(reset)s] "
    "%(log_color)s%(message)s%(reset)s"
)
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger("MantraClient")
log.setLevel(LOG_LEVEL)
log.addHandler(stream)


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

        if not os.path.exists("data"):
            os.makedirs("data")

        self.connect()

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
        clients = await self.server.register(self.username, self.password)
        if clients["status"] == "ok":
            log.info(f"Connected to {self.bind} as {self.username}")
            for client in clients["message"]:
                try:
                    await self.start_client(client)
                except Exception:
                    pass
        else:
            log.warn(f"Cannot connect to {self.bind} : {clients['message']}")

        while not self.stopped:
            try:
                await asyncio.wait_for(self.server.beat(self.username), 10)
            except asyncio.TimeoutError:
                log.warn("Server is not responding, reconnecting..")
                self.connect()
            else:
                await self.sync_setting()
                await asyncio.sleep(5)

    @expose
    async def start_client(self, data):
        se = MantraSE(helper=self)
        if data["setting"]:
            # load data received from the server
            se._setting.update(json.loads(data["setting"]))
        else:
            return

        # done = [False]
        # print(11)

        # def login():
        #     print(3)
        #     asyncio.set_event_loop(se.loop)
        #     se.loop.run_until_complete(se.login(token=se.authToken, clientType="ipad"))
        #     done[0] = True
        #     print(33)

        # t = Thread(target=login)
        # t.daemon = True
        # t.start()

        # while not done[0]:
        #     await asyncio.sleep(2)

        # Run client loop on another thread. Running two event-loop on the
        # same thread is not guaranteed to work
        await self.loop.run_in_executor(
            None,
            se.loop.run_until_complete,
            se.login(token=se.authToken, clientType="ipad"),
        )
        status = se.start()
        if status == -1:
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
            return {"status": "err", "message": "Mid not found."}

    @expose
    async def sync_setting(self):
        cached = os.listdir('data')
        for c in cached:
            with open(f"data/{c}") as file:
                try:
                    data = json.load(file)
                except ValueError:
                    log.warn(f"Incorrect json at {c}, skipping..")
                    continue
            await self.save_setting(c, data)
            os.remove(f"data/{c}")

    @expose
    def sub_add(self, mid):
        pass

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
        try:
            await asyncio.wait_for(
                self.server.save_setting(self.username, mid, setting), 10
            )
            log.info(f"{mid} saved to cloud.")
        except asyncio.TimeoutError:
            log.warn("Server is not responding, saving locally.")
            with open(f"data/{mid}", "w+") as file:
                json.dump(setting, file, ensure_ascii=False)

    def get(self, name):
        func = getattr(self, name)
        if hasattr(func, "expose"):
            return func
        else:
            return None
