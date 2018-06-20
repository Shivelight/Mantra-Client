# -*- coding: utf-8 -*-
from multidict import CIMultiDict

from .util.pl import plugin


LANGUAGE = CIMultiDict({
    "auto": "Detect language",
    "af": "Afrikaans",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "hy": "Armenian",
    "az": "Azerbaijani",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "ny": "Chichewa",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "co": "Corsican",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "tl": "Filipino",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "ht": "Haitian Creole",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "iw": "Hebrew",
    "hi": "Hindi",
    "hmn": "Hmong",
    "hu": "Hungarian",
    "is": "Icelandic",
    "ig": "Igbo",
    "id": "Indonesian",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "km": "Khmer",
    "ko": "Korean",
    "ku": "Kurdish (Kurmanji)",
    "ky": "Kyrgyz",
    "lo": "Lao",
    "la": "Latin",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "mi": "Maori",
    "mr": "Marathi",
    "mn": "Mongolian",
    "my": "Myanmar (Burmese)",
    "ne": "Nepali",
    "no": "Norwegian",
    "ps": "Pashto",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "sm": "Samoan",
    "gd": "Scots Gaelic",
    "sr": "Serbian",
    "st": "Sesotho",
    "sn": "Shona",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "sv": "Swedish",
    "tg": "Tajik",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zu": "Zulu",
})

langlist = "\n".join(f"{x} - {y}" for x, y in LANGUAGE.items() if x != "auto")


async def translator(session, source, dest, query):
    try:
        fullsource = LANGUAGE[source]
        fulldest = LANGUAGE[dest]
    except KeyError:
        return 1

    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        'client': "gtx",
        'sl': source,
        'tl': dest,
        'dt': "t",
        'dj': 1,
        'ie': "UTF-8",
        'oe': "UTF-8",
        'q': query,
    }
    headers = {
        'User-Agent': ("Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/65.0.3325.181 Safari/537.36")
    }
    result = await session.get(url, params=params, headers=headers)
    if result.status_code != 200:
        return 2

    jsn = result.json()
    trans = ''.join(x['trans'] for x in jsn['sentences'])

    if source == "auto":
        source = jsn['src']
        fullsource = LANGUAGE[source]

    return (source, dest, trans, query, fullsource, fulldest)


@plugin(group='Utility')
async def translate(self, msg, args):
    if len(args) <= 2:
        await self.sendText(msg.to, (
            "「 Translate 」\n"
            "Usage: {0} translate <lang> <text>\n\n"
            "Tip: See '{0} language' for available language."
        ).format(self.key.title()))
    else:
        trans = await translator(self.session, "auto", args[1], args[2])
        if trans == 1:
            await self.sendText(msg.to, (
                "「 Translate 」\n"
                "Invalid language parameters."))
        elif trans == 2:
            await self.sendText(msg.to, (
                "「 Translate 」\n"
                "Server is busy, try again later."))
        else:
            await self.sendText(msg.to, (
                "「 Translate 」\n"
                f"Source: {trans[4]} ({trans[0]})\n"
                f"Destination: {trans[5]} ({trans[1]})"))
            await self.sendText(msg.to, trans[2])


@plugin(group='Utility', in_help=False)
async def language(self, msg, args):
    await self.sendText(msg.to, (
        "「 Language 」\n"
        f"Available language:\n{langlist}"))
