import io
import os
import datetime

class Logger():
    log_file = None
    def __init__(self, filename=None, folder='logs'):
        if not os.path.exists(folder):
            os.makedirs(folder)
        if filename == None:
            dt_now = datetime.datetime.now()
            date_string = '%s-%s-%s_%s:%s:%s'%(dt_now.year,
                                               dt_now.month,
                                               dt_now.day,
                                               dt_now.hour,
                                               dt_now.minute,
                                               dt_now.second)
            filename = date_string + '.txt'
        print filename
        self.log_file = open(folder + '/' + filename, 'w')

    def write_line(self, line):
        self.log_file.write(line)

    def close(self):
        self.log_file.close()
