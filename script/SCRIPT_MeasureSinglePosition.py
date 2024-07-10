import time
import numpy as np  
import os
import sys
import pickle
from R12 import RobotBat
# from R12 import CombinationTools
from matplotlib import pyplot as plt


world_x = -200
world_y = 200
world_pitch = 0
world_yaw = 27.5
repeats = 50
reach_table = {'x': None, 'y': [0, 100, 200, 300], 'z': [500, 400, 300, 300]}
description = 'Test'


def do_measurement(world_x:int,
                   world_y:int,
                   world_pitch:int,
                   world_yaw:int,
                   repeats:int,
                   dry_run:bool,
                   plot:bool,
                   delay:float,
                   save_data:bool,
                   reach_table:dict,
                   description:str, save_path:str='../data/test'):
    R = RobotBat.RobotBat(connect_robot=True, connect_sonar=(not dry_run))
    world_z = np.interp(world_y, reach_table['y'], reach_table['z'])
    R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)
    if not dry_run:
        data =  R.measure(subtract_floor=True, plot=plot)
        data_array = np.zeros((repeats, data.shape[0], data.shape[1]))
        full_file_name = os.path.join(save_path, 'data.pkl')
        for i in range(repeats):
            print('###########', i)
            data = R.measure(plot=False, subtract_floor=False)
            data_array[i,:,:] = data
            time.sleep(delay)
    if not dry_run:
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
        if plot:
            plt.plot(np.mean(data_array, axis=0))
            plt.show()

if __name__=='__main__':
    do_measurement(world_x, world_y, world_pitch, world_yaw, repeats, False, False, 0.25, False, reach_table, description)