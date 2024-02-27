# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger()
print(logger)

import bpy
import sys

from import_svg import load_svg
# from SVG_MOD.import_svg import load_svg


def main():
    cntx = bpy.context
    f_path = r"C:\Users\dolgushin_an\Desktop\DO_1_0.2_fid_4212.svg"
    vot = load_svg(cntx, f_path, False)
    bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\dolgushin_an\Desktop\b.blend")


if __name__ == '__main__':
    main()
    print('vot')
