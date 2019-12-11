#!/usr/bin/python

import sys

from requests.exceptions import ConnectionError

from dualisbot.cmdline import parse_args
from dualisbot.config import read_config, get_config_val
from dualisbot.webnav import get_semesters, LoginFailed
from dualisbot.resultdata import sems_to_json, sems_pretty_print

def main():
    parse_args()
    read_config()
    try:
        sems = get_semesters()
    except ConnectionError:
        print("Failure establishing network connection. Please try reversing the polarity of the wifi cable.", file=sys.stderr)
        sys.exit(1)
    except LoginFailed as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    to_display = get_config_val('semester')
    if get_config_val('json'):
        print(sems_to_json(sems, to_display))
    else:
        sems_pretty_print(sems, to_display)

if __name__ == '__main__':
    main()

