# -*- coding: utf-8 -*-
from .util.pl import plugin


@plugin(group='Behavior')
async def autoadd(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Auto Add 」\n"
            "・Event Trigger\n"
            "on User Added\n"
            "\n"
            "・Behavior\n"
            "Add Back: {0}\n"
            "Auto Message: {1}\n"
            "{2}\n"
            "\n"
            "・Commands\n"
            "{3} autoadd on\n"
            "{3} autoadd off\n"
            "{3} autoadd setmsg\n"
            "{3} autoadd clearmsg"
        ).format(
            self._setting['autoadd'],
            "False" if not self._setting['automsg']
            else "True",
            self._setting['automsg'],
            self.key.title()))
    else:
        if args[1] == "on":
            self._setting['autoadd'] = True
            await self.sendText(msg.to, (
                "「 Auto Add 」\n"
                "Add back ENABLED."))
            self.saveSetting()
        elif args[1] == "off":
            self._setting['autoadd'] = False
            await self.sendText(msg.to, (
                "「 Auto Add 」\n"
                "Add back DISABLED."))
            self.saveSetting()
        elif args[1] == "setmsg":
            try:
                self._setting['automsg'] = f"\u200b{args[2]}"
                await self.sendText(msg.to, (
                    "「 Auto Add 」\n"
                    f"Auto message has been set to:\n{args[2]}"))
                self.saveSetting()
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Auto Add 」\n"
                    f"Usage: {self.key.title()} autoadd setmsg <text>"))
        elif args[1] == "clearmsg":
            automsg = self._setting['automsg']
            self._setting['automsg'] = ""
            self.saveSetting()
            await self.sendText(msg.to, (
                "「 Auto Add 」\n"
                "Auto message DISABLED.\n"
                "Message backup:\n"
                f"{automsg}"))


@plugin(group='Behavior')
async def autojoin(self, msg, args):
    state = {
        "0": "Disabled", "1": "Everyone",
        "2": "Whitelisted"
    }
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Auto Join 」\n"
            "・Event Trigger\n"
            "on User Invited\n"
            "\n"
            "・Behavior\n"
            "Auto Join: {1}\n"
            "Minimal Member: {2}\n"
            "\n"
            "・Commands\n"
            "{0} autojoin on\n"
            "{0} autojoin off\n"
            "{0} autojoin min").format(
            self.key.title(),
            state.get(self._setting['autojoin']['state']),
            self._setting['autojoin']['minmem']))
    else:
        if args[1] == "on":
            try:
                if args[2] in {"1", "2"}:
                    self._setting['autojoin']['state'] = args[2]
                    await self.sendText(msg.to, (
                        "「 Auto Join 」\n"
                        f"Auto join has been set to {state[args[2]]}."))
                    self.saveSetting()
                else:
                    raise IndexError
            except (IndexError, ValueError):
                await self.sendText(msg.to, (
                    "「 Auto Join 」\n"
                    "Usage: {0} autojoin on <value>\n"
                    "Value:\n"
                    "1 - Everyone\n"
                    "2 - Whitelisted"
                ).format(self.key.title()))
        elif args[1] == "off":
            self._setting['autojoin']['state'] = "0"
            await self.sendText(msg.to, (
                "「 Auto Join 」\n"
                "Auto join DISABLED."))
            self.saveSetting()
        elif args[1] == "min":
            try:
                amount = min(abs(int(args[2])), 499)
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Auto Join 」\n"
                    "Usage: {0} autojoin min <amount>"
                ).format(self.key.title()))
            except ValueError:
                await self.sendText(msg.to, (
                    "「 Auto Join 」\n"
                    "Amount must be positive integer."))
            else:
                self._setting['autojoin']['minmem'] = amount
                await self.sendText(msg.to, (
                    "「 Auto Join 」\n"
                    f"Minimal member has been set to {amount}."))
                self.saveSetting()


@plugin(group='Behavior')
async def autoread(self, msg, args):
    behavior = {
        "1": "Everyone", "2": "Whitelisted",
        "3": "Not Whitelisted"
    }
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Auto Read 」\n"
            "・Event Trigger\n"
            "on Personal Message: {0}\n"
            "on Group Message: {1}\n"
            "on Room Message: {2}\n"
            "\n"
            "・Behavior\n"
            "Auto read on: {3}\n"
            "\n"
            "・Commands\n"
            "{4} autoread on\n"
            "{4} autoread off\n"
            "{4} autoread behavior"
        ).format(
            self._setting['autoread']['chat'],
            self._setting['autoread']['group'],
            self._setting['autoread']['room'],
            behavior[
                self._setting['autoread']['behavior']
            ],
            self.key.title()
        ))
    else:
        if args[1] == "on":
            try:
                if args[2] == "0":
                    self._setting['autoread']['chat'] = True
                    self._setting['autoread']['group'] = True
                    self._setting['autoread']['room'] = True
                elif args[2] == "1":
                    self._setting['autoread']['chat'] = True
                elif args[2] == "2":
                    self._setting['autoread']['group'] = True
                elif args[2] == "3":
                    self._setting['autoread']['room'] = True
                else:
                    raise IndexError
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Auto read trigger has been updated."))
                self.saveSetting()
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Usage: {0} autoread on <trigger>"
                    "\nTrigger:\n"
                    "1 - Personal\n"
                    "2 - Group\n"
                    "3 - Room\n"
                    "0 - Turn on all of above"
                ).format(self.key.title()))
        elif args[1] == "off":
            try:
                if args[2] == "0":
                    self._setting['autoread']['chat'] = False
                    self._setting['autoread']['group'] = False
                    self._setting['autoread']['room'] = False
                elif args[2] == "1":
                    self._setting['autoread']['chat'] = False
                elif args[2] == "2":
                    self._setting['autoread']['group'] = False
                elif args[2] == "3":
                    self._setting['autoread']['room'] = False
                else:
                    raise IndexError
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Auto read trigger has been updated."))
                self.saveSetting()
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Usage: {0} autoread off <trigger>"
                    "\nTrigger:\n"
                    "1 - Personal\n"
                    "2 - Group\n"
                    "3 - Room\n"
                    "0 - Turn off all of above"
                ).format(self.key.title()))
        elif args[1] == "behavior":
            try:
                if args[2] in {"1", "2", "3"}:
                    val = args[2]
                else:
                    raise IndexError
                self._setting['autoread']['behavior'] = val
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Auto read behavior has been set to "
                    "{}.").format(behavior.get(val)))
                self.saveSetting()
            except IndexError:
                await self.sendText(msg.to, (
                    "「 Auto Read 」\n"
                    "Usage: {0} autoread behavior <type>\n"
                    "Type:\n"
                    "1 - Everyone\n"
                    "2 - Whitelisted\n"
                    "3 - Not Whitelisted"
                ).format(self.key.title()))
