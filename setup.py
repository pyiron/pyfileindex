"""
Setuptools based setup module
"""
from setuptools import setup, find_packages
import versioneer

setup(
    name='fileindex',
    version=versioneer.get_version(),
    description='fileindex - dynamic file system index',
    long_description='File index.',

    url='https://github.com/pysqa/pysqa',
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

    keywords='pysqa',
    packages=find_packages(exclude=["*tests*"]),
    install_requires=['pandas'],
    data_files=[("", ["LICENSE"])],
    cmdclass=versioneer.get_cmdclass(),
    )
