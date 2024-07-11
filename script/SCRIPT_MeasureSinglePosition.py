import time
import numpy as np  
import os
import sys
import pickle
import logging
from R12 import RobotBat
# from R12 import CombinationTools
from matplotlib import pyplot as plt


world_x = -200
world_y = 200
world_z = 300
world_pitch = 0
world_yaw = 27.5
repeats = 50
reach_lim = 450
# reach_table = {'x': None, 'y': [0, 100, 200, 300], 'z': [500, 400, 300, 300]}
description = 'Test'

def check_z_reach(y:int,z:int, reach:int):
    if y**2 + z**2 > reach**2:
        logging.info('Reach limit exceeded')
        logging.info('y = %s, z = %s, reach = %s', y, z, reach)
        new_z = int(np.sqrt(reach**2 - y**2))
        logging.info('new_z = %s',new_z)
        return new_z
    else: return z
    


def do_measurement(world_x:int,
                   world_y:int,
                   world_z:int,
                   world_pitch:int,
                   world_yaw:int,
                   repeats:int,
                   dry_run:bool,
                   plot:bool,
                   delay:float,
                   save_data:bool,
                   reach_lim:int,
                   #reach_table:dict,
                   description:str, save_path:str='../data/test'):
    connect_sonar = not dry_run
    R = RobotBat.RobotBat(connect_robot=True, connect_sonar=connect_sonar)
    world_z = check_z_reach(world_y, world_z, reach_lim)
    R.set_position(world_x, world_y, world_z, world_yaw, world_pitch)
    if connect_sonar:
        data =  R.measure(subtract_floor=True, plot=plot)
        data_array = np.zeros((repeats, data.shape[0], data.shape[1]))
        full_file_name = os.path.join(save_path, 'data.pkl')
        for i in range(repeats):
            print('###########', i)
            data = R.measure(plot=False, subtract_floor=False)
            data_array[i,:,:] = data
            time.sleep(delay)
    if connect_sonar:
        if save_data:
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
    do_measurement(world_x, world_y, world_pitch, world_yaw, repeats, False, True, 0.25, True, reach_lim, description)