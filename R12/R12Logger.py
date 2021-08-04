from R12 import HTML
from R12 import Settings
from pyBat import Misc
import time
import os.path as path
import webbrowser

input_color = "#a9cce3"
output_color = "##aeb6bf"

warning_color = '#f5cba7'
error_color = '#f5b7b1'
message_color = '#a2d9ce'


class Logger:
    def __init__(self):
        self.table = HTML.Table(header_row=['Time', 'Text'])
        self.print_comments = True

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
        if self.print_comments: print(level, text)

    def add_input(self, text):
        self.add(text, color=input_color, pre=True)

    def add_output(self, text):
        self.add(text, color=output_color, pre=True)

    def write(self, file_name):
        htmlcode = str(self.table)
        f = open(file_name, 'w')
        f.write(htmlcode)
        f.close()

    def view(self):
        out_file = path.join(Settings.log_dir, 'temp.html')
        self.write(out_file)
        webbrowser.open(out_file)

# l = logger()
# l.add('well', 'c')
# l.add('well well', 'step')
# l.add('sfdfd\r\n    fsdsf', 'o')
# l.view()
