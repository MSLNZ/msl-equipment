from msl.equipment import ConnectionRecord, EquipmentRecord
from msl.equipment.connection_msl import ConnectionMessageBased
from msl.equipment.resources.dmm import dmm_factory


def test_dmm1_group():

    # create a record with a model number that is in the _DMM1 group
    record = EquipmentRecord(model='34465A', connection=ConnectionRecord())
    dmm = dmm_factory(record.connection, ConnectionMessageBased)(record)
    cmd = dmm._cmd

    assert cmd('voltage', ACDC='AC', RANGE=None, RESOLUTION=None) == 'MEASURE:VOLTAGE:AC?'
    assert cmd('voltage', ACDC='DC', RANGE=None, RESOLUTION=None) == 'MEASURE:VOLTAGE:DC?'
    assert cmd('voltage', ACDC='AC', RANGE='AUTO', RESOLUTION=None) == 'MEASURE:VOLTAGE:AC? AUTO'
    assert cmd('voltage', ACDC='DC', RANGE='AUTO', RESOLUTION=None) == 'MEASURE:VOLTAGE:DC? AUTO'
    assert cmd('voltage', ACDC='AC', RANGE=10, RESOLUTION=None) == 'MEASURE:VOLTAGE:AC? 10'
    assert cmd('voltage', ACDC='DC', RANGE=10, RESOLUTION=None) == 'MEASURE:VOLTAGE:DC? 10'
    assert cmd('voltage', ACDC='DC', RANGE=0.001, RESOLUTION=None) == 'MEASURE:VOLTAGE:DC? 0.001'
    assert cmd('voltage', ACDC='DC', RANGE=0.001, RESOLUTION=1e-6) == 'MEASURE:VOLTAGE:DC? 0.001,1e-06'
    assert cmd('voltage', ACDC='DC', RANGE=None, RESOLUTION=1e-6) == 'MEASURE:VOLTAGE:DC?'


def test_dmm2_group():

    # create a record with a model number that is in the _DMM2 group
    record = EquipmentRecord(model='3458A', connection=ConnectionRecord())
    dmm = dmm_factory(record.connection, ConnectionMessageBased)(record)
    cmd = dmm._cmd

    assert cmd('voltage', ACDC='AC', RANGE=None, RESOLUTION=None) == 'FUNC ACV'
    assert cmd('voltage', ACDC='DC', RANGE=None, RESOLUTION=None) == 'FUNC DCV'
    assert cmd('voltage', ACDC='AC', RANGE='AUTO', RESOLUTION=None) == 'FUNC ACV,AUTO'
    assert cmd('voltage', ACDC='DC', RANGE='AUTO', RESOLUTION=None) == 'FUNC DCV,AUTO'
    assert cmd('voltage', ACDC='AC', RANGE=10, RESOLUTION=None) == 'FUNC ACV,10'
    assert cmd('voltage', ACDC='DC', RANGE=10, RESOLUTION=None) == 'FUNC DCV,10'
    assert cmd('voltage', ACDC='DC', RANGE=0.001, RESOLUTION=None) == 'FUNC DCV,0.001'
    assert cmd('voltage', ACDC='DC', RANGE=0.001, RESOLUTION=1e-6) == 'FUNC DCV,0.001,1e-06'
    assert cmd('voltage', ACDC='DC', RANGE=None, RESOLUTION=1e-6) == 'FUNC DCV'
