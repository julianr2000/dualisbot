from crontab import CronTab
import os

dir_path = os.path.dirname(os.path.abspath(__file__))

cron = CronTab(user=True)
command_path = "python3 \"" + dir_path + "/main.py\" --new"
print (command_path)
job = cron.new(command= command_path)
job.minute.every(15)
cron.write()

print('cron.write() was just executed')