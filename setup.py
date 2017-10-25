import re
import sys
from distutils.cmd import Command
from setuptools import setup, find_packages


class ApiDocs(Command):
    """
    A custom command that calls sphinx-apidoc
    see: http://www.sphinx-doc.org/en/latest/man/sphinx-apidoc.html
    """
    description = 'builds the api documentation using sphinx-apidoc'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sphinx.apidoc import main
        main([
            'sphinx-apidoc',
            '--force',  # overwrite existing files
            '--module-first',  # put module documentation before submodule documentation
            '--separate',  # put documentation for each module on its own page
            '-o', './docs/_autosummary',  # where to save the output files
            'msl',
        ])
        sys.exit(0)


class BuildDocs(Command):
    """
    A custom command that calls sphinx-build
    see: http://www.sphinx-doc.org/en/latest/man/sphinx-build.html
    """
    description = 'builds the documentation using sphinx-build'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from sphinx import build_main
        build_main([
            'sphinx-build',
            '-b', 'html',  # the builder to use, e.g., create a HTML version of the documentation
            '-a',  # generate output for all files
            '-E',  # ignore cached files, forces to re-read all source files from disk
            'docs',  # the source directory where the documentation files are located
            './docs/_build/html',  # where to save the output files
        ])
        sys.exit(0)


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
    author_email='joseph.borbely@measurement.govt.nz',
    url='https://github.com/MSLNZ/msl-equipment',
    description='Manage and communicate with equipment in the laboratory.',
    long_description=read('README.rst'),
    platforms='any',
    license='MIT',
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
    install_requires=[
        'enum34;python_version<"3.4"',
        'xlrd',
        'pyvisa>=1.6',
        'numpy',
        'msl-loadlib',
        'pyserial>=3.0',
        'python-dateutil',
    ],
    cmdclass={'docs': BuildDocs, 'apidocs': ApiDocs},
    packages=find_packages(include=('msl*',)),
    include_package_data=True,
)
