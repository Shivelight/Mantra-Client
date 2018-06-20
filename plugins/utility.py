# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from .util.pl import plugin


async def get_kbbi(session, query):
    url = f"https://kbbi.kemdikbud.go.id/entri/{query}"
    result = await session.get(url)
    result = await result.text()
    if "Entri tidak ditemukan." in result:
        return None

    result = result[result.find('<h2>'):result.find('<h4>')]
    result = BeautifulSoup(result, 'html.parser')
    result = result.find_all('ol') + result.find_all('ul')

    meanings = []
    for r in result:
        for meaning in r.find_all('li'):
            word_class = meaning.find(color="red").get_text().strip()
            full_meaning = meaning.get_text().strip()[len(word_class):]
            if word_class:
                temp = f"({word_class}){full_meaning}"
            else:
                temp = f"{full_meaning}"
            meanings.append(temp)

    return meanings


@plugin(group='Utility')
async def kbbi(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Kbbi 」\n"
            "Usage: /kbbi <word>"))
    else:
        word = ' '.join(args[1:])
        kbbi = await get_kbbi(self.session, word)
        if kbbi is not None:
            base = ""
            for id_, value in enumerate(kbbi, 1):
                base += f"\n\n{id_}. {value}"
            await self.sendText(msg.to, (
                "「 Kbbi 」\n"
                f"Word: {args[1]}"
                f"{base}"))
        else:
            await self.sendText(msg.to, (
                "「 Kbbi 」\n"
                f"No definition found for the word '{word}'."))
