#!/usr/bin/python

from dualisbot.webnav import get_semesters

sems = get_semesters()
for sem in sems:
    for res in sem.result_infos:
        res.pretty_print()
