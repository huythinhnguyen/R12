import copy
import platform
import warnings
import easygui
import numpy
import re

from pyBat import Geometry, Ports, Misc, MaxbotixRobot

from .r12 import arm
from R12 import R12Logger
from R12 import Settings

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


def ask_initialize():
    response = easygui.ynbox(title='Robot initialize?', msg='Do you want to initialize the robot?')
    return response

def find_integers(text):
    regex = r"[-+]?[0-9]+"
    found = re.findall(regex, text)
    new = []
    for x in found: new.append(int(x))
    return new


def world_to_arm_angles(world_yaw, world_pitch, wrist_orientation):
    r12_yaw = None
    r12_pitch = None
    r12_roll = None

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
        self.sonar = False
        self.connect_sonar = connect_sonar
        self.connect_robot = connect_robot

        if self.connect_sonar: self.sonar = MaxbotixRobot.Client(Settings.sonar_ip, Settings.sonar_port, verbose=True)

        if self.connect_robot:
            if os == 'Windows': port = Ports.get_port("USB Serial Port (COM5)")
            if os == 'Linux': port = Ports.get_port("FT232R USB UART")
            self.logger.add_comment(['Connecting to port', port])
            self.current_wrist_position = None
            self.arm = arm.Arm()
            self.arm.connect(port)

        self.frame = Geometry.Frame()
        self.frame_initialized = False
        self.execute = True

    def send_command(self, cmd, verbose=False, log=True):
        if not self.connect_robot:
            self.logger.add_comment('Robot not connected!')
            return
        self.arm.write(cmd)
        if log: self.logger.add_input(cmd)
        result = self.arm.read()
        if log: self.logger.add_output(result)
        if verbose: print(result)
        return result

    def send_batch(self, cmds, verbose=False, log=True):
        cmds = cmds.split('\n')
        for x in cmds: self.send_command(x, verbose, log)

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
        self.logger.view()

    def home(self):
        self.send_command(HOME)

    def view_log(self):
        self.logger.view()

    def set_tool_length(self, length=None):
        if length is None: length = Settings.tool_length
        self.logger.add_comment(['Set tool length:', length])
        cmd = '%i TOOL-LENGTH !' % (length * 10)
        result = self.send_command(cmd)
        return result

    def goto_track(self, track_x):
        self.logger.add_comment(['Goto track:', track_x])
        cmd = 'TELL TRACK %i MOVETO' % (track_x * 10 * Settings.track_correction_ratio)
        result = self.send_command(cmd)
        if not self.execute: return ('NOT EXECUTED')
        return result

    def goto_arm(self, arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll):
        self.logger.add_comment(['Goto:', arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll])
        cmd = '%i %i %i %i %i %i CM' % (arm_roll * 10, arm_yaw * 10, arm_pitch * 10, arm_z * 10, arm_y * 10, arm_x * 10)
        if not self.execute: return ('NOT EXECUTED')
        result = self.send_command(cmd)
        if arm_pitch < 0: self.current_wrist_position = 'up'
        if arm_pitch > 0: self.current_wrist_position = 'down'
        return result

    def goto_wrist(self, world_yaw=None, world_pitch=None, wrist_orientation='up'):
        #
        # WARNING: THIS DOES NOT UPDATE THE FRAME ATTACHED TO THE ROBOT!!!!
        #
        warnings.warn('WARNING: THIS DOES NOT UPDATE THE FRAME ATTACHED TO THE ROBOT!!!!', RuntimeWarning)
        position = self.get_position()
        if world_yaw is None: world_yaw = position[3]
        if world_pitch is None: world_pitch = position[4]
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation=wrist_orientation)
        result = self.send_command('CF')
        result = result.split(' ')
        x = int(result[1])
        y = int(result[2])
        z = int(result[3])
        new_yaw = arm_yaw * 10
        new_pitch = arm_pitch * 10
        new_roll = arm_roll * 10
        cmd = '%i %i %i %i %i %i CM' % (new_roll, new_yaw, new_pitch, z, y, x)
        if not self.execute: return ('NOT EXECUTED')
        result = self.send_command(cmd)
        if arm_pitch < 0: self.current_wrist_position = 'up'
        if arm_pitch > 0: self.current_wrist_position = 'down'
        return result

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

    def check_reachable(self, arm_x, arm_y, arm_z, world_yaw, world_pitch, wrist_orientation, pitch_axis_only=False, binary=False):
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation=wrist_orientation)
        result = self.simulate_arm(arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll)
        if pitch_axis_only: return result['pitch_axis']
        if binary: return result['success']
        return result

    def recommend_wrist_position(self, arm_x, arm_y, arm_z, world_yaw, world_pitch):
        # Returns the recommended wrist orientation for a given x, y, z and robot_sph_2_world_cart angles
        # Returns false if not attainable (using neither of the wrist orientations).

        angle_up = self.check_reachable(arm_x, arm_y, arm_z, world_yaw, world_pitch, 'up', pitch_axis_only=True)
        angle_down = self.check_reachable(arm_x, arm_y, arm_z, world_yaw, world_pitch, 'down', pitch_axis_only=True)

        angle_up = abs(angle_up)
        if not angle_up: angle_up = 1000
        if not angle_down: angle_down = 1000
        if min([angle_down, angle_up]) > 999: return False
        if angle_down < angle_up: return 'down'
        if angle_up < angle_down: return 'up'
        return False

    def recommend_wrist_track_position(self, world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='auto'):
        world_yaw = Geometry.phi_range(world_yaw)
        # track x should be larger than robot_sph_2_world_cart x
        proposed_track_positions = numpy.linspace(world_x - 600, world_x, 5)
        if abs(world_yaw) > 90:
            # unless looking backward, then track x should be smaller than robot_sph_2_world_cart x
            proposed_track_positions = numpy.linspace(world_x + 600, world_x, 5)

        proposed_track_positions = proposed_track_positions[proposed_track_positions > -1200]
        proposed_track_positions = proposed_track_positions[proposed_track_positions < 1200]

        for proposed_track_position in proposed_track_positions:
            self.logger.add_comment(['Try track position:', proposed_track_position])
            arm_x = world_x - proposed_track_position
            if wrist_orientation == 'auto':
                wrist_recommendation = self.recommend_wrist_position(arm_x, world_y, world_z, world_yaw, world_pitch)
                if wrist_recommendation: return wrist_recommendation, proposed_track_position, arm_x
            else:
                reachable = self.check_reachable(arm_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation, binary=True)
                if reachable: return wrist_orientation, proposed_track_position, arm_x
        return False, False, False

    def set_position_array(self, array, wrist_orientation='auto'):
        x = array[0]
        y = array[1]
        z = array[2]
        yaw = array[3]
        pitch = array[4]
        self.set_position(x, y, z, yaw, pitch, wrist_orientation)
        return True

    def set_position(self, world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='auto'):
        wrist_recommendation, proposed_track_position, arm_x = self.recommend_wrist_track_position(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)
        if not wrist_recommendation: return False
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_recommendation)

        self.goto_track(proposed_track_position)
        self.goto_arm(arm_x, world_y, world_z, arm_yaw, arm_pitch, arm_roll)  # world_y/z == arm_y/z, per definition

        self.frame = Geometry.Frame()
        self.frame_initialized = True
        self.frame.goto(world_x, world_y, world_z, world_yaw, world_pitch, arm_roll)
        return True

    def set_move(self, fwd_dst=0, fwd_hvr=0, lat_dst=0, ud_dst=0, yaw=0, pitch=0, roll=0, wrist_orientation='auto', cds_only=False):
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

        success = self.set_position(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)
        return success

    def measure(self):
        if not self.sonar: return numpy.random.random((2, 100))
        flip = False
        if self.connect_robot and self.current_wrist_position == 'up': flip = True
        data = self.sonar.measure(rate=Settings.sonar_rate, duration=Settings.sonar_duration)
        if flip: data = numpy.fliplr(data)
        return data

    def pitch_scan(self, pitches, wrist_orientation):
        position = self.get_position()
        current_pitch = position[4]
        measurements = []
        for x in pitches:
            self.goto_wrist(world_pitch=x, wrist_orientation=wrist_orientation)
            data = self.measure()
            measurements.append(data)
        self.goto_wrist(world_pitch=current_pitch, wrist_orientation=wrist_orientation)
        return measurements

    def world_cart_2_robot(self, world_x, world_y=None, world_z=None, spherical=True):
        if world_y is not None: world_x = [world_x, world_y, world_z]
        world = numpy.array(world_x)
        result = self.frame.world2frame(world, spherical=spherical)
        return result

    def robot_sph_2_world_cart(self, azimuth, elevation, distance):
        if elevation is None:
            azimuth = azimuth[0]
            elevation = azimuth[1]
            distance = azimuth[2]
        position = Geometry.sph2cart(azimuth, elevation, distance)
        position = numpy.array(position)
        result = self.frame.frame2world(position)
        return result

    def get_position(self, as_string=False):
        world_x = self.frame.x
        world_y = self.frame.y
        world_z = self.frame.z
        world_yaw = self.frame.euler[2]  # Yaw is z rot
        world_pitch = self.frame.euler[1]  # pitch is y rot
        data = [world_x, world_y, world_z, world_yaw, world_pitch]
        if as_string: return "%i %i %i %i %i" % tuple(data)
        return data

    @property
    def x(self):
        position = self.get_position()
        return position[0]

    @property
    def y(self):
        position = self.get_position()
        return position[1]

    @property
    def z(self):
        position = self.get_position()
        return position[2]

    @property
    def yaw(self):
        position = self.get_position()
        return position[3]

    @property
    def pitch(self):
        position = self.get_position()
        return position[4]
