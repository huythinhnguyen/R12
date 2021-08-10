from pyBat import Geometry, Ports, Misc, MaxbotixRobot
import warnings
import easygui
from .r12 import arm
from R12 import R12Logger
from R12 import Settings
from R12 import Recommender
import platform
import time
import re
import numpy
import copy
from matplotlib import pyplot

warnings.simplefilter('once', RuntimeWarning)

PURGE = 'PURGE'
ROBOFORTH = 'ROBOFORTH'
DECIMAL = 'DECIMAL'
START = 'START'
ALIGN = 'ALIGN'
JOINT = 'JOINT'
CALIBRATE = 'CALIBRATE'
CALIBRATE_TRACK = 'CALTRACK'
HOME = 'HOME'
WHERE = 'WHERE'
CARTESIAN = 'CARTESIAN'
SPEED = 'SPEED'
ACCEL = 'ACCEL'
MOVETO = 'MOVETO'
HAND = 'HAND'
WRIST = 'WRIST'
ENERGIZE = 'ENERGIZE'
DE_ENERGIZE = 'DE-ENERGIZE'
QUERY = ' ?'
IMPERATIVE = ' !'
TELL = 'TELL'
MOVE = 'MOVE'
CARTESIAN_NEW_ROUTE = 'CARTESIAN NEW ROUTE'
RESERVE = 'RESERVE'
OK = 'OK'


def find_integers(text):
    regex = r"[-+]?[0-9]+"
    found = re.findall(regex, text)
    new = []
    for x in found: new.append(int(x))
    return new


def find_track_position(world_x, world_y, world_z):
    start = time.time()

    reach = 450
    track_range = 1200
    resolution = 5
    tool_length = Settings.tool_length

    if world_x > 0:
        track_x = -track_range
        x_step = resolution
    else:
        track_x = track_range
        x_step = -resolution

    while True:
        S1 = ((world_x - track_x) ** 2 + world_y ** 2) ** 0.5
        S2 = (S1 ** 2 + world_z ** 2) ** 0.5
        if S2 <= reach - tool_length: break
        if abs(track_x) > track_range: break
        track_x = track_x + x_step

    success = abs(track_x) <= track_range

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


def ask_initialize():
    msg = 'Do you want to initialize the robot?'
    title = 'Robot initialize?'
    response = easygui.ynbox(title=title, msg=msg)
    return response


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
        r12_yaw = Geometry.phi_range(-world_yaw)
        r12_roll = Geometry.phi_range(+world_pitch)
        r12_pitch = 90

    return r12_yaw, r12_pitch, r12_roll


