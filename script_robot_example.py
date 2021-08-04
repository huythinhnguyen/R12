from R12 import RobotBat
from matplotlib import pyplot

R = RobotBat.RobotBat(connect_sonar=True)
R.initialize()
R.set_position(0, 0, 400, 0, 0)
R.set_position(-100, 0, 400, 0, 0)
data = R.measure()
pyplot.plot(data)
pyplot.show()