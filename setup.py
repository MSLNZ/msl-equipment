import os
import re
import sys
from setuptools import setup, find_packages

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), 'docs'))
import docs_commands


def read(filename):
    with open(filename) as fp:
        text = fp.read()
    return text


def fetch_init(key):
    # open the __init__.py file to determine the value instead of importing the package to get the value
    init_text = read('msl/equipment/__init__.py')
    return re.compile(r'{}\s*=\s*(.*)'.format(key)).search(init_text).group(1)[1:-1]


testing = {'test', 'tests', 'pytest'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if testing else []

needs_sphinx = {'doc', 'docs', 'apidoc', 'apidocs', 'build_sphinx'}.intersection(sys.argv)
sphinx = ['sphinx', 'sphinx_rtd_theme'] if needs_sphinx else []


setup(
    name='msl-equipment',
    version=fetch_init('__version__'),
    author=fetch_init('__author__'),
    author_email='joseph.borbely@callaghaninnovation.govt.nz',
    url='https://github.com/MSLNZ/msl-equipment',
    description='Manage and connect to equipment in the laboratory.',
    long_description=read('README.rst'),
    license='MIT',
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    setup_requires=sphinx + pytest_runner,
    tests_require=['pytest-cov', 'pytest'],
    install_requires=read('requirements.txt').splitlines(),
    dependency_links=['https://github.com/MSLNZ/msl-loadlib/tarball/master#egg=msl-loadlib'],
    cmdclass={
        'docs': docs_commands.BuildDocs,
        'apidocs': docs_commands.ApiDocs,
    },
    packages=find_packages(include=('msl*',)),
    include_package_data=True,
)
