log_dir = 'logs'

tool_length = 55
wrist_length = 63
robot_reach = 500-50
robot_reach_buffer = 25

sonar_ip = '192.168.1.5'
sonar_port = 1000
sonar_rate = 10000
sonar_duration = 20
sonar_floor = 1200

# The track is not in steps of 0.1 mm. This is an emperical conversion factor.
# displacement in 0.1 mm = x * track_correcton_ratio

#@ track = 14000 --> 2.52 m
#@ track = -14000 --> 0.24 m
track_correction_ratio = 1.219

# in the configuration with the wrist pointing downward


