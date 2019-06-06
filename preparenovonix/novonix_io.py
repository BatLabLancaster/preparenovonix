import sys, os.path
import numpy as np
from shutil import move, copy
import preparenovonix.novonix_variables as nv


def after_file_name(file_to_open):
    """
    Given a file name return as:
    [file_to_open root]_prep.[file-to_open_ending]

    Parameters
    ----------
    file_to_open : string
        Name of the input file.

    Returns
    --------
    after_file : string
        Full path to the (new) file.

    Examples
    ---------
    >>> from preparenovonix.novonix_io import after_file_name

    >>>> after_file_name('example_data/example_data.csv')
    """

    # Extract the path and file name
    dirname, fname = os.path.split(os.path.abspath(file_to_open))

    root = fname.split(".")[0]
    ending = fname.split(".")[1]
    fname = root + "_prep." + ending
    after_file = os.path.join(dirname, fname)

    return after_file


def get_infile(file_to_open, overwrite=False):
    """
    Given a file name return it after dealing
    with possible issues with the path  and 
    copy it if the overwrite flag is set to True.

    Parameters
    ----------
    infile_name : string
        Name of the input file.

    overwrite: boolean
        Yes : overwrite the input file
        No  : a new file will be created, appending '_prep' at the end of the
              original file file

    Returns
    --------
    infile : string
        Path to the (new) file.

    fname : string
        File name withouth the path.

    Examples
    ---------
    >>> from preparenovonix.novonix_io import get_infile

    >>>> get_infile('example_data/example_data.csv',overwrite=False)
    """

    # Extract the path and file name
    dirname, fname = os.path.split(os.path.abspath(file_to_open))

    if overwrite:
        infile = os.path.join(dirname, fname)
    else:
        infile = after_file_name(file_to_open)
        # If *prep* file already exists, it will be replaced.
        copy(file_to_open, infile)

    return infile, fname


def isnovonix(infile):
    """
    Given a data file, check if it exists and
    if looks like a Novonix data file, allowing for blank lines
    and commas after the commands due to having open the file in Excel

    Parameters
    ----------
    infile : string
        Name of the input Novonix data file

    Returns
    --------
    answer : boolean
        Yes=the file seems to be a Novonix data file

    Examples
    ---------
    >>>> from preparenovonix.novonix_io import isnovonix

    >>>> isnovonix('example_data/example_data.csv')
    True
    """

    answer = True

    # Test if the file exists
    if not os.path.isfile(infile):
        answer = False
        print(
            "STOP novonix_io.isnovonix \n"
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
                                "STOP novonix_io.isnovonix \n"
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
                    "STOP novonix_io.isnovonix \n"
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
                    "STOP novonix_io.isnovonix \n"
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
        Name of the input Novonix data file

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
    >>>> from preparenovonix.novonix_io import icolumn

    >>>> icolumn('example_data/example_data.csv','Step Number')
    2
    """

    icol = -1

    # Check if the file has the expected structure for a Novonix data file
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
            cs = col.strip()
            if column_name.casefold() == cs.casefold():
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
        Name of the input Novonix data file

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
    >>>> from preparenovonix.novonix_io import read_column

    >>>> col = read_column('example_data/example_data_prep.csv',
    'Step Number',outtype='int')

    >>>> print(col[0])
    0
    """

    # Check if the file has the expected structure for a Novonix data file
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

        # Find the position of the given column name
        icol = icolumn(infile, column_name)
        if icol < 0:
            sys.exit(
                "STOP novonix_io.readcolumn \n"
                + "REASON "
                + column_name
                + " columnn \n"
                + "      not found in "
                + str(infile)
                + " \n"
            )

        # Read the column of interest
        for line in ff:
            val = line.split(",")[icol].rstrip()
            column_data.append(val)

        # Transform the list into a numpy array
        column_data = np.array(column_data)

        column = column_data.astype(getattr(np, outtype))

    return column


def replace_file(newfile, infile, newbigger=False):
    """
    Replace infile by newfile, testing, if adequate,
    if the new file is larger than the older.

    Parameters
    ----------
    newfile : string
        Name of the new file

    infile : string
        Name of the file to be replaced.

    newbigger: boolean
        Yes : test if the newfile is larger than infile.
        No  : simply move the files

    Examples
    ---------
    >>> from preparenovonix.novonix_io import replace_file

    >>>> replace_file("example_data/example_data_prep.csv","example_data/example_data.csv")
    """

    if newbigger:
        # Check that the size of the newfile is
        # bigger than the original infile
        size_original = os.stat(infile).st_size
        size_tmp = os.stat(newfile).st_size
        if size_original > size_tmp:
            sys.exit(
                "STOP novonix_io.replace_file \n"
                + "REASON new file is smaller than the original one \n"
                + "       "
                + str(infile)
            )

    # Replace the input file with the new one
    move(newfile, infile)
    return


def get_format(line):
    """
    Given a file line, establish the format

    Parameters
    -----------
    line : string
        Line of the header

    Returns
    --------
    fmt_space : boolean
        True indicates the  main protocol commands 
        have words separated by spaces, which it is
        assumed to be connected with the presence of a 
        semi-colons in the header lines.

    commands : array of string
        Main protocol commands in the adequate format

    Examples
    ---------
    >>>> import preparenovonix.novonix_io as prep

    >>>> fmt_space, commands = prep.get_format('[0: Open_circuit_storage:]')
    False
    """

    if ":" in line:
        fmt_space = False
        commands = nv.com_prot
    else:
        fmt_space = True
        commands = []
        for com in nv.com_prot:
            newcom = com.replace("_", " ")
            commands.append(newcom)

    return fmt_space, commands


def get_command(line, fmt_space):
    """
    Given a header line, get the possible command

    Parameters
    -----------
    line : string
        Line of the header

    fmt_space : boolean
        Yes = Novonix format with spaces in the commands

    Returns
    --------
    command : string
        Instruction in the header line

    Examples
    ---------
    >>>> import preparenovonix.novonix_io as prep

    >>>> command = prep.get_command('[Open circuit storage]',fmt_space=True)
    Open circuit storage
    """

    command = " "

    fw = line.strip()
    # Find commands ignoring left spaces
    if fmt_space:
        command = fw[1:-1]
    else:
        if ":" in fw:
            command = fw.split(":")[1].strip()
        else:
            command = fw[1:-1]
    return command
