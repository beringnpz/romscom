"""
romscom: ROMS Communication Module

This module provides a number of functions designed to manipulate ROMS I/O, with
a focus on ROMS standard input and similar ascii-formatted input files.
"""

import copy
from datetime import datetime, timedelta
import os
import glob
import netCDF4 as nc
import math
import csv
import sys
import subprocess
import romscom.rcutils as r

"""
============================
Standard input functions
============================
This set of functions converts between parameter dictionary and ROMS standard
input format
"""

def readparamfile(filename, tconvert=False):
    """
    Reads parameter YAML file into an ordered dictionary

    Args:

        filename:   name of parameter file

    Optional keyword args (defaults in []):

        tconvert:   logical, True to convert time-related fields to datetimes
                    and timedeltas, False to keep in native ROMS format [False]

    Returns:
        parameter dictionary
    """

    with open(filename, 'r') as f:
        d = r.ordered_load(f)

    if tconvert:
        converttimes(d, "time")

    return d

def stringifyvalues(d, compress=False):
    """
    Formats all dictionary values to ROMS standard input syntax

    This function converts values to the Fortran-ish syntax used in ROMS
    standard input files.  Floats are converted to the double-precision format
    of Fortran read/write statements, booleans are converted to T/F, integers
    are converted straight to strings, and lists are converted to space-
    delimited strings of the above (compressed using * for repeated values where
    applicable).  Values corresponding to a few special KEYWORDS (e.g., POS)
    receive the appropriate formatting

    Args:

        d:          ROMS parameter dictionary

    Optional keyword args (defaults in []):

        compress:   True to compress repreated values (e.g., T T T -> 3*T),
                    False to leave as is [False]

    Returns:
        copy of d with all values replaced by ROMS-formatted strings
    """

    if compress:
        consecstep = 0
    else:
        consecstep=-99999

    newdict = copy.deepcopy(d)

    for x in newdict:

        # Start by checking for special cases

        if x == "no_plural":
            pass
        elif x == 'POS':
            # Stations table
            tmp = newdict[x]
            for idx in range(0,len(tmp)):
                if tmp[idx][1] == 1: # lat/lon pairs
                    tmp[idx] = '{:17s}{:4d} {:4d} {:12f} {:12f}'.format('', *tmp[idx])
                elif tmp[idx][1] == 0: # I/J pairs
                    tmp[idx] = '{:17s}{:4d} {:4d} {:12d} {:12d}'.format('', *tmp[idx])

            tablestr = '{:14s}{:4s} {:4s} {:12s} {:12s} {:12s}'.format('', 'GRID','FLAG', 'X-POS', 'Y-POS', 'COMMENT')
            tmp.insert(0, tablestr)

            newdict[x] = '\n'.join(tmp)

        elif x in ['BRYNAME', 'CLMNAME', 'FRCNAME']:
            # Multi-file entries (Single file strings are not modified)
            if isinstance(newdict[x], list):
                newdict[x] = r.multifile2str(newdict[x])

        elif x.endswith('LBC'):
            # LBC values are grouped 4 per line
            for k in newdict[x]:
                if len(newdict[x][k]) > 4:
                    nline = len(newdict[x][k])//4
                    line = []
                    for ii in range(0,nline):
                        s = ii*4
                        e = ii*4 + 4
                        line.append(' '.join(newdict[x][k][s:e]))
                    delim = f" \\\n"
                    newdict[x][k] = delim.join(line)
                else:
                    newdict[x][k] = ' '.join(newdict[x][k])
        elif x in ['fsh_age_offset', 'fsh_q_G', 'fsh_q_Gz', 'fsh_alpha_G', 
                   'fsh_alpha_Gz', 'fsh_beta_G', 'fsh_beta_Gz', 'fsh_catch_sel', 
                    'fsh_catch_01', 'fsh_catch_99']:
            # FEAST parses arrays via repeated keywords
            tmp = newdict[x]
            for ii in range(0,len(tmp)):
                tmp[ii] = r.list2str(tmp[ii], consecstep=-99999)
                if ii > 0:
                    tmp[ii] = f"{x} == {tmp[ii]}"
            newdict[x] = '\n'.join(tmp)
        else:
            if isinstance(newdict[x], float):
                newdict[x] = r.float2str(newdict[x])
            elif isinstance(newdict[x], bool):
                newdict[x] = r.bool2str(newdict[x])
            elif isinstance(newdict[x], int):
                newdict[x] = '{}'.format(newdict[x])
            elif isinstance(newdict[x], list):
                tmp = newdict[x]
                if isinstance(tmp[0], list):
                    newdict[x] = [r.list2str(i, consecstep=consecstep) for i in tmp]
                else:
                    newdict[x] = r.list2str(tmp, consecstep=consecstep)
            elif isinstance(newdict[x], dict):
                    newdict[x] = stringifyvalues(newdict[x], compress=compress)

    return newdict


