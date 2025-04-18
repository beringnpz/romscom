## Installation

The toolbox can be installed into your environment of choice from PyPI:

```
pip install romscom
```

or conda-forge:

``` 
conda install -c conda-forge romscom 
```


## Loading the modules

Once installed, the primary and accessory functions from this package can be accessed via:

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

This same documentation is also available on this website through the References pages for the [romscom module](reference_romscom.md) and [rcutils module](reference_rcutils.md).

## Preparing your ROMS application

Most users will come to this toolbox with an existing ROMS application.  To use this toolbox, you will first need to translate any existing .in files to YAML format.  For each ROMS application, I recommend creating one master set of YAML files, corresponding to the roms.in (ocean.in) standard input as well as any additional input ASCII parameters files (e.g., .in files) that are applicable to your setup; currently, this includes the APARNAM (assimilation), SPOSNAME (stations), FPOSNAM (drifter positions), SPARNAM (sediment), and BPARNAM (biology) parameter files.

The following instructions for formatting your YAML input files is also replicated in the header of the example files, similar to the instructions in the default .in files.

### YAML format for ROMS

The YAML ROMS input format mimics that of ROMS standard input (e.g., roms.in) files, but using a more flexible format that is both human-readable and more easily machine-parsable than the standard input format.  

These files are intended to be used with the ROMS Communication (romscom) toolbox.

Input parameters can be entered in (almost) any order (but there are a few exceptions, like the tiling parameters, so I suggest maintaining the original order.)  Comments are preceded by a # sign and are ignored on reading. Most values follow standard YAML format.  Parameters should be entered as dictionary entries, with the parameter name as key.  Note that unlike ROMS standard input, indentation is important in the YAML format, and all parameter keywords should be left-justified.

Integers are distinguished from floating point numbers by the presence or absence of decimal points (e.g., 1 = integer, 1.0 = float).
 
Lists of parameters should be entered for keywords that expect multiple values.  These can either be entered across multiple lines: 

```yaml
AKT_BAK:
  - 1.0e-6
  - 1.0e-6
  - 5.0e-6
  - 5.0e-6
```
or as "flow collections" on a single line:

```yaml
AKT_BAK: [1.0e-6, 1.0e-6, 5.0e-6, 5.0e-6]
```

or across multiple lines:

```yaml
AKT_BAK: [1.0e-6, 1.0e-6,
          5.0e-6, 5.0e-6]
```
  
The above three examples will all be interpreted identically.

NetCDF filename parameters can accept "multiple filenames", where a single input dataset is split across several files.  These are marked by vertical bar separators (|) in the ROMS standard input.  In the YAML format, these should be entered as nested arrays, e.g,:

```yaml
NFFILES: 6
FRCNAME: 
   - [my_lwrad_year1.nc, my_lwrad_year2.nc]
   - [my_swrad_year1.nc, my_swrad_year2.nc]
   - [my_winds_year1.nc, 
      my_winds_year2.nc]
   - [my_Pair_year1.nc, 
      my_Pair_year2.nc]
   - - my_Qair_year1.nc
     - my_Qair_year2.nc
   - - my_Tair_year1.nc
     - my_Tair_year2.nc
```

Again, all list syntaxes are valid, and may be used interchangeably as demonstrated here.

Parameters with nested indices (e.g. `Hout(idUvel)`, `Hout(idVvel)`) are represented as dictionaries, with the nested indices as keys, e.g.:

```yaml
Hout:
  idUvel: TRUE       # u                  3D U-velocity
  idVvel: TRUE       # v                  3D V-velocity
```

### The `no_plural` key

In multiple levels of nesting or multiple connected domains step-ups, `Ngrids` entries are expected for some of these parameters. In such case, the order of the entries for a parameter is critical. It must follow the same order (1:Ngrids) as in the state variable declaration.  In the ROMS standard input format, these values are marked by a `==` plural after the KEYWORD instead of a `=`.  

This is the one aspect of the ROMS standard input format for which I couldn't find an elegant counterpart in the YAML format.  Instead, each file starts with an additinal special `no_plural` key that lists the keywords in the rest of the file that are **not** grid-specific, i.e. that would use the `=` assignment (rather than `==`) in a standard .in file.

The majority of these types of parameters are those related to file I/O, and are found in the primary standard input files.  This is a bit of a moving target, since parameters may be added or removed with each new release of ROMS.  I specifically chose to make this part of the input files rather than the toolbox itself to avoid tying the functionality too closely to any specific version of ROMS. At the time of this writing (latest release: ROMS 4.2), the values for these across file types is as follows:

Standard input (ocean.in):

```yaml
no_plural: [TITLE, MyAppCPP, VARNAME, Ngrids, NestLayers, GridsInLayer, 
            Nbed, NAT, NPT, NCS, NNS, 
            ERstr, ERend, Nouter, Ninner, Nsaddle, Nintervals, 
            NEV, NCV
            LmultiGST, LrstGST, MaxIterGST, NGST, 
            Ritz_tol
            RHO0, BVF_BAK, Lmodel,
            DSTART, TIDE_START, TIME_REF, 
            NSLICE, Z_SLICE, NUSER, USER,
            INP_LIB, OUT_LIB, 
            PIO_METHOD, PIO_IOTASKS, PIO_STRIDE, PIO_BASE, PIO_AGGREG, 
            PIO_REAR, PIO_REARRCOM, PIO_REARRDIR, PIO_C2I_HS, PIO_C2I_Send,
            PIO_C2I_Preq, PIO_I2C_HS, PIO_I2C_Send, PIO_I2C_Preq,  
            NC_SHUFFLE, NC_DEFLATE, NC_DLEVEL]
```
APARNAM (assimilation) parameter file:

```yaml
no_plural: [LNM_flag, balance, Nvct, GradErr, HevecErr, LhessianEV, LhotStart,
            Lprecond, Lritz, NritzEV, NpostI, Nimpact, OuterLoop, Phases4DVAR,
            NextraObs, ExtraIndex, ExtraName, CnormM, CnormI, CnormB, CnormF,
            Nrandom, Hgamma, Vgamma]
```

SPOSNAME (stations) parameter file:

```yaml
no_plural: [POS]
```

FPOSNAM (drifter positions) parameter file

```yaml
no_plural: [POS]
```

SPARNAM (sediment) parameter file

```yaml
no_plural: []
```

BPARNAM (biology) parameter file:

```yaml
no_plural: []
```
(Note: depends on the biology module in question, but most do not include any exceptions)