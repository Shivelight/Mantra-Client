import argparse
import asyncio
import client
import uvloop

parser = argparse.ArgumentParser()
parser.add_argument("username", help="Bind Mantra-Client to this address.")
parser.add_argument("--bind", help="Bind Mantra-Client to this address.")
args = parser.parse_args()

loop = asyncio.new_event_loop()
# loop = uvloop.new_event_loop()

serv = client.MantraClient(args.bind, args.username, loop=loop)
serv.start()
