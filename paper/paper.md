---
title: 'The ROMS Communication Toolbox (romscom): input parameter utilities for the Regional Ocean Modeling System (ROMS)'
tags:
  - Python
  - oceanography
  - regional ocean model
  - ROMS
authors:
  - name: Kelly Kearney
    orcid: 0000-0002-6152-5236
    equal-contrib: true
    affiliation: 1 # (Multiple affiliations must be quoted)
affiliations:
 - name: NOAA NMFS Alaska Fisheries Science Center, Seattle, WA, USA
   index: 1
date: 27 June 2025
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
# aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
# aas-journal: Astrophysical Journal <- The name of the AAS journal.
---

# Summary

The Regional Ocean Modeling System (ROMS) is a primitive equations hydrodynamic model that is widely used in the field of oceanography [@Shchepetkin2005].  It is characterized by a split-explicit time stepping scheme, free surface, and terrain-following vertical coordinate system, all of which make it well suited to exploring ocean dynamics at regional scales [@Haidvogel2008].  The model has been in use for nearly three decades, and its community approach, open-source code base, and extensive suite of numerical algorithms have led to a proliferation of applications.

A specific implementation of ROMS requires of number of different parts: the core source code (.F Fortran files),  configuration files (.h header files) to selectively compile the appropriate options for a given application, parameter input files (.in plain text files) to set the values of parameters, and (if applicable) larger input datasets (.nc netCDF files) for gridded input such as surface and lateral boundary conditions of the simulation.  Managing and tracking these many different parts can be challenging, particularly when running complex sensitivity experiments or ensemble experiments.  This is particularly true with respect to the plain text parameter input files.  These files use a custom format, described in the documentation as having "similar functionality as Fortran input namelist but with additional capabilities."  These inputs can be read by ROMS's own parsing routine (inp_par.F), but do not use a format easily accessible to the high-level programming languages commonly used to manage a scientific workflow.  In a typical ROMS workflow, they are created and edited manually via a text editor.  In complex experiments, this can lead to a proliferation of files representing various stages of the experiment -- e.g., an original set of parameters, some changes that are meant to be permanent and carried forward for all subsequent runs, and other changes that were sensitivity tests but are no longer needed -- or files that are constantly modified and overwritten.

# Statement of need

The ROMS Communication Toolbox is a set of python utilities that facilitate the workflow management of one or more ROMS simulations.  The majority of the tools focus on programatic manipulation of the ROMS parameter input files.  In particular, the utilities allow one to:

- manage ROMS input parameters using the versatile YAML format, with options to import and export between YAML files and python dictionaries, and to export from python dictionaries to the traditional ROMS standard input format;
- manipulate time-related variables using dates and timedeltas, allowing more intuitive modification of ROMS start date, time step, archiving options, etc.; and
- automatically submit simulations for calculation, and resume simulations that were paused or crashed by analyzing existing restart and history output and then appropriately adjusting time step parameters and re-calling the ROMS executable; options are available to work past periods of numeric instability (leading to blow-ups) by temporarily reducing the model time step. 

This combination of tools allows one to manage and document complex regional modeling experiments using a single python script.  This supports transparency in the ROMS modeling process, and addresses the need for reproducible workflows covering the entirety of the regional modeling process [@polton_reproducible_2023].


<!-- `Gala` is an Astropy-affiliated Python package for galactic dynamics. Python
enables wrapping low-level languages (e.g., C) for speed without losing
flexibility or ease-of-use in the user-interface. The API for `Gala` was
designed to provide a class-based and user-friendly interface to fast (C or
Cython-optimized) implementations of common operations such as gravitational
potential and force evaluation, orbit integration, dynamical transformations,
and chaos indicators for nonlinear dynamics. `Gala` also relies heavily on and
interfaces well with the implementations of physical units and astronomical
coordinate systems in the `Astropy` package [@astropy] (`astropy.units` and
`astropy.coordinates`).

`Gala` was designed to be used by both astronomical researchers and by
students in courses on gravitational dynamics or astronomy. It has already been
used in a number of scientific publications [@Pearson:2017] and has also been
used in graduate courses on Galactic dynamics to, e.g., provide interactive
visualizations of textbook material [@Binney:2008]. The combination of speed,
design, and support for Astropy functionality in `Gala` will enable exciting
scientific explorations of forthcoming data releases from the *Gaia* mission
[@gaia] by students and experts alike. -->

<!-- # Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text. -->

<!-- # Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% } -->

# Acknowledgements

Thank you to my research colleagues and collaborators who tested this code over its progressive development: Al Hermann, Wei Cheng, Ivonne Ortiz, Darren Pilcher, and Kerim Aydin.

# Note for NOAA internal review

This paper is to be submitted to the [Journal of Open Source Software](https://joss.theoj.org/).  Peer review for this journal focuses on review of the source code and documentation of scientific software itself (rather than of a companion paper).  Links for the relevant components are as follows:

- Source code: https://github.com/beringnpz
- Documentation: https://beringnpz.github.io/romscom/

This section will be removed upon submission to JOSS, when these links will be incorporated into the final rendered document.

# References
