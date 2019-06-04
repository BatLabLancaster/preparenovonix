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
    >>>> import pycode.novonix_add as prep

    >>>> prep.select_com_val(2)
    'np.logical_or(step == com_val1[index], step == nv.com_val2[index])'
    """
    if nv.com_val2[index] is None:
        sel = "step == com_val1[index]"
    else:
        sel = "np.logical_or(step == com_val1[index], step == nv.com_val2[index])"
    return sel


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
    >>>> import pycode.novonix_add as prep

    >>>> prep.novonix_add_loopnr('example_data/example_data_prep.csv',verbose=True)
    The file example_data/example_data_prep.csv already has a Loop number column
    """

    # Check if the file already has the new State column
    icol = icolumn(infile, loop_col)
    if icol > -1:
        if verbose:
            print("The file {} already has a Loop number column".format(infile))
        return

    # Get the reduced protocol as a list
    protocol, viable_prot = create_reduced_protocol(infile, verbose=verbose)

    # Read the Step_Number column
    steps = read_column(infile, col_step, outtype="int")

    # Read the States and the set of measurements for a single state
    states = read_column(infile, state_col, outtype="int")
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
                    index = com_prot.index(com_repeat[irstep])
                    sel = select_com_val(index)
                    if sel:
                        if (step == CCCV_CVc or step == CCCV_CVd) and (
                            last_step == CCCV_CCc or last_step == CCCV_CCd
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

                elif command in com_prot[:-1]:
                    index = com_prot.index(command)
                    sel = select_com_val(index)
                    if sel:
                        if (step == CCCV_CVc or step == CCCV_CVd) and (
                            last_step == CCCV_CCc or last_step == CCCV_CCd
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
        new_head = str(line.rstrip()) + ", " + line_col + ", " + loop_col + " \n"
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

        # Check the size of the temporal file compared to the original
        size_original = os.stat(infile).st_size
        size_tmp = os.stat(tmp_file).st_size
        if size_original > size_tmp:
            sys.exit(
                "STOP function novonix_add_loopnr \n"
                + "REASON new file is smaller than original file \n"
                + "       "
                + str(infile)
            )

        # Replace the input file with the new one
        move(tmp_file, infile)
        if verbose:
            print(
                "{} contains now the columns Loop number and Protocol line".format(
                    infile
                )
            )

    return


protocol_first = "[Reduced Protocol] \n"
end_rprotocol = "[End Reduced Protocol] \n"


def read_reduced_protocol(infile, verbose=False):
    """
    Given a Novonix data file, read the reduced protocol
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

    continue_reading : bool
        False if there was no reduced protocol.

    Examples
    ---------
    >>>> import preparenovonix.protocol as prot

    >>>> protocol, continue_reading = prot.read_reduced_protocol(
    'example_data/example_data_prep.csv',verbose=True)

    >>>> print(continue_reading)
    False
    """

    continue_reading = True

    protocol = [protocol_first]
    print(protocol[0])

    fw = " "
    with open(infile, "r") as ff:
        while fw != protocol[0].strip():
            line = ff.readline()
            fw = line.strip()
            if fw == "[Data]":
                continue_reading = False
                return protocol, continue_reading

        if continue_reading:
            while fw != end_rprotocol.strip():
                line = ff.readline()
                fw = line.strip()
                if fw == "[Data]":
                    sys.exit(
                        "STOP function reduced_protocol \n"
                        + "REASON: line [End reduced protocol] not found \n"
                        + "       "
                        + str(infile)
                        + " \n"
                    )
                protocol.append(line)
            return protocol, continue_reading


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
    >>>> import preparenovonix.protocol as prot

    >>>> protocol, viable_prot = prep.reduced_protocol('example_data/example_data_prep.csv',verbose=True)

    >>>> print(viable_prot)
    True

    >>>> print(protocol[0],protocol[-1])
    [Reduced Protocol]
     [End Reduced Protocol]
    """

    viable_prot = True

    # Read the reduced protocol if it already exists
    protocol, continue_reading = read_reduced_protocol(infile, verbose=verbose)
    if not continue_reading:
        return protocol, viable_prot

    # Initialize the protocol array
    protocol = [protocol_first]

    # Header line counter
    ih = 0

    # Create the reduced protocol (if it does not already exist)
    with open(infile, "r") as ff:
        # Read until the protocol starts
        for line in ff:
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
        if ":" in line:
            fmt_space = False
            commands = com_prot
        else:
            fmt_space = True
            commands = []
            for com in com_prot:
                newcom = com.replace("_", " ")
                commands.append(newcom)

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

        # Read until the end of the protocol
        while "[End Protocol]" not in line:
            fw = line.strip()
            # Find commands ignoring left spaces
            if fmt_space:
                command = fw[1:-1]
            else:
                if ":" in fw:
                    command = fw.split(":")[1].strip()
                else:
                    command = fw[1:-1]

            if command in commands or command.split()[0] == "Repeat":
                iline += 1

                # Add previous line
                if iline > 1:
                    # Append the new line
                    protocol.append(new_line + "] \n")
                    new_line = " "

                    # Create an 'End Repeat line if needed
                    if istep == nstep and inrepeat:
                        new_line = (
                            "["
                            + str(iline)
                            + " : End Repeat "
                            + str(nstep)
                            + " steps :"
                        )
                        protocol.append(new_line + "] \n")
                        new_line = " "

                        iline += 1
                        inrepeat = False

                # Get the number of repetitions and repeated steps
                if command.split()[0] == "Repeat":
                    if inrepeat:
                        sys.exit(
                            "STOP function reduced_protocol \n"
                            + "    at header line: "
                            + str(ih)
                            + " \n"
                            + "REASON code not set to handle nested loops \n"
                            + "       "
                            + str(infile)
                            + " \n"
                        )

                    unexpected = False
                    if fmt_space:
                        line = ff.readline()
                        ih += 1
                        fw = line.strip()
                        if fw[1:-1].split()[0] == "Repeat":
                            ncount = fw[1:-1].split()[2]
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
                        if ":" in fw:
                            ncount = fw.split(":")[2].strip().split()[0]
                        else:
                            unexpected = True
                        if ":" in fw:
                            nstep = int(fw.split(":")[3][:-1])
                        else:
                            unexpected = True

                    if unexpected:
                        sys.exit(
                            "STOP function reduced_protocol \n"
                            + "REASON unexpected protocol syntax \n"
                            + "       "
                            + str(infile)
                            + " \n"
                        )

                    new_line = "[" + str(iline) + " : Repeat " + ncount + " times :"
                    istep = 0
                    inrepeat = True
                else:
                    if inrepeat:
                        istep += 1
                        istate = istate + int(ncount)
                    else:
                        istate += 1

                    new_line = (
                        "[" + str(iline) + " : " + command.replace(" ", "_") + " : "
                    )

            elif inrepeat and (
                command == increment1
                or command == increment1.replace(" ", "_")
                or command == increment2
                or command == increment2.replace(" ", "_")
            ):
                # Substract any Increment step
                nstep = nstep - 1

            else:
                # Append subcommands without brackets,
                # separated by semicoloms
                isub += 1

                subcommand = fw[1:-1]
                if subcommand not in ignore:
                    if isub == 1:
                        new_line = new_line + subcommand
                    else:
                        new_line = new_line + ";" + subcommand

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

        protocol.append(end_rprotocol)

        # Test that the number of protocol lines taking into account repetitions.
        step_number = read_column(infile, col_step, outtype="int")
        state_number = read_column(infile, state_col, outtype="int")
        # Find the number of different steps (CC-CV is considered one)
        ind = np.where(
            (state_number < 1) & (step_number != CCCV_CVc) & (step_number != CCCV_CVd)
        )
        uniq_step = np.shape(ind)[1]
        minus1 = np.shape(
            np.where(
                (state_number == -1)
                & (step_number != CCCV_CVc)
                & (step_number != CCCV_CVd)
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

    return protocol, viable_prot
