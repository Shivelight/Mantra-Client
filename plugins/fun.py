# -*- coding: utf-8 -*-
import random
import asyncio

from bs4 import BeautifulSoup
from mantra.util import parseMention

from .util.pl import plugin
from .util.aes256 import encrypt


GENIUS_TOKEN = "HP1halu_9Udi2yMJUyE5-rBSfjHSColCtKvd__s7lrB5BLb7s6lCXoz5WoZ1-Sso"
YODA_TOKEN = "andriod_YODAKoyqdRt0OjRBfjgurMNkCFh1AIMADoXkY4HAIy3BcfE2d"

ball_answers = [
    "It is certain",
    "It is decidedly so",
    "Without a doubt",
    "Yes definitely",
    "You may rely on it",
    "You can count on it",
    "As I see it, yes",
    "Most likely",
    "Outlook good",
    "Yes",
    "Signs point to yes",
    "Absolutely",
    "Reply hazy try again",
    "Ask again later",
    "Better not tell you now",
    "Cannot predict now",
    "Concentrate and ask again",
    "Don't count on it",
    "My reply is no",
    "My sources say no",
    "Outlook not so good",
    "Very doubtful",
    "Chances aren't good",
]


@plugin(name='8ball', group='Fun')
async def _8ball(self, msg, args):
    """Ask the 8ball a yes or no question.

    Usage: {key} 8ball <question>
    Example:
    {key} 8ball is Arkie awesome?
    """
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 8ball 」\n"
            "Usage: {} 8ball <question>"
        ).format(self.key.title()))
    else:
        answer = random.choice(ball_answers)
        # await self.sendText(msg.to, f"Waiting the 🎱 answer..")
        # await asyncio.sleep(random.random())
        await self.sendText(msg.to, f"\U00100402\U001001718ball\U0010ffff: {answer}")


@plugin(group='Fun')
async def dadjoke(self, msg, args):
    """Send a dad joke."""
    headers = {
        "Accept": "text/plain",
        "User-Agent": "Mantra, LINE Messenger Bot"
    }
    result = await self.session.get("https://icanhazdadjoke.com", headers=headers)
    if result.status_code != 200:
        await self.sendText(msg.to, (
            "「 Dad Joke 」\n"
            "Dad is busy, try again later.."))
    else:
        await self.sendText(msg.to, f"「 Dad Joke 」\n{result.text}")


@plugin(group='Fun')
async def chuck(self, msg, args):
    """Sends a Chuck Norris fact."""
    result = await self.session.get("https://api.chucknorris.io/jokes/random")
    if result.status_code == 200:
        joke = await result.json()
        await self.sendText(msg.to, f"「 Chuck Norris 」\n{joke['value']}")
    else:
        await self.sendText(msg.to, (
            "「 Chuck Norris 」\n"
            "Cannot catch ChuckNorrisException!"))


@plugin(group='Fun')
async def lyric(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Lyric 」\n"
            "Usage: {0} lyric <query>"
        ).format(self.key.title()))
        return

    headers = {'Authorization': f"Bearer {GENIUS_TOKEN}"}
    params = {'q': " ".join(args[1:])}
    result = await self.session.get("https://api.genius.com/search",
                                    params=params, headers=headers)
    if result.status_code == 200:
        js = result.json()
        if js['response']['hits'] and js['response']['hits'][0]['type'] == 'song':
            page = await self.session.get(js['response']['hits'][0]['result']['url'])
            html = BeautifulSoup(page.text, "html.parser")
            [h.extract() for h in html('script')]
            lyric = html.find("div", class_="lyrics").get_text().rstrip('\n\n')
            title = js['response']['hits'][0]['result']['full_title']
            await self.sendText(msg.to, (
                "「 Lyric 」\n"
                f"{title}{lyric}"))
        else:
            await self.sendText(msg.to, (
                "「 Lyric 」\n"
                "No lyric found.."))
    else:
        await self.sendText(msg.to, (
            "「 Lyric 」\n"
            "The server is busy.."))


@plugin(group='Fun')
async def mimic(self, msg, args):
    if len(args) == 1:
        if not self._var['mimic']:
            text = "Currently not mimicking anyone♪"
        else:
            text = "Mimicking {} ♪".format(
                (await self.Talk.getContact(self._var['mimic'])).displayName)
        await self.sendText(msg.to, (
            "「 Mimic 」\n"
            "{0}\n\n"
            "・Commands\n"
            "{1} mimic on <@|~>\n"
            "{1} mimic off"
        ).format(text, self.key.title()))
    else:
        if args[1] == "on":
            mention = parseMention(msg)
            if mention is not None:
                self._var['mimic'] = mention[0]
                await self.sendText(msg.to, (
                    "「 Mimic 」\n"
                    "Mimic ENABLED♪\n"
                    "Target: {}"
                ).format((await self.Talk.getContact(mention[0])).displayName))
        elif args[1] == "off":
            self._var['mimic'] = ""
            await self.sendText(msg.to, (
                "「 Mimic 」\n"
                "Mimic DISABLED♪"))


