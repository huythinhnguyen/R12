from R12 import HTML
from R12 import Settings
from pyBat import Misc, FileOperations
import time
import os.path as path
import webbrowser

cmd_color = "#a9cce3"
response_color = "##aeb6bf"

warning_color = '#f5cba7'
error_color = '#f5b7b1'
message_color = '#a2d9ce'


class Logger:
    def __init__(self, auto_write=True):
        self.table = HTML.Table(header_row=['Time', 'Text'])
        self.console_log = [0, 1, 2, 'cmd'] # options: [0, 1, 2, 'cmd', 'rsp']
        self.auto_write = auto_write

    def add(self, text, color=False, pre=False):
        if pre: text = '<pre>' + text + '</pre>'
        time_string = time.asctime()
        if color: A = HTML.TableCell(time_string, bgcolor=color)
        if not color: A = HTML.TableCell(time_string, bgcolor=color)
        B = HTML.TableCell(text)
        self.table.rows.append([A, B])

    def add_comment(self, text, level=0):
        if Misc.iterable(text): text = Misc.lst2str(text, sep=' ')
        if level == 0: self.add(text, color=message_color)
        if level == 1: self.add(text, color=warning_color)
        if level == 2: self.add(text, color=error_color)
        if self.auto_write: self.write()
        if level in self.console_log: print('lvl', level, text)

    def add_sent_cmd(self, text):
        self.add(text, color=cmd_color, pre=True)
        if 'cmd' in self.console_log: print('cmd', text)
        if self.auto_write: self.write()

    def add_received_response(self, text):
        self.add(text, color=response_color, pre=True)
        if 'rsp' in self.console_log: print('rsp', text)
        if self.auto_write: self.write()

    def write(self):
        out_file = path.join(Settings.log_dir, 'temp.html')
        html_code = str(self.table)
        f = open(out_file, 'w')
        f.write(html_code)
        f.close()
        return out_file

    def view(self):
        FileOperations.create_folder(Settings.log_dir)
        out_file = self.write()
        webbrowser.open(out_file)

