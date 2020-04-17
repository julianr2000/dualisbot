#!/usr/bin/python3

import asyncio
import sys

import aiohttp

from dualisbot.cmdline import parse_args
from dualisbot.config import read_config, save_credentials
from dualisbot.webnav import get_semesters, LoginFailed
from dualisbot.resultdata import do_output_io

async def main():
    parse_args()
    read_config()

    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            sems = await get_semesters(session)
            await do_output_io(session, sems)
    except aiohttp.client_exceptions.ClientConnectorError:
        print("Failure establishing network connection. Please try reversing the polarity of the wifi cable.", file=sys.stderr)
        sys.exit(1)
    except LoginFailed as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    else:
        save_credentials()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # don't print stacktrace
        sys.exit(1)