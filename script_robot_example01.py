from R12 import RobotBat
from matplotlib import pyplot

R = RobotBat.RobotBat(connect_sonar=True)
R.initialize()
R.set_position(0, 0, 300, 0, 0)
data = R.measure()
pyplot.plot(data)
pyplot.show()