import time
from matplotlib import pyplot
# all in mm
world_x = 500
world_y = 35000
world_z = 0

def find_track_position(world_x, world_y, world_z):

    start = time.time()

    reach = 500
    track_range = 1200
    resolution = 5
    tool_length = 40

    if world_x > 0:
        track_position = -track_range
        x_step = resolution
    else:
        track_position = track_range
        x_step = -resolution

    S2 = 100000
    #history = []
    while True:
        S1 = ((world_x - track_position) ** 2 + world_y ** 2) ** 0.5
        S2 = (S1 ** 2 + world_z ** 2) ** 0.5
        #history.append(S2)
        print(track_position)
        if S2 <= reach - tool_length: break
        if abs(track_position) > track_range: break
        track_position = track_position + x_step

    success = abs(track_position) <= track_range

    end = time.time()
    duration = end - start
    arm_x = world_x - track_position
    result = {}
    result['duration'] = duration
    result['success'] = success
    result['track_position'] = track_position
    result['arm_x'] = arm_x
    result['world_x'] = world_x
    return result

#pyplot.plot(history)
#pyplot.show()