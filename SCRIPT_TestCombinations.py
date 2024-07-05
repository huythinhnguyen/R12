from R12 import RobotBat
from R12 import CombinationTools
from os import path
import numpy as np
import pickle
import time
import sys
import inspect

############## SET POSITION PARAMETERS HERE
pitch = 0
repeats = 5
x_positions = np.linspace(-700, 0, 15) # min, max, number of steps
y_positions = np.linspace(0, 200, 3)
yaw_positions = np.linspace(0, 30, 3)
###########################################

script_text = inspect.getsource(sys.modules[__name__])
y_extents = [0, 100, 200, 300]
z_extents = [500, 400, 300, 300]

file_name, description = CombinationTools.get_file_name()
full_file_name = path.join('data', file_name + '.pck')

combinations = CombinationTools.generate_combinations(x_positions, y_positions, yaw_positions)

CombinationTools.print_as_integers('x_positions', x_positions)
CombinationTools.print_as_integers('y_positions', y_positions)
CombinationTools.print_as_integers('yaw_positions', yaw_positions)
print('Nr of combinations:', len(combinations))

R = RobotBat.RobotBat(connect_robot=True, connect_sonar=True)
test_data = R.measure(subtract_floor=False, plot=True)
test_data_shape = test_data.shape
nr_x_positions = len(x_positions)
nr_y_positions = len(y_positions)
nr_yaw_positions = len(yaw_positions)

data_array = np.zeros((nr_x_positions, nr_y_positions, nr_yaw_positions, repeats, test_data_shape[0], test_data_shape[1]))
success_array = np.zeros((nr_x_positions, nr_y_positions, nr_yaw_positions))

# Check whether an existing file matches the settings
existing_matches = False
last_index = 0
if path.exists(full_file_name):
    file = open(full_file_name, 'rb')
    existing_data = pickle.load(file)
    file.close()
    existing_combinations = existing_data['combinations']
    existing_pitch = existing_data['pitch']
    existing_y_extents = existing_data['y_extents']
    existing_z_extents = existing_data['z_extents']
    existing_matches = True
    if not combinations == existing_combinations: existing_matches = False
    if not pitch == existing_pitch: existing_matches = False
    if not y_extents == existing_y_extents: existing_matches = False
    if not z_extents == existing_z_extents: existing_matches = False

    if existing_matches:
        action = CombinationTools.ask_action()
        if action == 'Stop script':
            sys.exit('Stopped by user')
        if action == 'Continue existing data':
            data_array = existing_data['data_array']
            success_array = existing_data['success_array']
            last_index = existing_data['last_index']

for index, combination in enumerate(combinations):
    if index < last_index: continue
    print('#' * 25)
    print('>>>> POSITION', index, 'OF', len(combinations))
    print('#' * 25)

    position = combination[0]
    indices = combination[1]
    current_x = position[0]
    current_y = position[1]
    current_yaw = position[2]
    x_index = indices[0]
    y_index = indices[1]
    yaw_index = indices[2]
    z_position = np.interp(current_y, y_extents, z_extents)
    move_result = R.set_position(current_x, current_y, z_position, current_yaw, pitch)
    success_array[x_index, y_index, yaw_index] = move_result
    for i in range(repeats):
        plot = False
        if i == repeats - 1: plot = True
        data = R.measure(plot=plot, title=str(position))
        data_array[x_index, y_index, yaw_index, i, :, :] = data
        time.sleep(0.1)

    data_to_save = {
        'data_array': data_array,
        'success_array': success_array,
        'combinations': combinations,
        'x_positions': x_positions,
        'y_positions': y_positions,
        'y_extents': y_extents,
        'z_extents': z_extents,
        'yaw_positions': yaw_positions,
        'pitch': pitch,
        'repeats': repeats,
        'description': description,
        'script_text': script_text,
        'last_index': index
    }

    file = open(full_file_name, 'wb')
    pickle.dump(data_to_save, file)
    file.close()
