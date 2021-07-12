import os
import sys
import datetime

import pytest

from msl.equipment import Config, constants, Backend
from msl.equipment.record_types import RecordDict

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'db_files')


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()


def test_database_io_errors():

    # no <path></path> tag
    with pytest.raises(OSError, match=r'<path>'):
        Config(os.path.join(ROOT_DIR, 'db_err0.xml')).database()

    # database file does not exist
    with pytest.raises(OSError, match=r'Cannot find the database'):
        Config(os.path.join(ROOT_DIR, 'db_err1.xml')).database()

    # unsupported database file
    with pytest.raises(OSError, match=r'Unsupported equipment-registry database'):
        Config(os.path.join(ROOT_DIR, 'db_err2.xml')).database()

    # more than 1 Sheet in the Excel database
    with pytest.raises(ValueError, match=r'You must specify the name of the sheet to read'):
        Config(os.path.join(ROOT_DIR, 'db_err3.xml')).database()

    # the 'equipment' item in the xml file is not a valid Equipment Record
    with pytest.raises(AttributeError, match=r'attributes'):
        Config(os.path.join(ROOT_DIR, 'db_err4.xml')).database()

    # the 'equipment' item in the xml file is not a unique Equipment Record
    with pytest.raises(AttributeError, match=r'unique'):
        Config(os.path.join(ROOT_DIR, 'db_err5.xml')).database()

    # the 'equipment' item in the xml file is has multiple aliases
    with pytest.raises(ValueError, match=r'aliases'):
        Config(os.path.join(ROOT_DIR, 'db_err6.xml')).database()

    # invalid Sheet name in Excel database
    with pytest.raises(ValueError, match=r'There is no sheet'):
        Config(os.path.join(ROOT_DIR, 'db_err7.xml')).database()


def test_database():

    path = os.path.join(ROOT_DIR, 'db.xml')
    c = Config(path)

    dbase = c.database()
    assert path == dbase.path
    assert len(dbase.records()) == 7 + 18
    assert len(dbase.records(manufacturer='NOPE!')) == 0
    assert len(dbase.records(manufacturer='^Ag')) == 10  # all records from Agilent
    assert len(dbase.records(manufacturer='^Ag', connection=True)) == 3  # all records from Agilent with a ConnectionRecord
    assert len(dbase.records(manufacturer='Agilent', model='83640L')) == 1
    assert len(dbase.records(manufacturer=r'H.*P')) == 2  # all records from Hewlett Packard
    assert len(dbase.records(manufacturer=r'H.*P|^Ag')) == 12  # all records from Hewlett Packard or Agilent
    assert len(dbase.records(manufacturer='Bd6d850614')) == 1
    assert len(dbase.records(model='00000')) == 1
    num_connections_expected = 4
    assert len(dbase.records(connection=True)) == num_connections_expected
    assert len(dbase.records(connection=False)) == len(dbase.records()) - num_connections_expected
    assert len(dbase.records(connection=1)) == num_connections_expected
    assert len(dbase.records(connection=0)) == len(dbase.records()) - num_connections_expected
    assert len(dbase.records(connection='anything that converts to a bool=True')) == num_connections_expected
    assert len(dbase.records(connection='')) == len(dbase.records()) - num_connections_expected

    dbase.records(flags=1)  # a flags argument name is ok even though it not an EquipmentRecord property name
    with pytest.raises(NameError):
        dbase.records(unknown_name=None)

    assert len(dbase.connections()) == 10
    assert len(dbase.connections(backend='MSL')) == 5
    assert len(dbase.connections(backend=constants.Backend.MSL)) == 5
    assert len(dbase.connections(backend='PYVISA')) == 0
    assert len(dbase.connections(backend='PyVISA')) == 5
    assert len(dbase.connections(backend=constants.Backend.PyVISA)) == 5
    assert len(dbase.connections(backend='PyVISA|MSL')) == 10
    assert len(dbase.connections(backend='XXXXX')) == 0
    assert len(dbase.connections(serial='A10008')) == 1
    assert len(dbase.connections(manufacturer='^Ag')) == 4  # all records from Agilent
    assert len(dbase.connections(model='DTMc300V_sub')) == 1
    assert len(dbase.connections(manufacturer='Agilent', serial='G00001')) == 1
    assert len(dbase.connections(manufacturer='Agilent|Fluke|Thorlabs')) == 6
    assert len(dbase.connections(interface='SERIAL')) == 2  # != 3 since "Coherent Scientific" uses PyVISA
    assert len(dbase.connections(interface=constants.MSLInterface.SDK)) == 2
    assert len(dbase.connections(interface='SERIAL|SDK')) == 4
    assert len(dbase.connections(interface=constants.MSLInterface.SERIAL)) == 2  # != 3 since "Coherent Scientific" uses PyVISA
    assert len(dbase.connections(interface='XXXXXX')) == 0

    dbase.connections(flags=1)  # a flags argument name is ok even though it not a ConnectionRecord property name
    with pytest.raises(NameError):
        dbase.connections(unknown_name=None)

    assert len(dbase.equipment) == 2
    assert '712ae' in dbase.equipment  # the model number is used as the key
    assert 'dvm' in dbase.equipment  # the alias is used as the key