def dict2standardin(d, compress=False, file=None):
    """
    Converts a parameter dictionary to standard input text, and optionally
    writes to file

    Args:

        d:          parameter dictionary

    Optional keyword args (defaults in []):

        compress:   True to compress repeated values (i.e., T T T -> 3*T),
                    [False]
        file:       name of output file.  If included, text will be printed to
                    file rather than returns

    Returns:
        text string of standard input text (only if output file not provided)

    """
    if 'DT' in d:
        istime = r.fieldsaretime(d)
    else:
        istime = False
    if istime:
        converttimes(d, "ROMS")
    dstr = stringifyvalues(d, compress)
    no_plural = dstr.pop('no_plural')
    txt = []
    for ky in dstr:
        if isinstance(dstr[ky], list):
            for i in dstr[ky]:
                txt.append(r.formatkeyvalue(ky, i, no_plural))
        elif isinstance(dstr[ky], dict):
            for i in dstr[ky]:
                newkey = '{}({})'.format(ky,i)
                txt.append(r.formatkeyvalue(newkey, dstr[ky][i], no_plural))
        else:
            txt.append(r.formatkeyvalue(ky, dstr[ky], no_plural))

    delim =  ''
    txt = delim.join(txt)

    if istime:
        converttimes(d, "time")

    if file is None:
        return txt
    else:
        with open(file, 'w') as f:
            f.write(txt)

