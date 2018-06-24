# -*- coding: utf-8 -*-
import time
import asyncio

from mantra.util import parseMention, buildMention
from mantra.service.ttypes import TalkException, Message

from .util import util
from .util.pl import plugin


@plugin()
async def about(self, msg, args):
    await self.sendText(msg.to, (
        "「 About 」\n"
        "Mantra SEॐ\n"
        "A mantra for self control.\n"
        "\n"
        "「 Subscription 」\n"
        "Expired in: {}\n"
        "Key: {}\n"
        "Instance: {}"
        "\n"
        "「 Contact 」\n"
        "・ LINE: line://ti/p/~flysbee_\n"
        "\n"
        "︙MantraSE-{}ॐ"
    ).format(
        util.timeUnit(int(self._setting['subscription'] - time.time())),
        self.key.title(), self.helper.username, self.version))


@plugin()
async def abort(self, msg, args):
    await self._state['wait']['queue'].put(None)
    self._state.update({
        "broadcast": False,
        "fancyname": False,
        "mayhem": False,
        "purgeblocked": False,
        "wait": {
            "type": set(),
            "queue": asyncio.Queue(loop=self.loop),
        }
    })
    self._var['mimic'] = ''


@plugin()
async def getinfo(self, msg, args):
    if msg.toType == 0:  # USER
        contact = await self.Talk.getContact(msg.to)
        try:
            if args[1] == "id":
                await self.sendText(msg.to, contact.mid)
                return
            elif args[1] == "name":
                await self.sendText(msg.to,
                                    contact.displayName)
                return
            elif args[1] == "status":
                await self.sendText(msg.to,
                                    contact.statusMessage)
                return
        except IndexError:
            pass
        await self.sendText(msg.to, (
            "「 Info 」\n"
            "Name:\n"
            "{}\n"
            "\n"
            "Status:\n"
            "{}\n"
            "\n"
            "User ID:\n"
            "{}\n"
            "Whitelisted: {}"
        ).format(
            contact.displayName, contact.statusMessage, contact.mid,
            "Yes" if contact.mid in self._setting['whitelist'] else "No"))
    elif msg.toType in {1, 2}:  # ROOM, GROUP
        mention = parseMention(msg)
        if mention is not None:
            conts = await self.Talk.getContacts(mention)
            for cont in conts:
                try:
                    if args[1] == "id":
                        await self.sendText(msg.to, cont.mid)
                        continue
                    elif args[1] == "name":
                        await self.sendText(msg.to, cont.displayName)
                        continue
                    elif args[1] == "status":
                        await self.sendText(msg.to, cont.statusMessage)
                        continue
                except IndexError:
                    pass
                await self.sendText(msg.to, (
                    "「 Info 」\n"
                    "Name:\n"
                    "{}\n"
                    "\n"
                    "Status:\n"
                    "{}\n"
                    "\n"
                    "User ID:\n"
                    "{}\n"
                    "Whitelisted: {}"
                ).format(
                    cont.displayName, cont.statusMessage, cont.mid,
                    "Yes" if cont.mid in self._setting['whitelist'] else "No"))
        else:
            group = (await self.Talk.getGroupsV2([msg.to]))[0]
            try:
                if args[1] == 'id':
                    await self.sendText(msg.to, msg.to)
                elif args[1] == 'name':
                    await self.sendText(msg.to, group.name)
                return
            except IndexError:
                pass
            await self.sendText(msg.to, (
                "「 Info 」\n"
                "Group Name:\n"
                "{}\n"
                "\n"
                "Group ID:\n"
                "{}\n"
                "\n"
                "Members: {}\n"
                "Invitations: {}\n"
                "\n"
                "Created at:\n"
                "{} UTC\n"
                "by {}"
            ).format(
                group.name, group.id, len(group.memberMids),
                len(group.inviteeMids) if group.inviteeMids else 0,
                util.timestampToDate(group.createdTime, True),
                "None" if group.creator is None else group.creator.displayName))


@plugin()
async def mentionall(self, msg, args):
    group = (await self.Talk.getGroupsV2([msg.to]))[0]
    try:
        group.memberMids.remove(self.mid)
    except ValueError:
        pass
    members = util.splitList(group.memberMids, 100)
    for chunk in members:
        base = ("「 Mention 」{}").format(
            "\n・@!" * len(chunk)
        )
        mention = buildMention(base, chunk)
        message = Message(to=msg.to, text=base,
                          contentType=0,
                          contentMetadata=mention)
        await self.Talk.sendMessage(0, message)


@plugin()
async def contact(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Contact 」\n"
            "Usage: {} contact <mid|userid>"
        ).format(self.key.title()))
    else:
        if args[1][0] == "u" and len(args[1]) == 33:
            contact = await self.Talk.getContacts([args[1]])
            if contact:
                await self.sendContact(msg.to, args[1])
            else:
                await self.sendText(msg.to, "「 Contact 」\nCannot find mid!")
        else:
            try:
                contact = await self.Talk.findContactByUserid(args[1])
                await self.sendContact(msg.to, contact.mid)
            except TalkException:
                await self.sendText(msg.to, "「 Contact 」\nCannot find userid!")
