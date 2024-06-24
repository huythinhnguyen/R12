import time
import numpy
from R12 import RobotBat, Target

R = RobotBat.RobotBat(connect_robot=True, connect_sonar=False)

world_x = 0
world_y = 0
world_z = 300
world_pitch = 0
world_yaw = 90

x_positions = numpy.linspace(-500, 500, 1)
for world_x in x_positions:
    R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)
    time.sleep(1)

