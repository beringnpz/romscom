# romscom: ROMS Communication Toolbox

This python toolbox provides tools to communicate with the Regional Ocean Modeling System (ROMS) model.  The primary goal of this toolbox is to allow ROMS simulations to be run programmatically, simplifying tasks such as resetting time variables to extend or restart simulations, running parameter sensitivity studies, or running large ensembles.

## The concept

I've paired YAML-formatted input files with python-based utilities to manipulate values.

The YAML files mimic the original ROMS standard input format, with key/value pairs for each ROMS input parameter. This format is easy to read by a human (especially with a text editor with YAML syntax highlighting), and allows for the same amount of ample commenting as in the traditional input files.  For each ROMS application, I recommend creating one master set of YAML files, corresponding to the roms.in (ocean.in) standard input as well as any additional input ASCII parameters files (e.g., .in files); currently, this includes the APARNAM (assimilation), SPOSNAME (stations), FPOSNAM (drifter positions), SPARNAM (sediment), and BPARNAM (biology) parameter files.

These YAML files offer an advantage over the traditional standard input in that they can be (easily) read by high-level computing languages (like python) and then manipulated programmatically.

With this YAML/dictionary idea at its base, the toolbox then adds tools to maniplate ROMS I/O in order to prepare, run, and check in on simulations.  In particular, it offers tools to:

- Convert between YAML files, python dictionaries, and traditional ROMS standard input format
- Manipulate time-related variables using dates and timedeltas, allowing more intuitive modification of ROMS start date, time step, archiving options, etc.
- Examine existing output files to restart a simulation that was paused or crashed
- Runs ROMS past periods of instability (leading to blow-ups) by temporarily reducing the model time step 

Note that this toolbox does *not* focus on building netCDF input files for ROMS simulations.  There are existing tools out there for that (e.g., [myroms.org pre- and post-processing tools](https://myroms.org/index.php?page=RomsPackages), [pyroms](https://github.com/ESMG/pyroms)); the focus here is on running simulations once the primary input is in place.

## Package functions

Once installed (see below), the primary and accessory functions from this package can be accessed via:

```python
import romscom.romscom
import romscom.rcutils
```

Functions within the romscom submodule provide the primary tools:

- **converttimes**: Converts time-related parameter fields between ROMS format and datetimes/timedeltas.
- **dict2standardin**: Converts a parameter dictionary to standard input text, and optionally writes to file
- **readparamfile**: Reads parameter YAML file into an ordered dictionary
- **runtodate**: Sets up I/O and runs ROMS simulation through indicated date, with options to restart and work past blowups
- **setoutfilenames**: Resets the values of output file name parameters in a dictionary to use a systematic naming scheme
- **simfolders**: Generate folder path names for the 3 I/O folders used by runtodate
- **stringifyvalues**: Formats all dictionary values to ROMS standard input syntax strings

The rcutils submodule provides several additional utility functions that are used by the functions above.  While users are less likely to need to call these directly, they may be useful occasionally:

- **bool2str**: Formats input boolean as string 'T' or 'F'
- **fieldsaretime**: True if all time-related fields in parameter dictionary are in datetime/timedelta format
- **flatten**: flatten nested list
- **float2str**: Formats input float as Fortran-style double-precision string
- **formatkeyvalue**: Formats key/value pair as ROMS parameter assignment statement
- **inputfilesexist**: Check if input files in parameter dictionary exist
- **list2str**: Convert list of bools, floats, or integers to string
- **multifile2str**: Convert a multifile list of filenames (with possible nesting) to string
- **ordered_load**: Load YAML file as OrderedDict
- **parseromslog**: Parse ROMS standard output log for details of simulation success or failure
- **parserst**: Parse restart counters from ROMS simulation restart files
- **timefieldlist**: Get list of time-related dictionary keys

Full function help, including syntax descriptions, can be accessed via the help command:

```python
help(romscom.romscom) # All primary functions
help(romscom.rcutils) # All utility functions
help(romscom.romscom.runtodate) # Single function
```

## To build

Stable releases for this toolbox will become available once testing is further along.  Until then, I recommend building locally in develop mode. Develop mode allows new changes to the source code to be immediately seen by any code importing this package, without the need rebuild. Clone or copy this repository, and then run the following command from within the cloned/copied folder:

`python setup.py develop`

(or, if you want/need to write to a user-specific location rather than the system default location)

`python setup.py develop --user`

To rebuild in final mode rather than develop mode:

`python setup.py install [--user]`

