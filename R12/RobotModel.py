from R12 import Settings
from R12 import Geometry
import math
import numpy


def world_to_arm_angles(world_yaw, world_pitch, wrist_orientation):
    r12_yaw = None
    r12_pitch = None
    r12_roll = None
    wrist_orientation = wrist_orientation.lower()

    if wrist_orientation == 'up':
        r12_yaw = Geometry.phi_range(world_yaw)
        r12_roll = Geometry.phi_range(-world_pitch)
        r12_pitch = -90

    if wrist_orientation == 'down':
        r12_yaw = Geometry.phi_range(-world_yaw)  # the axis around which yaw is measured flips direction
        r12_roll = Geometry.phi_range(+world_pitch)
        r12_pitch = 90

    return r12_yaw, r12_pitch, r12_roll


# Gives the location of the sensor with respect to the forearm end point
def hand_offset(world_yaw, wrist_orientation):
    delta_x = None
    delta_y = None
    delta_z = None
    tool_length = Settings.tool_length
    if wrist_orientation == 'up':
        radians = math.radians(world_yaw - 90)
        delta_x = math.cos(radians) * tool_length
        delta_y = math.sin(radians) * tool_length
        delta_z = Settings.wrist_length

    if wrist_orientation == 'down':
        radians = math.radians(world_yaw + 90)
        delta_x = math.cos(radians) * tool_length
        delta_y = math.sin(radians) * tool_length
        delta_z = -Settings.wrist_length
    delta = numpy.array([delta_x, delta_y, delta_z])
    return delta


def forearm_position(world_x, world_y, world_z, world_yaw, wrist_orientation):
    delta = hand_offset(world_yaw, wrist_orientation)
    world_forearm_x = world_x - delta[0]
    world_forearm_y = world_y - delta[1]
    world_forearm_z = world_z - delta[2]
    result = [world_forearm_x, world_forearm_y, world_forearm_z]
    result = numpy.array(result)
    return result


def find_track_position(world_x, world_y, world_z, world_yaw, wrist_orientation):
    world_forearm = forearm_position(world_x, world_y, world_z, world_yaw, wrist_orientation)
    world_forearm_x = world_forearm[0]
    world_forearm_y = world_forearm[1]
    world_forearm_z = world_forearm[2]

    robot_reach = Settings.robot_reach
    track_positions = numpy.linspace(-1200, 1200, 2401)
    side = ((world_forearm_x - track_positions) ** 2 + world_forearm_y ** 2 + world_forearm_z ** 2) ** 0.5
    possible_track_positions = track_positions[side < robot_reach]

    if len(possible_track_positions) == 0: return False

    if Settings.track_position == 'auto':
        selected_i = numpy.argmax(possible_track_positions)
        if abs(world_yaw) < 90: selected_i = numpy.argmin(possible_track_positions)
    if Settings.track_position == 'down':
        selected_i = numpy.argmin(possible_track_positions)
    if Settings.track_position == 'up':
        selected_i = numpy.argmax(possible_track_positions)

    track_x = possible_track_positions[selected_i]
    return track_x


def get_wrist_angle(world_x, world_y, world_z, world_yaw, track_x, wrist_orientation):
    print_inventor = False
    world_forearm = forearm_position(world_x, world_y, world_z, world_yaw, wrist_orientation)

    # position of the forearm in arm frame
    x_f = world_forearm[0] - track_x
    y_f = world_forearm[1]
    z_f = world_forearm[2]

    p1 = ((z_f ** 2 + y_f ** 2 + x_f ** 2) ** 0.5) / 500
    p1 = - math.acos(p1)
    p2 = ((y_f ** 2 + x_f ** 2) ** 0.5) / z_f
    p2 = - math.atan(p2)
    wrist_angle = p1 + p2 + math.pi
    wrist_angle = math.degrees(wrist_angle)

    if wrist_angle > 180: wrist_angle = wrist_angle - 180
    if wrist_angle < -180: wrist_angle = wrist_angle + 180
    if wrist_orientation == 'down': wrist_angle = 180 - wrist_angle
    forearm_tilt = 180 - (90 + wrist_angle)

    if print_inventor:
        d_flat = (x_f ** 2 + y_f ** 2) ** 0.5
        print('For inventor')
        print('wrist', wrist_orientation)
        print('d_flat', d_flat)
        print('z_f', z_f)
        print('wrist angle', wrist_angle)

    return wrist_angle, forearm_tilt


def run_model_single_orientation(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation):
    arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation)
    track_x = find_track_position(world_x, world_y, world_z, world_yaw, wrist_orientation)
    wrist_angle = 0
    forearm_tilt = 0
    if track_x: wrist_angle, forearm_tilt = get_wrist_angle(world_x, world_y, world_z, world_yaw, track_x, wrist_orientation)
    arm_x = world_x - track_x
    result = {}
    result['wrist_orientation'] = wrist_orientation
    result['track_x'] = track_x
    result['success'] = abs(track_x) > 0
    result['arm_x'] = arm_x
    result['arm_y'] = world_y
    result['arm_z'] = world_z
    result['wrist_angle'] = wrist_angle
    result['forearm_tilt'] = forearm_tilt
    result['arm_yaw'] = arm_yaw
    result['arm_pitch'] = arm_pitch
    result['arm_roll'] = arm_roll
    result['success'] = track_x
    result['array'] = [arm_x, world_y, world_z, arm_yaw, arm_pitch, arm_roll]
    print('model for', wrist_orientation, result['success'])
    return result


def run_model(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation):
    result_up = run_model_single_orientation(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='up')
    result_down = run_model_single_orientation(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='down')
    # Handling explicit setting of orientation
    if result_up['success'] and wrist_orientation == 'up': return result_up
    if result_down['success'] and wrist_orientation == 'down': return result_down
    if wrist_orientation != 'auto': return False
    # Handling cases in which none of them work
    angle_up = result_up['wrist_angle']
    angle_down = result_down['wrist_angle']
    if angle_up + angle_down == 0: return False
    print('angles:', angle_up, angle_down)
    if angle_up > angle_down: return result_up
    if angle_down > angle_up: return result_down
