.. _configuration:

==================
Configuration File
==================
A configuration file is used by **MSL-Equipment** to:

1. Specify which :ref:`Databases <database>` to use, which contain equipment and connection records
2. Specify the **equipment** that is being used to perform a measurement
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

       <!-- Add a single path to where resource files are located -->
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
         Equipment-Registry Database. For example, if there is only 1 equipment record in
         the Equipment-Registry Databases that you specify (see the <equipment_registers>
         tag below) that is from "Company XYZ" then specifying manufacturer="Company XYZ"
         is enough information to uniquely identify the equipment record in the
         configuration file. If in the future another equipment record is added to an
         Equipment-Registry Database for "Company XYZ" then an exception will be raised
         telling you to specify more information in the configuration file to uniquely
         identify a single equipment record.
       -->
       <equipment alias="ref" manufacturer="Keysight" model="34465A"/>
       <equipment alias="scope" manufacturer="Pico Technologies"/>
       <equipment alias="flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

       <!-- Specify the Equipment-Register Databases to load equipment records from -->
       <equipment_registers>
         <!-- The "team" attribute is used to define which MSL Team the Registry belongs to -->
         <register team="P&amp;R">
             <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
             <!--
               If there are multiple Sheets in the Excel file then you must specify the
               name of the Sheet that contains the appropriate records. This Excel file
               also contains connection records (see the <equipment_connections> tag below)
              -->
             <sheet>Equipment</sheet>
         </register>
         <register team="Electrical">
           <path>H:\Quality\Registers\Equipment.xlsx</path>
           <!-- No need to specify the Sheet name if there is only 1 Sheet in the Excel file -->
         </register>
         <!-- For a text-based database (csv/txt) you should specify how the dates are formatted -->
         <register team="Time" date_format="%d.%m.%y">
           <path>W:\Registers\Equip.csv</path>
         </register>
         <register team="Mass" date_format="%Y-%m-%d">
           <!--
             You can also specify the database path to be relative to the location of the
             configuration file. For example, the equip-reg.txt file is located in the
             same directory as the configuration file.
           -->
           <path>equip-reg.txt</path>
         </register>
       </equipment_registers>

       <!--
         Specify the database that contains the information required to connect to the
         equipment. Unlike Equipment-Register Databases you can only specify a single
         Connections Database. The reason being that since equipment can be shared
         between people some connection values, like the GPIB address, can vary depending
         on who is using the equipment and what other equipment they are using. Therefore,
         everyone could have their own Connections Database and connection records can be
         copied from one Connection Database to another when equipment is being borrowed.
         As opposed to equipment records in an Equipment-Register Database MUST NEVER be
         copied to another Equipment-Register Database in order to ensure that an official
         registry of equipment is maintained
        -->
       <equipment_connections>
         <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
         <sheet>Connections</sheet>
       </equipment_connections>

   </msl>

The :class:`~msl.equipment.config.Config` class is used to load a configuration file. For example:

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('msl/examples/equipment/example.xml')

.. _XML: https://www.w3schools.com/Xml/