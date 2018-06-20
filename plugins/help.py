# -*- coding: utf-8 -*-
from inspect import cleandoc

from .util.pl import plugin


@plugin(name='help', in_help=False)
async def _help(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Mantra 」\n"
            f"{self._help}\n"
            "mykey\n"
            "\n"
            "Tip: '{0} help <command>' "
            "to view detailed info♪"
        ).format(self.key.title()))
    else:
        if args[1] == "help":
            await self.sendText(msg.to, "You really need help for the help command?")
        elif args[1] in self.commands and self.commands[args[1]].__doc__:
            doc = f"{cleandoc(self.commands[args[1]].__doc__)}"
            await self.sendText(msg.to, (
                "「 Mantra 」\n"
                f"Help: {args[1]}\n\n{doc}"
            ).format(key=self.key.title()))
        else:
            await self.sendText(msg.to, (
                f"「 Mantra 」\nCannot find help page for '{args[1]}'."))
