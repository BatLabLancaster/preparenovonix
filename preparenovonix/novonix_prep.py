import sys, os
import numpy as np
from shutil import move, copy
from .protocol import create_reduced_protocol
import novonix_variables as nv
from novonix_io import icolumn

"""
A python module to add information to the Novonix data.
"""


def cleannovonix(infile):
    """
    Given a Novonix file remove blank lines, correct the header
    and remove failed tests if needed.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    Notes
    -----
    This code returns a cleaned Novonix file

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> prep.cleannovonix('example_data/example_data_prep.csv')
    """

    summary = "[Summary]"

    # Check if there are unfinished tests
    ntests = 0
    with open(infile, "r") as ff:
        for line in ff:
            if line.strip():  # Jump empty lines
                if summary in line:
                    # Count failed tests for each start of file
                    ntests += 1
    if ntests > 1:
        # Find the capacity colum
        icapacity = icolumn(infile, nv.col_capacity)

    # Start reading the last test
    # Remove blank lines if present in the header
    itest = 0
    header = []
    lastline = " "
    last_capacity = 0.0
    with open(infile, "r") as ff:
        for line in ff:
            if line.strip():
                if summary in line:
                    itest += 1

                    if ntests > 1 and itest > 1:
                        # Add last capacity of each failed test
                        last_capacity = last_capacity + float(
                            lastline.split(",")[icapacity]
                        )

                    if itest == ntests:
                        header.append(summary + " \n")
                        break
                lastline = line

        # Read until the line with [Data]
        for line in ff:
            if line.strip():
                char1 = line.strip()[0]
                if char1 == "[":
                    cleanhead = line.split("]")
                    header.append(cleanhead[0] + "] \n")
                    if cleanhead[0] == "[Data":
                        break
                else:
                    header.append(line)

        # From the data header, read the column names
        for line in ff:
            if line.strip():
                colnames = line.split(",")
                break

        # Remove triling blancks and end of lines
        colnames = [x.strip() for x in colnames]

        # Check that the number of data columns matches the header
        line_data1 = ff.readline()
        data = line_data1.split(",")
        diff = len(data) - len(colnames)

        if diff > 0:
            # Add dum headers
            dums = ""
            for idiff in range(diff):
                dums = dums + ",dum" + str(idiff)

                new_head = str(line.rstrip()) + dums + " \n"
            header.append(new_head)

        elif diff < 0:
            sys.exit(
                "STOP function cleannovonix \n"
                + "REASON less data columns than header names \n"
                + "       "
                + str(infile)
                + " \n"
            )
        else:
            header.append(line)

        # Create a temporary file without blanck lines
        # and new header if needed
        tmp_file = "tmp.csv"
        with open(tmp_file, "w") as tf:
            for item in header:
                tf.write(str(item))

        # Append the data
        with open(tmp_file, "a") as tf:
            # Write the first data row
            if ntests > 1:
                # Modify the Capacity column in case of failed tests
                new_capacity = float(data[icapacity]) + float(last_capacity)
                data[icapacity] = str(new_capacity)

                new_line = data[0]
                for col in data[1:]:
                    new_line = new_line + "," + col
                tf.write(new_line)
            else:
                tf.write(line_data1)

            # Write the rest of the data
            for line in ff:
                if ntests > 1:
                    # Modify the Capacity column in case of failed tests
                    columns = line.split(",")
                    new_capacity = float(columns[icapacity]) + float(last_capacity)
                    columns[icapacity] = str(new_capacity)

                    new_line = columns[0]
                    for col in columns[1:]:
                        new_line = new_line + "," + col
                    tf.write(new_line)
                else:
                    tf.write(line)

        # Replace the input file with the new one
        move(tmp_file, infile)
    return