class RobotBat:
    def __init__(self, connect_robot=True, connect_sonar=True):
        self.logger = R12Logger.Logger()
        os = platform.system()
        self.connect_sonar = connect_sonar
        self.connect_robot = connect_robot
        self.current_wrist_orientation = None
        self.recommender = Recommender.Recommender()
        self.use_recommender = True

        if self.connect_sonar:
            self.sonar = MaxbotixRobot.Client(Settings.sonar_ip, Settings.sonar_port, verbose=True)
        else:
            self.sonar = False
            self.logger.add_comment(['Not connecting to sonar'])

        if self.connect_robot:
            if os == 'Windows': port = Ports.get_port("USB Serial Port (COM5)")
            if os == 'Linux': port = Ports.get_port("FT232R USB UART")
            self.logger.add_comment(['Connecting to port', port])
            self.arm = arm.Arm()
            self.arm.connect(port)
        else:
            self.arm = False
            self.logger.add_comment(['Not connecting to robot'])

        self.frame = Geometry.Frame()
        self.frame_initialized = False
        self.execute = True

    def view_log(self):
        self.logger.view()

    def send_command(self, cmd):
        self.logger.add_sent_cmd(cmd)
        if not self.connect_robot:
            self.logger.add_comment('Robot not connected!', level=2)
            self.logger.add_received_response('Robot not connected!')
            return
        self.arm.write(cmd)
        response = self.arm.read()
        self.logger.add_received_response(response)
        return response

    def set_tool_length(self, length=None):
        if length is None: length = Settings.tool_length
        self.logger.add_comment(['Set tool length:', length])
        cmd = '%i TOOL-LENGTH !' % (length * 10)
        result = self.send_command(cmd)
        return result

    def initialize(self, ask=True):
        if ask:
            response = ask_initialize()
            if not response: return

        self.send_command(ROBOFORTH)
        self.send_command(START)
        self.send_command(CALIBRATE)
        self.send_command(CALIBRATE_TRACK)
        self.send_command(DECIMAL)
        self.send_command(CARTESIAN)
        self.send_command(ALIGN)
        self.send_command(HOME)
        self.send_command(WHERE)
        self.set_tool_length()
        self.view_log()

    def simulate_arm(self, arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll):
        # Simulates the robot arm for a given arm xyz and arm angles.
        if not self.connect_robot: return {'success': True, 'pitch_axis': False}
        cmd = '%i %i %i %i %i %i CG' % (arm_roll * 10, arm_yaw * 10, arm_pitch * 10, arm_z * 10, arm_y * 10, arm_x * 10)
        self.send_command(cmd)
        self.send_command('WHERE')
        transform_response = self.send_command('TRANSFORM')
        if 'ABORTED' in transform_response: return {'success': False, 'pitch_axis': False}
        self.send_command('TRANSFORM DROP')

        pitch_axis = self.send_command('TARGET 6 + @ 90DEG M* W-RATIO M/ .')
        pitch_axis = find_integers(pitch_axis)[2] / 100
        return {'success': True, 'pitch_axis': pitch_axis}

    def goto_track(self, track_x):
        self.logger.add_comment(['Goto track:', track_x])
        cmd = 'TELL TRACK %i MOVETO' % (track_x * 10 * Settings.track_correction_ratio)
        result = self.send_command(cmd)
        return result

    def goto_arm(self, arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll):
        arm_x = round(arm_x, 1)
        arm_y = round(arm_y, 1)
        arm_z = round(arm_z, 1)
        arm_yaw = round(arm_yaw, 1)
        arm_pitch = round(arm_pitch, 1)
        arm_roll = round(arm_roll, 1)

        self.logger.add_comment(['Goto arm:', arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll])
        cmd = '%i %i %i %i %i %i CM' % (arm_roll * 10, arm_yaw * 10, arm_pitch * 10, arm_z * 10, arm_y * 10, arm_x * 10)
        result = self.send_command(cmd)
        return result

    def set_position(self, world_x, world_y=0, world_z=0, world_yaw=0, world_pitch=0, wrist_orientation='auto'):
        if Misc.iterable(world_x, allow_string=False):
            return self.set_position_array(world_x, wrist_orientation)
        else:
            return self.set_position_individual(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)

    def set_position_array(self, array, wrist_orientation='up'):
        x = array[0]
        y = array[1]
        z = array[2]
        yaw = array[3]
        pitch = array[4]
        result = self.set_position_individual(x, y, z, yaw, pitch, wrist_orientation)
        return result

    def set_position_individual(self, world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='auto'):
        find_track_position_result = find_track_position(world_x, world_y, world_z)

        success = find_track_position_result['success']
        track_x = find_track_position_result['track_x']
        arm_x = find_track_position_result['arm_x']

        if not success:
            self.logger.add_comment('No track position found', level=2)
            return False
        self.logger.add_comment('Track position found: ' + str(track_x))

        if wrist_orientation == 'auto':
            if self.use_recommender:
                self.logger.add_comment('Using recommender for wrist position')
                wrist_orientation = self.look_up_wrist_position(arm_x, world_y, world_z, world_yaw, world_pitch)
            else:
                wrist_orientation = self.calculate_wrist_position(arm_x, world_y, world_z, world_yaw, world_pitch)
            self.logger.add_comment('Recommended wrist orientation: ' + wrist_orientation)

        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation)
        self.goto_track(track_x)
        self.goto_arm(arm_x, world_y, world_z, arm_yaw, arm_pitch, arm_roll)  # world_y/z == arm_y/z, per definition
        self.frame = Geometry.Frame()
        self.frame_initialized = True
        self.frame.goto(world_x, world_y, world_z, world_yaw, world_pitch, arm_roll)
        self.current_wrist_orientation = wrist_orientation
        return True

    def move(self, fwd_dst=0, fwd_hvr=0, lat_dst=0, ud_dst=0, yaw=0, pitch=0, roll=0, wrist_orientation='auto', cds_only=False):
        # Apply fwd movement and rotation angles
        if not self.frame_initialized: return False
        frame_back_up = copy.copy(self.frame)
        self.frame.move(time=1, yaw=yaw, pitch=pitch, roll=roll, speed=fwd_dst)

        # Apply lateral motion
        motion_vector = numpy.array([0, 1, 0])
        motion_vector = Misc.normalize_vector(motion_vector)
        body_step = numpy.dot(self.frame.rotation_matrix_frame2world, motion_vector) * lat_dst
        self.frame.position = self.frame.position + body_step

        # Hover fwd (keep height constant)
        motion_vector = numpy.array([1, 0, 0])
        motion_vector = Misc.normalize_vector(motion_vector)
        body_step = numpy.dot(self.frame.rotation_matrix_frame2world, motion_vector) * fwd_hvr
        body_step[2] = 0
        self.frame.position = self.frame.position + body_step

        world_x = self.frame.x
        world_y = self.frame.y
        world_z = self.frame.z + ud_dst
        world_yaw = self.frame.euler[2]  # Yaw is z rot
        world_pitch = self.frame.euler[1]  # pitch is y rot
        if cds_only:
            self.frame = frame_back_up
            return world_x, world_y, world_z, world_yaw, world_pitch

        success = self.set_position_individual(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)
        return success

    def look_up_wrist_position(self, arm_x, arm_y, arm_z, world_yaw, world_pitch, return_angles=False):
        found_instance = self.recommender.recommend(arm_x, arm_y, arm_z)
        angle_down = found_instance.angle_down
        angle_up = found_instance.angle_up
        if return_angles: return angle_up, angle_down
        return found_instance.recommendation

    def calculate_wrist_position(self, arm_x, arm_y, arm_z, world_yaw, world_pitch, return_angles=False):
        self.logger.add_comment('Check angles for wrist orientation up')
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation='up')
        result = self.simulate_arm(arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll)
        angle_up = result['pitch_axis']
        angle_up = abs(angle_up)
        if not angle_up: angle_up = 100000

        self.logger.add_comment('Check angles for wrist orientation down')
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation='down')
        result = self.simulate_arm(arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll)
        angle_down = result['pitch_axis']
        if not angle_down: angle_down = 100000

        if return_angles: return angle_up, angle_down

        if min(angle_up, angle_down) > 10000:
            self.logger.add_comment('Neither wrist position was reachable', level=2)
            return False
        if angle_down < angle_up: return 'down'
        if angle_up < angle_down: return 'up'

    def measure(self, plot=False):
        if not self.sonar: return numpy.random.random((2, 100))
        flip = False
        if self.connect_robot and self.current_wrist_orientation == 'down': flip = True
        data = self.sonar.measure(rate=Settings.sonar_rate, duration=Settings.sonar_duration)
        if flip: data = numpy.fliplr(data)
        if plot:
            pyplot.plot(data)
            pyplot.legend(['Left', 'Right'])
            pyplot.show()
        return data
