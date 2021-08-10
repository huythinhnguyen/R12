from pyBat import Geometry, Ports, Misc, MaxbotixRobot
import warnings
import easygui
from .r12 import arm
from R12 import R12Logger
from R12 import Settings
import platform
import time

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


def find_track_position(world_x, world_y, world_z):
    start = time.time()

    reach = 500
    track_range = 1200
    resolution = 5
    tool_length = Settings.tool_length

    if world_x > 0:
        track_position = -track_range
        x_step = resolution
    else:
        track_position = track_range
        x_step = -resolution

    while True:
        S1 = ((world_x - track_position) ** 2 + world_y ** 2) ** 0.5
        S2 = (S1 ** 2 + world_z ** 2) ** 0.5
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

    def goto_track(self, track_x):
        self.logger.add_comment(['Goto track:', track_x])
        cmd = 'TELL TRACK %i MOVETO' % (track_x * 10 * Settings.track_correction_ratio)
        result = self.send_command(cmd)
        return result

    def goto_arm(self, arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll):
        self.logger.add_comment(['Goto arm:', arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll])
        cmd = '%i %i %i %i %i %i CM' % (arm_roll * 10, arm_yaw * 10, arm_pitch * 10, arm_z * 10, arm_y * 10, arm_x * 10)
        result = self.send_command(cmd)
        return result

    def set_position(self, world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='UP'):
        arm_yaw, arm_pitch, arm_roll = world_to_arm_angles(world_yaw, world_pitch, wrist_orientation)
        result = find_track_position(world_x, world_y, world_z)
        success = result['success']
        track_position = result['track_position']
        arm_x = result['arm_x']
