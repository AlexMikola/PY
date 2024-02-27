import subprocess as sp
import sys
import win32com

from win32com.client import combrowse

import serial.tools.list_ports


def scan_comports():
    correct_port = 'none'
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        print("%s %s" % (p[0], p[1]))
        if str(p[1]).startswith("SomeComportName"):
            correct_port = p[0]

    print('stop')

scan_comports()

combrowse.main()

# sp.Popen('python -m win32com.client.combrowse', shell=True)  # запуск COM brouwser на ПК
print('asd')