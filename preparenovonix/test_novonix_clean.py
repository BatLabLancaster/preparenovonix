import os
from shutil import copy
import preparenovonix.novonix_variables as nv
import preparenovonix.novonix_clean as prep


exfile = "example_data/example_data.csv"
exfile_prep = "example_data/example_data_prep.csv"


def test_count_tests():
    ntests = prep.count_tests(exfile)
    assert ntests == 2


def test_header_data_columns():
    header = ["# Example header"]
    prep.header_data_columns("a,b", [1, 2, 3], header)
    lastl = header[-1].strip()
    assert lastl == "a,b,dum0"


def test_capacity_failed_tests():
    capacity = prep.capacity_failed_tests(7, 2, exfile)
    assert abs(capacity - 0.4956498) < nv.eps


def test_cleannovonix():
    ff = "dumfile"
    copy(exfile, ff)
    assert os.path.isfile(ff) is True
    prep.cleannovonix(ff)
    assert os.stat(ff).st_size < os.stat(exfile).st_size
    os.remove(ff)
