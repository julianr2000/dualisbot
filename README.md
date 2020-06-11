# Dualisbot with Pushbullet Integration
A script to scrape test results from DHBW Dualis and send any updates to you or your channel via Pushbullet

## Installation
**Requirements:** `Python >= 3.8.0`
- Clone this repository
```
$ git clone 'https://github.com/julianr2000/dualisbot-notification'
$ cd dualisbot-notification
```
- Install dependencies
```
$ python3 -m pip install -r requirements.txt --user
```


## Basic usage
Inside the `dualisbot-notification` directory, execute
```
$ python3 main.py
```

Sample output (shortened):
```
$ python3 main.py 
Mathematik II (WiSe 2019/20)
Versuch                  Prüfung                  Bewertung               
WiSe 2019/20             Klausur (50%)            noch nicht gesetzt      
Gesamt:                                           noch nicht gesetzt      
Datenbanken (WiSe 2019/20)
Versuch                  Prüfung                  Bewertung               
WiSe 2019/20             Klausurarbeit oder       noch nicht gesetzt      
                         Kombinierte Prüfung                              
                         (100%)                                           
Gesamt:                                           noch nicht gesetzt      
Kommunikations- und Netztechnik (WiSe 2019/20)
Versuch                  Prüfung                  Bewertung               
WiSe 2019/20             Klausur (100%)                                   
                         Netztechnik I (60%)      90,0                    
Gesamt:                                           noch nicht gesetzt      
...
```

You can restrict the search to one semester (this is faster than querying all pages):
```
$ python3 main.py --semester 3
```

Additionally, you can output only test results that have changed since the last invocation of the script and let it send you a pushbullet notification of these results manually
```
$ python3 main.py --new
```

## Cronjob (run it automatically in the background)
Only possible on Unix systems like Linux and macOS. Set to run every 15 minutes.
```
$ python3 Install_Crontab.py
```

## Pushbullet Channel
If you also want to use a Pushbullet Channel (different to normal notifications) to recieve these results, you have to change usePushbulletChannel in the file resultdata.py to True and if you have multiple channels, you have to change the channel. 
