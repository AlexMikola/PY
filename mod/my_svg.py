"""# -*- coding: utf-8 -*-"""
import typing
from typing import Iterator, Tuple, List, Union, Any
import shapely
from shapely.geometry import *
from shapely import wkt
from shapely.affinity import translate as tr
import textwrap
import pathlib
import os


def my_svg(mult_geom, scale_factor=1., fill_color=None):
    """Returns SVG path element for the Polygon geometry.

    Parameters
    ==========
    scale_factor : float
        Multiplication factor for the SVG stroke-width.  Default is 1.
    fill_color : str, optional
        Hex string for fill color. Default is to use "#66cc99" if
        geometry is valid, and "#ff3333" if invalid.
    """
    if mult_geom.is_empty:
        return '<g />'
    if fill_color is None:
        fill_color = "#66cc99" if mult_geom.is_valid else "#ff3333"
    exterior_coords = [
        ["{},{}".format(*c) for c in mult_geom.exterior.coords]]
    interior_coords = [
        ["{},{}".format(*c) for c in interior.coords]
        for interior in mult_geom.interiors]
    path = " ".join([
        "M {} L {} z".format(coords[0], " L ".join(coords[1:]))
        for coords in exterior_coords + interior_coords])
    return (
        '<path fill-rule="evenodd" fill="{2}" stroke="#555555" '
        'stroke-width="{0}" opacity="0.6" d="{1}" />'
    ).format(2. * scale_factor, path, fill_color)

def svg_multi(mult_geom, scale_factor=1., fill_color=None):
    """Returns group of SVG path elements for the MultiPolygon geometry.

    Parameters
    ==========
    scale_factor : float
        Multiplication factor for the SVG stroke-width.  Default is 1.
    fill_color : str, optional
        Hex string for fill color. Default is to use "#66cc99" if
        geometry is valid, and "#ff3333" if invalid.
    """
    if mult_geom.is_empty:
        return '<g />'
    if fill_color is None:
        fill_color = "#66cc99" if mult_geom.is_valid else "#ff3333"
    return '<g>' + \
        ''.join(p.my_svg(mult_geom, scale_factor, fill_color) for p in mult_geom) + \
        '</g>'

def export_wkt_to_svg(coord: str, f_path: str, f_name: str) -> None:
    """     экспорт wkt координат в svg файл
    coord       -  координаты в формате wkt (строка)
    f_path      -  путь к каталогу, куда сохраняем
    f_name      -  имя файла, который сохраняем
    """
    ex = '.svg'
    if f_name == "" and f_path == "":
        f_name = "file_from_py.svg"
        full_path = os.path.join(pathlib.Path().resolve(), f'{f_name}{ex}')
    elif f_name != "" and f_path != "":
        full_path = os.path.join(f_path, f'{f_name}{ex}')
    elif f_path == "":
        full_path = os.path.join(pathlib.Path().resolve(), f'{f_name}{ex}')
    elif f_name == "":
        full_path = os.path.join(f_path, f'{f_name}{ex}')

    key_color = {"NZH": "#e89816", "OB": "#e89816", "PR": "#c27ede", "ZH": "#c63c38", "DE": "#ffe8d0", "DE2": "#ffe8d0",
                 "DO": "#c8c8c8", "HP": "#75b7dd", "OV": "#fbc6c5", "PP": "#c8c8c8", "SP": "#83b8ff", "TP": "#e6e6e6",
                 "TR": "#e6e6e6", "VD": "#bc0064", "VP": "#a5bfdd", "VS": "#e78bb7", "ZE": "#bedebe"}

    if f_name.split("_")[0] in key_color.keys():
        clr_hex = key_color[f_name.split("_")[0]]
    else:
        clr_hex = "#D0D0D0"

    # shapely svg
    area = wkt.loads(coord)
    # area = tr(geom_w, xoff=0, yoff=10000, zoff=0)  # смещаем геометрии по y оси
    with open(full_path, 'w') as f:
        # масштаб
        scale = 10000
        bound = area.bounds

        props = {
            'version': '1.1',
            'baseProfile': 'full',
            'width': '{width:.0f}cm'.format(width=10*scale),
            'height': '{height:.0f}cm'.format(height=10*scale),
            'viewBox': '%.1f,%.1f,%.1f,%.1f' % (0, -1*scale, 1*scale, 1*scale),
            'transform': "scale(-1, 1)",
            # 'viewBox': '%f,%f,%f,%f' % (0, 0, 1*scale, 1*scale),
            'xmlns': 'http://www.w3.org/2000/svg',
            'xmlns:ev': 'http://www.w3.org/2001/xml-events',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink'
        }

        f.write(textwrap.dedent(r'''
            <?xml version="1.0" encoding="utf-8" ?>
            <svg {attrs:s}>
            {data:s}
            </svg>
        ''').format(
            attrs=' '.join(['{key:s}="{val:s}"'.format(key=key, val=props[key]) for key in props]),
            data=area.svg(fill_color=clr_hex)
        ).strip())
