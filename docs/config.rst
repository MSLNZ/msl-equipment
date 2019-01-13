.. _configuration_file:

==================
Configuration File
==================
A configuration file is used by **MSL-Equipment** to:

1. Specify which :ref:`Databases <database>` to use
2. Specify the equipment that is being used to perform a measurement
3. Specify constants to use in your Python program

The configuration file uses the eXtensible Markup Language (XML_) format to specify this information.

The following illustrates an example configuration file.

.. code-block:: xml

   <?xml version="1.0" encoding="utf-8"?>
     <msl>
       <!--
         Use PyVISA-py as the PyVISA backend library.
         Allowed values are: @ni, @py, @sim, /path/to/lib\@ni
       -->
       <pyvisa_library>@py</pyvisa_library>

       <!-- Open all connections in demo mode. -->
       <demo_mode>true</demo_mode>

       <!--
         Add a single path to where external resource files are located.
         The paths get appended to Config.PATH and os.environ['PATH'].
       -->
       <path>I:\Photometry\SDKs</path>
       <path recursive="false">D:\code\resources\lib</path>
       <!-- Recursively add all subfolders starting from a root path (includes the root path). -->
       <path recursive="true">C:\Program Files\Thorlabs</path>

       <!-- Also, the user can define their own constants. -->
       <max_temperature units="C">60</max_temperature>

       <!--
         Specify the equipment that is being used to perform the measurement and assign an
         "alias" that you want to use to associate for each equipment. You only need to
         specify enough XML attributes to uniquely identify the equipment record in an
         Equipment-Registry database. For example, if there is only 1 equipment record in
         the Equipment-Registry databases (see the <registers> tag below) that is from
         "Company XYZ" then specifying manufacturer="Company XYZ" is enough information to
         uniquely identify the equipment record in the configuration file. If in the future
         another equipment record is added to an Equipment-Registry database for "Company XYZ"
         then an exception will be raised telling you to specify more information in the
         configuration file to uniquely identify a single equipment record.
       -->
       <equipment alias="dmm" manufacturer="Keysight" model="34465A"/>
       <equipment alias="scope" manufacturer="Pico Technologies"/>
       <equipment alias="flipper" manufacturer="Thorlabs" model="MFF101/M" serial="37871232"/>

       <!-- Specify the Equipment-Register Databases to load equipment records from. -->
       <registers>
         <!--
           The "team" attribute is used to specify which research team the Equipment-Register
           database belongs to.
         -->
         <register team="P&amp;R">
             <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
             <!--
               If there are multiple Sheets in the Excel database then you must specify the
               name of the Sheet that contains the equipment records. This Excel database
               also contains connection records (see the <connections> tag below) and so
               the <sheet> tag must be specified.
             -->
             <sheet>Equipment</sheet>
         </register>
         <register team="Electrical">
           <path>H:\Quality\Registers\Equipment.xlsx</path>
           <!-- No need to specify the Sheet name if there is only 1 Sheet in the Excel database. -->
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
             location of the configuration file. For example, this "equip-reg.txt" file is
             located in the same directory as the configuration file.
           -->
           <path>equip-reg.txt</path>
         </register>
         <register team="Length" user_defined="apples, pears, oranges">
           <!--
             An EquipmentRecord has standard properties (e.g, manufacturer, model, ...) that
             are read from the database. You can also include additional fields from the database
             that are not part of the standard properties. Include a "user_defined" list
             (comma-separated) of additional properties to include. The field names that
             contain the text "apples", "pears" and "oranges" are added to the "user_defined"
             dictionary for all EquipmentRecord's in this register.
           -->
           <path>I:\LS-Equip-Reg\reg.csv</path>
         </register>
       </registers>

       <!-- Specify the Connections Databases to load connection records from. -->
       <connections>
         <connection>
           <path>Z:\QUAL\Equipment\Equipment Register.xls</path>
           <!--
             Must also specify which Sheet in this Excel database contains the connection records.
             This "Equipment Register.xls" file also contains an "Equipment" Sheet, see the
             <register team="P&amp;R"> element above.
           -->
           <sheet>Connections</sheet>
         </connection>
         <!-- You can set the encoding that is used for a text-based database. -->
         <connection encoding="utf-16">
           <!-- Specify a relative path (relative to the location of the configuration file). -->
           <path>data/my_connections.txt</path>
         </connection>
       </connections>

     </msl>

The :class:`~msl.equipment.config.Config` class is used to load a configuration file and it is the main entryway
in to the **MSL-Equipment** package. For example:

.. code-block:: python

  >>> from msl.equipment import Config
  >>> cfg = Config('/path/to/my/configuration/file.xml')  # doctest: +SKIP

.. _XML: https://www.w3schools.com/Xml/
