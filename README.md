# romscom: ROMS Communication Toolbox

This python toolbox provides tools to communicate with the Regional Ocean Modeling System (ROMS) model.  The primary goal of this toolbox is to allow ROMS simulations to be run programmatically, simplifying tasks such as resetting time variables to extend or restart simulations, running parameter sensitivity studies, running large ensembles, or documenting a ROMS workflow.

## The concept

I've paired YAML-formatted input files with python-based utilities to manipulate values.

The YAML files mimic the original ROMS standard input format, with key/value pairs for each ROMS input parameter. This format is easy to read by a human (especially with a text editor with YAML syntax highlighting), and allows for the same amount of ample commenting as in the traditional input files.  These YAML files offer an advantage over the traditional standard input in that they can be (easily) read by high-level computing languages (like python) and then manipulated programmatically.

With this YAML/dictionary idea at its base, the toolbox then adds tools to maniplate ROMS I/O in order to prepare, run, and check in on simulations.  In particular, it offers tools to:

- Convert between YAML files, python dictionaries, and traditional ROMS standard input format
- Manipulate time-related variables using dates and timedeltas, allowing more intuitive modification of ROMS start date, time step, archiving options, etc.
- Examine existing output files to restart a simulation that was paused or crashed
- Runs ROMS past periods of instability (leading to blow-ups) by temporarily reducing the model time step 

See the included [documentation](https://beringnpz.github.io/romscom/) for a more detailed description, examples of usage, and function syntax and documentation.

## Installation and use

The toolbox can be installed into your environment of choice from PyPI:

```
pip install romscom
```

(Option to install via conda from conda-forge coming soon!)

<!-- or conda-forge:

``` 
conda install -c conda-forge romscom 
``` -->

Once installed, the primary and accessory functions from this package can be accessed in python via:

```python
import romscom.romscom
import romscom.rcutils
```

Full function help, including syntax descriptions, can be accessed via the help command:

```python
help(romscom.romscom) # All primary functions
help(romscom.rcutils) # All utility functions
help(romscom.romscom.runtodate) # Single function
```

This same documentation can also be viewed on the [documentation website](https://beringnpz.github.io/romscom/) References pages.
