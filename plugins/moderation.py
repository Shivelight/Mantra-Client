# -*- coding: utf-8 -*-
import asyncio
import time

from mantra.service.ttypes import Message, MessageBoxV2MessageId
from mantra.util import parseMention, buildMention

from .util import util
from .util.pl import plugin


@plugin(group='Moderation')
async def cancelall(self, msg, args):
    if msg.toType != 2:
        return
    group = await self.Talk.getGroupsV2([msg.to])
    if not group[0].inviteeMids:
        await self.sendText(msg.to, "「 Cancel 」\nNothing to cancel♪")
    else:
        for mid in group[0].inviteeMids:
            await self.Talk.cancelGroupInvitation(0, group[0].id, [mid])
            await asyncio.sleep(0.8)
        await self.sendText(msg.to, (
            "「 Cancel 」\n"
            f"{len(group[0].inviteeMids)} invitations cancelled♪"))


@plugin(group='Moderation')
async def kick(self, msg, args):
    if msg.toType != 2:
        return
    mentions = parseMention(msg)
    if mentions is not None:
        tasks = [
            self.Talk.kickoutFromGroup(0, msg.to,
                                       [mention])
            for mention in mentions
        ]
        done, pending = await asyncio.wait(tasks)
        for t in pending:
            print(t)
            t.cancel()
    else:
        await self.sendText(msg.to, (
            "「 Kick 」\n"
            "You have to mention at least a user♪"))


@plugin(group='Moderation')
async def lurk(self, msg, args):
    if msg.toType != 2:
        return
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Lurk 」\n"
            "{0} lurk on\n"
            "{0} lurk off\n"
            "{0} lurk result"
        ).format(self.key))
    else:
        if args[1] == "on":
            try:
                del self._var['lurk'][msg.to]
            except KeyError:
                pass
            self._var['lurk'][msg.to] = {"id": msg.id,
                                         "lurker": [],
                                         "exclude": set()}
            await self.sendText(msg.to, (
                "「 Lurk 」\n"
                "Lurk point set♪"))
        elif args[1] == "off":
            try:
                del self._var['lurk'][msg.to]
            except KeyError:
                pass
            await self.sendText(msg.to, (
                "「 Lurk 」\n"
                "Lurk point unset♪"))
        elif args[1] == "result":
            try:
                if not self._var['lurk'][msg.to]['lurker']:
                    await self.sendText(msg.to, (
                        "「 Lurk 」\n"
                        "Lurkers:\nNone"))
                else:
                    L = self._var['lurk'][msg.to]['lurker']
                    base = ("「 Lurking 」\n"
                            "Lurkers:{}"
                            ).format("\n・@!" * len(L))
                    mts = buildMention(base, L)
                    message = Message(to=msg.to, text=base,
                                      contentType=0,
                                      contentMetadata=mts)
                    await self.Talk.sendMessage(0, message)
            except KeyError:
                await self.sendText(msg.to, (
                    "「 Lurk 」\n"
                    "Lurk point is not set♪"))


@plugin(group='Moderation')
async def rejectall(self, msg, args):
    groups = await self.Talk.getGroupIdsInvited()
    for group in groups:
        await self.Talk.rejectGroupInvitation(0, group)
    await self.sendText(msg.to, (
        "「 Reject 」\n{} groups rejected♪").format(len(groups)))


@plugin(group='Moderation')
async def mayhem(self, msg, args):
    if msg.toType != 2:
        return
    group = await self.Talk.getGroupsV2([msg.to])
    members = group[0].memberMids
    try:
        members.remove(self.mid)
    except ValueError:
        pass
    for whitelisted in self._setting['whitelist']:
        try:
            members.remove(whitelisted)
        except ValueError:
            pass
    task = [
        self.Talk.kickoutFromGroup(0, msg.to, [x])
        for x in members
    ]
    done, pending = await asyncio.wait(task)
    for t in pending:
        t.cancel()


