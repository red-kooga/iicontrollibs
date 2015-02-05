#!/usr/bin/env python

import os, sys, inspect

top_folder = os.path.split(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))[0]
if top_folder not in sys.path:
    sys.path.insert(0, top_folder)

import unittest
import importlib


def runalltests():
    unittest.main()


class TestFunction(unittest.TestCase):
    def systemstatus(self):
        import systemstatus
        systemstatus.runsystemstatus(True)
        self.assertTrue(True)

    def updateio(self):
        from updateio import updateiodata
        from pilib import controldatabase
        updateiodata(controldatabase)

    def netconfig(self):
        import netconfig
        netconfig.runconfig(True)


class TestImport(unittest.TestCase):
    def test(self):
        importsuccess = False
        try:
            # Import module by name
            importlib.import_module(self.modulename)
        except:
            pass
        else:
            importsuccess=True
        self.assertTrue(importsuccess)


class ImportTester(TestImport):
    def __init__(self, methodname, modulename):
        # Call init to add parameters without overriding
        TestImport.__init__(self, methodname)
        self.modulename = modulename


def testmodule(modulename):
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(ImportTester(methodname='test', modulename=modulename))
    stringfailures=[]
    for failure in result.failures:
        stringfailures.append(str(failure))
    resultdict = {'module':modulename, 'testsrun':result.testsRun, 'errors':result.errors, 'failuremessages': 'blurg', 'failurecount': len(result.failures)}
    return resultdict


def testfunction(functionname):
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(TestFunction('systemstatus'))
    stringfailures=[]
    for failure in result.failures:
        stringfailures.append(str(failure))
    # resultdict = {'module':functionname, 'testsrun':result.testsRun, 'errors':str(result.errors[0]), 'failuremessages': stringfailures, 'failurecount': len(result.failures)}
    # resultdict = {'module':functionname, 'testsrun':result.testsRun, 'errors':str('blurg'), 'failuremessages': stringfailures, 'failurecount': len(result.failures)}
    resultdict={'blurg':'blurg'}
    # print(type(result.errors))
    # print(result.errors[0])
    # print(result.errors[0][0])
    import json
    print(json.dumps(resultdict))
    return resultdict


def testmodules(modulenames):
    resultdictarray=[]
    for modulename in modulenames:
        resultdictarray.append(testmodule(modulename))

    return resultdictarray


if __name__ == "__main__":

    # modules = ['cupid.pilib', 'cupid.picontrol', 'cupid.controllib', 'cupid.netconfig', 'cupid.netfun', 'cupid.owfslib', 'cupid.processactions', 'cupid.sessioncontrol', 'cupid.systemstatus', 'cupid.cupiddaemon']
    modules = ['cupid.pilib', 'cupid.picontrol']
    results = testmodules(modules)
    testfunction('systemstatus')
