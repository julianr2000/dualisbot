#!/usr/bin/python

import sys

from requests.exceptions import ConnectionError

from dualisbot.cmdline import parse_args
from dualisbot.config import read_config, save_credentials
from dualisbot.webnav import get_semesters, LoginFailed
from dualisbot.resultdata import do_output_io

def main():
    parse_args()
    read_config()

    try:
        sems = get_semesters()
        save_credentials()
    except ConnectionError:
        print("Failure establishing network connection. Please try reversing the polarity of the wifi cable.", file=sys.stderr)
        sys.exit(1)
    except LoginFailed as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    do_output_io(sems)

if __name__ == '__main__':
    main()

