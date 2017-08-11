import pytest

from msl.equipment.config import Config


def test_config():

    with pytest.raises(IOError):
        c = Config('does not exist')

