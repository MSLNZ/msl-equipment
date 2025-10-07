# Validate

You may use any XML validating tool to validate [equipment registers][] and [connection][connections] files against the schema; however, some of the values of the XML elements are not _completely_ validated by the schema alone. For example, the value of an element in an equipment register could be the SHA-256 checksum of a file. The schema will validate that the SHA-256 checksum value has the correct string length and that the checksum only contains the allowed alphanumeric characters, but, the schema does not validate that the checksum value is correct for the associated file. For these additional validation steps, another tool must be used. The `msl-equipment-validate` command-line tool validates the XML files against the schema and also provides the additional validation steps.

## Install {: #validate-install }

`msl-equipment-validate` is available on [PyPI](https://pypi.org/project/msl-equipment-validate/) and can be installed with a variety of Python package managers

=== "pip"
    ```console
    pip install msl-equipment-validate
    ```

=== "pipx"
    ```console
    pipx install msl-equipment-validate
    ```

=== "uv"
    ```console
    uv tool install msl-equipment-validate
    ```

This will install a command-line tool that you can use to validate the content of equipment registers and connection files.

If you used a package manager that does not automatically add the `msl-equipment-validate` executable to your PATH environment variable (without activating a [virtual environment](https://docs.python.org/3/library/venv.html)), you may want to add the directory to where the `msl-equipment-validate` executable is located to your PATH. This will allow you to validate XML documents from any directory without having to first activate a virtual environment.

### Command alias

You may also want to create a command alias, since the executable name `msl-equipment-validate` is rather long. The following assigns an alias `check` for the `msl-equipment-validate` executable, but you should pick an alias that you prefer.

=== "Unix"
    Add the following to your `.bashrc` (or `.zshrc`) file

    ```
    alias check="msl-equipment-validate"
    ```

=== "Windows"
    You can create an alias in your PowerShell profile script. To determine where this file is located, run the following command from your terminal, e.g., PowerShell or Windows Terminal (not Command Prompt)

    ```console
    echo $PROFILE
    ```

    Open (or create) the `Microsoft.PowerShell_profile.ps1` file that was displayed in the previous command in a text editor and add the following line

    ```powershell
    Set-Alias check C:\Update\to\be\the\path\to\msl-equipment-validate.exe
    ```

    save it then open a new terminal (or run `. $PROFILE` in the current terminal to reload the PowerShell profile).

    !!! warning "Caution"
        If you get an error that the profile script *cannot be loaded because running scripts is disabled on this system*, run the following command in an elevated (admin) terminal

        ```console
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned
        ```

        then restart the terminal.

## Usage {: #validate-usage }

To see the help for the tool run

```console
msl-equipment-validate --help
```

To recursively validate all XML files (that are used by `msl-equipment`) in the current working directory and all sub directories, run the command without arguments

```console
msl-equipment-validate
```

or specify a specific file to validate

```console
msl-equipment-validate my/equipment/register.xml
msl-equipment-validate my/equipment/connections.xml
```

If the `msl-equipment` package is also installed, you can use its command-line interface to validate documents. *(Note the removal of the hyphen between `equipment` and `validate`.)*

```console
msl-equipment validate
```

or to display the help

```console
msl-equipment help validate
```

## Release Notes {: #validate-release-notes }

--8<-- "packages/validate/CHANGELOG.md"