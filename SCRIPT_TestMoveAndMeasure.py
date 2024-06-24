import time
import numpy
from R12 import RobotBat, Target

R = RobotBat.RobotBat(connect_robot=True, connect_sonar=True)

world_x = 0
world_y = 0
world_z = 400
world_pitch = -10
world_yaw = 0

x_positions = numpy.linspace(-500, 1000, 10)

for world_x in x_positions:
    R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)
    R.measure(plot=True)
    time.sleep(0.25)