def test_connection_properties():

    dbase = Config(os.path.join(ROOT_DIR, 'db.xml')).database()
    props = dbase.records(serial='37871232')[0].connection.properties

    assert props['a'] == 1
    assert props['b'] == 1.1
    assert isinstance(props['c'], bool) and props['c']
    assert isinstance(props['d'], bool) and props['d']
    assert isinstance(props['e'], bool) and not props['e']
    assert isinstance(props['f'], bool) and not props['f']
    assert props['g'] is None
    assert props['h'] == ''
    assert props['i_termination'] == constants.LF
    assert props['j_termination'] == constants.CR
    assert props['k_termination'] == constants.CR + constants.LF
    assert props['l'] == 'some text'
    assert props['m'] == 'D:\\Data\\'


def test_encoding():

    IS_PYTHON2 = sys.version_info[0] == 2
    if IS_PYTHON2:
        reload(sys)  # required for the sys.setdefaultencoding() calls below

    print('')
    for cfg in ['utf8_txt.xml', 'cp1252_txt.xml', 'xlsx.xml']:
        db = Config(os.path.join(ROOT_DIR, 'db_encoding_' + cfg)).database()

        if IS_PYTHON2:
            if cfg.startswith('cp1252'):
                sys.setdefaultencoding('cp1252')  # a legacy encoding used by Microsoft Windows
            elif cfg.startswith('utf8'):
                sys.setdefaultencoding('utf-8')

        print(db.path)

        # test printing the database records
        for r in db.records():
            print(r)
            r.to_dict()
            r.to_xml()
        for r in db.connections():
            print(r)
            r.to_dict()
            r.to_xml()

        assert db.records(manufacturer='Kepco')[0].manufacturer == u'Kepco and \u201cTMK\u201d shunt'
        assert db.records(model='MFF101/M')[0].description == u'Motorized Filter Flip Mount for \xd825mm Optics'


def test_database_user_defined():
    path = os.path.join(ROOT_DIR, 'db_user_defined.xml')
    cfg = Config(path)
    db = cfg.database()
    for record in db.records():
        if record.team == 'Any':
            assert len(record.user_defined) == 2
            assert record.user_defined['nothing_relevant'] == 'XXXXXXXXXX'
            assert record.user_defined['policies'] == 'MSLE.X.YYY'
        else:
            assert len(record.user_defined) == 0

    path = os.path.join(ROOT_DIR, 'db_user_defined_bad.xml')
    cfg = Config(path)
    db = cfg.database()
    for record in db.records():
        if record.team == 'Any':
            assert len(record.user_defined) == 1
            assert record.user_defined['policies'] == 'MSLE.X.YYY'
        else:
            assert len(record.user_defined) == 0


