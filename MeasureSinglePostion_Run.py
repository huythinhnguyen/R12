import sys
import os
import logging
import datetime
import time


DATE = datetime.datetime.now().strftime('%h%d')
TIME = datetime.datetime.now().strftime('%H:%M:%S')
SAVE_PATH = os.path.join('data', DATE+'_'+TIME)
LOG_FILE = os.path.join(SAVE_PATH, 'log.txt')
# Path to the directory where the script is located
if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')
from script import SCRIPT_MeasureSinglePosition as script
#####################################################
######### USER EDIT FROM HERE #######################

WORLD_X = -200 #mm 
WORLD_Y = 200 #mm
WORLD_PITCH = 0 #deg
WORLD_YAW = 27.5 #deg
DRY_RUN = False # Set False to do measurement, True to skip measurement
REPEATS = 50
RT_PLOT = False # Set True to plot the data in real time
DELAY = 0.25
SAVE_DATA = False # Set True to save the data
# This is need to revise to a function of a circle --> Not optimal but leave it here for now
DESCRIPTION = ''


######### USER EDIT UNTIL HERE #######################
######################################################

REACH_TABLE = {
    'x': None,
    'y': [0, 100, 200, 300],
    'z': [500, 400, 300, 300],
}
logging.info("WORLD_X = %s", WORLD_X)
logging.info("WORLD_Y = %s", WORLD_Y)
logging.info("WORLD_PITCH = %s", WORLD_PITCH)
logging.info("WORLD_YAW = %s", WORLD_YAW)
logging.info("DRY_RUN = %s", DRY_RUN)
logging.info("REPEATS = %s", REPEATS)
logging.info("RT_PLOT = %s", RT_PLOT)
logging.info("DELAY = %s", DELAY)
logging.info("SAVE_DATA = %s", SAVE_DATA)
logging.info("DESCRIPTION = %s", DESCRIPTION)
logging.info("SAVE_PATH = %s", SAVE_PATH)

def main():
    return script.do_measurement(WORLD_X, WORLD_Y, WORLD_PITCH, WORLD_YAW,
                                 REPEATS, DRY_RUN, RT_PLOT, DELAY, SAVE_DATA,
                                 REACH_TABLE, DESCRIPTION, SAVE_PATH)


if __name__ == '__main__':
    main()


