# AvaSpec SDK

Wrapper around the `avaspec` SDK from [Avantes](https://www.avantes.com/){:target="_blank"}.

The wrapper was written using v9.7.0.0 of the SDK. The `avaspec` SDK may require a Visual C++ Redistributable Package to be installed (on Windows).

The main class is [AvaSpec][msl.equipment_resources.avantes.avaspec.AvaSpec] and the [Enums and Structs][avaspec-enums-structs] are available once the `avantes` module is imported, for example,

```python
from msl.equipment.resources import avantes

cfg = avantes.MeasConfigType()
cfg.m_IntegrationTime = 5  # in milliseconds
cfg.m_NrAverages = 1  # number of averages
```

::: msl.equipment_resources.avantes.avaspec.AvaSpec
    options:
        show_root_full_path: false
        show_root_heading: true

## Enums and Structs {: #avaspec-enums-structs }

::: msl.equipment_resources.avantes.avaspec
    options:
        filters: ["!AvaSpec"]
