from R12 import RobotBat
from R12 import Target
import numpy
from pyBat import Misc
from matplotlib import pyplot

R = RobotBat.RobotBat()
R.initialize()

record = open('R12/recommendations.txt', 'w')

reach = 500
tool_length = 40
for x in numpy.linspace(-500, 500, 10):
    for y in numpy.linspace(-500, 500, 10):
        for z in numpy.linspace(-500, 500, 10):
            S1 = (x ** 2 + y ** 2) ** 0.5
            S2 = (S1 ** 2 + z ** 2) ** 0.5
            if S2 <= reach - tool_length:
                angles = R.calculate_wrist_position(x, y, z, 0, 0, return_angles=True)
                angle_up = angles[0]
                angle_down = angles[1]
                if angle_down < angle_up: recommendation = 'down'
                if angle_up < angle_down: recommendation =  'up'
                line = [x, y, z, angle_up, angle_down, recommendation]
                line = Misc.lst2str(line) + '\n'
                record.write(line)
record.close()

