"""**ROMS Communication Module utility functions**

This module provides a number of small helper functions used by the primary romscom
functions.

- `ordered_load(stream,...)` ensures YAML dictionary loads preserve order across different python versions
- `bool2str(x)` formats a scalar boolean as 'T'/'F'
- `float2str(x)` formats a float as a double-precision string
"""

import glob
import os
import re
import warnings
from collections import OrderedDict
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np
import yaml


def ordered_load(stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    """
    This function was pulled from https://stackoverflow.com/questions/5121931/.
    It makes sure YAML dictionary loads preserve order, even in older
    versions of python.

    Args:
        stream: input stream
        loader: loader (default: yaml.SafeLoader)

    usage example:
    ordered_load(stream, yaml.SafeLoader)

    Returns:
        (OrderedDict): dictionary

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

    Args:
        x (logical)

    Returns:
        (string): 'T' or 'F', corresponding to True or False, respectively
    """
    if not isinstance(x, bool):
        return x
    y = '{}'.format(x)[0]
    return y

def float2str(x):
    """
    Formats input float as Fortran-style double-precision string

    Args:
        x (float): input value

    Returns:
        (string): x in Fortran double-precision syntax (e.g., "1.0d0")
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
        data (list): list of numeric values
        stepsize (numeric): difference between consecutive elements to use for
            grouping. Default = 0, i.e. identical values grouped

    Returns:
        (list of lists): values grouped.

    Examples:

        >>> consecutive([1, 1, 1, 2, 2, 4, 5])
        [[1, 1, 1], [2, 2], [4], [5]]

        >>> consecutive([1, 1, 1, 2, 2, 4, 5], 1)
        [[1], [1], [1, 2], [2], [4, 5]]
    """
    data = np.array(data)
    tmp = np.split(data, np.where(np.diff(data) != stepsize)[0]+1)
    tmp = [x.tolist() for x in tmp]
    return tmp

def list2str(tmp, consecstep=-99999):
    """
    Convert list of bools, floats, or integers to string

    Args:
        tmp (list): a list of either all bools, all floats, all integers, or all
            strings
        consecstep (numeric): step size to use for compression.
            Default = -99999, i.e. no compression; use 0 for ROMS-style
            compression (i.e. T T T F -> 3*T F).  Not applicable to string lists.

    Returns:
        (string): ROMS-appropriate string version of list values
    """
    if not (all(isinstance(x, float) for x in tmp) or
            all(isinstance(x, bool)  for x in tmp) or
            all(isinstance(x, int)   for x in tmp) or
            all(isinstance(x, str)   for x in tmp)):
        warnings.warn(f"Mixed data types found in list ({tmp}); skipping string conversion", stacklevel=2)
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
        tmp (string or list of strings): names of files and multi-files

    Returns:
        (string): ROMS multi-file formatted as string
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
    Check that all dictionary entries have been stringified, and print the keys cooresponding
    to non-stringified values (primary diagnostic)

    Args:
        x (dict): ROMS parameter dictionary
        prefix (string, optional): prefix applied to printout of non-stringified value's key
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
    """
    Format dictionary entries as ROMS parameter assignments

    Args:
        kw (string): key
        val (string): stringified value
        singular (list of strings): list of keys that should be treated as
            unvarying across ROMS grids (i.e. uses a = assignment vs ==)

    Returns:
        (string): key/value as a line of text, e.g. 'key == value'
    """
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
        filebase (string): base name for restart files (can include full path)

    Returns:
        (dict): with the following keys:

            Key        |Value type|Value description
            -----------|----------|-----------------
            `lastfile` |`string`  |full path to last restart file
            `cnt`      |`int`     |restart counter of last file incremented by 1 (i.e. count you would want to restart with in runtodate)
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

    Args:
        d (dict): parameter dictionary

    Returns:
        (boolean): True if all time-related fields are in datetime/timedelta
            format, False if all are numeric.  
        
    Raises:
        Exception: if a mix of numeric and datetime/timedelta values are found
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
    """
    Get list of time-related dictionary keys

    Args:
        d (dict): ROMS parameter dictionary

    Returns:
        (list of strings): keys in d that are time-related
    """

    timeflds = ['NTIMES', 'NTIMES_ANA', 'NTIMES_FCT',
                'NRST', 'NSTA', 'NFLT', 'NINFO', 'NHIS', 'NAVG', 'NAVG2', 'NDIA',
                'NQCK', 'NTLM', 'NADJ', 'NSFF', 'NOBC',
                'NDEFHIS', 'NDEFQCK', 'NDEFAVG', 'NDEFDIA', 'NDEFTLM', 'NDEFADJ']

    rem = []
    for x in timeflds:
        if not x in d:
            rem.append(x)

    timeflds = [x for x in timeflds if x not in rem]

    return timeflds

def inputfilesexist(ocean):
    """
    Check that all ROMS input files exist.  If a filename starts with the string
    "placeholder", it is ignored in this check (this allows you to keep unused
    parameters in the YAML files, but clearly indicates that these files will
    not be required)

    Args:
        ocean (dict): ROMS parameter dictionary

    Returns:
        (boolean): True if all files exist (or are marked as placeholders),
            False otherwise
    """

    fkey = ['GRDNAME','ININAME','ITLNAME','IRPNAME','IADNAME','FWDNAME',
           'ADSNAME','FOInameA','FOInameB','FCTnameA','FCTnameB','NGCNAME',
           'CLMNAME','BRYNAME','NUDNAME','SSFNAME','TIDENAME','FRCNAME',
           'APARNAM','SPOSNAM','FPOSNAM','IPARNAM','BPARNAM','SPARNAM',
           'USRNAME']

    rem = []
    for x in fkey:
        if not x in ocean:
            rem.append(x)

    fkey = [x for x in fkey if x not in rem]

    files = flatten([ocean[x] for x in fkey])
    flag = True

    for f in files:
        if not f.startswith('placeholder') and not os.path.isfile(f):
            warnings.warn(f"Cannot find file {f}")
            flag = False

def flatten(A):
    """
    Recursively flatten a list of lists (of lists of lists...)

    Args:
        A (list): list that may contains nested lists

    Returns:
        (list): contents of A where all sub-lists have been flattened to a single
            level

    """
    rt = []
    for i in A:
        if isinstance(i,list): rt.extend(flatten(i))
        else: rt.append(i)
    return rt

def parseromslog(fname):
    """
    Parse ROMS standard output log for some details about the success (or not) of a ROMS
    simulation

    Args
        fname (string): name of file with ROMS standard output

    Returns:
        (dict): dictionary with the following fields:

            Key        |Value type|Value description
            -----------|----------|-----------------
            `cleanrun` |`boolean` | True if simulation ran without errors
            `blowup`   |`boolean` | True if simulation blew up
            `laststep` |`int`     | Index of last step recorded
            `lasthis`  |`string`  | Name of last history file defined
    """

    with open(fname, 'r') as f:
        lines = f.read()
        lnnum = lines.find('ROMS/TOMS: DONE')
        cleanrun = lnnum != -1

        lnnum1 = lines.find('Blowing-up: Saving latest model state into  RESTART file')
        lnnum2 = lines.find('MAIN: Abnormal termination: BLOWUP')
        blowup = (lnnum1 != -1) | (lnnum2 != -1)

    step = []
    lasthis = []
    if cleanrun:
        with open(fname, 'r') as f:

            datablock = False

            for line in f:
                if line.find('STEP   Day HH:MM:SS  KINETIC_ENRG   POTEN_ENRG    TOTAL_ENRG    NET_VOLUME') != -1:
                    datablock = True
                elif line.find('Elapsed CPU time (seconds):') != -1:
                    datablock = False
                elif datablock:
                    tmp = line.split() #string.split(line.strip())
                    if len(tmp) == 7 and tmp[0].isdigit():
                        step = int(tmp[0])
                    if len(tmp) == 6 and tmp[0] == 'DEF_HIS':
                        lasthis = tmp[-1]

    return {'cleanrun': cleanrun, 'blowup': blowup, 'laststep': step, 'lasthis':lasthis}

def findclosesttime(folder, targetdate, pattern='*his*.nc'):
    """
    Search folder for history file with time closest to the target date

    Args:
        folder (string): pathname to folder holding output of a BESTNPZ ROMS
            simulation, with history files matching the pattern provided.
            Alternatively, can be a list of history filenames (useful if you
            want to include a smaller subset from within a folder that can't be
            isolated via pattern)
        targetdate (datetime): target date
        pattern (string): pattern-matching string appended to folder name
            as search string to identify history files Default = '*his*.nc'

    Returns:
        (dict): with the following keys/values:

            Key       |Value type  |Value description
            ---       |----------  |-----------------
            `filename`|`string`    |full path to history file including nearest date
            `idx`     |`int`       |time index within that file (0-based) of nearest date
            `dt`      |`timedelta` |time between nearest date and target date
            `unit`    |`string`    |time units used in history file
            `cal`     |`string`    |calendar used by history file
    """

    if (type(folder) is str) and os.path.isdir(folder):
        hisfiles = glob.glob(os.path.join(*(folder, pattern)))
    else:
        hisfiles = folder

    f = nc.Dataset(hisfiles[0], 'r')
    tunit = f.variables['ocean_time'].units
    tcal = f.variables['ocean_time'].calendar

    dtmin = []

    d = {}
    for fn in hisfiles:
        try:
            f = nc.Dataset(fn, 'r')
            time = nc.num2date(f.variables['ocean_time'][:], units=tunit, calendar=tcal)

            dt = abs(time - targetdate)

            if not d:
                d['filename'] = fn
                d['idx'] = np.argmin(dt)
                d['dt'] = dt[d['idx']]
                d['time'] = time[d['idx']]
            else:
                if min(dt) < d['dt']:
                    d['filename'] = fn
                    d['idx'] = np.argmin(dt)
                    d['dt'] = dt[d['idx']]
                    d['time'] = time[d['idx']]
        except:
            pass

    d['unit'] = tunit
    d['cal'] = tcal

    return d