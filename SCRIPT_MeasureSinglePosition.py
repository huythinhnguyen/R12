import time
import numpy
from os import path
import pickle
from R12 import RobotBat
from R12 import CombinationTools
from matplotlib import pyplot

R = RobotBat.RobotBat(connect_robot=True, connect_sonar=True)

world_x = -200
world_y = 200
world_pitch = 0
world_yaw = 27.5
repeats = 50

world_z = numpy.interp(world_y, [0, 100, 200, 300], [500, 400, 300, 300])
R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)
test_data = R.measure(subtract_floor=True, plot=False)
test_data_shape = test_data.shape

data_array = numpy.zeros((repeats, test_data_shape[0], test_data_shape[1]))

file_name, description = CombinationTools.get_file_name()
full_file_name = path.join('data', file_name + '.pck')

for i in range(repeats):
    print('###########', i)
    data = R.measure(plot=False, subtract_floor=False)
    data_array[i,:,:] = data
    time.sleep(0.25)


data_to_save = {
    'data_array': data_array,
    'world_x': world_x,
    'world_y': world_y,
    'world_z': world_z,
    'world_pitch': world_pitch,
    'world_yaw': world_yaw,
    'repeats': repeats,
    'description': description
}

file = open(full_file_name, 'wb')
pickle.dump(data_to_save, file)
file.close()

average = numpy.mean(data_array, axis=0)
pyplot.figure()
pyplot.plot(average)
pyplot.show()
