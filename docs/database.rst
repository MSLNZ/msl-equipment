.. _database:

MSL-Equipment Database Formats
==============================
Databases are used by **MSL-Equipment** to store :class:`~msl.equipment.record_types.EquipmentRecord`\'s
in an `Equipment-Register Database`_ and :class:`~msl.equipment.record_types.ConnectionRecord`\'s
in a `Connections Database`_. The database file formats that are currently supported are **.txt**,
**.csv** and **.xls(x)**. A database is made up of **fields** (columns) and **records** (rows).

Equipment-Register Database
---------------------------
To adhere to international ISO/IEC 17025 standards, the information about the equipment that is
used for a calibration or for a comparison must be known and it must be up to date. Keeping a central
database of the equipment that is available in the lab allows for managing this information and
for helping to ensure that the equipment that is being used for a calibration/comparison meets the
requirements needed to achieve the final measurement uncertainty.

**MSL-Equipment** does not require that a *single* database is used for **ALL** equipment from **ALL**
MSL sections. However, it is vital that each equipment record can only be uniquely found in **ONE**
**Equipment-Register** database. These databases are never to be copied from one MSL team to another
*(although keeping backups are required)*. Rather if you are borrowing equipment from another team you
simply specify the path to that teams **Equipment-Register** database in your configuration file. See
:obj:`msl.equipment.config.Config` for more details on how to specify multiple **Equipment-Register**
databases in a configuration file. The owner of the equipment is responsible for ensuring that the
information about the equipment is updated in their **Equipment-Register** database. The user of
the equipment has access to this information through an :class:`~msl.equipment.record_types.EquipmentRecord`
object.

Each **record** in an **Equipment-Register** database is converted into an
:class:`~msl.equipment.record_types.EquipmentRecord` object when a configuration file is loaded.
Each **field** is an property name for an :class:`~msl.equipment.record_types.EquipmentRecord`.

Example **Equipment-Register** database:

.. role:: red

.. tabularcolumns:: |p{0.5cm}|p{0.5cm}|l|

+--------------------------+----------------------------------------------------------------+----------------+
| The :red:`Register`      | A column header can be any text. The name of an                | :red:`Model` # |
| number used for Policies | :class:`~msl.equipment.record_types.EquipmentRecord`           |                |
| and Procedures.          | property must appear somewhere in the header text to           |                |
|                          | associate the values in this column with the                   |                |
|                          | :class:`~msl.equipment.record_types.EquipmentRecord`           |                |
|                          | property value. This column is used to specify the             |                |
|                          | :red:`Manufacturer` of the equipment. Since the text           |                |
|                          | *Manufacturer* appears in this header the value in             |                |
|                          | this column will be used for                                   |                |
|                          | :obj:`~msl.equipment.record_types.EquipmentRecord.manufacturer`|                |
+==========================+================================================================+================+
| Manager                  |                                                                |                |
+--------------------------+----------------------------------------------------------------+----------------+


Connections Database
--------------------
Describe
