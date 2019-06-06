import sys
import numpy as np
import preparenovonix.novonix_variables as nv
from preparenovonix.novonix_io import get_infile
from preparenovonix.novonix_io import icolumn
from preparenovonix.novonix_io import isnovonix
from preparenovonix.novonix_add import create_reduced_protocol
from preparenovonix.novonix_add import novonix_add_loopnr
from preparenovonix.novonix_add import novonix_add_state
from preparenovonix.novonix_clean import cleannovonix


def prepare_novonix(
    file_to_open, addstate=False, lprotocol=False, overwrite=False, verbose=False
):
    """
    Given a Novonix data file, it prepare it to be handled.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    addstate : boolean
        Yes = add a State column

    lprotocol : boolean
        Yes = add to the initial header a 'reduced' protocol with a step per line and add lines with the loop number and protocol lines

    overwrite: boolean
        Yes : overwrite the input file
        No  : a new file will be created, appending '_prep' at the end of the
              original file file

    verbose : boolean
        Yes = print out some informative statements


    Notes
    -----
    This function returns a clean Novonix file with, possibly,
    3 extra columns.

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> prep.prepare_novonix('example_data/example_data.csv',addstate=True,lprotocol=True,overwrite=False,verbose= False)
    File example_data_prep.csv has been prepared.
    """

    # Get the input file to work on
    infile, fname = get_infile(file_to_open, overwrite=overwrite)

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(infile)
    if not answer:
        sys.exit("STOP Input not from Novonix, {}".format(infile))

    # Clean the Novonix file
    cleannovonix(infile)

    if addstate:
        # Check if the file has a State column and if not, create it
        novonix_add_state(infile, verbose=verbose)

    if lprotocol:
        # Check if the file has a Loop number and Protocol line columns
        # and if not, create it
        novonix_add_loopnr(infile, verbose=verbose)

    print("File {} has been prepared.".format(fname))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prepare_novonix(
            sys.argv[1], addstate=True, lprotocol=True, overwrite=False, verbose=True
        )