def runtodate(ocean, simdir, simname, enddate, dtslow=None, addcounter="most",
               compress=False, romscmd=["mpirun","romsM"], dryrunflag=True,
               permissions=0o755, count=1):
    """
    Sets up I/O and runs ROMS simulation through indicated date

    Args:

        ocean:      ROMS parameter dictionary for standard input
        simdir:     string, folder where I/O subfolders are found/created
        simname:    string, base name for simulation, used as prefix for auto-generated
                    input, standard output and error files, and .nc output.
        enddate:    datetime, simulation end date

    Optional keyword args (defaults in []):

        dtslow:     timedelta, length of time step used during slow-stepping
                    (blowup) periods.  If None, this will be set to half the
                    primary (i.e., ocean['DT']) time step [None]
        addcounter: output file types for which a counter index will be added.
                    (See setoutfilenames) ["most"]
        compress:   logical, True to compress repeated values in standard input
                    file (see stringifyvalues) [False]
        romscmd:    string, command used to call the ROMS executable.
                    ["mpirun romsM"]
        dryrunflag: True to perform a sry run, where I/O is prepped but ROMS
                    executable is not called
        permissions:folder permissions applied to I/O subfolders if they don't
                    already exist (see os.chmod). [0o755]
    """

    # Get some stuff from dictionary, before we make changes

    converttimes(ocean, "time") # make sure we're in datetime/timedelta mode
    inifile = ocean['ININAME']
    dt = ocean['DT']
    drst = ocean['NRST']
    nrrec = ocean['NRREC']
    if dtslow is None:
        dtslow = dt/2

    # Set up input, output, and log folders

    fol = simfolders(simdir, create=True, permissions=permissions)

    # Initialization file: check for any existing restart files, and if not
    # found, start from the initialization file

    rstinfo = r.parserst(os.path.join(fol['out'], simname))
    if rstinfo['lastfile']:
        cnt = rstinfo['count']
        ocean['ININAME'] = rstinfo['lastfile']
        ocean['NRREC'] = -1
    else:
        cnt = count
        ocean['ININAME'] = inifile
        ocean['NRREC'] = nrrec

    # Check that all input files exist (better to do this here than let ROMS try and fail)

    r.inputfilesexist(ocean)

    # Get starting time from initialization file

    f = nc.Dataset(ocean['ININAME'], 'r')
    tunit = f.variables['ocean_time'].units
    tcal = f.variables['ocean_time'].calendar
    tini = max(nc.num2date(f.variables['ocean_time'][:], units=tunit, calendar=tcal))

    # Create log file to document slow-stepping time periods

    steplog = os.path.join(fol['log'], f"{simname}_step.txt")

    if not os.path.isfile(steplog):
        fstep = open(steplog, "w+")
        fstep.close()

    # Run sim

    while tini < (enddate - drst):

        # Set end date as furthest point we can run.  This will be either
        # the simulation end date  or the end of the slow-stepping period (if we
        # are in one), whichever comes first

        # Check if in slow-stepping period

        endslow = enddate
        ocean['DT'] = dt
        with open(steplog) as fstep:
            readCSV = csv.reader(fstep, delimiter=',')
            for row in readCSV:
                t1 = datetime.strptime(row[0], '%Y-%m-%d-%H-%M:%S')
                t2 = datetime.strptime(row[1], '%Y-%m-%d-%H-%M:%S')
                if (tini >= t1) & (tini <= (t2-drst)): # in a slow-step period
                    endslow = t2
                    ocean['DT'] = dtslow

        tend = min(enddate, endslow)
        ocean['NTIMES'] = tend - ocean['DSTART']

        # Set names for output files

        setoutfilenames(ocean, os.path.join(fol['out'], simname), cnt, addcounter=addcounter)

        # Names for standard input, output, and error

        standinfile  = os.path.join(fol['in'],  f"{simname}_{cnt:02d}_ocean.in")
        standoutfile = os.path.join(fol['log'], f"{simname}_{cnt:02d}_log.txt")
        standerrfile = os.path.join(fol['log'], f"{simname}_{cnt:02d}_err.txt")

        # Export parameters to standard input file

        converttimes(ocean, "ROMS")
        dict2standardin(ocean, compress=compress, file=standinfile)
        converttimes(ocean, "time")

        # Print summary

        cmdstr = ' '.join(romscmd)

        print("Running ROMS simulation")
        print(f"  Counter block:   {cnt}")
        print(f"  Start date:      {tini.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End date:        {tend.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  ROMS command:    {cmdstr}")
        print(f"  Standard input:  {standinfile}")
        print(f"  Standard output: {standoutfile}")
        print(f"  Standard error:  {standerrfile}")

        if dryrunflag:
            print("Dry run")
            return 'dryrun'
        else:
            with open(standoutfile, 'w') as fout, open(standerrfile, 'w') as ferr:
                subprocess.run(romscmd+[standinfile], stdout=fout, stderr=ferr)

        rsim = r.parseromslog(standoutfile)

        # Did the run crash (i.e. anything but successful end or blowup)? If
        # so, we'll exit now

        if (not rsim['cleanrun']) & (not rsim['blowup']):
            print('  Similation block terminated with error')
            return 'error'

        # Did it blow up?  If it did so during a slow-step period, we'll exit
        # now.  If it blew up during a fast-step period, set up a new
        # slow-step period and reset input to start with last history file.
        # If it ran to completion, reset input to start with last restart
        # file

        rstinfo = r.parserst(os.path.join(fol['out'], simname))
        cnt = rstinfo['count']

        if rsim['blowup']:
            if ocean['DT'] == dtslow:
                print('  Simulation block blew up in a slow-step period')
                return 'blowup'

            # Find the most recent history file written to
            hisfile = rsim['lasthis']

            if not hisfile: # non-clean blowup, no his file defined
                allhis = sorted(glob.glob(os.path.join(fol['out'], simname + "*his*.nc")))
                hisfile = allhis[-1]

            fhis = nc.Dataset(hisfile)
            if len(fhis.variables['ocean_time']) == 0:
                allhis = glob.glob(os.path.join(fol['out'], simname + "*his*.nc"))
                allhis = sorted(list(set(allhis) - set([hisfile])))
                hisfile = allhis[-1]

            ocean['ININAME'] = hisfile
            ocean['NRREC'] = -1

            f = nc.Dataset(ocean['ININAME'], 'r')
            tunit = f.variables['ocean_time'].units
            tcal = f.variables['ocean_time'].calendar
            tini = max(nc.num2date(f.variables['ocean_time'][:], units=tunit, calendar=tcal))

            t1 = tini.strftime('%Y-%m-%d-%H-%M:%S')
            t2 = (tini + timedelta(days=30)).strftime('%Y-%m-%d-%H-%M:%S')
            fstep = open(steplog, "a+")
            fstep.write('{},{}\n'.format(t1,t2))
            fstep.close()

        else:
            ocean['ININAME'] = rstinfo['lastfile']
            ocean['NRREC'] = -1

            f = nc.Dataset(ocean['ININAME'], 'r')
            tunit = f.variables['ocean_time'].units
            tcal = f.variables['ocean_time'].calendar
            tini = max(nc.num2date(f.variables['ocean_time'][:], units=tunit, calendar=tcal))

    # Print completion status message

    print('Simulation completed through specified end date')
    return 'success'


def simfolders(simdir, create=False, permissions=0o755):

    outdir = os.path.join(simdir, "Out")
    indir  = os.path.join(simdir, "In")
    logdir = os.path.join(simdir, "Log")

    if create:
        if not os.path.exists(indir):
            os.makedirs(indir, permissions)
            os.chmod(indir, permissions)
        if not os.path.exists(outdir):
            os.makedirs(outdir, permissions)
            os.chmod(outdir, permissions)
        if not os.path.exists(logdir):
            os.makedirs(logdir, permissions)
            os.chmod(logdir, permissions)

    return {"out": outdir, "in": indir, "log": logdir}

