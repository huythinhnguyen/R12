import pandas
import numpy
import os


class Recommender:
    def __init__(self):
        data_file = os.path.join('R12','recommendations.txt')
        self.data = pandas.read_csv(data_file, header=None)
        self.data.columns = ['x', 'y', 'z', 'angle_up', 'angle_down', 'recommendation']
        self.x_values = self.data.x.values
        self.y_values = self.data.y.values
        self.z_values = self.data.z.values

    def recommend(self, x, y, z):
        dx = ((self.x_values - x) ** 2) ** 0.5
        dy = ((self.y_values - y) ** 2) ** 0.5
        dz = ((self.z_values - z) ** 2) ** 0.5
        sm = dx + dy + dz
        min_index = numpy.argmin(sm)
        selected = self.data.iloc[min_index, :]
        return  selected
