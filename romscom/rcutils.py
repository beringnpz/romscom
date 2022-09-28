"""
romscom utility module

Provides a number of small helper functions used by the top-level romscom 
functions.  Not exposed to the user by default.
"""


from collections import OrderedDict
import yaml
import numpy as np
import sys
from datetime import datetime, timedelta
import glob
import os

def ordered_load(stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    """
    This function pulled from https://stackoverflow.com/questions/5121931/.
    It makes sure YAML dictionary loads preserve order, even in older
    versions of python.

    Args:
        stream: input stream
        loader: loader (default: yaml.SafeLoader)

    usage example:
    ordered_load(stream, yaml.SafeLoader)
    """

    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def bool2str(x):
    """
    Formats input boolean as string 'T' or 'F'
    """
    if not isinstance(x, bool):
        return x
    y = '{}'.format(x)[0]
    return y

def float2str(x):
    """
    Formats input float as Fortran-style double-precision string

    Args:
        x:  scalar float

    Returns:
        y:  string with x in Fortran double-precision syntax (e.g., "1.0d0")
    """
    if not isinstance(x, float):
        return
    y = '{}'.format(x).replace('e','d')
    if not 'd' in y:
    # if not any(x in y for x in ['d','.']):
        y = '{}d0'.format(y)
    return y

def consecutive(data, stepsize=0):
    """
    Groups values in list based on difference between consecutive elements

    Args:
        data:       a list
        stepsize:   difference between consecutive elements to use for
                    grouping. Default = 0, i.e. identical values grouped

    Returns:
        list of lists, values grouped.

    Example:
        consecutive([1, 1, 1, 2, 2, 4, 5]) -> [[1, 1, 1], [2, 2], [4], [5]]
        consecutive([1, 1, 1, 2, 2, 4, 5], 1) -> [[1], [1], [1, 2], [2], [4, 5]]
    """
    data = np.array(data)
    tmp = np.split(data, np.where(np.diff(data) != stepsize)[0]+1)
    tmp = [x.tolist() for x in tmp]
    return tmp

def list2str(tmp, consecstep=-99999):
    """
    Convert list of bools, floats, or integers to string

    Args:
        tmp:        a list of either all bools, all floats, all
                    integers, or all strings
        consecstep: step size to use for compression.  Default = -99999,
                    i.e. no compression; use 0 for ROMS-style compression
                    (i.e. T T T F -> 3*T F).  Not applicable to string lists.

    Returns:
        string, ROMS-appropriate string of inputs
    """
    if not (all(isinstance(x, float) for x in tmp) or
            all(isinstance(x, bool)  for x in tmp) or
            all(isinstance(x, int)   for x in tmp) or
            all(isinstance(x, str)   for x in tmp)):
        return tmp

    if isinstance(tmp[0], str):
        y = ' '.join(tmp)
    else:

        consec = consecutive(tmp, stepsize=consecstep)

        consecstr = [None]*len(consec)

        for ii in range(0, len(consec)):
            n = len(consec[ii])
            if isinstance(tmp[0], float):
                sampleval = float2str(consec[ii][0])
            elif isinstance(tmp[0], bool):
                sampleval = bool2str(consec[ii][0])
            else:
                sampleval = consec[ii][0]

            if n > 1:
                consecstr[ii] = '{num}*{val}'.format(num=n,val=sampleval)
            else:
                consecstr[ii] = '{val}'.format(val=sampleval)

        y = ' '.join(consecstr)
    return y

def multifile2str(tmp):
    """
    Convert a multifile list of filenames (with possible nesting) to string

    Args:
        tmp:    a list of either strings or lists of strings (can include both)

    Returns:
        string, ROMS multi-file formated
    """

    for idx in range(0, len(tmp)):
        if isinstance(tmp[idx], list):
            delim = f" |\n"
            tmp[idx] = delim.join(tmp[idx])

    delim = f" \\\n"
    newstr = delim.join(tmp)
    return newstr


def checkforstring(x, prefix=''):
    """
    Check that all dictionary entries have been stringified
    """
    for ky in x.keys():
        if isinstance(x[ky], dict):
            checkforstring(x[ky], ky)
        else:
            if not (isinstance(x[ky], (str)) or
                    (isinstance(x[ky],list) and
                    (all(isinstance(i,str) for i in x[ky])))):
                print('{}{}'.format(prefix, ky))


def formatkeyvalue(kw, val, singular):
    if kw in singular:
        return '{:s} = {}\n'.format(kw,val)
    else:
        return '{:s} == {}\n'.format(kw,val)


def parserst(filebase):
    """
    Parse restart counters from ROMS simulation restart files

    This function finds the name of, and parses the simulation counter,
    from a series of ROMS restart files.  It assumes that those files
    were using the naming scheme from runtodate, i.e. filebase_XX_rst.nc
    where XX is the counter for number of restarts.

    Args:
        filebase:   base name for restart files (can include full path)

    Returns:
        d:          dictionary object with the following keys:
                    lastfile:   full path to last restart file
                    cnt:        restart counter of last file incremented
                                by 1 (i.e. count you would want to
                                restart with in runtodate)
    """
    allrst = sorted(glob.glob(os.path.join(filebase + "_??_rst.nc")))

    # If a process crashes between the def_rst call and the first wrt_rst,
    # we're left with a .rst file with 0-length time dimension.  If that happens,
    # we need to back up one counter

    while len(allrst) > 0:
        f = nc.Dataset(allrst[-1], 'r')
        if len(f.variables['ocean_time']) > 0:
            break
        else:
            allrst.pop()

    # Parse counter data from last rst file

    if len(allrst) == 0:
        rst = []
        cnt = 1
    else:

        rst = allrst[-1]

        pattern = filebase + "_(\d+)_rst.nc"
        m = re.search(pattern, rst)
        cnt = int(m.group(1)) + 1

    return {'lastfile': rst, 'count': cnt}



def fieldsaretime(d):
    """
    True if all time-related fields are in datetime/timedelta format
    """
    timeflds = timefieldlist(d)

    isnum = isinstance(d['DT'], float) and \
            isinstance(d['DSTART'], float) and \
            all(isinstance(d[x], int) for x in timeflds) and \
            isinstance(d['TIME_REF'], float)

    istime = isinstance(d['DT'], timedelta) and \
             isinstance(d['DSTART'], datetime) and \
             all(isinstance(d[x], timedelta) for x in timeflds) and \
             isinstance(d['TIME_REF'], datetime)

    if isnum:
        return False
    elif istime:
        return True
    else:
        raise Exception("Unexpected data types in time-related fields")

def timefieldlist(d):
    timeflds = ['NTIMES', 'NTIMES_ANA', 'NTIMES_FCT',
                'NRST', 'NSTA', 'NFLT', 'NINFO', 'NHIS', 'NAVG', 'NAVG2', 'NDIA',
                'NQCK', 'NTLM', 'NADJ', 'NSFF', 'NOBC',
                'NDEFHIS', 'NDEFQCK', 'NDEFAVG', 'NDEFDIA', 'NDEFTLM', 'NDEFADJ']

    for x in timeflds:
        if not x in d:
            timeflds.remove(x)

    return timeflds


def inputfilesexist(ocean):

    fkey = ['GRDNAME','ININAME','ITLNAME','IRPNAME','IADNAME','FWDNAME',
           'ADSNAME','FOInameA','FOInameB','FCTnameA','FCTnameB','NGCNAME',
           'CLMNAME','BRYNAME','NUDNAME','SSFNAME','TIDENAME','FRCNAME',
           'APARNAM','SPOSNAM','FPOSNAM','IPARNAM','BPARNAM','SPARNAM',
           'USRNAME']

    files = flatten([ocean[x] for x in fkey])
    flag = False

    for f in files:
        if not f.startswith('placeholder') and not os.path.isfile(f):
            print('WARNING!: Cannot find file {}'.format(f))
            flag = True
    if flag:
        sys.exit()

def flatten(A):
    rt = []
    for i in A:
        if isinstance(i,list): rt.extend(flatten(i))
        else: rt.append(i)
    return rt
