"""# -*- coding: utf-8 -*-"""
from typing import List, Tuple, Dict, Union
from types import FunctionType
import pydoc

import inspect

class Inspect_Func:

    def get_all_funct_methods(obj) -> tuple:
        fun = inspect.getmembers(obj, predicate=inspect.isfunction)
        meth = inspect.getmembers(obj, predicate=inspect.ismethod)
        return [x[0] for x in fun], [x[0] for x in meth]

    def get_all_funct_methods_by_dir(ds) -> List:
        method_list = [func for func in dir(ds) if callable(getattr(ds, func))]
        return method_list

    def get_all_by_dir_without_magic_methods(ds) -> List:
        method_list = [
            func for func in dir(ds) if callable(getattr(ds, func)) and not func.startswith("__")
            ]
        return method_list

    def get_all_by_dict_methods(ds) -> List:
        return [x for x, y in ds.__dict__.items() if type(y) == FunctionType]

    def get_attr_by_dir(ds) -> List:
        atr = [getattr(ds, m) for m in dir(ds) if not m.startswith('__')]
        return atr

    def get_all_by_dir(ds) -> List:
        atr = [m for m in dir(ds) if not m.startswith('__')]
        return atr


    def get_all_fun(ds) -> List:
        method_list = [func[0] for func in inspect.getmembers(ds, predicate=inspect.isroutine) if
                       callable(getattr(ds, func[0]))]
        return method_list

    def get_all_atr(ds) -> List:
        meth = inspect.getmembers(ds, predicate=inspect.ismethod)
        atr_list = [inspect.signature(x[1]) for x in meth]
        return atr_list

    def get_all_doc(ds):
        meth = inspect.getmembers(ds, predicate=inspect.ismethod)
        doc_list = [pydoc.getdoc(x[1]) for x in meth]
        return doc_list

    # def get_all_meth(ds):
    #     meth = inspect.getmembers(ds, predicate=inspect.ismethod)
    #     doc_list = [pydoc. (x[1]) for x in meth]
    #     return doc_list

    """
    аfтрибуты считывать
    inspect.signature(x[1])
    
    
    
    """