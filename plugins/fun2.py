# -*- coding: utf-8 -*-

from mantra.util import parseMention

from .util.pl import plugin


@plugin(group='Fun')
async def gift(self, msg, args):
    if msg.toType in {1, 2}:
        mids = parseMention(msg)
        if mids is not None:
            for mid in mids:
                await self.sendPresent(mid)
            await self.sendText(msg.to, "「 Gift 」\nGift sent.")
            return
    await self.sendPresent(msg.to)

