#
# Code for working with the maxbotix sonar head using the pyboard D
#

# 192.168.200.162
import socket
import time
import numpy
import re
from matplotlib import pyplot

break_char = '*'


def get_axes(n, rate):
    max_time = 1000 * (n / rate)
    time_axis = numpy.linspace(0, max_time, n)
    dist_axis = time_axis * 17
    return time_axis, dist_axis


def plot_data(data, rate, first, second, axis='sample'):
    channel_names = ['ch1', 'ch2']
    n = data.shape[0]
    time_axis, dist_axis = get_axes(n, rate)
    if axis.startswith('s'): pyplot.plot(data)
    if axis.startswith('t'): pyplot.plot(time_axis, data)
    if axis.startswith('d'): pyplot.plot(dist_axis, data)
    pyplot.legend([channel_names[first - 1], channel_names[second - 1]])
    pyplot.show()


class Client:
    def __init__(self, ip, port, verbose=False):
        self.ip = ip
        self.port = port
        self.sock = None
        self.verbose = verbose
        self.server_address = (self.ip, self.port)

    def connect(self):
        while True:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(2)
                self.sock.connect(self.server_address)
                self.sock.settimeout(10)
                break
            except socket.timeout:
                self.sock.close()
                print('sonar: Trying to reconnect')
                time.sleep(3)


    def disconnect(self):
        self.sock.close()

    def get_data(self, first=1, second=2, rate=10000, duration=10):
        command = str(first) + ',' + str(second) + ',' + str(rate) + ',' + str(duration) + break_char
        data, success = self.send_command(command)
        data = re.findall(r'[0-9]+', data)
        data = [int(i) for i in data]
        data = numpy.array(data)
        return data, success

    def measure(self, first=1, second=2, rate=10000, duration=30, plot=False):
        start = time.time()
        data = None
        success = False
        for i in range(3):
            print('Sonar: connecting')
            self.connect()
            data, success = self.get_data(first, second, rate, duration)
            self.disconnect()
            if success: break
        data = numpy.reshape(data, (2, -1))
        data = numpy.transpose(data)
        end = time.time()
        duration = end - start
        if self.verbose: print('Sonar: Measurement duration', duration, success)
        if plot: plot_data(data, rate, first, second, axis='d')
        return data

    def send_command(self, command, expect_answer=True):
        if not command.endswith(break_char): command += break_char
        self.sock.send(command.encode())
        data = ''
        if not expect_answer: return data
        while 1:
            packet = self.sock.recv(1024)
            packet = packet.decode()
            data += packet
            if data.endswith(break_char): break
        data = data.rstrip(break_char)
        return data, True

    # def send_command(self, command, expect_answer=True):
    #     if not command.endswith(break_char): command += break_char
    #     self.sock.send(command.encode())
    #     data = ''
    #     if not expect_answer: return data
    #     start_time = time.time()
    #     success = False
    #     print('Sonar: waiting for data > .', end='')
    #     while 1:
    #         try:
    #             packet = self.sock.recv(1024)
    #             packet = packet.decode()
    #             data += packet
    #             print('.', end='')
    #         except socket.timeout:
    #             print('*', end='')
    #         if data.endswith(break_char): success = True
    #         if time.time() - start_time > 2: break
    #         if success: break
    #     print()
    #     data = data.rstrip(break_char)
    #     return data, success


if __name__ == "__main__":
    import random
    client = Client('192.168.1.5', 1000, verbose=True)
    for x in range(1000):
        echo = client.measure(rate=10000, duration=30)
        s = random.random() * 2
        time.sleep(s)
    pyplot.show()
