.. _configuration:

==================
Configuration File
==================
A configuration file is used by **MSL-Equipment** to:

1. Specify which :ref:`Databases <database>` to use, which contain equipment and connection records
2. Specify the equipment that is being used to perform a measurement
3. Specify constants to use in your Python program

The configuration file uses the eXtensible Markup Language (XML_) format to specify this information.

The following illustrates an example configuration file.

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
     <msl>

       <!-- MSL-Equipment has it's own pre-defined variables that you can modify the value of -->

       <!-- Use PyVISA-py as the PyVISA backend library -->
       <PyVISA_LIBRARY>@py</PyVISA_LIBRARY>

       <!-- Open all connections in demo mode -->
       <DEMO_MODE>true</DEMO_MODE>

       <!-- Add a single path to where external resource files are located -->
       <PATH>I:\Photometry\SDKs</PATH>
       <PATH recursive="false">D:\code\resources\lib</PATH>

       <!-- Recursively add all subfolders starting from a root path (includes the root path) -->
       <PATH recursive="true">C:\Program Files\Thorlabs</PATH>

       <!-- Also, the user can define their own constants -->
       <MAX_TEMPERATURE units="C">60</MAX_TEMPERATURE>

       <!--
         Specify the equipment that is being used to perform the measurement and assign an
         "alias" that you want to use to associate for each equipment. You only need to
         specify enough XML attributes to uniquely identify the equipment record in an
         Equipment-Registry database. For example, if there is only 1 equipment record in
         the Equipment-Registry databases that you specify (see the <equipment_registers>
         tag below) that is from "Company XYZ" then specifying manufacturer="Company XYZ"
         is enough information to uniquely identify the equipment record in the
         configuration file. If in the future another equipment record is added to an
         Equipment-Registry database for "Company XYZ" then an exception will be raised
         telling you to specify more information in the configuration file to uniquely
         identify a single equipment record.
       -->
       <equipment alias="ref" manufacturer="Keysight" model="34465A"/>
       <equipment alias="scope" manufacturer="Pico Technologies"/>
       <equipment alias="flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

       <!-- Specify the Equipment-Register databases to load equipment records from -->
       <equipment_registers>
         <!--
           The "team" attribute is used to specify which research team the Equipment-Register
           database belongs to
         -->
         <register team="P&amp;R">
             <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
             <!--
               If there are multiple Sheets in the Excel database then you must specify the
               name of the Sheet that contains the equipment records. This Excel database
               also contains connection records (see the <equipment_connections> tag below)
               and so the <sheet> tag must be specified
             -->
             <sheet>Equipment</sheet>
         </register>
         <register team="Electrical">
           <path>H:\Quality\Registers\Equipment.xlsx</path>
           <!-- No need to specify the Sheet name if there is only 1 Sheet in the Excel database -->
         </register>
         <!--
           For a text-based database (e.g., CSV, TXT files) you can specify how the dates are
           formatted and the encoding that is used in the file (UTF-8 is assumed if the encoding
           is not specified). A CSV database uses "," as the delimiter and a TXT database uses
           "\t" as the delimiter.
         -->
         <register team="Time" date_format="%d.%m.%y" encoding="cp1252">
           <path>W:\Registers\Equip.csv</path>
         </register>
         <register team="Mass" date_format="%Y-%m-%d">
           <!--
             You can also specify the database path to be a path that is relative to the
             location of the configuration file. For example, the "equip-reg.txt" file is
             located in the same directory as the configuration file.
           -->
           <path>equip-reg.txt</path>
         </register>
       </equipment_registers>

       <!--
         Specify the databases that contain the information required to connect to the
         equipment. You can create as many <equipment_connections> tags as you want
       -->
       <equipment_connections>
         <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
         <!-- Must also specify which Sheet in this Excel database contains the connection records -->
         <sheet>Connections</sheet>
       </equipment_connections>
       <!--
         You can also set the encoding that is used for a text-based database. The "my_connections.txt"
         file is located in the "resources" subfolder (relative to the path of the configuration file)
         and it is encoded with UTF-16.
       -->
       <equipment_connections encoding="utf-16">
         <path>resources/my_connections.txt</path>
       </equipment_connections>

   </msl>

The :class:`~msl.equipment.config.Config` class is used to load a configuration file and it is the main entryway
in to the **MSL-Equipment** package. For example:

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('/path/to/my/configuration_file.xml')

.. _XML: https://www.w3schools.com/Xml/