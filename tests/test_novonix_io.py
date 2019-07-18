import sys
import os
import preparenovonix.novonix_variables as nv
import preparenovonix.novonix_io as prep

exfile = "example_data/example_data.csv"
exfile_prep = "example_data/example_data_prep.csv"


def test_after_file_name():
    after_file = prep.after_file_name("example_data/example_data.csv")
    dirname, fname = os.path.split(os.path.abspath(exfile_prep))
    assert after_file == os.path.join(dirname, fname)


def test_get_infile():
    exprep = "example_data/example_data_prep_prep.csv"
    prep.get_infile(exfile_prep, overwrite=False)
    assert os.stat(exfile_prep).st_size == os.stat(exprep).st_size
    os.remove(exprep)


def test_isnovonix():
    assert prep.isnovonix(exfile) is True
    assert prep.isnovonix("novonix_add") is False


def test_icolumn():
    assert prep.icolumn(exfile_prep, nv.col_step) > -1
    assert prep.icolumn(exfile_prep, nv.col_tstep) > -1
    assert prep.icolumn(exfile_prep, "Random name") == -1


def test_read_column():
    col = prep.read_column(exfile_prep, nv.col_step, outtype="int")
    assert len(col) > 1
    assert min(col) > -1


def test_replace_file():
    longf = "test_l.txt"
    lf = open(longf, "w")
    lf.write("This is a longer file")
    lf.close()
    shortf = "test_s.txt"
    sf = open(shortf, "w")
    sf.write("Short file")
    sf.close()
    prep.replace_file(longf, shortf, newbigger=True)
    assert os.path.isfile(longf) is False
    os.remove(shortf)


def test_get_format():
    fmt_space, commands = prep.get_format("[0: Open_circuit_storage:]")
    assert fmt_space is False
    fmt_space, commands = prep.get_format("[Open circuit storage]")
    assert fmt_space is True


def test_get_command():
    strval = "Open circuit storage"
    assert prep.get_command("[" + strval + "]", fmt_space=True) == strval
    assert prep.get_command("[0 :" + strval + ":]", fmt_space=False) == strval


def test_get_col_names():
    col_names = prep.get_col_names(exfile_prep)
    assert col_names[2] == nv.col_step


def test_get_num_measurements():
    nm = prep.get_num_measurements('example_data/example_data_prep.csv')
    assert nm == 5752
