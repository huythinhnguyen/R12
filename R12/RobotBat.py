import warnings
import platform
import re
import numpy
import easygui
from matplotlib import pyplot

from R12 import R12Logger
from R12 import Settings
from R12 import RobotModel
from R12 import Geometry
from R12 import Ports
from R12 import Misc
from R12 import Maxbotix

try:
    from r12 import arm
except:
    from .r12 import arm



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


def ask_initialize():
    msg = 'Do you want to initialize the robot?'
    title = 'Robot initialize?'
    response = easygui.ynbox(title=title, msg=msg)
    return response


class RobotBat:
    def __init__(self, connect_robot=True, connect_sonar=True):
        os = platform.system()

        self.logger = R12Logger.Logger()
        self.connect_sonar = connect_sonar
        self.connect_robot = connect_robot
        self.current_wrist_orientation = None

        if self.connect_sonar:
            self.sonar = Maxbotix.Client(Settings.sonar_ip, Settings.sonar_port, verbose=True)
        else:
            self.sonar = False
            self.logger.add_comment(['Not connecting to sonar'])

        if self.connect_robot:
            p = Ports.Ports()
            p.print()
            if os == 'Windows': port = Ports.get_port("USB Serial Port (COM3)")
            if os == 'Linux': port = Ports.get_port("FT232R USB UART")
            self.logger.add_comment(['Connecting to port', port])
            self.arm = arm.Arm()
            self.arm.connect(port)
        else:
            self.arm = False
            self.logger.add_comment(['Not connecting to robot'])

        self.frame = Geometry.Frame()
        self.frame_initialized = False

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

    def set_position(self, world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation='auto'):
        if Misc.iterable(world_x, allow_string=False):
            world_x = world_x[0]
            world_y = world_x[1]
            world_z = world_x[2]
            world_yaw = world_x[3]
            world_pitch = world_x[4]

        if world_x is None: world_x = self.x
        if world_y is None: world_y = self.y
        if world_z is None: world_z = self.z
        if world_yaw is None: world_yaw = self.yaw
        if world_pitch is None: world_pitch = self.pitch

        result = RobotModel.run_model(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)
        if not result:
            self.logger.add_comment('Position can not be reached', level=2)
            return False
        track_x = result['track_x']
        arm_x = result['arm_x']
        arm_y = result['arm_y']
        arm_z = result['arm_z']
        arm_yaw = result['arm_yaw']
        arm_pitch = result['arm_pitch']
        arm_roll = result['arm_roll']
        wrist_orientation = result['wrist_orientation']
        self.logger.add_comment('Selected wrist_orientation: ' + wrist_orientation)

        self.goto_track(track_x)
        self.goto_arm(arm_x, arm_y, arm_z, arm_yaw, arm_pitch, arm_roll)  # world_y/z == arm_y/z, per definition
        self.frame = Geometry.Frame()
        self.frame.goto(world_x, world_y, world_z, world_yaw, world_pitch, 0)
        self.current_wrist_orientation = wrist_orientation
        return True

    def move(self, fwd_dst=0, fwd_hvr=0, lat_dst=0, ud_dst=0, yaw=0, pitch=0, wrist_orientation='auto'):
        # Apply pitch and yaw
        # I use this approach instead of the move function for the frame
        # to rotate around the y and z axis aligned with the world coordinate frame
        # not with the rotated axes attached to the bat
        world_yaw = self.yaw + yaw
        world_pitch = self.pitch + pitch
        world_x = self.x
        world_y = self.y
        world_z = self.z
        self.frame = Geometry.Frame()
        self.frame.goto(world_x, world_y, world_z, world_yaw, world_pitch, 0)
        
        # Apply forward motion
        motion_vector = numpy.array([1, 0, 0])
        motion_vector = Misc.normalize_vector(motion_vector)
        body_step = numpy.dot(self.frame.rotation_matrix_frame2world, motion_vector) * fwd_dst
        self.frame.position = self.frame.position + body_step

        # Apply lateral motion
        motion_vector = numpy.array([0, 1, 0])
        motion_vector = Misc.normalize_vector(motion_vector)
        body_step = numpy.dot(self.frame.rotation_matrix_frame2world, motion_vector) * lat_dst
        self.frame.position = self.frame.position + body_step

        # Hover fwd (keep height constant)
        motion_vector = numpy.array([1, 0, 0])
        motion_vector = Misc.normalize_vector(motion_vector)
        body_step = numpy.dot(self.frame.rotation_matrix_frame2world, motion_vector)
        body_step[2] = 0
        body_step_length = numpy.sum(body_step ** 2) ** 0.5
        body_step = (body_step / body_step_length) * fwd_hvr
        self.frame.position = self.frame.position + body_step

        # Get frame data and apply
        world_x = self.frame.x
        world_y = self.frame.y
        world_z = self.frame.z + ud_dst
        world_yaw = self.frame.euler[2]  # Yaw is z rot
        world_pitch = self.frame.euler[1]  # pitch is y rot
        success = self.set_position(world_x, world_y, world_z, world_yaw, world_pitch, wrist_orientation)
        return success

    def measure(self, plot=False, subtract_floor=True):
        self.logger.add_comment('Starting echo measurement')
        if not self.sonar: return numpy.random.random((200, 2)), numpy.arange(0,200)
        flip = False
        if self.connect_robot and self.current_wrist_orientation == 'down': flip = True
        data = self.sonar.measure(rate=Settings.sonar_rate, duration=Settings.sonar_duration)
        if flip: data = numpy.fliplr(data)
        if subtract_floor: data = data - Settings.sonar_floor
        data[data < 0] = 0
        if plot:
            pyplot.plot(data)
            pyplot.legend(['Left', 'Right'])
            pyplot.show()
        return data

    def relative(self, azimuth, distance):
        cart = Geometry.sph2cart(azimuth, 0, distance)
        cart = numpy.array(cart)
        world = self.frame.frame2world(cart)
        return world

    @property
    def position(self): return list(self.frame.position)

    @property
    def x(self): return self.frame.x

    @property
    def y(self): return self.frame.y

    @property
    def z(self): return self.frame.z

    @property
    def euler(self): return self.frame.euler

    @property
    def yaw(self):
        euler = self.euler
        yaw = euler[2]
        return yaw

    @property
    def pitch(self):
        euler = self.euler
        pitch = euler[1]
        return pitch

    @property
    def roll(self):
        euler = self.euler
        yaw = euler[0]
        return yaw




