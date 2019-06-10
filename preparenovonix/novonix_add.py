import sys
import numpy as np
import preparenovonix.novonix_variables as nv
from preparenovonix.novonix_io import replace_file
from preparenovonix.novonix_io import icolumn
from preparenovonix.novonix_io import read_column
from preparenovonix.novonix_io import get_command
from preparenovonix.novonix_io import get_format


def column_check(infile, col_name, verbose=False):
    """
    Given a cleaned Novonix data file,
    check if the col_name column exists.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    col_name : string
        Name of the column

    verbose : boolean
        True to print information out.

    Returns
    -------
    column_exists : boolean
        True when the column name has been found in the header

    Examples
    ---------
    >>> import preparenovonix.novonix_variables as nv
    >>> import preparenovonix.novonix_add as prep
    >>> prep.column_check('example_data/example_data_prep.csv',nv.col_step)
    True
    """

    icol = icolumn(infile, col_name)
    if icol > -1:
        if verbose:
            print("The file already has the column {}".format(col_name))
        return True
    else:
        return False


def state_check(state):
    """
    Perform tests on the State array

    Parameters
    -----------
    state : array of integers
        State array

    col_name : string
        Name of the column

    Returns
    -------
    answer : boolean
        True when the tests went fine

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> prep.state_check([0,1,2])
    True
    """

    answer = True
    # Check if the first and last state values have adequate values
    if state[0] != 0 or state[-1] != 2:
        answer = False
        print(
            "WARNING novonix_add.state_check \n"
            + "REASON the State column was not properly populated \n"
        )

    # Check that there are the same numbers of 0s and 2s
    izeros = np.where(np.array(state) == 0)
    itwos = np.where(np.array(state) == 2)
    if np.shape(izeros)[1] != np.shape(itwos)[1]:
        answer = False
        print(
            "WARNING novonix_add.state_check \n"
            + "REASON there is a mismath between State=0 and 2 \n"
        )
    return answer


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
    >>> import preparenovonix.novonix_add as prep
    >>> prep.novonix_add_state('example_data/example_data_prep.csv',verbose=True)
    The file example_data/example_data_prep.csv already has a State column
    """

    # Check if the State column already exists
    col_exists = column_check(infile, nv.state_col, verbose=verbose)
    if col_exists:
        return

    # Find the Step Number column
    icol = icolumn(infile, nv.col_step)
    icolt = icolumn(infile, nv.col_tstep)

    # Read the input file
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
        steps = []
        # Read the data adding values to the state
        for il, line in enumerate(ff):
            data.append(line)
            step = line.split(",")[icol]
            steps.append(step)
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
                                    ": Measurement to be nv.ignored",
                                )
                            if state[-3] == -1:
                                # Avoid 2 single measurements in a row
                                state[-3] = -99
                                if verbose:
                                    print(
                                        "WARNING Measurement to be nv.ignored: line=",
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
                            + " \n"
                        )
            last_step = step
            last_t = stime
        state[-1] = 2

        # Check the new column
        check_pass = state_check(state)
        if not check_pass:
            sys.exit("STOP novonix_add.novonix_add_state \n" + str(infile) + " \n")

        # Write the new data to the temporary file
        with open(tmp_file, "a") as tf:
            ii = 0
            for idata in data:
                if state[ii] > -99:
                    new_line = str(idata.rstrip()) + "," + str(state[ii]) + "\n"
                    tf.write(new_line)
                ii += 1

        # Replace the input file by the tmp_file,
        # which should be bigger.
        replace_file(tmp_file, infile, newbigger=True)

        if verbose:
            print("{} contains now a State column".format(infile))
    return


def select_com_val(index):
    """
    Establish the selection statement for the
    one or two possible command values (com_val#)

    Parameters
    -----------
    index : integer
       Index within the above arrays com_val1, nv.com_val2

    Returns
    --------
    sel : string
       String with the selection using either one or two values

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> prep.select_com_val(2)
    'np.logical_or(step == com_val1[index], step == nv.com_val2[index])'
    """
    if nv.com_val2[index] is None:
        sel = "step == nv.com_val1[index]"
    else:
        sel = "np.logical_or(step == nv.com_val1[index], step == nv.com_val2[index])"
    return sel


def read_reduced_protocol(infile, verbose=False):
    """
    Given a cleaned Novonix data file, read the reduced protocol
    if it exists.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes = print out some informative statements

    Returns
    --------
    protocol : list
        List with the reduced protocol.

    protocol_exists : bool
        False if there is no reduced protocol.

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> protocol, continue_reading = prep.read_reduced_protocol(
    'example_data/example_data_prep.csv',verbose=True)
    >>> print(continue_reading)
    False
    """

    protocol_exists = False

    protocol = [nv.protocol_first]

    fw = " "
    with open(infile, "r") as ff:
        while fw != protocol[0].strip():
            line = ff.readline()
            fw = line.strip()
            if fw == "[Data]":
                return protocol, protocol_exists

        while fw != nv.end_rprotocol.strip():
            line = ff.readline()
            fw = line.strip()
            if fw == "[Data]":
                sys.exit(
                    "STOP novonix_add.read_reduced_protocol \n"
                    + "REASON: line [End reduced protocol] not found \n"
                    + "       "
                    + str(infile)
                    + " \n"
                )
            protocol.append(line)
            protocol_exists = True
        return protocol, protocol_exists


def protocol_check(infile, istate, verbose=False):
    """
    Given a cleaned Novonix data file
    and the expected number of different measurements from the header,
    check if the obtained protocol is reasonable given the data.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    istate : int
        Number of measurements derived from reading the protocol

    verbose : boolean
        True to print information statements

    Returns
    -------
    viable_prot : boolean
        True when the reduced protocol is adequate given the data

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> prep.protocol_check('example_data/example_data_prep.csv',103)
    True
    """

    viable_prot = True

    # Test that the number of protocol lines taking into account repetitions.
    step_number = read_column(infile, nv.col_step, outtype="int")
    state_number = read_column(infile, nv.state_col, outtype="int")

    # Find the number of different steps (CC-CV is considered one)
    ind = np.where(
        (state_number < 1) & (step_number != nv.CCCV_CVc) & (step_number != nv.CCCV_CVd)
    )
    uniq_step = np.shape(ind)[1]
    minus1 = np.shape(
        np.where(
            (state_number == -1)
            & (step_number != nv.CCCV_CVc)
            & (step_number != nv.CCCV_CVd)
        )
    )[1]
    if verbose:
        print(
            "Unique steps = {} (step=-1: {}), Steps from protocol = {}".format(
                uniq_step, minus1, istate
            )
        )

    if istate > uniq_step and verbose:
        print(
            "WARNING function reduced_protocol \n"
            + "REASON Mismatched protocol ("
            + str(istate)
            + ") and steps ("
            + str(uniq_step)
            + "): "
            + str(infile)
            + " \n"
        )

    if istate < uniq_step:
        viable_prot = False
        if verbose:
            print(
                "WARNING function reduced_protocol \n"
                + "REASON Less protocol lines ("
                + str(istate)
                + ") than actual steps ("
                + str(uniq_step)
                + "): \n"
                + str(infile)
                + " \n"
            )

    return viable_prot


def rep_info_not_fmtspace(line, fmt_space):
    """
    Given a line from a file with format: fmt_space=False,
    get the number or repetitions and 
    the number of steps that are being repeated

    Parameters
    -----------
    line : string
        Line with data from a Novonix data file

    fmt_space : boolean
        This function only works if this variable is False

    Returns
    -------
    ncount : int
        Number of repetitions in a loop

    nstep : int
        Number or steps in a loop

    unexpected : boolean
        Flag to state if an unexpected syntax has been encountered

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> ncount, nstep, unexpected = prep.rep_info_not_fmtspace('[5: Repeat: 24 time(s) Node count: 4]',False)
    >>> print(ncount, nstep, unexpected)
    24 4 False
    """

    if fmt_space:
        sys.exit("STOP novonix_add.rep_info_not_fmtspace: wrong format")

    unexpected = False
    linestrip = line.strip()
    if ":" in linestrip:
        fw = linestrip.split(":")
        if len(fw) < 4:
            unexpected = True
        else:
            ncount = int(fw[2].strip().split()[0])
            nstep = int(fw[3][:-1])
    else:
        unexpected = True

    return ncount, nstep, unexpected


def create_end_repeat(nstep, iline, protocol, inrepeat):
    """
    Given a line from a file with format:
    add to the protocol an [# : End repeat nstep steps :] line

    Parameters
    -----------
    nstep : int
        Number of steps in a loop

    iline : int
        Counter for protocol lines

    protocol : array of strings
        Array with the reduced protocol

    inrepeat : boolean
        True if inside a loop

    Returns
    -------
    protocol : array of strings
        Array with the reduced protocol,
        with the added new line

    inrepeat : boolean
        Set to False by this function

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> protocol, inrepeat = prep.create_end_repeat(34,1,['Example'],True)
    >>> print(protocol[-1],inrepeat)
    [0 : End Repeat 34 steps :]
     False
    """

    new_line = "[" + str(iline - 1) + " : End Repeat " + str(nstep) + " steps :"
    protocol.append(new_line + "] \n")

    inrepeat = False

    return protocol, inrepeat


def create_reduced_protocol(infile, verbose=False):
    """
    Given a Novonix data file, get a reduced protocol
    with one command per line.

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes = print out some informative statements

    Returns
    --------
    protocol : list
        List with the reduced protocol

    viable_prot : bool
        False if there was a problem creating the reduced protocol.

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> protocol, viable_prot = prep.create_reduced_protocol('example_data/example_data_prep.csv',verbose=True)
    >>> print(viable_prot)
    True
    >>> print(protocol[0],protocol[-1])
    [Reduced Protocol]
     [End Reduced Protocol]
    """

    # Read the reduced protocol if it already exists
    protocol, protocol_exists = read_reduced_protocol(infile, verbose=verbose)
    if protocol_exists:
        return protocol, protocol_exists

    # Initialize the protocol array
    protocol = [nv.protocol_first]

    # Header line counter
    ih = 0

    # Create the reduced protocol (if it does not already exist)
    with open(infile, "r") as ff:
        # Read until the protocol starts
        for line in ff:
            ih += 1
            if "[Protocol]" in line:
                break

        # Read until the first character is '[' and compare to the commands
        continue_reading = True
        while continue_reading:
            line = ff.readline()
            ih += 1

            if line[0] == "[":
                # Skip the operating limits if present
                if line.split()[0] != "[Protocol" and line.split()[0] != "[End":
                    continue_reading = False

        # Establish which format is this file
        fmt_space, commands = get_format(line)

        # Set counters to 0 for the number of lines, steps,
        # 'State' blocks (0,1,...,1,2), commands and subcommands
        iline = 0
        new_line = " "
        istep = 0
        nstep = 0
        inrepeat = False
        istate = 0
        command = " "
        isub = 0
        doneendrepeat = False

        # Read until the end of the protocol
        while "[End Protocol]" not in line:
            command = get_command(line, fmt_space)

            if command in commands or command.split()[0] == "Repeat":
                iline += 1
                if iline > 1 and not doneendrepeat:
                    # Append the new line
                    protocol.append(new_line + "] \n")
                    new_line = " "

                    # Create an 'End Repeat line if needed
                    if istep == nstep and inrepeat and not doneendrepeat:
                        iline += 1
                        protocol, inrepeat = create_end_repeat(
                            nstep, iline, protocol, inrepeat
                        )
                        new_line = " "
                doneendrepeat = False

                # Get the number of repetitions and repeated steps
                if command.split()[0] == "Repeat":
                    if inrepeat:
                        sys.exit(
                            "STOP novonix_add.create_reduced_protocol \n"
                            + "    at header line: "
                            + str(ih)
                            + " \n"
                            + "REASON code not set to handle nested loops \n"
                            + "       "
                            + str(infile)
                            + " \n"
                        )

                    # Get the number of repetitions and steps within the loop
                    unexpected = False
                    if fmt_space:
                        line = ff.readline()
                        ih += 1
                        fw = line.strip()
                        if fw[1:-1].split()[0] == "Repeat":
                            ncount = int(fw[1:-1].split()[2])
                        else:
                            unexpected = True
                        line = ff.readline()
                        ih += 1
                        fw = line.strip()
                        if fw[1:-1].split()[0] == "Step":
                            nstep = int(fw[1:-1].split()[2])
                        else:
                            unexpected = True
                    else:
                        ncount, nstep, unexpected = rep_info_not_fmtspace(
                            line, fmt_space
                        )

                    if unexpected:
                        sys.exit(
                            "STOP novonix_add.create_reduced_protocol \n"
                            + "REASON unexpected protocol syntax \n"
                            + "       "
                            + str(infile)
                            + " \n"
                        )

                    new_line = (
                        "[" + str(iline) + " : Repeat " + str(ncount) + " times :"
                    )
                    istep = 0
                    inrepeat = True
                else:
                    if inrepeat:
                        istep += 1
                        istate = istate + ncount
                    else:
                        istate += 1

                    new_line = (
                        "[" + str(iline) + " : " + command.replace(" ", "_") + " : "
                    )

            elif inrepeat and (
                command == nv.increment1
                or command == nv.increment1.replace(" ", "_")
                or command == nv.increment2
                or command == nv.increment2.replace(" ", "_")
            ):
                # Substract any Increment step
                nstep = nstep - 1

            else:
                # Append subcommands without brackets,
                # separated by semicoloms
                isub += 1
                subcommand = command

                if subcommand not in nv.ignore:
                    if isub == 1:
                        new_line = new_line + subcommand
                    else:
                        new_line = new_line + ";" + subcommand

                if subcommand.strip().casefold() == nv.endrepeat.casefold():
                    # Append the last line
                    protocol.append(new_line + "] \n")
                    iline += 1

                    # Create an 'End Repeat line for files with fmt_space=True
                    # which have an endrepeat statement
                    protocol, inrepeat = create_end_repeat(
                        nstep, iline + 1, protocol, inrepeat
                    )

                    new_line = " "
                    doneendrepeat = True

            # Continue reading
            line = ff.readline()
            ih += 1

        # Add last line if not done already
        ilast = int(protocol[-1].split()[0].split("[")[1])

        if iline > ilast:
            protocol.append(new_line + "] \n")

            # Create an 'End Repeat line if needed
            if istep == nstep and inrepeat:
                new_line = (
                    "[" + str(iline + 1) + " : End Repeat " + str(nstep) + " steps :"
                )
                protocol.append(new_line + "] \n")
                new_line = " "

        protocol.append(nv.end_rprotocol)

        # Test the obtained protocol
        viable_prot = protocol_check(infile, istate, verbose=verbose)

    return protocol, viable_prot


def novonix_add_loopnr(infile, verbose=False):
    """
    Given a cleaned Novonix data file, it adds a 'Loop number' column,
    with monotonically increasing numbers and
    the protocol line corresponding to a given measurement.

    Measurements that are not being repeated are assinged: Loop number=0.

    This values are determined by the change in the 'State' and
    the protocol description in the header

    Parameters
    -----------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes = print out some informative statements

    Notes
    -----
    This code returns a Novonix file with two extra columns.

    Examples
    ---------
    >>> import preparenovonix.novonix_add as prep
    >>> prep.novonix_add_loopnr('example_data/example_data_prep.csv',verbose=True)
    The file already has the column Loop number
    """

    # Check if the file already has the new Loop column
    col_exists = column_check(infile, nv.loop_col, verbose=verbose)
    if col_exists:
        return

    # Get the reduced protocol as a list
    protocol, viable_prot = create_reduced_protocol(infile, verbose=verbose)

    # Read the Step_Number column
    steps = read_column(infile, nv.col_step, outtype="int")

    # Read the States and the set of measurements for a single state
    states = read_column(infile, nv.state_col, outtype="int")
    izeros, = np.where(np.logical_or(states == 0, states == -1))
    itwos, = np.where(np.logical_or(states == 2, states == -1))

    linenr = np.zeros(shape=len(steps), dtype=int)
    linenr.fill(-999.0)
    loopnr = np.zeros(shape=len(steps), dtype=int)
    loopnr.fill(-999.0)

    if viable_prot:
        loopnr.fill(0)

        # Prepare to loop over the protocol lines
        prot = protocol[1:-1]
        iprot = 0
        inrepeat = False
        com_repeat = []
        ntimes = 0
        itimes = 0
        iloop = 0
        last_step = -1

        # Loop over the measurement sets
        for iz, it in zip(izeros, itwos):
            # Step of the Data Subset
            step = steps[iz]

            # Read protocol line
            continue_reading = True
            while continue_reading:
                command = prot[iprot].split(":")[1].strip()
                if command.split(" ")[0].strip() == "Repeat":
                    inrepeat = True
                    com_repeat = []
                    iloop += 1
                    itimes = 0
                    irstep = 0
                    ntimes = int(command.split(" ")[1].strip())

                    iprot += 1
                    first_rep = iprot + 1
                    firstend = True

                elif command.split(" ")[0].strip() == "End":
                    nrstep = int(command.split(" ")[2].strip())
                    if firstend:
                        irstep = 0
                        itimes += 1
                        iloop += 1
                        firstend = False

                    # Check that the array of repeated steps has the expected lenght
                    if len(com_repeat) != nrstep:
                        sys.exit(
                            "STOP function novonix_add_loopnr \n"
                            + "REASON array of repeated steps has an unexpected length \n"
                            + "       "
                            + str(len(com_repeat))
                            + " != "
                            + str(nrstep)
                            + " \n"
                            + "       "
                            + str(infile)
                            + " \n"
                        )

                    # Repeated commands
                    index = nv.com_prot.index(com_repeat[irstep])
                    sel = select_com_val(index)
                    if sel:
                        if (step == nv.CCCV_CVc or step == nv.CCCV_CVd) and (
                            last_step == nv.CCCV_CCc or last_step == nv.CCCV_CCd
                        ):
                            # 1 protocol line for CC-CV
                            last_step = -1
                            irstep = irstep - 1

                        # Compare the protocol and step values
                        linenr[iz : it + 1] = first_rep + irstep
                        loopnr[iz : it + 1] = iloop
                        continue_reading = False

                    # Adequately deal with the reduced protocol counters
                    if itimes == ntimes - 1 and irstep == nrstep - 1:
                        # Last command of the last repetition: reset
                        iprot += 1
                        inrepeat = False
                        itimes = 0
                        ntimes = 0
                        nrstep = 0
                        first_rep = 0
                    elif itimes < ntimes - 1 and irstep == nrstep - 1:
                        # Last command within a repetition
                        irstep = 0
                        itimes += 1
                        iloop += 1
                    else:
                        irstep += 1

                elif command in nv.com_prot[:-1]:
                    index = nv.com_prot.index(command)
                    sel = select_com_val(index)
                    if sel:
                        if (step == nv.CCCV_CVc or step == nv.CCCV_CVd) and (
                            last_step == nv.CCCV_CCc or last_step == nv.CCCV_CCd
                        ):
                            # 1 protocol line for CC-CV
                            last_step = -1
                            iprot = iprot - 1
                        else:
                            if inrepeat:
                                com_repeat.append(command)

                        linenr[iz : it + 1] = iprot + 1
                        if inrepeat:
                            loopnr[iz : it + 1] = iloop
                        continue_reading = False

                    iprot += 1
                    if iprot == len(prot):
                        continue_reading = False
                else:
                    sys.exit(
                        "STOP function novonix_add_loopnr \n"
                        + "REASON unexpected command in reduced protocol \n"
                        + "       "
                        + str(infile)
                        + " \n"
                    )
            last_step = step

    # Create a temporary file with the new header
    header = []
    fw = "fw"
    tmp_file = "tmp.csv"
    with open(infile, "r") as ff:
        # Read until the line with [End Protocol]
        while fw != "[Data]":
            line = ff.readline()
            header.append(line)
            fw = line.split()[0]

        # Create a temporary file with the header as it was
        with open(tmp_file, "w") as tf:
            for item in header[:-1]:
                tf.write(str(item))

        # Add the reduced protocol
        with open(tmp_file, "a") as tf:
            for item in protocol:
                tf.write(str(item))
            # Add [Data] line
            tf.write(str(header[-1]))

        # Read the column names and add the 'Loop' and 'Line'
        line = ff.readline()
        new_head = str(line.rstrip()) + ", " + nv.line_col + ", " + nv.loop_col + " \n"
        with open(tmp_file, "a") as tf:
            tf.write(str(new_head))

        # Write the data + 2 new columns in the temporary file
        for ii, line in enumerate(ff):
            # Write the new data to the temporary file
            with open(tmp_file, "a") as tf:
                new_line = (
                    line.rstrip() + "," + str(linenr[ii]) + "," + str(loopnr[ii]) + "\n"
                )
                tf.write(new_line)

        # Replace the input file by the tmp_file,
        # which should be bigger.
        replace_file(tmp_file, infile, newbigger=True)

        if verbose:
            print(
                "{} contains now the columns Loop number and Protocol line".format(
                    infile
                )
            )

    return
