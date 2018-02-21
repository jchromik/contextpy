[![Build Status](https://travis-ci.org/jchromik/contextpy.svg?branch=master)](https://travis-ci.org/jchromik/contextpy)
[![Coverage Status](https://coveralls.io/repos/github/jchromik/contextpy/badge.svg?branch=master)](https://coveralls.io/github/jchromik/contextpy)

# ContextPy

This project aims at improving ContextPy by Christian Schubert and Michael Perscheid.
It is based on [ContextPy 1.1](https://pypi.python.org/pypi/ContextPy). 

## Improvements

- [x] Make ContextPy run on Python 3.x
- [x] Lint code to be more pythonic (variable naming, spaces, etc.)
- [ ] In-code documentation (docstrings)
- [x] Address behavioral anomalies: For example, layers can be activated twice using thread-local **and** system-global layer stack. Changes will be listed below.
- [ ] Describe interface of ContextPy in module's `README`
- [x] Test still uncovered lines of code

## Changes over Version 1.1

### Behavioral Changes

- Layer Stack Merging: If a layer is activated in thread-local layer stack (`_TLS.activelayers`) and in system-global layer stack (`_BASELAYERS`), the corresponding partial methods are executed only once. We are merging layer stacks without producing duplicate entries.

### Interface Changes

- Renamed `layer` class to `Layer` (capitalized)
- Renamed `globalActivateLayer` method to `global_activate_layer` (lowercase and with underscore)
- Renamed `globalDecctivateLayer` method to `global_deactivate_layer` (lowercase and with underscore)

These changes were made to comply with [PEP 8](https://www.python.org/dev/peps/pep-0008/).