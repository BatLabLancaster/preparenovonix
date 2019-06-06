import sys
import preparenovonix.novonix_variables as nv
from preparenovonix.novonix_io import replace_file
from preparenovonix.novonix_io import icolumn


summary = "[Summary]"


def count_tests(infile):
    """
    Given a Novonix data file, count the number of tests
    it contains, by looking for the "[Summary]" line
    that starts all Novonix data files.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    Returns
    -------
    ntests : int
       Number of tests found in the file

    Examples
    ---------
    >>>> from preparenovonix.novonix_clean import count_tests

    >>>> count_tests('example_data/example_data.csv')
    2
    """

    ntests = 0
    with open(infile, "r") as ff:
        for line in ff:
            if line.strip():  # Jump empty lines
                if summary in line:
                    # Count failed tests for each start of file
                    ntests += 1
    return ntests


def header_data_columns(head_line, data_cols, header):
    """
    Given a Novonix data file, compare the columns
    according to the data and the header.
    If there are more data columns than implied in the header,
    dummy colum names are added (dum#).
    If there are less data columns than implied in the header,
    the program stops.

    Parameters
    -----------
    head_line : string
        Header line with column names.

    data_cols : array of floats
        First line with data

    header: array of strings
        Header. If needed, this header will be modified.

    Examples
    ---------
    >>>> from preparenovonix.novonix_clean import header_data_columns

    >>>> header = ['# Example header']

    >>>> header_data_columns("a,b",[1,2,3],header)

    >>>> print(header[-1])
    a,b,dum0

    """

    colnames = head_line.split(",")

    # Remove triling blancks and end of lines
    colnames = [x.strip() for x in colnames]

    # Difference between columns in the header and in the data
    diff = len(data_cols) - len(colnames)

    if diff > 0:
        # Add dum headers
        dums = ""
        for idiff in range(diff):
            dums = dums + ",dum" + str(idiff)

            new_head = str(head_line.rstrip()) + dums + " \n"
        header.append(new_head)

    elif diff < 0:
        sys.exit(
            "STOP novonix_clean.header_data_columns \n"
            + "REASON less data columns than header names \n"
        )
    else:
        header.append(head_line)

    return


def capacity_failed_tests(icapacity, ntests, infile):
    """
    Given a Novonix data file, add up the last capacity
    measurement of each failed test in the file.

    Parameters
    -----------
    icapacity: int
        Column position for the capacity

    ntests : int
        Number of tests in the file

    infile : string
        Input file

    Returns
    -------

    last_capacity: float
        Sum of the last capacity measurements for each test 
        before the last one in the file.

    Examples
    ---------
    >>>> from preparenovonix.novonix_clean import capacity_failed_tests

    >>>> capacity_failed_tests(2,"example_data/example_data.csv")
    0.4956497995
    """

    last_capacity = 0.0
    if ntests > 1:
        itest = 0
        lastline = " "
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
                            return last_capacity
                    lastline = line

    return last_capacity


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
    >>>> from preparenovonix.novonix_clean import cleannovonix

    >>>> cleannovonix('example_data/example_data.csv')
    """

    # Count the number of tests
    ntests = count_tests(infile)

    # Find the capacity colum
    icapacity = icolumn(infile, nv.col_capacity)

    # Deal with the capacity of the failed tests
    last_capacity = capacity_failed_tests(icapacity, ntests, infile)

    # Start reading the last test
    # Remove blank lines if present in the header
    itest = 0
    header = []
    with open(infile, "r") as ff:
        for line in ff:
            if line.strip():
                if summary in line:
                    itest += 1
                    if itest == ntests:
                        header.append(summary + " \n")
                        break

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
                break

        # Check that the number of data columns matches the header
        line_data1 = ff.readline()
        data = line_data1.split(",")
        header_data_columns(line, data, header)

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
        replace_file(tmp_file, infile, newbigger=False)
    return
