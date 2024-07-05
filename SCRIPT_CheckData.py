import pickle
import numpy as np
from matplotlib import pyplot as plt

filename = 'data/test'

file = open(filename, 'rb')
data = pickle.load(file)
file.close()

print(data.keys())

data_array = data['data_array']
success_array = data['success_array']
last_index = data['last_index']
combinations = data['combinations']
combos = len(combinations)

successes = np.sum(success_array)

selected = data_array[0, 0, 0, 0, :, 0]
plt.figure()
plt.plot(selected)
plt.show()

