# -*- coding: utf-8 -*-
import datetime
import json

UNIT_INTERVALS = (
    ('years', 31536000),
    ('months', 2628000),
    ('weeks', 604800),
    ('days', 86400),
    ('hours', 3600),
    ('minutes', 60),
    ('seconds', 1),
)


def timeUnit(seconds, granularity=2):
    result = []
    for name, count in UNIT_INTERVALS:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def timestampToDate(timestamp, millis=False):
    timestamp = timestamp if millis is False else timestamp / 1000
    return datetime.datetime.utcfromtimestamp(
        timestamp).strftime('%Y-%m-%d %H:%M:%S')


def splitList(llist, size):
    for i in range(0, len(llist), size):
        yield llist[i:i + size]


def parseInt(string, maxInt):
    selection = set()
    tokens = [x.strip() for x in string.split(',')]
    for i in tokens:
        if len(i) > 0:
            if i[:1] == "<":
                i = "1-{}".format(i[1:])
            elif i[:1] == ">":
                i = "{}-{}".format(i[1:], maxInt)
        try:
            selection.add(abs(int(i)))
        except Exception:
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    first = token[0]
                    last = token[len(token) - 1]
                    for x in range(first, last + 1):
                        selection.add(abs(x))
            except Exception:
                pass
    return selection