@plugin(group='Fun')
async def steal(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Steal 」\n"
            "Usage: {0} steal <type> [target]\n"
            "Type: pic, cover, vid\n"
            "Target: mention, mid"
        ).format(self.key.title()))
    else:
        if args[1] not in {"pic", "cover", "vid"}:
            return

        async def _steal(type_, mid):
            if type_ == "pic":
                await self.sendProfileImage(msg.to, mid)
            elif type_ == "cover":
                await self.sendProfileCover(msg.to, mid)
            elif type_ == "vid":
                c = await self.Talk.getContact(mid)
                if c.videoProfile:
                    url = f"https://obs.line-apps.com/os/p/{mid}"
                    messages = [{
                        "type": "video",
                        "originalContentUrl": f"{url}/vp",
                        "previewImageUrl": f"{url}"
                    }]
                    try:
                        await self.sendMessageViaApps(msg.to, messages)
                    except Exception:
                        await self.sendProfileVideo(msg.to, mid)
                else:
                    raise Exception

        if msg.toType == 0:
            try:
                try:
                    await _steal(args[1], args[2])
                except IndexError:
                    await _steal(args[1], msg.to)
                except Exception:
                    raise
            except Exception:
                await self.sendText(msg.to, (
                    "「 Steal 」\n"
                    "Nothing to steal♪"))

        elif msg.toType in {1, 2}:
            mention = parseMention(msg)
            if mention is None and msg.toType == 2:
                await self.sendGroupImage(msg.to, msg.to)
            elif mention is not None:
                try:
                    await _steal(args[1], mention[0])
                except Exception:
                    await self.sendText(msg.to, (
                        "「 Steal 」\n"
                        "Nothing to steal♪"))
            else:
                await self.sendText(msg.to, (
                    "「 Steal 」\n"
                    "You have to input a user♪"))


@plugin(name='coin', group='Fun')
async def flipcoin(self, msg, args):
    if msg.to in self._var['coin']:
        await self.sendText(msg.to, "The coin is still spinning..")
        return
    try:
        self._var['coin'].add(msg.to)
        choice = random.choice(['Heads', 'Tails'])
        await self.sendText(msg.to, "Flipping a coin.. heads or tails?")
        await asyncio.sleep(5)
        await self.sendText(msg.to, "\U00100b01\U00100180\U0010ffff25 seconds..")
        await asyncio.sleep(15)
        await self.sendText(msg.to, "\U00100b01\U00100181\U0010ffff10 seconds..")
        await asyncio.sleep(10)
        await self.sendText(msg.to, f"\U00100b01\U00100182\U0010ffff{choice}")
    except Exception:
        pass
    finally:
        self._var['coin'].remove(msg.to)


@plugin(group='Fun')
async def yoda(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Yoda 」\n"
            "Usage: {} yoda <sentence>"
        ).format(self.key.title()))
    else:
        auth = {'X-Orthosie-Api-Secret': YODA_TOKEN}
        result = await self.session.post(
            "http://api.funtranslations.com/translate/yoda.json",
            headers=auth, json={'text': ' '.join(args[1:])})
        try:
            await self.sendText(msg.to, result.json()['contents']['translated'])
        except KeyError:
            await self.sendText(msg.to, (
                "「 Yoda 」\n"
                "Busy, Yoda is. Try again later, please."))


@plugin(group='Fun')
async def urban(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Urban 」\n"
            "Usage: {0} urban <word>"
        ).format(self.key.title()))
    else:
        words = args[1:]
        result = await self.session.get("http://api.urbandictionary.com/v0/define",
                                        params={'term': words})
        terms = result.json()
        if terms is None or any(x in terms for x in {'error', 'errors'}) or \
                terms['result_type'] == "no_results":
            await self.sendText(msg.to, (
                "「 Urban 」\n"
                "There is no definition for {}♪"
            ).format(args[1:]))
        else:
            example = terms['list'][0]['example']
            await self.sendText(msg.to, (
                "「 Urban 」\n"
                "Word: {}\n"
                "Definition:\n"
                "{}{}"
            ).format(terms['list'][0]['word'], terms['list'][0]['definition'],
                     f"\n\n{example}" if example else ""))


@plugin(group='Fun')
async def tweet(self, msg, args):
    if len(args) == 1:
        await self.sendText(msg.to, (
            "「 Tweet 」\n"
            "Usage: {} tweet <username> <text>"
        ).format(self.key.title()))
    elif len(args) >= 3:
        url = ("https://nekobot.xyz/api/imagegen?type=tweet"
               f"&username={args[1]}&text={args[2]}")
        result = await self.session.get(url)
        rjson = await result.json()
        if rjson['success'] is True:
            tweet = f"mantra.arkiee.me/sv/{encrypt(rjson['message'])}"
            ori = f"https://images.weserv.nl/?q=70&il&url={tweet}"
            prev = f"https://images.weserv.nl/?q=70&il&w=250&h=250&url={tweet}"
            try:
                messages = [{
                    "type": "image",
                    "originalContentUrl": ori,
                    "previewImageUrl": prev,
                }]
                await self.sendMessageViaApps(msg.to, messages)
            except Exception as e:
                print("Tweet error: ", e)
