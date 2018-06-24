# -*- coding: utf-8 -*-
import time

from .util.pl import plugin


@plugin(in_help=False)
async def mantra(self, msg, args):
    (
        "*｡★･\n"
        "\u3000\u3000･ *ﾟ｡\u3000\u3000 *\n"
        "\u3000 ･ ﾟ*｡･ﾟ★｡\n"
        "\u3000\u3000\u3000☆ﾟ･｡°*. ﾟ\n"
        " \u3000\u3000ﾟ｡·*･｡ ﾟ*\n"
        "\u3000\u3000\u3000ﾟ *.｡☆｡★\u3000･\n"
        "\u3000\u3000* ☆ ｡･ﾟ*.｡\n"
        "\u3000\u3000  \u3000 *\u3000★ ﾟ･｡ *  ｡\n"
        "\u3000\u3000\u3000\u3000･\u3000\u3000ﾟ☆ ｡\n"
        "                  ｡･ﾟ*.*\u3000★ ﾟ･｡ *\n"
        "                 ☆∴｡\u3000*\n"
        "       \u3000･ﾟ*｡★･\n"
        "\u3000\u3000･ *ﾟ｡\u3000\u3000 *\n"
        " ･ ﾟ*｡･ﾟ★｡\n"
        "     \u3000ﾟ｡·*･｡\n"
        "    \u3000ﾟ｡·*･｡\n"
        "          \U00100402\U0010018a\U0010ffff")


#@plugin(in_help=False)
async def debug(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Debug 」\n"
            "{0} debug speed"
        ).format(self.key.title()))
    else:
        if args[1] == "speed":
            debug_speed_a = time.time()
            await self.Talk.fetchOperations(0, 1)
            debug_speed_b = time.time()
            await self.sendText(msg.to, (
                "「 Debug 」\n"
                "Type: speed\n"
                "Time taken: {}"
            ).format(debug_speed_b - debug_speed_a))
