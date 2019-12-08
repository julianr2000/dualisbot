#!/usr/bin/python

from dualisbot.cmdline import parse_args
from dualisbot.config import read_config, get_config_val
from dualisbot.webnav import get_semesters

def main():
    parse_args()
    read_config()
    sems = get_semesters()
    for sem in sems:
        to_display = get_config_val('semester')
        if to_display is None or sem.number == to_display:
            for res in sem.result_infos:
                res.pretty_print()

if __name__ == '__main__':
    main()

