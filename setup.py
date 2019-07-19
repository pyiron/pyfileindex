"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='pyfileindex',
    version=versioneer.get_version(),
    description='pyfileindex - pythonic file system index',
    long_description='pyfileindex creates a dynamic file system index inside a pandas DataFrame.',

    url='https://github.com/pyfileindex/pyfileindex',
    author='Jan Janssen',
    author_email='janssen@mpie.de',
    license='BSD',

    classifiers=['Development Status :: 5 - Production/Stable',
                 'Topic :: Scientific/Engineering :: Physics',
                 'License :: OSI Approved :: BSD License',
                 'Intended Audience :: Science/Research',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7'],

    keywords='pyfileindex',
    packages=find_packages(exclude=["*tests*", "*binder*", "*notebooks*"]),
    install_requires=['pandas', 'scandir'],
    data_files=[("", ["LICENSE"])],
    cmdclass=versioneer.get_cmdclass(),
    )
