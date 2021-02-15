# ABGDpy

Primary species delimitation using automatic barcode gap discovery.

This is a Python wrapper for ABGD: <https://bioinfo.mnhn.fr/abi/public/abgd/>

*(you will need a C compiler when building from source)*

## Quick start

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

## Launch without installing

Before the first time you use the program, you must install any required modules, build the ABGD core and auto-compile the Qt resource files:
```
$ pip install -r requirements.txt
$ python setup.py build_ext --inplace
$ python setup.py build_qt
```

You can now launch the GUI:
```
$ python launcher.py
```

## Packaging

You must first compile the ABGD C module, auto-compile Qt resources,
then use PyInstaller on the launcher **spec** file:
```
$ pip install pyinstaller
$ python setup.py build_ext --inplace
$ python setup.py build_qt
$ pyinstaller launcher.spec
```

## Module

You may import and use the ABGD module in your python scripts.

To launch the GUI:
```
>>> import abgdpy.qt
>>> abgdpy.qt.main.show()
```

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

N Puillandre, A Lambert, S Brouillet and G Achaz ABGD,\
[Automatic Barcode Gap Discovery for primary species delimitation][paper],\
Mol Ecol. 2011.

- Original C code by G. Achaz
- Code update by Sophie Brouillet
- BIONJ by Olivier Gascuel

[paper]: https://pubmed.ncbi.nlm.nih.gov/21883587/
