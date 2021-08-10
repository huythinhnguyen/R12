from R12 import RobotBat2

a = RobotBat2.RobotBat(connect_robot=True, connect_sonar=False)
a.initialize()
a.set_position(1, 100, 350, 0, 0)