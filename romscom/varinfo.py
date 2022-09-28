"""
romscom varinfo module

This module provides functions to read and write varinfo.dat and varinfo.yaml 
files.  Still a work in progress.
"""

import pandas as pd
import yaml

def readfile(file, type="classic"):
    """
    Reads varinfo.dat file into a list of dictionaries

    Args:
        file:   file holding variable info
        type:   file format, can be one of the following
                "classic":  classic varinfo.dat style
                "yaml":     newer varinfo.yaml style
    Returns:
        a:      a list of dictionaries, where each entry corresponds to
                one I/O variable (i.e., the metadata array from the ROMS
                varinfo.yaml format).  Dictionary keys correspond to ROMS
                variable info fields.
    """

    if type == "classic":
        a = 1
    elif type == "yaml":
        # TODO: default varinfo.yaml isn't compatible due to colons in some fields... I double-quoted those, but should figure out a workaround
        # Also, figure out how to read/write comments?
        with open(file, 'r') as f:
            a= yaml.load(f)
            a = a['metadata']
    return a


def writefile(a, fname, type="classic"):
    """
    Writes I/O variable info to file

    Args:
        a:      variable info list of dictionaries
        fname:  name of file to create
        type:   file format, can be one of the following
                "classic":  classic varinfo.dat style
                "yaml":     newer varinfo.yaml style
    """

    if type == "classic":
        with open(fname, 'w') as f:
            for v in a:
                f.write((f"'{v['variable']}'\n"
                         f"  '{v['long_name']}'\n"
                         f"  '{v['units']}'\n"
                         f"  '{v['field']}'\n"
                         f"  '{v['time']}'\n"
                         f"  '{v['index_code']}'\n"
                         f"  '{v['type']}'\n"
                         f"  {v['scale']}\n\n"
                        ))
    elif type == "yaml":
        out = {'metadata': a}
        with open(fname, 'w') as f:
            yaml.dump(out, f)
