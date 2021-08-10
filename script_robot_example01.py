import numpy

from R12 import RobotBat, Target
import time
from matplotlib import pyplot


R = RobotBat.RobotBat()
#R.initialize()

for target_x in numpy.linspace(-500,500, 10):

    target = Target.Target(x=target_x, y=700, z = 350, rotation=-90)
    result = target.get_robot_position(distance=500,  azimuth=0)
    R.set_position(result)
    time.sleep(1)
    data = R.measure(plot=True)
