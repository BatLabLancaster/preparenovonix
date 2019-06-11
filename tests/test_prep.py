import os
from shutil import copy
import preparenovonix.novonix_prep as prep

exfile = "example_data/example_data.csv"


def test_prepare_novonix():
    ff = "dumfile.csv"
    ffout = "dumfile_prep.csv"
    copy(exfile, ff)
    assert os.path.isfile(ff) is True
    prep.prepare_novonix(
        ff, addstate=True, lprotocol=True, overwrite=False, verbose=True
    )
    assert os.stat(ff).st_size > os.stat(ffout).st_size
    os.remove(ff)
    os.remove(ffout)
