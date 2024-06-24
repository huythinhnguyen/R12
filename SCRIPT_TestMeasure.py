from R12 import RobotBat
import time
R = RobotBat.RobotBat(connect_robot=False, connect_sonar=True)

for i in range(5):
    R.measure(plot=True)
    time.sleep(1)
