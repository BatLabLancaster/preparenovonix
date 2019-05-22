import preparenovonix.novonix_add as prep
import numpy as np
import pytest

exfile = '../example_data/example_data.csv'
exfile_prep = '../example_data/example_data_prep.csv'

def test_select_com_val():
    one = 'step == com_val1[index]'
    two = 'np.logical_or(step == com_val1[index], step == com_val2[index])'
    assert prep.select_com_val(0) == one
    assert prep.select_com_val(1) == one
    assert prep.select_com_val(2) == two
    assert prep.select_com_val(3) == two
    assert prep.select_com_val(4) == two

def test_isnovonix():
    assert prep.isnovonix(exfile) == True
    assert prep.isnovonix('novonix_add') == False

def test_icolumn():
    assert prep.icolumn(exfile_prep,'Step Number') > -1
    assert prep.icolumn(exfile_prep,'Step Time (h)') > -1

def test_read_column():
    col = prep.read_column(exfile_prep,'Step Number',outtype='int')
    assert len(col) > 1
    assert min(col) > -1

def test_reduced_protocol():
    prot = prep.reduced_protocol(exfile_prep)
    assert len(prot) > 1
