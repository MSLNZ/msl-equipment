# Resources

Resources are custom classes for interfacing with specific equipment. In previous releases of `msl-equipment` (versions < 1.0), the resources were automatically bundled with `msl-equipment`. As of v1.0, the resources are maintained in another package, `msl-equipment-resources`, that must be installed separately.

Some of the resources might not work in your application because the resource might depend on an external dependency, e.g., the Software Development Kit (SDK) provided by a manufacturer, and this external dependency might not be available for your operating system.

!!! examples
    There are examples on how to use the resources in the [repository](https://github.com/MSLNZ/msl-equipment/tree/main/packages/resources/examples){:target="_blank"}.

!!! danger "Attention"
    Companies that sell equipment that are used for scientific research are identified in this guide in order to illustrate how to adequately use `msl-equipment-resources` in your application. Such identification is not intended to imply recommendation or endorsement by the Measurement Standards Laboratory of New Zealand, nor is it intended to imply that the companies identified are necessarily the best for the purpose.

## Install

`msl-equipment-resources` is currently only available for installation from source. It can be installed using a variety of package managers.

=== "pip"
    ```console
    pip install msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "uv"
    ```console
    uv add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "poetry"
    ```console
    poetry add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

=== "pdm"
    ```console
    pdm add msl-equipment-resources@git+https://github.com/MSLNZ/msl-equipment#subdirectory=packages/resources
    ```

## Create a resource

To create a new resource you must create a class that inherits from [Interface][msl.equipment.schema.Interface] and specify the manufacturer and model number (product series) that the resource can be used for. This inheritance may also be acquired by sub-classing from one of the [interface][connections-interfaces] protocols (see also [Multiple interfaces][]).

The following example shows how to create a new resource for equipment that use the RS-232 protocol for communication. The values specified for the `manufacturer` and `model` support a [regular-expression pattern](https://regexr.com/){:target="_blank"}.

```python
# my_resource.py
from __future__ import annotations

from msl.equipment import Equipment, Serial

class MyResource(Serial, manufacturer=r"Company Name", model=r"ABC"):

    def __init__(self, equipment: Equipment) -> None:
        """My custom resource.

        Args:
            equipment: An `Equipment` instance.
        """
        super().__init__(equipment)

    def do_something(self) -> None:
        self.write("The command to write to the equipment")
```

When `my_resource` is imported, the `MyResource` class is automatically registered as a resource that will be used when [connect][msl.equipment.schema.Equipment.connect]ing to the equipment if the values of [manufacturer][msl.equipment.schema.Equipment.manufacturer] and [model][msl.equipment.schema.Equipment.model] match the specified [regular-expression pattern](https://regexr.com/){:target="_blank"}.

## Contribute a resource

!!! important
    As an ISO/IEC 17025 accredited laboratory, the resources in the [repository]{:target="_blank"} are part of the Quality Management System of MSL. As such, contributions from people outside of MSL may be considered but the equipment must be available to MSL staff for the code to be checked and validated.

When adding a new resource to the [repository]{:target="_blank"} the following steps should be performed.

[uv]{:target="_blank"} is used as the package and project manager for `msl-equipment` development, it is recommended to install it. [mypy]{:target="_blank"} and [basedpyright]{:target="_blank"} are used as type checkers, [ruff]{:target="_blank"} is used as the formatter/linter and the documentation is built with [MkDocs]{:target="_blank"} using the [Material]{:target="_blank"} theme and the [mkdocstrings-python]{:target="_blank"} plugin. Installation of these packages is automatically managed for you by [uv]{:target="_blank"}. [CSpell]{:target="_blank"} provides spell checking and can be installed by running `npm install -g cspell@latest` (which requires [Node.js and npm]{:target="_blank"} to be installed).

1. Create a [fork]{:target="_blank"} of the [msl-equipment repository](https://github.com/MSLNZ/msl-equipment){:target="_blank"}.

2. Resources are located in the `packages/resources/src/msl/equipment_resources` directory. A sub-directory is the name of the *manufacturer* of the equipment. If the *manufacturer* directory does not exists for the new resource, create it (also create an `__init__.py` file in the *manufacturer* directory).

3. Create a new Python file within the *manufacturer* directory with a filename that represents the *model* number or product series of the equipment that the resource is used for. Follow the example in [Create a resource][] to implement the resource class in this file.

4. Import your resource class in the `packages/resources/src/msl/equipment_resources/MANUFACTURER/__init__.py` and the `packages/resources/src/msl/equipment_resources/__init__.py` modules and alphabetically add the class to the `__all__` variable.

5. Add at least one example on how to use the resource to the `packages/resources/examples` directory. Create a new *manufacturer* sub-directory if it does not already exist.

6. From the `packages/resources` directory, lint `uv run ruff check`, format `uv run ruff format` and type check `uv run basedpyright`, `uv run mypy .` the code. These checks are also performed once you do Step 12. Type checking with [mypy]{:target="_blank"} requires the `MYPYPATH=src` environment variable to be defined to fix the *Source file found twice under different module names* issue.

7. If you are able to create a test for the new resource, that does not depend on the equipment being attached to a computer, add a test to the `packages/resources/tests` directory. Run `uv run pytest` to verify the tests pass.

8. To add the resource to the documentation, create a new Markdown file in the `docs/resources` directory. The format follows the `docs/resources/MANUFACTURER/MODEL.md` structure. Also, add the new resource, alphabetically, to the *nav:* &rarr; *Resources:* &rarr; *MANUFACTURER:* section in the `mkdocs.yml` file. Follow what is done for the other resources.

9. Update `CHANGELOG.md` stating that you added this new resource.

10. From the root directory of the repository, build the documentation `uv run mkdocs serve` and check that your resource renders correctly.

11. Run the spell checker `cspell .`. Since this step requires [Node.js and npm]{:target="_blank"} to be installed, you may skip it. This check is also performed once you do Step 12.

12. If running the tests pass and linting, formatting, type/spell checking and building the documentation do not show errors/warnings then create a [pull request]{:target="_blank"}.

## Multiple interfaces

If the equipment supports multiple interfaces for message-based protocols (e.g., [Socket][msl.equipment.interfaces.socket.Socket], [Serial][msl.equipment.interfaces.serial.Serial], [GPIB][msl.equipment.interfaces.gpib.GPIB], ...) you can create a resource that inherits from the [MultiMessageBased][msl.equipment_resources.multi_message_based.MultiMessageBased] class. Upon calling [super][] in the subclass, the connection is established with the appropriate protocol class.


[fork]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo
[pull request]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork
[repository]: https://github.com/MSLNZ/msl-equipment/tree/main/packages/resources
[uv]: https://docs.astral.sh/uv/
[mypy]: https://mypy.readthedocs.io/en/stable/index.html
[basedpyright]: https://docs.basedpyright.com/latest/
[ruff]: https://docs.astral.sh/ruff/
[MkDocs]: https://www.mkdocs.org/
[Material]: https://squidfunk.github.io/mkdocs-material/
[mkdocstrings-python]: https://mkdocstrings.github.io/python/
[CSpell]: https://cspell.org/
[Node.js and npm]: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
