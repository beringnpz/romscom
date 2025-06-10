# About

## Motivation

A ROMS application typically includes a number of different [text files](https://www.myroms.org/wiki/Input_Parameter_Files) that are used to set the input parameters for its various components, including the main physical ocean parameters as well as any biology, sediment, ice, etc. parameters that may be active.  These input files, usually marked with a .in extension, use ROMS' Fortran-like custom namelist format; the format is easily human-readable and can be edited with any text editor, but is difficult to parse or edit programmatically (except by ROMS' non-standalone parser).  

In a research context, I was frustrated with this format for a few reasons:

- Our workflows often involved running many variations on a base simulation, resulting in a plethora of different input files that needed to be manually edited and tracked.  In practice, it was easy to loose track of when parameters had been changed and by who and why.
- Our simulations were often run on computer clusters where jobs could be unpredictably cancelled and resubmitted for various queue management reasons.  Restarting ROMS simulations requires certain edits to the inputs to ensure the simulation picks up where it left off.  Manually editing the input files is not compatible with automatic resubmission.

## What it is

This toolbox is designed to address the above problems.  It's based on the idea of storing the parameters in a more flexible file format (YAML) that can be read into python dictionaries for easy manipulation.

The YAML files mimic the original ROMS standard input format, with key/value pairs for each ROMS input parameter. This format is easy to read by a human (especially with a text editor with YAML syntax highlighting), and allows for the same amount of ample commenting as in the traditional input files.  In addition, these YAML files offer an advantage over the traditional standard input in that they can be (easily) read by high-level computing languages (like python) and then manipulated programmatically.

With this YAML/dictionary idea at its base, the toolbox then adds tools to maniplate ROMS I/O in order to prepare, run, and check in on simulations.  In particular, it offers tools to:

- Convert between YAML files, python dictionaries, and traditional ROMS standard input format
- Manipulate time-related variables using dates and timedeltas, allowing more intuitive modification of ROMS start date, time step, archiving options, etc.
- Examine existing output files to restart a simulation that was paused or crashed
- Run ROMS past periods of numeric instability (leading to blow-ups) by temporarily reducing the model time step 


## What it is not

This toolbox is not ROMS!  A quick quote from the [ROMS GitHub](https://github.com/myroms/roms):

    The ROMS framework is intended for users interested in ocean modeling. It requires an extensive background in ocean dynamics, numerical modeling, and computers to configure, run, and analyze the results to ensure you get the correct solution for your application. Therefore, we highly recommend users register at https://www.myroms.org and set up a username and password to access the ROMS forum, email notifications for bugs/updates, technical support from the community, trac code maintenance history, tutorials, workshops, and publications. The user's ROMS forum has over 24,000 posts with helpful information. Technical support is limited to registered users. We do not provide user technical support, usage, or answers in GitHub.

ROMS is not the easiest tool to get started with.  Even a simple implementation requires the user to run their own builds of the source code, including locating the required libraries, compilers, etc.  There are hundreds of spinoffs of the code maintained by various research groups, in various states of development, use, and disrepair.  The romscom toolbox *should* work with most of these versions, and can help make the process of designing and running experiments a little smoother, and help keep your ROMS application folders a little neater.  But the process of building and configuring a new model domain or application is yours to conquer on your own!

This toolbox also does *not* focus on building netCDF input files for ROMS simulations.  There are existing tools out there for that (e.g., [myroms.org pre- and post-processing tools](https://myroms.org/index.php?page=RomsPackages), [pyroms](https://github.com/ESMG/pyroms)).  These are, as pyroms puts it, a little rough around the edges (at best), but creating a more robust option is well outside the scope of this little toolbox.  