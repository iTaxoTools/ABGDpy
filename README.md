# ABGDpy

Primary species delimitation using automatic barcode gap discovery.

This is a Python wrapper for ABGD: <https://bioinfo.mnhn.fr/abi/public/abgd/>


## Quick start

### To launch the GUI without installing:

Before the first time you use the program, you must build the ABGD module:
```
$ python setup.py build_ext --inplace
```
*(you will need a C compiler)*

Launch the GUI:
```
$ python launcher.py
```

You may need to install the required libraries first:
```
$ pip install -r requirements.txt
```

## Installation

Install using pip:

```
$ pip install .
```

Run the GUI:

```
$ abgdpy-qt
```

Simple command line tool:

```
$ abgdpy tests/test.fas
```

## Packaging

You must first compile the ABGD module,
then use PyInstaller on the launcher **spec** file:
```
$ python setup.py build_ext --inplace
$ pyinstaller launcher.spec
```

## Module

You may import and use the ABGD module in your python scripts.
More examples to follow soon.

### Python interactive example

From the root directory, launch the Python interpreter:
```
$ python -i
```

Initialize an analysis on your file:
```
>>> a = abgd.BarcodeAnalysis('tests/test.fas')
```

Browse and change parameters:
```
>>> a.param.keys()
>>> a.param.general.keys()
>>> a.param.general.all = True
```

Run the analysis:
```
>>> abgd.launch(a)
```

You can find the results inside the folder `a.results`.
Save them in a new directory:
```
>>> print(a.results)
>>> a.fetch('./my_results')
```

## Acknowledgements

N Puillandre, A Lambert, S Brouillet and G Achaz ABGD, [Automatic Barcode Gap Discovery for primary species delimitation][paper], Mol Ecol. 2011.


- Original C code by G. Achaz
- Code update by Sophie Brouillet
- BIONJ by Olivier Gascuel

[paper]: https://pubmed.ncbi.nlm.nih.gov/21883587/
