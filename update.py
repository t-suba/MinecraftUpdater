import os
import time
import shutil
import hashlib
import time
from datetime import datetime
import logging
import requests


# CONFIGURATION
UPDATE_TO_SNAPSHOT = False
BACKUP_DIR = 'world_backups'
LOG_FILENAME = 'auto_updater.log'
RAM_INITIAL = '10G'
RAM_MAX = '10G'

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

logging.basicConfig(filename=LOG_FILENAME,level=logging.INFO)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# retrieve version manifest
response = requests.get(MANIFEST_URL)
data = response.json()

if UPDATE_TO_SNAPSHOT:
    minecraft_ver = data['latest']['snapshot']
else:
    minecraft_ver = data['latest']['release']

# get checksum of running server
if os.path.exists('/home/opc/minecraft/server/server.jar'):
    sha = hashlib.sha1()
    f = open("/home/opc/minecraft/server/server.jar", 'rb')
    sha.update(f.read())
    cur_ver = sha.hexdigest()
else:
    cur_ver = ""

for version in data['versions']:
    if version['id'] == minecraft_ver:
        jsonlink = version['url']
        jar_data = requests.get(jsonlink).json()
        jar_sha = jar_data['downloads']['server']['sha1']

        logging.info('Your sha1 is ' + cur_ver + '. Latest version is ' + str(minecraft_ver) + " with sha1 of " + jar_sha)

        if cur_ver != jar_sha:
            logging.info('Updating server...')
            link = jar_data['downloads']['server']['url']
            logging.info('Downloading .jar from ' + link + '...')
            response = requests.get(link)
            with open('server.jar', 'wb') as jar_file:
                jar_file.write(response.content)
            logging.info('Downloaded.')
            os.system('tmux send-keys -t minecraft-server "say Server will shutdown temporarily to update in 5 minutes." Enter')
            logging.info('Shutting down server in 5 minutes.')

            
            time.sleep(240)
            os.system('tmux send-keys -t minecraft-server "say Server will shutdown temporarily to update in 1 minute." Enter')

            time.sleep(90)

            logging.info('Stopping server.')
            os.system('tmux kill-session -t minecraft-server')
            time.sleep(5)
            
            logging.info('Updating server .jar')

            if os.path.exists('/home/opc/minecraft/server/server.jar'):
                os.remove('/home/opc/minecraft/server/server.jar')

            os.rename('server.jar', '/home/opc/minecraft/server/server.jar')
            logging.info('Starting server...')
            os.chdir("/home/opc/minecraft/server")
            os.system('tmux new-session -d -s minecraft-server')
            os.system('tmux send-keys -t minecraft-server "java -Xms10G -Xmx10G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dusing.aikars.flags=https://mcflags.emc.gs -Daikars.new.flags=true -jar server.jar nogui" Enter')

        else:
            logging.info('Server is already up to date.')

        break
