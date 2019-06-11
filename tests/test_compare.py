import sys, os
from preparenovonix import compare

exfile = "example_data/example_data.csv"
exfile_prep = "example_data/example_data_prep.csv"


def test_plot_vct():
    compare.plot_vct(exfile)
    dirname, fname = os.path.split(os.path.abspath(exfile))
    figname = os.path.join(dirname, "compare_vct.pdf")
    assert os.path.isfile(figname) is True
