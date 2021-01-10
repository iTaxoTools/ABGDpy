
/*

Extension Module for ABGD

Consider using multi-phase extension module initialization instead:
https://www.python.org/dev/peps/pep-0489/

*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include "abgd.h"

static PyObject *
abgd_system(PyObject *self, PyObject *args)
{
    const char *command;
    int sts;

    if (!PyArg_ParseTuple(args, "s", &command))
        return NULL;
    sts = system(command);
    return PyLong_FromLong(sts);
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
    {"system",  abgd_system, METH_VARARGS,
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
