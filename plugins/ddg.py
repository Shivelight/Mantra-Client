# -*- coding: utf-8 -*-
import re
import random
from urllib.parse import quote_plus

from .util.pl import plugin
from .util.aes256 import encrypt

DDG = "https://duckduckgo.com"
VQD_REGEX = re.compile(r'vqd=(\d+)')


async def search_image(session, query):
    res = await session.post(DDG, data={'q': query})

    # Extract the vqd value
    vqd = VQD_REGEX.search(await res.text()).group(1)

    params = {
        'l': "wt-wt",
        'o': "json",
        'q': query,
        'vqd': vqd,
        'f': ",,,",
        'p': "-1",
    }

    # Safe search: 1 = strict, -1 = Moderate, -2 = Off
    cookies = "p=-2"

    url = f"{DDG}/i.js"
    res = await session.get(url, params=params, headers={'Cookie': cookies})
    data = await res.json(content_type=None)
    return data["results"]
    # requestUrl = url + data["next"];


@plugin(group='Fun')
async def img(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Image 」\n"
            "Usage: {} img <query>"
        ).format(self.key.title()))
    else:
        images = await search_image(self.session, ' '.join(args[1:]))
        image = random.choice(images)['image']
        imgurl = f"mantra.arkiee.me/sv/{encrypt(image)}"
        ori = f"https://images.weserv.nl/?q=70&il&url={imgurl}"
        prev = f"https://images.weserv.nl/?q=70&il&w=200&h=200&url={imgurl}"
        messages = [{
            "type": "image",
            "originalContentUrl": ori,
            "previewImageUrl": prev,
        }]
        try:
            await self.sendMessageViaApps(msg.to, messages)
        except Exception as e:
            print("img error: ", e)
