import time


def find_track_position(world_x, world_y, world_z, world_yaw, simple=False, trace=False):
    find_track_position_result = find_track_position_both(world_x, world_y, world_z, world_yaw, trace=trace)
    successes = find_track_position_result['success']
    possibilities = {}
    if successes[0]: possibilities['up'] = find_track_position_result['up']['track_x']
    if successes[1]: possibilities['down'] = find_track_position_result['down']['track_x']
    up_track_x = find_track_position_result['up']['track_x']
    down_track_x = find_track_position_result['down']['track_x']

    find_track_position_result['possibilities'] = possibilities
    if simple: return [up_track_x, down_track_x, find_track_position_result]
    return find_track_position_result


def find_track_position_both(world_x, world_y, world_z, world_yaw, trace=False):
    up_result = find_track_position_single(world_x, world_y, world_z, world_yaw, trace=trace, wrist_position='up')
    down_result = find_track_position_single(world_x, world_y, world_z, world_yaw, trace=trace, wrist_position='down')
    result = {}
    success_up = up_result['success']
    success_down = down_result['success']
    result['up'] = up_result
    result['down'] = down_result
    result['success'] = [success_up, success_down]
    return result


def find_track_position_single(world_x, world_y, world_z, world_yaw, wrist_position='up', trace=False):
    start = time.time()

    reach = 500
    track_range = 1200
    resolution = 5
    tool_length = 40
    wrist_length = 32

    threshold = reach - tool_length  # worst case scenario
    if wrist_position == 'up': world_z = world_z - wrist_length
    if wrist_position == 'down': world_z = world_z + wrist_length

    if abs(world_yaw) < 90:
        track_x = -track_range
        x_step = resolution
    else:
        track_x = track_range
        x_step = -resolution

    while True:
        s1 = ((world_x - track_x) ** 2 + world_y ** 2) ** 0.5
        s2 = (s1 ** 2 + world_z ** 2) ** 0.5
        if trace: print(wrist_position, track_x, s2, threshold)
        if s2 <= threshold: break
        if abs(track_x) > track_range: break
        track_x = track_x + x_step

    success = abs(track_x) <= track_range
    if not success: track_x = False

    end = time.time()
    duration = end - start
    arm_x = world_x - track_x
    result = {}
    result['duration'] = duration
    result['success'] = success
    result['track_x'] = track_x
    result['arm_x'] = arm_x
    result['world_x'] = world_x
    return result


if __name__ == "__main__":
    r = find_track_position(490.89520395684394, 280.7569753596211, 300.0, 35.0, trace=True)
