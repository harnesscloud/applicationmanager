from distutils.core import setup, Extension
import os 
module1 = Extension('neuralnetwork', sources = ['neuralnetwork.c'], libraries = ['fann'])
 
setup (name = 'PackageName',
        version = '1.0',
        description = 'This is a demo package',
        ext_modules = [module1])


os.rename("build/lib.linux-x86_64-2.7/neuralnetwork.so", "./neuralnetwork.so")
os.system("rm -r build")


