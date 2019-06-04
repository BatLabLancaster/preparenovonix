import os.path
from pathlib import Path
import numpy as np
import novonix_variables as nv


def file_name(file_name, overwrite=False):
    # Extract the path and file name
    dirname, fname = os.path.split(os.path.abspath(file_name))

    # Modify the slashes in the input path if needed
    file_to_open = Path(dirname) / fname

    if not overwrite:
        root = fname.split(".")[0]
        ending = fname.split(".")[1]
        fname = root + "_prep." + ending
        # If *prep* file already exists, it will be replaced.
        copy(infile, os.path.join(dirname, fname))
        return infile

    copy(infile, os.path.join(dirname, fname))
    return infile


def isnovonix(infile):
    """
    Given a data file, check if it exists and
    if looks like a Novonix file, allowing for blank lines
    and commas after the commands due to having open the file in Excel

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    Returns
    --------
    answer : boolean
        Yes=the file seems to be a Novonix file

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> prep.isnovonix('example_data/example_data.csv')
    True
    """

    answer = True

    # Test if the file exists
    if not os.path.isfile(infile):
        answer = False
        print(
            "STOP function isnovonix \n"
            + "REASON Input file not found: "
            + str(infile)
            + " \n"
        )
        return answer
    else:
        with open(infile, "r") as ff:
            # Read until different header statement
            keyws = ["Summary", "Novonix", "Protocol", "Data"]
            for keyw in keyws:
                for line in ff:
                    if line.strip():
                        char1 = line.strip()[0]
                        if char1 in nv.numberstr:
                            answer = False
                            print(
                                "STOP function isnovonix \n"
                                + "REASON Reached the end of the input file \n"
                                + "       "
                                + str(infile)
                                + ", \n"
                                + "       without the "
                                + keyw
                                + " entry."
                            )
                            return answer
                        else:
                            if keyw in line:
                                break

            # Read until the data starts
            for line in ff:
                if line.strip():
                    char1 = line.strip()[0]
                    if char1 in nv.numberstr:
                        break
                    else:
                        last_line = line.strip()

            # From the data header, read the column names
            colnames = last_line.split(",")

            # Remove triling blancks and end of lines
            colnames = [x.strip() for x in colnames]

            # Check the existance of the "Step Number" column
            if nv.col_step not in colnames:
                answer = False
                print(
                    "STOP function isnovonix \n"
                    + 'REASON No "Step Number" colum found in input file \n'
                    + "       "
                    + str(infile)
                    + " \n"
                )
                return answer

            # Check the existance of the "Step time" column
            if nv.col_tstep not in colnames:

                answer = False
                print(
                    "STOP function isnovonix \n"
                    + 'REASON No "Step Time" colum found in input file \n'
                    + "       "
                    + str(infile)
                    + " \n"
                )
                return answer

    return answer


def icolumn(infile, column_name):
    """
    Given a Novonix data file, find the column position of the
    given column_name

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    column_name : string
        Name of the column name to find

    icolumn : integer
        icolumn = -1 : the column has not been found.
        If icolumn > -1: icolumn is the index of the column.

    Returns
    --------
    icol : integer
       Position of the column with name 'column_name',
       in the range form 0 to the number of columns - 1

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> prep.icolumn('example_data/example_data.csv','Step Number')
    2
    """

    icol = -1

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(infile)
    if not answer:
        sys.exit("STOP Input not from Novonix, {}".format(infile))

    with open(infile, "r") as ff:
        # Read until the line with [Data]
        for line in ff:
            if "[Data]" in line:
                break

        # From the data header, read the column names
        line = ff.readline()
        colnames = line.split(",")

        # Find the position of the given column name
        ii = 0
        for col in colnames:
            if column_name == col.strip():
                icol = ii
                return icol
            ii += 1

    return icol


def read_column(infile, column_name, outtype="float"):
    """
    Given a Novonix data file, read a column as an array of the
    type given in the variable astype.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    column_name : string
        Name of the column to be read

    outtype : string
        Type of data of the column to be read

    Returns
    --------
    column_data : numpy array of the given type
        Column of interest read as a str

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> col = prep.read_column('example_data/example_data_prep.csv',
    'Step Number',outtype='int')

    >>>> print(col[0])
    0
    """

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(infile)
    if not answer:
        sys.exit("STOP Input not from Novonix, {}".format(infile))

    # Initialise empty list
    column_data = []

    with open(infile, "r") as ff:
        # Read until the line with [Data]
        for line in ff:
            if "[Data]" in line:
                break

        # Read the column names
        line = ff.readline()
        colnames = line.split(",")

        # Find the position of the given column name
        ii = -1
        for col in colnames:
            ii += 1
            if column_name == col.strip():
                icolumn = ii
                break

        # Read the column of interest
        for line in ff:
            val = line.split(",")[icolumn].rstrip()
            column_data.append(val)

        # Transform the list into a numpy array
        column_data = np.array(column_data)

        column = column_data.astype(getattr(np, outtype))
    return column
