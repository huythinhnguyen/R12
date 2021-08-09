import numpy
from matplotlib import pyplot

from pyBat import Geometry

"""
Azimuth/Elevation are the positions of target as seen from the robot.
Azimuth = 45 returns a position at which the target is at azimuth 45 with respect to the robot

Aspect angles are the positions of target as seen from the target.
h_aspect = 45 returns a position at which the robot is at azimuth 45 with respect to the target
"""

class Target:
    def __init__(self, x=0, y=0, z=0, rotation=180):
        self.x = x
        self.y = y
        self.z = z
        self.rotation = rotation
        self.leaf_frame = Geometry.Frame()
        # Initialize the leaf frame
        self.leaf_frame.goto(x, y, z, yaw=rotation)
        self.world_frame_leaf_position = numpy.array([x, y, z])

    def get_robot_position(self, distance, h_aspect=0, v_aspect=0, azimuth=0, elevation=0, plot=False, simple=False):
        # In the leaf frame, what is the required position of the robot?
        leaf_frame_robot_position = Geometry.sph2cart(h_aspect, v_aspect, distance)
        leaf_frame_robot_position = numpy.array(leaf_frame_robot_position)
        # Convert the leaf frame robot position to robot_sph_2_world_cart coordinates
        world_frame_robot_position = self.leaf_frame.frame2world(leaf_frame_robot_position)

        # Initialize  the robot frame (= robot_sph_2_world_cart frame)
        robot_frame = Geometry.Frame()
        robot_frame.goto(world_frame_robot_position[0], world_frame_robot_position[1], world_frame_robot_position[2])
        # What azimuth elevation should the robot assume to look at the leaf (ie az = el = 0)
        robot_spherical = robot_frame.world2frame(self.world_frame_leaf_position, spherical=True)
        # apply the desired leaf and azimuth positions, world_cart_2_robot to the robot
        robot_yaw = +(robot_spherical[0] + azimuth)
        robot_pitch = -(robot_spherical[1] - elevation)
        robot_frame.move(yaw=robot_yaw, pitch=robot_pitch, time=1)

        robot_norm = robot_frame.frame2world(numpy.array([distance, 0, 0]))
        distance_to_leaf = numpy.sqrt(numpy.sum((world_frame_robot_position - self.world_frame_leaf_position) ** 2))
        simple_coordinates = [world_frame_robot_position[0], world_frame_robot_position[1], world_frame_robot_position[2], robot_yaw, robot_pitch]

        result = {}
        result['robot_cart'] = world_frame_robot_position
        result['robot_sph'] = [robot_yaw, robot_pitch]
        result['robot_norm'] = robot_norm
        result['check_distance'] = distance_to_leaf
        result['robot_frame'] = robot_frame
        result['simple_coordinates'] = simple_coordinates
        if plot: self.plot_leaf(result)
        if simple: return simple_coordinates
        return result

    def plot_leaf(self, result):
        robot_cart = result['robot_cart']
        robot_norm = result['robot_norm']

        pyplot.subplot(1, 2, 1)

        pyplot.plot([-1000, 1000], [0, 0], color='k')
        pyplot.scatter(self.x, self.y, c='green')
        pyplot.scatter(robot_cart[0], robot_cart[1])
        pyplot.plot([robot_cart[0], robot_norm[0]], [robot_cart[1], robot_norm[1]], alpha=0.5)

        pyplot.xlim([-200, 1200])
        pyplot.ylim([-700, 700])

        pyplot.title('Top View')
        pyplot.xlabel('X')
        pyplot.ylabel('Y')

        ax = pyplot.gca()
        ax.set_aspect('equal')

        pyplot.subplot(1, 2, 2)

        pyplot.plot([-1000, 1000], [-300, -300], color='k')
        pyplot.scatter(self.x, self.z, c='green')
        pyplot.scatter(robot_cart[0], robot_cart[2])
        pyplot.plot([robot_cart[0], robot_norm[0]], [robot_cart[2], robot_norm[2]], alpha=0.5)

        pyplot.xlim([-200, 1200])
        pyplot.ylim([-700, 700])

        pyplot.title('Side View')
        pyplot.xlabel('X')
        pyplot.ylabel('Z')

        ax = pyplot.gca()
        ax.set_aspect('equal')

        pyplot.tight_layout()

        pyplot.show()



#%%
if __name__ == "__main__":
    leaf_x = 1000
    leaf_y = 0
    leaf_z = 300
    leaf = Target(leaf_x, leaf_y, leaf_z)
    r = leaf.get_robot_position(distance=500,azimuth=0, h_aspect=-90, plot=True)
    r = leaf.get_robot_position(distance=500, elevation=0, v_aspect=45, plot=True)