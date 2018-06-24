# -*- coding: utf-8 -*-
from inspect import getmembers, isfunction
from importlib import reload, import_module
from os.path import basename
from collections import defaultdict
import glob
import time
import asyncio

from multidict import CIMultiDict


async def NOTIFIED_ADD_CONTACT(self, op):
    if self._setting["autoadd"]:
        await self.Talk.findAndAddContactsByMid(0, op.param1, 0, None)
    if self._setting["automsg"]:
        await self.sendText(op.param1, self._setting["automsg"])


async def NOTIFIED_INVITE_INTO_GROUP(self, op):
    if self._setting["autojoin"]["state"] == "0":
        return
    if self.mid in op.param3.split("\x1e"):
        # check if group total member fulfill the condition
        group = (await self.Talk.getGroupsV2([op.param1]))[0]
        if len(group.memberMids) < self._setting["autojoin"]["minmem"]:
            return

        if self._setting["autojoin"]["state"] == "1":
            await self.Talk.acceptGroupInvitation(0, op.param1)
        elif self._setting["autojoin"]["state"] == "2" and op.param2 in set(
            self._setting["whitelist"]
        ):
            await self.Talk.acceptGroupInvitation(0, op.param1)


async def SEND_MESSAGE(self, op):
    try:
        if op.message.text.endswith("\u200b"):
            return
    except Exception:
        pass
    else:
        if op.message.text.startswith("mykey"):
            args = op.message.text.split(maxsplit=2)
            if len(args) == 1:
                await self.sendText(
                    op.message.to,
                    (
                        "Your key: {}\n"
                        "mykey set - set your key\n"
                        "mykey off - disable your key\n"
                        "mykey reset - reset your key"
                    ).format("DISABLED" if not self.key else self.key.title()),
                )
            else:

                def change_key(key):
                    self._setting["key"] = key.lower()
                    self.saveSetting()

                if args[1] == "reset":
                    change_key("mantra")
                    await self.sendText(op.message.to, "Key has been set to Mantra")
                elif args[1] == "off":
                    change_key("")
                    await self.sendText(op.message.to, "Key disabled.")
                elif args[1] == "set":
                    try:
                        change_key(args[2][:25])
                        await self.sendText(
                            op.message.to,
                            "Key has been set to {}".format(self.key.title()),
                        )
                    except IndexError:
                        await self.sendText(op.message.to, "Usage: mykey set <key>")
            return
        lenn = len(self.key)
        if op.message.text[0:lenn].lower() == self.key:
            now = time.time()
            if now > self._setting["subscription"]:
                det = now - self._setting["subscription"]
                if det < self.grace_period:
                    await self.sendText(
                        op.message.to,
                        (
                            "「 Mantra 」\n"
                            "Your account is currently in grace period.\n"
                            "Renew your subscription as soon as possible "
                            "to avoid getting purged."
                        ),
                    )
                    if lenn == 0:
                        self._setting["key"] = "mantra"
                        self.saveSetting()
                        await self.sendText(op.message.to, "Key has been set to Mantra")
                    return
                else:
                    self.purged = True
                    self.stop()
                    if self.helper is not None:
                        coro = self.helper.purge(self.mid)
                        asyncio.run_coroutine_threadsafe(coro, self.helper.loop)
                    await self.sendText(op.message.to, "Your account has been purged.")
                    return
            cmd = op.message.text[lenn:].split(maxsplit=2)
            try:
                await self.commands[cmd[0]](self, op.message, cmd)
            except (KeyError, IndexError):
                pass

    if op.message.contentType in self._state["wait"]["type"]:
        await self._state["wait"]["queue"].put(op.message)


async def RECEIVE_MESSAGE(self, op):
    msg = op.message
    try:
        self._var["lurk"][msg.to]["lurker"].remove(msg.from_)
        self._var["lurk"][msg.to]["exclude"].add(msg.from_)
    except (KeyError, ValueError):
        pass
    if msg.toType == 0:  # USER
        if self._setting["autoread"]["chat"] is True:
            if self._setting["autoread"]["behavior"] == "1":
                await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "2":
                if msg.from_ in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "3":
                if msg.from_ not in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
        return

    elif msg.toType == 1:  # ROOM
        if self._setting["autoread"]["room"] is True:
            if self._setting["autoread"]["behavior"] == "1":
                await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "2":
                if msg.from_ in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "3":
                if msg.from_ not in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)

    elif msg.toType == 2:  # GROUP
        if self._setting["autoread"]["group"] is True:
            if self._setting["autoread"]["behavior"] == "1":
                await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "2":
                if msg.from_ in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
            elif self._setting["autoread"]["behavior"] == "3":
                if msg.from_ not in set(self._setting["whitelist"]):
                    await self.Talk.sendChatChecked(0, msg.to, msg.id, None)
    try:
        if msg.from_ == self._var["mimic"] and not msg.text.endswith("\u200b"):
            if msg.contentType in {0, 1, 2, 13, 19}:
                await self.forwardMessage(msg.to, msg)
    except AttributeError:
        pass


async def NOTIFIED_READ_MESSAGE(self, op):
    try:
        if (
            op.param2 not in self._var["lurk"][op.param1]["exclude"] and
            op.param2 not in self._var["lurk"][op.param1]["lurker"]
        ):
            self._var["lurk"][op.param1]["lurker"].append(op.param2)
    except KeyError:
        pass


def setup(cls):
    cls.operation.update(
        {
            5: NOTIFIED_ADD_CONTACT,
            13: NOTIFIED_INVITE_INTO_GROUP,
            25: SEND_MESSAGE,
            26: RECEIVE_MESSAGE,
            55: NOTIFIED_READ_MESSAGE,
        }
    )
    # reload(commands)
    cls.commands = CIMultiDict()
    help_list = defaultdict(list)  # temp cmd categorizer
    helps = []  # formated help

    pls = glob.glob("./plugins/*.py")
    for pl in pls:
        try:
            mod = import_module(f"plugins.{basename(pl)[:-3]}")

            # remove all attribute so there is no duplicate in case any
            # of it is removed from the source
            for attr in dir(mod):
                if attr not in ("__name__", "__file__"):
                    delattr(mod, attr)

            module = reload(mod)
        except Exception as e:
            print("Cannot load plugin: ", pl)
            print(e)
            continue
        for name, fn in getmembers(module, isfunction):
            if not hasattr(fn, "is_plugin"):
                continue

            name = fn.name if fn.name else fn.__name__
            cls.commands.update({name: fn})
            if not fn.in_help:
                continue

            group = fn.group if fn.group is not None else "General"
            help_list[group.title()].append(name)

    core = help_list.pop("General", [])
    if core:
        helps.append("・General\n")
        helps.append("\n".join([f"{{0}} {c}" for c in sorted(core)]))
        helps.append("\n")
    for cat, cmd in sorted(help_list.items()):
        helps.append(f"\n・{cat}\n")
        helps.append("\n".join([f"{{0}} {c}" for c in sorted(cmd)]))
        helps.append("\n")
    cls._help = "".join(helps)