@plugin(group='Moderation')
async def unsend(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Unsend 」\n"
            "Usage: {} unsend <amount>").format(self.key.title()))
    else:
        try:
            amount = min(abs(int(args[1])), 100)
        except ValueError:
            await self.sendText(
                msg.to, "「 Unsend 」\nAmount must be positive integer.")
        else:
            msg_lookup = await self.Talk.getPreviousMessagesV2WithReadCount(
                msg.to, MessageBoxV2MessageId(msg.createdTime, int(msg.id)), 101)
            remaining = amount

            # LINE is using millis
            currtime = int(time.time() * 1000)
            for message in msg_lookup:
                # Message unsend period in millis = 86400000
                if remaining and (currtime - message.createdTime) < 86400000:
                    if message.from_ == self.mid and message.id != msg.id:
                        await self.Talk.unsendMessage(0, message.id)
                        await asyncio.sleep(0.1)
                        remaining -= 1
                else:
                    break
            await self.sendText(msg.to, (
                f"「 Unsend 」\n{amount - remaining} messages retracted."))


# Whitelist command

def add_whitelist(self, mids):
    seen = set(self._setting['whitelist'])
    for mid in mids:
        if mid not in seen:
            self._setting['whitelist'].append(mid)
    self.saveSetting()


def del_whitelist(self, mids, index=False):
    if index is True:
        self._setting['whitelist'] = [
            mid for index, mid in enumerate(self._setting['whitelist'], 1)
            if index not in mids]  # mids = indexes
    else:
        for mid in mids:
            try:
                self._setting['whitelist'].remove(mid)
            except ValueError:
                pass
    self.saveSetting()


@plugin(group='Moderation')
async def whitelist(self, msg, args):
    if len(args) == 1:
        whitelist = []
        if self._setting['whitelist']:
            contacts = await self.Talk.getContacts(
                self._setting['whitelist'])
            for index, contact in enumerate(contacts, 1):
                whitelist.append(f"{index}. {contact.displayName}\n")
        await self.sendText(msg.to, (
            "「 Whitelist 」\n"
            "・Whitelisted Users\n"
            "{0}\n"
            "・Commands\n"
            "{1} whitelist add\n"
            "{1} whitelist del\n"
            "{1} whitelist clear\n"
            "See '{1} help whitelist' for detail♪"
        ).format(
            "None\n" if not whitelist else ''.join(whitelist),
            self.key.title()
        ))
    else:
        if args[1] == "add":
            if msg.toType == 0:
                add_whitelist(self, [msg.to])
                await self.sendText(msg.to, (
                    "「 Whitelist 」\n"
                    "Added to whitelist♪"))
            elif msg.toType == 2:
                mention = parseMention(msg)
                if mention is not None:
                    add_whitelist(self, mention)
                    await self.sendText(msg.to, (
                        "「 Whitelist 」\n"
                        "Mentioned users has been added "
                        "to the whitelist♪"))
                else:
                    await self.sendText(msg.to, (
                        "「 Whitelist 」\n"
                        "You have to mention atleast a "
                        "user♪"))

        elif args[1] == "del":
            if msg.toType == 0:
                del_whitelist(self, [msg.to])
                await self.sendText(msg.to, (
                    "「 Whitelist 」\n"
                    "Removed from whitelist♪"))
            elif msg.toType == 2:
                mention = parseMention(msg)
                if mention is not None:
                    del_whitelist(self, mention)
                    await self.sendText(msg.to, (
                        "「 Whitelist 」\n"
                        "Mentioned users has been removed "
                        "from the whitelist♪"))
                else:
                    del args[0:2]
                    indexes = util.parseInt(
                        ",".join(args),
                        len(self._setting['whitelist']))
                    if indexes:
                        del_whitelist(self, indexes, True)
                        await self.sendText(msg.to, (
                            "「 Whitelist 」\n"
                            "Specified indexes has been "
                            "removed from the whitelist♪"))
                    else:
                        await self.sendText(msg.to, (
                            "「 Whitelist 」\n"
                            "You have to mention atleast a "
                            "user♪"))

        elif args[1] == "clear":
            self._setting['whitelist'] = []
            await self.sendText(msg.to, (
                "「 Whitelist 」\n"
                "Specified indexes has been removed from "
                "the whitelist♪"))
            self.saveSetting()
