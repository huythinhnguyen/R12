from R12 import RobotBat
from R12 import Target
import numpy
from matplotlib import pyplot

R = RobotBat.RobotBat(connect_sonar=False)
R.initialize()

target = Target.Target(1000, 0, 350)

for aspect in numpy.linspace(-30, 30, 5):
    result = target.get_robot_position(distance=250, h_aspect=aspect, simple=True)
    R.set_position_array(result)


for azimuth in numpy.linspace(-30, 30, 5):
    result = target.get_robot_position(distance=250, azimuth=azimuth, simple=True)
    R.set_position_array(result)