def setoutfilenames(ocean, base, cnt=1, outtype="all", addcounter="none"):
    """
    Resets the values of output file name parameters

    This function systematically resets the output file name values using the
    pattern {base}_{prefix}.nc, where prefix is a lowercase version of the 3- or
    4-letter prefix of the various XXXNAME parameters.

    Args:
        ocean:      parameter dictionary
        base:       base name for output files (including path when applicable)
        cnt:        counter to be added, if requested [default=1]
        outtype:    list of output filename prefixes corresponding to those to
                    be modified (e.g., ['AVG', 'HIS']), or one of the following
                    special strings:
                    all:    modify all output types (default)
        addcounter: list of output filename prefixes corresponding to those
                    where a counter index should be added to the name, or one of
                    the following special strings
                    all:    add counter to all output types
                    most:   add counter only to output types that do not have
                            the option of being broken into smaller files on
                            output (i.e. those that do not have an NDEFXXX
                            option)
                    none:   do not add counter to any (default)
    """

    outopt = ['DAI', 'GST', 'RST', 'HIS', 'QCK', 'TLF', 'TLM', 'ADJ', 'AVG',
                'HAR', 'DIA', 'STA', 'FLT', 'AVG2']

    if isinstance(outtype, str):
        if outtype == "all":
            outtype = outopt

    if isinstance(addcounter, str):
        if addcounter == "none":
            addcounter = []
        elif addcounter == "most":
            default_nocount = ['AVG', 'AVG2', 'HIS', 'DIA', 'TLM', 'ADJ']
            addcounter = [x for x in outtype if x not in default_nocount]
        elif addcounter == "all":
            addcounter = outtype

    for fl in outtype:
        if fl in addcounter:
            ocean[fl+'NAME'] = f"{base}_{cnt:02d}_{fl.lower()}.nc"
        else:
            ocean[fl+'NAME'] = f"{base}_{fl.lower()}.nc"


def converttimes(d, direction):
    """
    Converts time-related parameter fields between ROMS format and
    datetimes/timedeltas.  The conversions include

    DSTART:     float, days since initialization <-> datetime, starting
                date and time
    TIME_REF:   float, reference time (yyyymmdd.f) <-> datetime, reference
                date and time
    NTIMES*:    integer, number of time steps in simulation <-> timedelta,
                duration of simulation
    N###:       integer, number of time steps per <-> timedelta, length of time
                per
    NDEF###:    integer, number of time steps per <-> timedelta, length of time
                per
    DT:         integer, number of seconds <-> timedelta, length of time

    Args:

        d:          ROMS parameter dictionary
        direction:  "ROMS" = convert to ROMS standard input units
                    "time" = convert to datetime/timedelta values

    Returns:
        no return argument, input dictionary altered in place
    """

    timeflds = r.timefieldlist(d)
    istime = r.fieldsaretime(d)

    if not istime and direction == "time":
        # Convert from ROMS standard input units to datetimes and timedeltas

        if d['TIME_REF'] in [-1, 0]:
            Exception("360-day and 365.25-day calendars not compatible with this function")
        elif d['TIME_REF'] == -2:
            d['TIME_REF'] = datetime(1968,5,23)
        else:
            yr = math.floor(d['TIME_REF']/10000)
            mn = math.floor((d['TIME_REF']-yr*10000)/100)
            dy = math.floor(d['TIME_REF'] - yr*10000 - mn*100)
            dyfrac = d['TIME_REF'] - yr*10000 - mn*100 - dy
            hr = dyfrac * 24
            mnt = (dyfrac-math.floor(hr))*60
            hr = math.floor(hr)
            sc = math.floor((mnt - math.floor(mnt))*60) # Note: assuming no fractional seconds
            mnt = math.floor(mnt)

            d['TIME_REF'] = datetime(yr,mn,dy,hr,mnt,sc)

        d['DT'] = timedelta(seconds=d['DT'])

        d['DSTART'] = d['TIME_REF'] + timedelta(days=d['DSTART'])

        for fld in timeflds:
            d[fld] = d['DT']*d[fld]

    elif istime and direction == "ROMS":
        # Convert from datetimes and timedeltas to ROMS standard input units
        dfrac = (d['TIME_REF'] - datetime(d['TIME_REF'].year, d['TIME_REF'].month, d['TIME_REF'].day)).total_seconds()/86400.0
        datefloat = float('{year}{month:02d}{day:02d}'.format(year=d['TIME_REF'].year, month=d['TIME_REF'].month, day=d['TIME_REF'].day))

        d['DSTART'] = (d['DSTART'] - d['TIME_REF']).total_seconds()/86400.0

        d['TIME_REF'] = datefloat + dfrac

        for fld in timeflds:
            d[fld] = int(d[fld].total_seconds()/d['DT'].total_seconds())

        d['DT'] = d['DT'].total_seconds()


