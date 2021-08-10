from R12 import RobotBat2

a = RobotBat2.RobotBat(connect_robot=False, connect_sonar=False)
a.set_position(1000,0,350,0,0)
a.view_log()