def test_json_and_xml_db():

    for filename in ['config_json.xml', 'config_xml.xml']:

        db = Config(os.path.join(ROOT_DIR, filename)).database()

        #
        # EquipmentRecords
        #

        assert len(db.records()) == 3
        assert len(db.records(is_operable=True)) == 2
        assert len(db.records(is_operable=False)) == 1
        assert len(db.records(category='Logger')) == 1

        records = db.records(unique_key='AK1')
        assert len(records) == 1
        r = records[0]
        assert len(r.calibrations) == 2
        c0 = r.calibrations[0]
        assert c0.report_date == datetime.date(2012, 10, 20)
        assert c0.calibration_date == datetime.date(2012, 10, 20)
        assert c0.report_number == 'PTB 44183/12'
        assert c0.calibration_cycle == 5
        assert len(c0.measurands) == 1
        m = c0.measurands['spectral_radiance_d6']
        assert m.type == 'spectral_radiance_d6'
        assert m.unit == ''
        assert m.conditions.measured_area_diameter == 10
        assert m.conditions.measured_area_diameter_unit == 'mm'
        assert m.conditions.bandwidth_below_1100_nm == 3
        assert m.conditions.bandwidth_below_1100_nm_unit == 'nm'
        assert m.conditions.bandwidth_above_1100_nm == 6
        assert m.conditions.bandwidth_above_1100_nm_unit == 'nm'
        assert m.calibration.calibration_type == 'dependent_artefact_values'
        assert m.calibration.dependent_parameter == 'wavelength'
        assert m.calibration.dependent_unit == 'nm'
        assert m.calibration.dependent_minimum == 250
        assert m.calibration.dependent_maximum == 2450
        with pytest.raises(TypeError):  # cannot change value
            m.calibration.dependent_maximum = 1000
        assert m.calibration.artefact_values == ((250, 0.938), (260, 0.945), (270, 0.950), (2450, 0.934))
        assert m.calibration.expanded_uncertainty == ((0, 0.011), (0, 0.011), (0, 0.004), (0, 0.019))
        assert m.calibration.coverage_factor == 2
        assert m.calibration.level_of_confidence == 0.95
        assert m.calibration.correlation_matrix == ()
        c1 = r.calibrations[1]
        assert c1.report_date == datetime.date(2012, 10, 20)
        assert c1.calibration_date == datetime.date(2012, 10, 20)
        assert c1.report_number == 'PTB 44188/12'
        assert c1.calibration_cycle == 5
        assert len(c1.measurands) == 1
        m = c1.measurands['spectral_radiance_factor']
        assert m.type == 'spectral_radiance_factor'
        assert m.unit == ''
        assert m.conditions.measured_area_diameter == "ellipse, 10 and 10/cos(theta_d)"
        assert m.conditions.measured_area_diameter_unit == 'mm'
        assert m.conditions.bandwidth_below_900_nm == 3
        assert m.conditions.bandwidth_below_900_nm_unit == 'nm'
        assert m.conditions.bandwidth_above_900_nm == 6
        assert m.conditions.bandwidth_above_900_nm_unit == 'nm'
        assert m.conditions.divergence_of_incident_beam == 1.5
        assert m.conditions.divergence_of_incident_beam_unit == 'degrees'
        assert m.conditions.divergence_of_detection_beam == 0.32
        assert m.conditions.divergence_of_detection_beam_unit == 'degrees'
        assert m.calibration.calibration_type == 'dependent_artefact_values'
        assert m.calibration.dependent_measurands.wavelength.minimum == 350
        assert m.calibration.dependent_measurands.wavelength['maximum'] == 800
        assert m.calibration.dependent_measurands.wavelength.unit == 'nm'
        assert m.calibration.dependent_measurands['incident_angle']['minimum'] == 45
        assert m.calibration.dependent_measurands['incident_angle'].maximum == 45
        assert m.calibration.dependent_measurands.incident_angle.unit == 'degrees'
        assert m.calibration.dependent_measurands.detection_angle.minimum == -30
        assert m.calibration['dependent_measurands']['detection_angle'].maximum == 65
        assert m.calibration.dependent_measurands.detection_angle.unit == 'degrees'
        assert m.calibration.artefact_values == ((350, 45, -30, 1.039), (400, 45, -30, 1.048), (800, 45,  65, 0.909))
        assert m.calibration.expanded_uncertainty == ((0, 0, 0, 0.017), (0, 0, 0, 0.005), (0, 0, 0, 0.002), (0, 0, 0, 0.002))
        assert m.calibration.coverage_factor == 2
        assert m.calibration.level_of_confidence == 0.95
        assert m.calibration.correlation_matrix == ()
        assert r.category == 'reflectance standard'
        assert r.connection is None
        assert r.description == 'spectralon 99% reflectance standard'
        assert r.is_operable
        assert len(r.maintenances) == 0
        assert r.manufacturer == 'Labsphere'
        assert r.model == 'AS-01159-060, USRS-99-020, BT69E'
        assert r.serial == '0.99'
        assert r.team == 'Light'
        assert r.unique_key == 'AK1'
        assert isinstance(r.user_defined, RecordDict)
        assert len(r.user_defined) == 0

        records = db.records(manufacturer='OMEGA')
        assert len(records) == 1
        r = records[0]
        assert len(r.calibrations) == 2
        c0 = r.calibrations[0]
        assert c0.report_date == datetime.date(2018, 7, 21)
        assert c0.calibration_date == datetime.date(2018, 6, 8)
        assert c0.report_number == 'Humidity/2018/386'
        assert c0.calibration_cycle == 2
        assert len(c0.measurands) == 2
        t = c0.measurands['temperature']
        assert t.type == 'temperature'
        assert t.unit == 'C'
        assert t.conditions.lab_temperature == 21
        assert t.conditions.lab_temperature_uncertainty == 1
        assert t.conditions.lab_temperature_unit == 'C'
        assert t.calibration.minimum == 18
        assert t.calibration.maximum == 24
        assert t.calibration.correction_coefficients == (0.01,)
        assert t.calibration.expanded_uncertainty == 0.13
        assert t.calibration.coverage_factor == 2
        assert t.calibration.level_of_confidence == 0.95
        assert t.calibration.correlation_matrix == ()
        h = c0.measurands['humidity']
        assert h.type == 'humidity'
        assert h.unit == '%rh'
        assert h.conditions.lab_temperature == 21
        assert h.conditions.lab_temperature_uncertainty == 1
        assert h.conditions.lab_temperature_unit == 'C'
        assert h.calibration.minimum == 30
        assert h.calibration.maximum == 85
        assert h.calibration.correction_coefficients == (-9.5, 0.326, -0.00505, 0.0000321)
        assert h.calibration.expanded_uncertainty == 0.9
        assert h.calibration.coverage_factor == 2
        assert h.calibration.level_of_confidence == 0.95
        assert h.calibration.correlation_matrix == ()
        c1 = r.calibrations[1]
        assert c1.report_date == datetime.date(2016, 2, 22)
        assert c1.calibration_date == datetime.date(2016, 1, 20)
        assert c1.report_number == 'Humidity/2016/322'
        assert c1.calibration_cycle == 2
        assert len(c1.measurands) == 2
        t = c1.measurands['temperature']
        assert t.type == 'temperature'
        assert t.unit == 'C'
        assert t.conditions.lab_temperature == 21
        assert t.conditions.lab_temperature_uncertainty == 1
        assert t.conditions.lab_temperature_unit == 'C'
        assert t.calibration.minimum == 17
        assert t.calibration.maximum == 23
        assert t.calibration.correction_coefficients == (0.05,)
        assert t.calibration.expanded_uncertainty == 0.12
        assert t.calibration.coverage_factor == 2
        assert t.calibration.level_of_confidence == 0.95
        assert t.calibration.correlation_matrix == ()
        h = c1.measurands['humidity']
        assert h.type == 'humidity'
        assert h.unit == '%rh'
        assert h.conditions.lab_temperature == 21
        assert h.conditions.lab_temperature_uncertainty == 1
        assert h.conditions.lab_temperature_unit == 'C'
        assert h.calibration.minimum == 30
        assert h.calibration.maximum == 80
        assert h.calibration.correction_coefficients == (-3.44, 0.0487)
        assert h.calibration.expanded_uncertainty == 0.8
        assert h.calibration.coverage_factor == 2
        assert h.calibration.level_of_confidence == 0.95
        assert h.calibration.correlation_matrix == ()
        assert r.category == "Logger"
        assert r.description == "Temperature, relative humidity and dew point reader"
        assert r.is_operable
        assert len(r.maintenances) == 2
        m0 = r.maintenances[0]
        assert m0.date == datetime.date(2019, 3, 24)
        assert m0.comment == 'Nothing changed'
        m1 = r.maintenances[1]
        assert m1.date == datetime.date(2018, 1, 17)
        assert m1.comment == 'ABCDEF ghijkl MNOP qrstuvwxyz'
        assert r.manufacturer == "OMEGA"
        assert r.model == "iTHX-W3-5"
        assert r.serial == "4070777"
        assert r.team == 'Light'
        assert r.unique_key == "137154e9-da33-46c9-b85b-3a1a351969d6"
        assert len(r.user_defined) == 1
        assert r.user_defined['my_custom_key'] == "whatever I want"

        r = db.records(manufacturer='foo')[0]
        assert r.manufacturer == 'foo'
        assert r.model == 'bar'
        assert r.maintenances == tuple()
        assert not r.is_operable
        assert r.serial == 'xyz'
        assert r.calibrations == tuple()
        assert r.team == 'Light'
        assert len(r.user_defined) == 0

        #
        # ConnectionRecords
        #

        assert len(db.connections()) == 3
        assert len(db.connections(backend=Backend.MSL)) == 2
        assert len(db.connections(backend=Backend.PyVISA)) == 1
        assert len(db.connections(manufacturer='foo')) == 1

        c = db.connections(manufacturer='foo')[0]
        assert c is db.equipment['The A Team'].connection
        assert c.manufacturer == 'foo'
        assert c.model == 'bar'
        assert c.address == 'COM7'
        assert c.backend == Backend.MSL
        assert c.serial == 'xyz'
        assert len(c.properties) == 5
        assert c.properties['timeout'] == 5
        assert c.properties['baud_rate'] == 38400
        assert c.properties['termination'] == b'\r\n'
        assert c.properties['parity'] == constants.Parity.ODD
        assert c.properties['data_bits'] == constants.DataBits.SEVEN

        c = db.connections(manufacturer='Company B')[0]
        assert c.manufacturer == 'Company B'
        assert c.model == 'DEF'
        assert c.address == 'TCP::169.254.146.227::9221'
        assert c.backend == Backend.MSL
        assert c.serial == '123456'
        assert isinstance(c.properties, dict)
        assert len(c.properties) == 0

        c = db.connections(manufacturer='Company C')[0]
        assert c.manufacturer == 'Company C'
        assert c.model == 'GHI'
        assert c.address == 'GPIB::22'
        assert c.backend == Backend.PyVISA
        assert c.serial == 'aabbcc'
        assert len(c.properties) == 1
        assert c.properties['termination'] == b'\r'

        #
        # Equipment tag
        #

        assert db.connections(manufacturer='foo')[0] is db.equipment['The A Team'].connection
