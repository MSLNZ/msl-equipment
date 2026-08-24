# Web Application

The web application runs a server on a computer which allows people to interact with equipment registers via a web browser from any computer that is on the same network. Only the computer that runs the server must have access to the equipment registers of each team. That access could either be through a shared network drive or by cloning a repository.

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

The Python packages that are required to run the web application are automatically installed, but there are non-Python dependencies that can also be installed on the computer that runs the server.

The web application provides the option to convert $\LaTeX$ and Microsoft Word documents to the PDF/A format and the option to sync equipment registers that are cloned from a repository. As such, the following additional executables should be available on the computer that runs the web application, if that feature is to be supported.

* [git](https://git-scm.com/) &mdash; For syncing an equipment register with its repository.

=== "Windows"
    ```console
    winget install --id Git.Git
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install git
    ```

=== "macOS"
    ```console
    brew install git
    ```

* [Microsoft 365](https://www.microsoft.com/en/microsoft-365/microsoft-office) &mdash; To convert Microsoft Word documents to PDF/A.

* `pdflatex` &mdash; To convert $\LaTeX$ documents to PDF/A. You may prefer to install [MiKTeX](https://miktex.org/download) on a non-Windows operating system. A benefit of MiKTeX is that it can be configured to automatically install missing packages that may be required to build a $\LaTeX$ document. The web application only requires the `pdflatex` executable to be available, it does not manage a TeX distribution for you.

=== "Windows"
    ```console
    winget install --id MiKTeX.MiKTeX
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install texlive-latex-base
    ```

=== "macOS"
    ```console
    brew install --cask basictex
    ```

* [veraPDF](https://verapdf.org/software/) &mdash; For validating PDF/A documents. See [here](https://docs.verapdf.org/install/) for install instructions.

* [java](https://www.java.com/en/) &mdash; Required to run the `veraPDF` tool. The `java` runtime executable must be available from your terminal (i.e., running `java -version` should return the version of java)

=== "Windows"
    ```console
    winget install --id Oracle.JDK.26
    ```

=== "Debian/Ubuntu"
    ```console
    sudo apt install default-jre
    ```

=== "macOS"
    ```console
    brew install openjdk
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

The configuration file uses the [JSON](https://www.json.org/json-en.html) format. The following shows an example configuration file that defines every possible name-value pair that can be customised for your requirements; however, every name-value pair is optional and does not need to be defined in your JSON file. If a name-value pair is omitted, the default value is used for the web application.

```json
{
  "git": "git", // (1)!
  "host": "0.0.0.0", // (2)!
  "navbar": { // (3)!
    "colour": "dark", // (4)!
    "dark": true, // (5)!
    "logo": { // (6)!
      "height": 50, // (7)!
      "margin_left": 5, // (8)!
      "margin_right": 25, // (9)!
      "src": "https://www.measurement.govt.nz/assets/msl-footer-logo.png" // (10)!
    }
  },
  "nmi": "MSL", // (11)!
  "pdflatex": "pdflatex", // (12)!
  "port": 17025, // (13)!
  "price": { // (14)!
    "format": ",.2f", // (15)!
    "decimal": ".", // (16)!
    "thousands": ",", // (17)!
    "grouping": [3], // (18)!
    "currency": { // (19)!
      "prefix": "", // (20)!
      "suffix": "" // (21)!
    }
  },
  "registers": [ // (22)!
    "~/repos/Length-register",
    "path/to/Mass/register",
    "//192.168.1.2/Time/register"
  ],
  "set_props_delay": 0.01, // (23)!
  "sha256_validation": { // (24)!
    "Length": { // (25)!
      "skip": true, // (26)!
      "roots": [] // (27)!
    },
    "Time": {
      "skip": false,
      "roots": ["//192.168.1.2/Time/data-files"]
    }
  },
  "static": "static", // (28)!
  "theme": "simplex", // (29)!
  "verapdf": "~/verapdf/verapdf.bat", // (30)!
  "wordapp": "Word.Application" // (31)!
}
```

1.  The path to the `git` executable. Default value assumes that `git` is available on the `PATH` environment variable.

    Can use the `~` character to expand the user's home directory.

2.  The network interface to run the server on. Default value is `0.0.0.0` (use all network interfaces).

3.  Customise the Navigation Bar (at the top of each page).

4.  The colour of the Navigation Bar. Default value is `dark`.

    Main options are `primary`, `light` and `dark`. You can also choose one of the other contextual classes provided by Bootstrap (`secondary`, `success`, `warning`, `danger`, `info`, `white`) or any valid CSS colour of your choice (e.g., a hex code, a decimal code or a CSS colour name).

5.  Whether to apply the `navbar-dark` class to the Navigation Bar. Default value is `true`.

    Causes text in the children of the Navigation Bar to use light or dark colours for contrast and visibility.

6.  Customise the logo (image) to display in the Navigation Bar.

7.  Image height (in pixels). Default value is `50`.

8.  Amount of space (in pixels) required on the left side of the image. Default value is `5`.

9.  Amount of space (in pixels) required on the right side of the image. Default value is `25`.

10. Image source. Default value is an empty string (i.e., do not display an image).

    Can be a relative path to an image file in the `static` directory (e.g., `static/logo.png`) or a URL to an image file.

11. Name of the National Metrology Institute. Default value is `MSL`.

    This text is displayed in the title bar of the web browser and on the API web page.

12. The path to the `pdflatex` executable. Default value assumes that `pdflatex` is available on the `PATH` environment variable.

    Can use the `~` character to expand the user's home directory.

13. The network port to run the server on. Default value is `17025`.

14. Customise how pricing information is displayed. See [d3-formatLocale](https://d3js.org/d3-format#formatLocale) for more information.

15. The format to use to display the price value. Default value is `,.2f`. See [d3-format](https://d3js.org/d3-format) for more information.

16. The symbol to use for the decimal point. Default value is `.`.

17. The symbol to use for the group separator. Default value is `,`.

    Note that the thousands property name is a misnomer, as the grouping definition allows groups other than thousands (3).

18. The array of group sizes, cycled as needed. Default value is `[3]`.

19. The currency symbols to use for each price.

20. Price prefix symbol. Default value is an empty string.

21. Price suffix symbol. Default value is an empty string.

22. An array of directories to the equipment registers to make available in the web application. Default value is an empty array.

    Can use the `~` character to expand the user's home directory.

23. The number of seconds to wait after calling `dash.set_props` in a callback. Default value is `0.01`.

    If the value is too small, components might not update properly while the dash callback is running.

24. Customise the validation of `<sha256>` elements in an equipment register. Default is an empty JSON object, which sets `skip` to `false` and an empty `roots` array for every equipment register.

25. The name of the team that is responsible for the equipment register.

26. Whether to skip validating `<file>` and `<digitalReport>` elements containing a sha256 checksum. Default value is `false`.

27. Additional root paths to use during validation. Default value is an empty array.

    These paths may be required when validating `<file>` or `<digitalReport>` elements that specify a relative path for the value of the `<url>` element.

28. Path to the *static* directory. Default value is `static`, which is relative to where the `msl-equipment-validate` package is installed.

    You can save the favicon.ico, webapp.css and the logo image here.

29. The name of a [Bootstrap](https://bootswatch.com/) theme to use for the web application. Default value is `BOOTSTRAP`.

30. Path to the [veraPDF](https://verapdf.org/) executable. Default value assumes that `verapdf` is available on the `PATH` environment variable.

    Can use the `~` character to expand the user's home directory.

31. Name of the COM object to load for the [Microsoft Word Application](https://learn.microsoft.com/en-us/office/vba/api/word.application). Default value is `Word.Application`.

## Release Notes {: #webapp-release-notes }

--8<-- "packages/webapp/CHANGELOG.md"