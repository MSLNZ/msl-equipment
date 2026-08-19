# Web Application

The web application runs a server on a computer which allows people to interact with equipment registers via a web browser from any computer that is on the same network. The computer that runs the server must have access to the equipment registers of each team. That access could either be through a shared network drive or by cloning a repository.

The web application has pages for viewing equipment that

* is a capital expenditure,
* requires maintenance or recalibration,
* matches a specified search pattern,

and it can generate PDF/A documents.

The web application also provides an Application Programming Interface (API) that can be invoked through custom software (via the HTTP methods GET and POST) to extract information from equipment registers or to generate a PDF/A document.

## Install {: #webapp-install }

<!--
`msl-equipment-webapp` is available on [PyPI](https://pypi.org/project/msl-equipment-webapp/) and can be installed with a variety of Python package managers.

=== "pip"
    ```console
    pip install msl-equipment-webapp
    ```

=== "pipx"
    ```console
    pipx install msl-equipment-webapp
    ```

=== "uv"
    ```console
    uv tool install msl-equipment-webapp
    ```
-->

`msl-equipment-webapp` is currently only available for installation from source. It can be installed using a variety of package managers.

=== "pip"
    ```console
     pip install msl-equipment-webapp@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/webapp
    ```

=== "pipx"
    ```console
    pipx install msl-equipment-webapp@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/webapp
    ```

=== "uv"
    ```console
    uv tool install msl-equipment-webapp@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/webapp
    ```

This will install a command-line tool to run the web application.

### Dependencies {: #webapp-dependencies }

The Python packages that are required to run the web application are automatically installed, but there are non-Python dependencies that must also be installed on the computer running the server.

The web application provides the option to convert $\LaTeX$ and Microsoft Word documents to the PDF/A format and the option to sync equipment registers that are cloned from a repository. As such, the following additional executables should be available on the computer running the web application (if necessary).

* [git](https://git-scm.com/) &mdash; For syncing an equipment register with its repository.

=== "Windows"
    ```console
    winget install --id Git.Git
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install git
    ```

* [java](https://www.java.com/en/) &mdash; Required to run the `veraPDF` tool.

=== "Windows"
    ```console
    winget install --id Oracle.JDK.26
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install default-jre
    ```

* [veraPDF](https://verapdf.org/software/) &mdash; For validating PDF/A documents. See [here](https://docs.verapdf.org/install/) for install instructions.

* [Microsoft 365](https://www.microsoft.com/en/microsoft-365/microsoft-office) &mdash; To convert Microsoft Word documents to PDF/A.

* `pdflatex` &mdash; To convert $\LaTeX$ documents to PDF/A.

=== "Windows"
    ```console
    winget install --id MiKTeX.MiKTeX
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install texlive-latex-base
    ```

## Usage {: #webapp-usage }

Typical usage involves passing the path to a [configuration file][webapp-configuration] as an argument to the executable.

```console
msl-equipment-webapp path/to/config.json
```

There are a few command-line options that can override values defined in the configuration file. Run the `--help` command to see what options are supported.

```console
msl-equipment-webapp --help
```

## Configuration File {: #webapp-configuration }

The configuration file is based on the JSON format. The following shows an example configuration file that defines every possible name-value pair that can be customised for your requirements; however, each name-value pair is considered optional and does not need to be defined in your JSON file. If a name-value pair is omitted, the default value is used.

```json
{
  "git": "git", // (1)!
  "host": "0.0.0.0", // (2)!
  "logo": {
    "src": "https://www.measurement.govt.nz/assets/msl-footer-logo.png",
    "height": 50,
    "margin_left": 5,
    "margin_right": 25
  },
  "navbar": {
    "color": "dark",
    "dark": true
  },
  "nmi": "MSL",
  "pdflatex": "pdflatex",
  "port": 17025,
  "price": {
    "format": ",.2f",
    "decimal": ".",
    "thousands": ",",
    "grouping": [3],
    "currency": {
      "prefix": "",
      "suffix": ""
    }
  },
  "registers": [
    "~/repos/Length-register",
    "path/to/Mass/register",
    "//192.168.1.2/Time/register",
  ],
  "set_props_delay": 0.01,
  "skip_checksum": {
    "Light": true,
    "Length": false,
    "Temperature": false
  },
  "static": "static",
  "theme": "simplex",
  "validation_roots": [
    "//192.168.1.2/Time/data-files",
  ],
  "verapdf": "~/verapdf/verapdf.bat",
  "wordapp": "Word.Application"
}
```

1. The path to the `git` executable. Default assumes that `git` is available on the `PATH` environment variable.
2. The network interface to run the server on. Default assumes all network interfaces.
