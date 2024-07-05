import time
import numpy
from R12 import RobotBat

R = RobotBat.RobotBat(connect_robot=True, connect_sonar=False)

world_x = -200
world_y = 200
world_pitch = 0
world_yaw = 27.5

world_z = numpy.interp(world_y, [0, 100, 200, 300], [500, 400, 300, 300])
R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)


