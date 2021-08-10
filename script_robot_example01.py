from R12 import RobotBat2

from matplotlib import pyplot

R = RobotBat2.RobotBat()
R.initialize()
R.set_position(1000, 100, 300, 0, 0)
data = R.measure(plot=True)
