# Equipment

::: msl.equipment.schema
    options:
        filters: ["Equipment", "from_xml", "to_xml", "entered_by", "checked_by", "checked_date", "alias", "keywords", "id", "manufacturer", "model", "^serial$", "description", "specifications", "location", "status", "loggable", "traceable", "calibrations", "maintenance", "alterations", "firmware", "specified_requirements", "reference_materials", "quality_manual", "latest_reports", "latest_report"]

::: msl.equipment.schema
    options:
        filters: ["^Latest$", "calibration_interval", "^date$", "name", "quantity", "is_calibration_due"]

::: msl.equipment.schema
    options:
        filters: ["LatestPerformanceCheck", "^check$"]

::: msl.equipment.schema
    options:
        filters: ["LatestReport", "^report$"]