def novonix_add_state(infile, verbose=False):
    """
    Given a cleaned Novonix data file, it adds a 'State' column,
    which mimimcs Basytec format with:

    0 = Start of a measurement type (charge/discharge, etc)
    1 = Regular data point (measuring, no mode change)
    2 = End of cycle (last point of the measurement)

    This values are determined by the change in the 'Step Number' from Novonix
    and the 'Step time', which goes to 0 with each new 'Step'.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes : print out some informative statements

    Notes
    -----
    This code returns a Novonix file with an extra 'State' column.

    Examples
    ---------
    >>>> import pycode.novonix_add as prep

    >>>> prep.novonix_add_state('example_data/example_data_prep.csv',verbose=True)
    The file example_data/example_data_prep.csv already has a State column
    """

    # Check if the file already has the new State column
    icol = icolumn(infile, nv.state_col)
    if icol > -1:
        if verbose:
            print("The file {} already has a State column".format(infile))
        return

    # Find the Step Number column
    icol = icolumn(infile, col_step)
    icolt = icolumn(infile, nv.col_tstep)

    # The file need to have a 'State' column
    header = []
    fw = "fw"
    with open(infile, "r") as ff:
        # Read until the line with [Data]
        for line in ff:
            header.append(line)
            fw = line.rsplit()
            if fw[0] == "[Data]":
                break

        # Read the column names and add the 'State' one
        line = ff.readline()
        new_head = str(line.rstrip()) + ", " + nv.state_col + " \n"
        header.append(new_head)

        # Create a temporary file with the new header
        tmp_file = "tmp.csv"
        ihead = 0
        with open(tmp_file, "w") as tf:
            for item in header:
                tf.write(str(item))
                ihead += 1

        # The State column
        state = []
        data = []
        last_step = -99  # Create a starting last state value
        last_t = 99.0  # Create a starting step time value
        stnv.eps = []
        # Read the data adding values to the state
        for il, line in enumerate(ff):
            data.append(line)
            step = line.split(",")[icol]
            stnv.eps.append(step)
            stime = float(line.split(",")[icolt])
            if step == last_step and stime > last_t:
                state.append(1)
            else:
                state.append(0)

                # Change the previous value
                if len(state) > 1:
                    if state[-2] == 0:
                        if last_t < nv.eps:
                            # Single measurement
                            state[-2] = -1
                        else:
                            # Jump lines affected by software bug and
                            # 2 single measurements in a row
                            # (this can happen when current overshoots)
                            state[-2] = -99
                            if verbose:
                                # Line count starts with 1, thus (il+1)
                                print(
                                    "WARNING line=",
                                    str(il + ihead),
                                    ", last step time=" + str(last_t),
                                    ": Measurement to be ignored",
                                )
                            if state[-3] == -1:
                                # Avoid 2 single measurements in a row
                                state[-3] = -99
                                if verbose:
                                    print(
                                        "WARNING Measurement to be ignored: line=",
                                        str(il - 1 + ihead),
                                        ", last step time=" + str(last_t),
                                    )

                    elif state[-2] == 1:
                        state[-2] = 2
                    else:
                        sys.exit(
                            "STOP function novonix_add_state \n"
                            + "REASON unexpected state \n"
                            + "      "
                            + str(infile)
                        )
            last_step = step
            last_t = stime
        state[-1] = 2

        # Check if the first and last state values have adequate values
        if state[0] != 0 or state[-1] != 2:
            sys.exit(
                "STOP function novonix_add_state \n"
                + "REASON the State column was not properly populated \n"
                + "       "
                + str(infile)
            )

        # Check that there are the same numbers of 0s and 2s
        izeros = np.where(np.array(state) == 0)
        itwos = np.where(np.array(state) == 2)
        if np.shape(izeros)[1] != np.shape(itwos)[1]:
            sys.exit(
                "STOP function novonix_add_state \n"
                + "REASON there is a mismath between State=0 and 2 \n"
                + "       "
                + str(infile)
            )

        # Write the new data to the temporary file
        with open(tmp_file, "a") as tf:
            ii = 0
            for idata in data:
                if state[ii] > -99:
                    new_line = str(idata.rstrip()) + "," + str(state[ii]) + "\n"
                    tf.write(new_line)
                ii += 1

        # Check the size of the temporal file compared to the original
        size_original = os.stat(infile).st_size
        size_tmp = os.stat(tmp_file).st_size
        if size_original > size_tmp:
            sys.exit(
                "STOP function novonix_add_state \n"
                + "REASON file with State column is smaller than original file \n"
                + "       "
                + str(infile)
            )

        # Replace the input file with the new one
        move(tmp_file, infile)
        if verbose:
            print("{} contains now a State column".format(infile))

    return


def prepare_novonix(
    infile, addstate=False, lprotocol=False, overwrite=False, verbose=False
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

    # Extract the path and file name
    dirname, fname = os.path.split(os.path.abspath(file_name))

    # Modify the slashes in the input path if needed
    file_to_open = Path(dirname) / fname

    infile = file_name(file_to_open, overwrite=overwrite)

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(file_to_open)
    if not answer:
        sys.exit("STOP Input not from Novonix, {}".format(file_to_open))

    # Clean the Novonix file
    cleannovonix(file_to_open)

    if addstate:
        # Check if the file has a State column and if not, create it
        novonix_add_state(file_to_open, verbose=verbose)

    if lprotocol:
        # Check if the file has a Loop number and Protocol line columns
        # and if not, create it
        novonix_add_loopnr(file_to_open, verbose=verbose)

    print("File {} has been prepared.".format(fname))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prepare_novonix(
            sys.argv[1], addstate=True, lprotocol=True, overwrite=False, verbose=True
        )
