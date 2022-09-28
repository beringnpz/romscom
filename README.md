# romscom: ROMS Communication Toolbox

This python toolbox provides tools to communicate with the Regional Ocean Modeling System (ROMS) model.  The primary goal of this toolbox is to allow ROMS simulations to be run programmatically, simplifying tasks such as resetting time variables to extend or restart simulations, running parameter sensitivity studies, or running large ensembles.

## The concept

I've paired YAML-formatted input files with python-based utilities to manipulate values.

The YAML files mimic the original ROMS standard input format, with key/value pairs for each ROMS input parameter. This format is easy to read by a human (especially with a text editor with YAML syntax highlighting), and allows for the same amount of ample commenting as in the traditional input files.  For each ROMS application, I recommend creating one master set of YAML files, corresponding to the roms.in (ocean.in) standard input as well as any additional input ASCII paramters files (e.g., .in files); currently, this includes the APARNAM (assimilation), SPOSNAME (stations), FPOSNAM (drifter positions), SPARNAM (sediment), and BPARNAM (biology) parameter files.

These YAML files offer an advantage over the traditional standard input in that they can be (easily) read by high-level computing languages (like python) and then manipulated programmatically.

With this YAML/dictionary idea at its base, the toolbox then adds tools to maniplate ROMS I/O in order to prepare, run, and check in on simulations.

Note that this toolbox does *not* focus on building netCDF input files for ROMS simulations.  There are existing tools out there for that (e.g., [myroms.org pre- and post-processing tools](https://myroms.org/index.php?page=RomsPackages), [pyroms](https://github.com/ESMG/pyroms)); the focus here is on running simulations once the primary input is in place.

## Package functions

## To build

To rebuild in development mode:

`python setup.py develop`

(or, if you want/need to write to a user-specific location rather than the system default location)

`python setup.py develop --user`

To rebuild in final mode:

`python setup.py install [--user]`

