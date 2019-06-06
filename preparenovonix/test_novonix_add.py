import os
from shutil import copy
import preparenovonix.novonix_variables as nv
import preparenovonix.novonix_add as prep

exfile = "example_data/example_data.csv"
exfile_prep = "example_data/example_data_prep.csv"


def test_column_cehck():
    assert prep.column_check("example_data/example_data_prep.csv", nv.col_step) is True


def test_state_check():
    assert prep.state_check([0, 1, 2]) is True
    assert prep.state_check([0, 1, 2, 2]) is False


def test_novonix_add_state():
    ff = "dumfile"
    copy(exfile_prep, ff)
    assert os.path.isfile(ff) is True
    prep.novonix_add_state(ff, verbose=True)
    assert os.stat(exfile_prep).st_size <= os.stat(ff).st_size
    os.remove(ff)


def test_select_com_val():
    one = "step == nv.com_val1[index]"
    two = "np.logical_or(step == nv.com_val1[index], step == nv.com_val2[index])"
    assert prep.select_com_val(0) == one
    assert prep.select_com_val(1) == one
    assert prep.select_com_val(2) == two
    assert prep.select_com_val(3) == two
    assert prep.select_com_val(4) == two


def test_read_reduced_protocol():
    protocol, protocol_exists = prep.read_reduced_protocol(exfile_prep, verbose=False)
    assert len(protocol) > 1
    assert protocol_exists is True


def test_protocol_check():
    assert prep.protocol_check("example_data/example_data_prep.csv", 103) is True


def test_create_reduced_protocol():
    prot, viable_prot = prep.create_reduced_protocol(exfile_prep)
    assert len(prot) > 1
    assert viable_prot is True


def test_novonix_add_loopnr():
    ff = "dumfile"
    copy(exfile_prep, ff)
    assert os.path.isfile(ff) is True
    prep.novonix_add_loopnr(ff, verbose=True)
    assert os.stat(exfile_prep).st_size <= os.stat(ff).st_size
    os.remove(ff)
