
/*

Extension Module for ABGD

Consider using multi-phase extension module initialization instead:
https://www.python.org/dev/peps/pep-0489/

*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include "abgd.h"

/*
\t-m    : if present the distance Matrix is supposed to be MEGA CVS (other formats are guessed)\n\
\t-a    : output all partitions and tree files (default only graph files)\n\
\t-s    : output all partitions in 's'imple results txt files\n\
\t-p #  : minimal a priori value (default is 0.001) -Pmin-\n\
\t-P #  : maximal a priori value (default is 0.1) -Pmax-\n\
\t-n #  : number of steps in [Pmin,Pmax] (default is 10)\n\
\t-b #	: number of bids for graphic histogram of distances (default is 20\n\
\t-d #  : distance (0: Kimura-2P, 1: Jukes-Cantor --default--, 2: Tamura-Nei 3:simple distance)\n\
\t-o #  : existent directory where results files are written (default is .)\n\
\t-X #  : mininmum Slope Increase (default is 1.5)\n\
\t-t #  : transition/transversion (for Kimura) default:2\n");
*/

static PyObject *
abgd_main(PyObject *self, PyObject *args)
{
    PyObject *dict;
    PyObject *file;

    // Accept a dictionary-like python object
    if (!PyArg_ParseTuple(args, "O", &dict))
      return NULL;
    if (!PyDict_Check(dict)) {
      PyErr_SetString(PyExc_TypeError, "Not a dictionary");
      return NULL;
    }
    file = PyDict_GetItemString(dict, "file");
    if (file == NULL) {
      PyErr_SetString(PyExc_KeyError, "Key not found: file");
      return NULL;
    }

    PyObject* str = PyUnicode_AsEncodedString(file, "utf-8", "~E~");
    if (str == NULL) return NULL;
    const char *bytes = PyBytes_AS_STRING(str);
    printf("File = %s\n", bytes);
    Py_XDECREF(str);

    //return PyLong_FromLong(sts);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
abgd_foo(PyObject *self, PyObject *args)
{
    long num, res;

    if (!PyArg_ParseTuple(args, "l", &num))
        return NULL;
    res = foo(num);
    return PyLong_FromLong(res);
}

static PyMethodDef AbgdMethods[] = {
    {"main",  abgd_main, METH_VARARGS,
     "Execute a shell command."},
    {"foo",  abgd_foo, METH_VARARGS,
    "Add 42."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyDoc_STRVAR(abgd_doc,
"This is a template module just for instruction.");

static struct PyModuleDef abgdmodule = {
    PyModuleDef_HEAD_INIT,
    "abgd",   /* name of module */
    abgd_doc, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    AbgdMethods
};

PyMODINIT_FUNC
PyInit__abgdc(void)
{
    return PyModule_Create(&abgdmodule);
}
