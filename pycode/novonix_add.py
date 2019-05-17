import sys, os
import numpy as np
from pathlib import Path
from shutil import move

"""A python module to add information to the Novonix data.

.. moduleauthor:: Violeta Gonzalez-Perez <violegp@gmail.com>

"""
eps = 1.e-5

# Novonix columns
col_step  = 'Step Number'
col_tstep = 'Step Time (h)'
col_capacity = 'Capacity (Ah)'

state_col = 'State (0=Start 1=Regular 2=End -1=Single Measurement)'
loop_col = 'Loop number'
line_col = 'Protocol Line (it refers to the reduced protocol)'

# Commands in Protocols
increment1 = 'Increment the cycle counter'
increment2 = 'Increment cycle counter'

ignore = ['End storage','End charge','End discharge','End repeat',
          increment1,increment2,'End increment',
          'Trip conditions','End trip conditions',
          'Save conditions','End save conditions',
          'Operating limits','End operating limits',
          'Emergency limits','End emergency limits']

com_prot = ['Open_circuit_storage',
            'Constant_current_charge',
            'Constant_current_discharge',
            'CC-CV_charge',
            'CC-CV_discharge',
            'Repeat']

# Novonix step values
OCV = 0
CCc = 1
CCd = 2 #in some cases this is also set to 1
CCCV_CCc = 7
CCCV_CVc = 8
CCCV_CCd = 9
CCCV_CVd = 10

com_val1 = [OCV,CCc,CCd,CCCV_CCc,CCCV_CCd]
com_val2 = [None,None,CCc,CCCV_CVc,CCCV_CVd]

numberstr = ['0','1','2','3','4','5','6','7','8','9','-']

def select_com_val(index):
    '''
    Establish the selection statement for the
    one or two possible command values (com_val#)
    '''
    if (com_val2[index] is None):
        sel = 'step == com_val1[index]'
    else:
        sel = 'np.logical_or(step == com_val1[index], step == com_val2[index])'
    return sel
                
def isnovonix(infile):
    """
    Given a data file, check if it exists and 
    if looks like a Novonix file, allowing for blank lines
    and commas after the commands due to having open the file in Excel

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    answer : boolean
        Yes=the file seems to be a Novonix file
    """

    answer = True
    
    # Test if the file exists
    if(not os.path.isfile(infile)):
        answer = False
        print('STOP function isnovonix \n'+\
              'REASON Input file not found: '+str(infile)+' \n')
        return
    else:
        with open(infile,'r') as ff:
            # Read until different header statement
            keyws = ['Summary','Novonix','Protocol','Data']
            for keyw in keyws:
                for line in ff:
                    if line.strip():
                        char1 = line.strip()[0]
                        if (char1 in numberstr):
                            answer = False
                            print('STOP function isnovonix \n'+\
                                  'REASON Reached the end of the input file \n'+\
                                  '       '+str(infile)+', \n'+\
                                  '       without the '+keyw+' entry.')
                            return
                        else:
                            if (keyw in line):                
                                break

            # Read until the data starts
            for line in ff:
                if line.strip():
                    char1 = line.strip()[0]
                    if (char1 in numberstr):
                        break
                    else:
                        last_line = line.strip()

            # From the data header, read the column names            
            colnames = last_line.split(',')

            # Remove triling blancks and end of lines
            colnames = [x.strip() for x in colnames] 

            # Check the existance of the "Step Number" column
            if (col_step not in colnames):
                answer = False
                print('STOP function isnovonix \n'+\
                      'REASON No "Step Number" colum found in input file \n'+\
                      '       '+str(infile)+' \n')
                return
                
            # Check the existance of the "Step time" column
            if (col_tstep not in colnames):

                answer = False
                print('STOP function isnovonix \n'+\
                      'REASON No "Step Time" colum found in input file \n'+\
                      '       '+str(infile)+' \n')
                return

    return answer

def icolumn(infile,column_name):
    """
    Given a Novonix data file, find the column position of the
    given column_name

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    column_name : string
        Name of the column name to find

    icolumn : integer
        If icolumn > -1
    """

    icol = -1
    
    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(infile)
    if (not answer): sys.exit('STOP Input not from Novonix, {}'.format(file_to_open))

    with open(infile,'r') as ff:
        # Read until the line with [Data]
        for line in ff:
            if ("[Data]" in line):
                break

        # From the data header, read the column names
        line = ff.readline() 
        colnames = line.split(',')
        
        # Find the position of the given column name
        ii = 0 
        for col in colnames:
            if (column_name == col.strip()):
                icol = ii
                return icol
            ii += 1
                
    return icol

def read_column(infile,column_name,outtype='float'):
    """
    Given a Novonix data file, read a column as an array of the
    type given in the variable astype.

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    column_name : string
        Name of the column to be read

    outtype : string
        Type of data of the column to be read

    Output
    ------
    column_data : numpy array of the given type
        Column of interest read as a str
    """

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(infile)
    if (not answer): sys.exit('STOP Input not from Novonix, {}'.format(file_to_open))

    # Initialise empty list
    column_data = []

    with open(infile,'r') as ff:
        # Read until the line with [Data]
        for line in ff:
            if ("[Data]" in line):
                break

        # Read the column names
        line = ff.readline() 
        colnames = line.split(',')

        # Find the position of the given column name
        ii = -1
        for col in colnames:
            ii += 1
            if (column_name == col.strip()):
                icolumn = ii
                break

        # Read the column of interest
        for line in ff:
            val = line.split(',')[icolumn].rstrip()
            column_data.append(val)

        # Transform the list into a numpy array
        column_data = np.array(column_data)

        column = column_data.astype(getattr(np,outtype))
    return column

def cleannovonix(infile,overwrite=False):
    """
    Given a Novonix file remove blank lines, correct the header
    and remove failed tests if needed.

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    overwrite: boolean
        Yes : overwrite the input file
        No  : a new file will be created, appending '_prep' at the end of the
              original file file

    Output:
    -------
    Clened Novonix file
    """

    summary = '[Summary]'
    
    # Check if there are unfinished tests
    ntests = 0
    with open(infile,'r') as ff:
        for line in ff:
            if line.strip(): #Jump empty lines
                if (summary in line):
                    # Count failed tests for each start of file
                    ntests += 1
    if (ntests > 1):
        # Find the capacity colum
        icapacity = icolumn(infile,col_capacity)

    # Start reading the last test
    # Remove blank lines if present in the header
    itest = 0 ; header = [] ; lastline = ' '
    last_capacity = 0.
    with open(infile,'r') as ff:
        for line in ff:
            if line.strip():
                if (summary in line):
                    itest += 1
                    
                    if(ntests > 1 and itest > 1):
                        #Add last capacity of each failed test
                        last_capacity = last_capacity + float(lastline.split(',')[icapacity])

                    if (itest == ntests):
                        line1 = line.strip()
                        header.append(summary+' \n')
                        break
                lastline = line

        # Read until the line with [Data]
        for line in ff:
            if line.strip():
                char1 = line.strip()[0]
                if(char1 == '['):
                    cleanhead = line.split(']')
                    header.append(cleanhead[0]+'] \n')
                    if (cleanhead[0] == '[Data'):
                        break
                else:
                    header.append(line) 

        # From the data header, read the column names
        for line in ff:
            if line.strip():
                colnames = line.split(',')
                break

        # Remove triling blancks and end of lines
        colnames = [x.strip() for x in colnames] 

        # Check that the number of data columns matches the header
        line_data1 = ff.readline()
        data = line_data1.split(',')
        diff = len(data) - len(colnames)

        if(diff>0):
            # Add dum headers
            dums = ''
            for idiff in range(diff):
                dums = dums+',dum'+str(idiff)
                
                new_head = str(line.rstrip())+dums+' \n'
            header.append(new_head)

        elif(diff<0):
            sys.exit('STOP function cleannovonix \n'+\
                     'REASON less data columns than header names \n'+\
                     '       '+str(infile)+' \n')
        else:
            header.append(line)

        # Create a temporary file without blanck lines
        # and new header if needed
        tmp_file = 'tmp.csv'
        with open(tmp_file, 'w') as tf:
            for item in header:
                tf.write(str(item))

        # Append the data
        with open(tmp_file, 'a') as tf:
            # Write the first data row
            if (ntests > 1):
                # Modify the Capacity column in case of failed tests
                new_capacity = float(data[icapacity]) + float(last_capacity)
                data[icapacity] = str(new_capacity)

                new_line = data[0]
                for col in data[1:]:
                    new_line = new_line+','+col
                tf.write(new_line)
            else:
                tf.write(line_data1)

            # Write the rest of the data
            for line in ff:
                if (ntests > 1):
                    # Modify the Capacity column in case of failed tests
                    columns = line.split(',')
                    new_capacity = float(columns[icapacity]) + float(last_capacity)
                    columns[icapacity] = str(new_capacity)

                    new_line = columns[0]
                    for col in columns[1:]:
                        new_line = new_line+','+col
                    tf.write(new_line)
                else:
                    tf.write(line)

        # Replace the input file with the new one
        move(tmp_file,infile)
    return

def novonix_add_state(infile,overwrite=False,verbose=False):
    """
    Given a cleaned Novonix data file, it adds a 'State' column, 
    which mimimcs Basytec format with:

    0 = Start of a measurement type (charge/discharge, etc)
    1 = Regular data point (measuring, no mode change)
    2 = End of cycle (last point of the measurement)

    This values are determined by the change in the 'Step Number' from Novonix
    and the 'Step time', which goes to 0 with each new 'Step'.

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    overwrite: boolean
        Yes : overwrite the input file
        No  : a new file will be created, appending '_prep' at the end of the
              original file file

    verbose : boolean
        Yes : print out some informative statements

    Example
    -------
    $ python novonix_add_state([path to Novonix file],overwrite=False,verbose=True)

    """
    
    # Check if the file already has the new State column
    icol = icolumn(infile,state_col)
    if (icol>-1):
        if verbose:
            print('The file {} already has a State column'.format(infile))
        return

    # Find the Step Number column
    icol = icolumn(infile,col_step)
    icolt = icolumn(infile,col_tstep)

    # The file need to have a 'State' column
    header = [] ; fw = 'fw'
    with open(infile,'r') as ff:
        # Read until the line with [Data]
        for line in ff:
            header.append(line)
            fw = line.rsplit()
            if (fw[0] == "[Data]"):
                break
        
        # Read the column names and add the 'State' one
        line = ff.readline() 
        new_head = str(line.rstrip())+', '+state_col+' \n'
        header.append(new_head)

        # Create a temporary file with the new header
        tmp_file = 'tmp.csv' ; ihead = 0
        with open(tmp_file, 'w') as tf:
            for item in header:
                tf.write(str(item))
                ihead += 1

        # The State column
        state = [] ; data = []
        last_step = -99 # Create a starting last state value
        last_t = 99. # Create a starting step time value
        steps = []
        # Read the data adding values to the state        
        for il,line in enumerate(ff):
            data.append(line)
            step = line.split(',')[icol] ; steps.append(step)
            stime = float(line.split(',')[icolt])
            if (step == last_step and stime > last_t):
                state.append(1)
            else:
                state.append(0)

                # Change the previous value
                if (len(state)>1):
                    if(state[-2] == 0):
                        if (last_t < eps):
                            # Single measurement 
                            state[-2] = -1
                        else:
                            # Jump lines affected by software bug and
                            # 2 single measurements in a row
                            # (this can happen when current overshoots)
                            state[-2] = -99
                            if (verbose):
                                # Line count starts with 1, thus (il+1)
                                print('WARNING line=',str(il+ihead),', last step time='+ str(last_t),': Measurement to be ignored')
                            if (state[-3] == -1):
                                # Avoid 2 single measurements in a row
                                state[-3] = -99
                                if (verbose):
                                    print('WARNING Measurement to be ignored: line=',str(il-1+ihead),', last step time='+ str(last_t))

                    elif(state[-2] == 1):
                        state[-2] = 2
                    else:
                        sys.exit('STOP function novonix_add_state \n'+\
                                 'REASON unexpected state \n'+\
                                 '      '+str(infile))
            last_step = step
            last_t = stime
        state[-1] = 2

        # Check if the first and last state values have adequate values
        if (state[0] != 0 or state[-1] != 2):
            sys.exit('STOP function novonix_add_state \n'+\
                     'REASON the State column was not properly populated \n'+\
                     '       '+str(infile))

        # Check that there are the same numbers of 0s and 2s
        izeros = np.where(np.array(state) == 0)
        itwos  = np.where(np.array(state) == 2)
        if (np.shape(izeros)[1] != np.shape(itwos)[1]):
            sys.exit('STOP function novonix_add_state \n'+\
                     'REASON there is a mismath between State=0 and 2 \n'+\
                     '       '+str(infile))
        
        # Write the new data to the temporary file
        with open(tmp_file, 'a') as tf:
            ii = 0 
            for idata in data:
                if (state[ii]>-99):
                    new_line = str(idata.rstrip())+','+str(state[ii])+'\n'
                    tf.write(new_line)
                ii+= 1

        # Check the size of the temporal file compared to the original
        size_original = os.stat(infile).st_size
        size_tmp = os.stat(tmp_file).st_size
        if (size_original > size_tmp):
            sys.exit('STOP function novonix_add_state \n'+\
                     'REASON file with State column is smaller than original file \n'+\
                     '       '+str(infile))
    
        # Replace the input file with the new one
        move(tmp_file,infile)
        if verbose:
            print('{} contains now a State column'.format(infile))
            
    return

def reduced_protocol(infile,verbose=False):
    """
    Given a Novonix data file, get a reduced protocol 
    with one command per line.

    Input Parameters
    ----------------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes = print out some informative statements

    Output Parameters
    ----------------
    protocol : list
        List with the reduced protocol
    """

    viable_prot = True
    protocol = ['[Reduced Protocol] \n']
    end_rprotocol = '[End Reduced Protocol] \n'    

    # Read the reduced protocol if it is already in place
    continue_reading = True ; fw = ' '
    with open(infile,'r') as ff:
        while (fw != protocol[0].strip()):
            line = ff.readline() ; fw = line.strip()
            if (fw == "[Data]"):
                continue_reading = False
                break
            
        if (continue_reading):
            while (fw != end_rprotocol.strip()):
                line = ff.readline() ; fw = line.strip()
                print(fw)
                if (fw == "[Data]"):
                    sys.exit('STOP function reduced_protocol \n'+\
                             'REASON: line [End reduced protocol] not found \n'+\
                             '       '+str(infile)+' \n')
                protocol.append(line)
            protocol.append(end_rprotocol)
            return protocol, viable_prot

    # Create the reduced protocol (if it does not already exist)
    with open(infile,'r') as ff:
        # Read until the protocol starts
        for line in ff:
            if ("[Protocol]" in line):
                break

        # Read until the first character is '[' and compare to the commands
        continue_reading = True
        while (continue_reading):
            line = ff.readline() 

            if (line[0] == '['):
                # Skip the operating limits if present
                if (line.split()[0] != '[Protocol' and
                    line.split()[0] != '[End'):
                    continue_reading = False

        # Establish which format is this file
        if (':' in line):
            fmt_space = False ; commands = com_prot
        else:
            fmt_space = True
            commands = []
            for com in com_prot:
                newcom = com.replace('_',' ')
                commands.append(newcom)

        # Set counters to 0 for the number of lines, steps,
        # 'State' blocks (0,1,...,1,2), commands and subcommands
        iline = 0 ; new_line = ' '
        istep = 0 ; nstep = 0 ; inrepeat = False
        istate = 0
        command = ' ' ; isub = 0 

        # Read until the end of the protocol
        while ('[End Protocol]' not in line):
            fw = line.strip()
            # Find commands ignoring left spaces
            if (fmt_space):
                command = fw[1:-1]
            else:
                try:
                    command = fw.split(':')[1].strip()
                except:
                    command = fw[1:-1]

            if (command in commands or command.split()[0] == 'Repeat'):
                iline += 1
                
                # Add previous line
                if (iline>1):                        
                    # Append the new line
                    protocol.append(new_line+'] \n')
                    new_line = ' '

                    # Create an 'End Repeat line if needed
                    if (istep == nstep and inrepeat): 
                        new_line = '['+str(iline)+' : End Repeat '+str(nstep)+' steps :'
                        protocol.append(new_line+'] \n')
                        new_line = ' '
                        
                        iline += 1
                        inrepeat = False

                # Get the number of repetitions and repeated steps
                if (command.split()[0] == 'Repeat'):
                    if (inrepeat):
                        sys.exit('STOP function reduced_protocol \n'+\
                                 'REASON code not set to handle nested loops \n'+\
                                 '       '+str(infile)+' \n')

                    unexpected = False
                    if (fmt_space):
                        line = ff.readline() ; fw = line.strip()
                        if (fw[1:-1].split()[0] == 'Repeat'):
                            ncount = fw[1:-1].split()[2]
                        else:
                            unexpected = True
                        line = ff.readline() ; fw = line.strip()
                        if (fw[1:-1].split()[0] == 'Step'):
                            nstep = int(fw[1:-1].split()[2])
                        else:
                            unexpected = True
                    else:
                        try:
                            ncount = fw.split(':')[2].strip().split()[0]
                        except:
                            unexpected = True
                        try:
                            nstep = int(fw.split(':')[3][:-1])
                        except:
                            unexpected = True

                    if unexpected:
                        sys.exit('STOP function reduced_protocol \n'+\
                                 'REASON unexpected protocol syntax \n'+\
                                 '       '+str(infile)+' \n')

                    new_line = '['+str(iline)+' : Repeat '+\
                        ncount+' times :'
                    istep = 0 ; inrepeat = True
                else:
                    if (inrepeat):
                        istep += 1
                        istate = istate + int(ncount)
                    else:
                        istate +=1

                    new_line = '['+str(iline)+' : '+\
                        command.replace(' ','_')+' : '

            elif (inrepeat and
                  (command == increment1 or
                   command == increment1.replace(' ','_') or
                   command == increment2 or
                   command == increment2.replace(' ','_'))):
                # Substract any Increment step
                nstep = nstep - 1

            else:
                # Append subcommands without brackets,
                # separated by semicoloms
                isub += 1
                
                subcommand = fw[1:-1]
                if (subcommand not in ignore):
                    if (isub == 1):
                        new_line = new_line + subcommand
                    else:
                        new_line = new_line + ';' + subcommand
                    
            # Continue reading
            line = ff.readline()

        # Add last line if not done already
        ilast = int(protocol[-1].split()[0].split('[')[1])

        if (iline>ilast):
            protocol.append(new_line+'] \n')

            # Create an 'End Repeat line if needed
            if (istep == nstep and inrepeat): 
                new_line = '['+str(iline+1)+' : End Repeat '+str(nstep)+' steps :'
                protocol.append(new_line+'] \n')
                new_line = ' '
                        
        protocol.append(end_rprotocol)

        # Test that the number of protocol lines taking into account repetitions.
        step_number  = read_column(infile,col_step,outtype='int')
        state_number = read_column(infile,state_col,outtype='int')
        # Find the number of different steps (CC-CV is considered one)
        ind = np.where((state_number < 1) &
                       (step_number != CCCV_CVc) &
                       (step_number != CCCV_CVd))
        uniq_step = np.shape(ind)[1]
        minus1 = np.shape(np.where((state_number == -1) &
                                   (step_number != CCCV_CVc) & (step_number != CCCV_CVd)))[1]
        if verbose:
            print('Unique steps = {} (step=-1: {}), Steps from protocol = {}'.format(uniq_step,minus1,istate))
            
        if(istate > uniq_step and verbose):
            print('WARNING function reduced_protocol \n'+\
                  'REASON Mismatched protocol ('+str(istate)+\
                  ') and steps ('+str(uniq_step)+'): '+str(infile)+' \n')
        if(istate < uniq_step):
            viable_prot = False
            if (verbose):
                print('WARNING function reduced_protocol \n'+\
                      'REASON Less protocol lines ('+str(istate)+\
                      ') than actual steps ('+str(uniq_step)+'): \n'+
                      str(infile)+' \n')

    return protocol,viable_prot

def novonix_add_loopnr(infile,overwrite=False,verbose=False):
    """
    Given a cleaned Novonix data file, it adds a 'LoopNr' column, 
    with monotonically increasing numbers and 
    the protocol line corresponding to a given measurement.

    This values are determined by the change in the 'State' and 
    the protocol description in the header

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    overwrite: boolean
        Yes : overwrite the input file
        No  : a new file will be created, appending '_prep' at the end of the
              original file file

    verbose : boolean
        Yes = print out some informative statements

    Example
    -------
    $ python novonix_add_loopnr [path to cleaned Novonix file]

    """

    # Check if the file already has the new State column
    icol = icolumn(infile,loop_col)
    if (icol>-1):
        if verbose:
            print('The file {} already has a Loop number column'.format(infile))
        return
    
    # Get the reduced protocol as a list
    protocol, viable_prot = reduced_protocol(infile,verbose=verbose)

    # Read the Step_Number column
    steps  = read_column(infile, col_step, outtype='int')

    # Read the States and the set of measurements for a single state
    states = read_column(infile, state_col,outtype='int')
    izeros, = np.where(np.logical_or(states == 0,states == -1))
    itwos,  = np.where(np.logical_or(states == 2, states == -1))

    linenr = np.zeros(shape=len(steps),dtype=int) ; linenr.fill(-999.)
    loopnr = np.zeros(shape=len(steps),dtype=int) ; loopnr.fill(-999.)

    if (viable_prot):
        loopnr.fill(0)
        
        # Prepare to loop over the protocol lines
        prot = protocol[1:-1]
        iprot = 0
        inrepeat = False ; com_repeat = []
        ntimes = 0 ; itimes = 0 ; iloop = 0
        last_step = -1

        # Loop over the measurement sets
        for iz,it in zip(izeros,itwos):
            # Step of the Data Subset
            step = steps[iz]

            # Read protocol line
            continue_reading = True
            while (continue_reading):
                command = prot[iprot].split(':')[1].strip()
                if(command.split(' ')[0].strip() == 'Repeat'):
                    inrepeat = True ; com_repeat = []
                    iloop += 1 
                    itimes = 0 ; irstep = 0
                    ntimes = int(command.split(' ')[1].strip())
           
                    iprot += 1
                    first_rep  = iprot + 1
                    firstend = True
                                          
                elif(command.split(' ')[0].strip() == 'End'):
                    nrstep = int(command.split(' ')[2].strip())
                    if firstend:
                        irstep = 0 ; itimes += 1
                        iloop += 1
                        firstend = False
           
                    # Check that the array of repeated steps has the expected lenght
                    if (len(com_repeat) != nrstep):
                        sys.exit('STOP function novonix_add_loopnr \n'+\
                                 'REASON array of repeated steps has an unexpected length \n'+\
                                 '       '+str(len(com_repeat))+' != '+str(nrstep)+' \n'+
                                 '       '+str(infile)+' \n')
           
                    # Repeated commands
                    index = com_prot.index(com_repeat[irstep])
                    sel = select_com_val(index)
                    if(sel):
                        if ((step==CCCV_CVc or step==CCCV_CVd) and
                            (last_step==CCCV_CCc or last_step==CCCV_CCd)):
                            # 1 protocol line for CC-CV
                            last_step = -1
                            irstep = irstep - 1
                           
                        # Compare the protocol and step values
                        linenr[iz:it+1] = first_rep + irstep
                        loopnr[iz:it+1] = iloop
                        continue_reading = False
           
                    # Adequately deal with the reduced protocol counters
                    if (itimes == ntimes-1 and irstep == nrstep-1):
                        # Last command of the last repetition: reset
                        iprot += 1
                        inrepeat = False
                        itimes = 0 ; ntimes = 0
                        nrstep = 0 ; first_rep = 0
                    elif(itimes < ntimes-1 and irstep == nrstep-1):
                        # Last command within a repetition
                        irstep = 0 ; itimes += 1 
                        iloop += 1 
                    else:
                        irstep += 1
           
                elif(command in com_prot[:-1]): 
                    index = com_prot.index(command)
                    sel = select_com_val(index)
                    if (sel):
                        if ((step==CCCV_CVc or step==CCCV_CVd) and
                            (last_step==CCCV_CCc or last_step==CCCV_CCd)):
                            # 1 protocol line for CC-CV
                            last_step = -1
                            iprot = iprot - 1
                        else:
                            if inrepeat:
                                com_repeat.append(command)
           
                        linenr[iz:it+1] = iprot + 1
                        if inrepeat:
                            loopnr[iz:it+1] = iloop
                        continue_reading = False
                       
                    iprot += 1
                    if (iprot == len(prot)):
                        continue_reading = False
                else:
                    sys.exit('STOP function novonix_add_loopnr \n'+\
                             'REASON unexpected command in reduced protocol \n'+\
                             '       '+str(infile)+' \n')
            last_step = step
            
    # Create a temporary file with the new header
    header = [] ; fw = 'fw' 
    tmp_file = 'tmp.csv'
    with open(infile,'r') as ff:
        # Read until the line with [End Protocol]
        while (fw != "[Data]"):
            line = ff.readline() ; header.append(line)
            fw = line.split()[0]            

        # Create a temporary file with the header as it was
        with open(tmp_file, 'w') as tf:
            for item in header[:-1]:
                tf.write(str(item))

        # Add the reduced protocol
        with open(tmp_file, 'a') as tf:
            for item in protocol:
                tf.write(str(item))
            # Add [Data] line
            tf.write(str(header[-1]))

        # Read the column names and add the 'Loop' and 'Line'
        line = ff.readline() 
        new_head = str(line.rstrip())+\
            ', '+line_col+', '+loop_col+' \n'
        with open(tmp_file, 'a') as tf:
            tf.write(str(new_head))

        # Write the data + 2 new columns in the temporary file
        for ii,line in enumerate(ff):
            # Write the new data to the temporary file
            with open(tmp_file, 'a') as tf:
                new_line = line.rstrip()+','+\
                    str(linenr[ii])+','+str(loopnr[ii])+'\n'
                tf.write(new_line)

        # Check the size of the temporal file compared to the original
        size_original = os.stat(infile).st_size
        size_tmp = os.stat(tmp_file).st_size
        if (size_original > size_tmp):
            sys.exit('STOP function novonix_add_loopnr \n'+\
                     'REASON new file is smaller than original file \n'+\
                     '       '+str(infile))
    
        # Replace the input file with the new one
        move(tmp_file,infile)
        if verbose:
            print('{} contains now the columns Loop number and Protocol line'.format(infile))

    return

def prepare_novonix(infile,addstate=False,lprotocol=False,overwrite=False,verbose=False):
    """
    Given a Novonix data file, it prepare it to be handled.

    Parameters
    ----------
    infile : string
        Name of the input Novonix file

    verbose : boolean
        Yes = print out some informative statements

    lprotocol : boolean
        Yes = add to the initial header a 'reduced' protocol with a step per line and add lines with the loop number and protocol lines

    Example
    -------
    $ python prepare_novonix([path to Novonix file])

    """
    
    # Extract the path and file name
    dirname, fname = os.path.split(os.path.abspath(infile))

    # Modify the slashes in the input path if needed
    file_to_open = Path(dirname) / fname 

    # Check if the file has the expected structure for a Novonix file
    answer = isnovonix(file_to_open)
    if (not answer): sys.exit('STOP Input not from Novonix, {}'.format(file_to_open))

    # Clean the Novonix file
    cleannovonix(file_to_open,overwrite=overwrite)

    if addstate:
        # Check if the file has a State column and if not, create it
        novonix_add_state(file_to_open,overwrite=overwrite,verbose=verbose)

    if lprotocol:
        # Check if the file has a Loop number and Protocol line columns
        # and if not, create it
        novonix_add_loopnr(file_to_open,overwrite=overwrite,verbose=verbose)
    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        prepare_novonix(sys.argv[1],addstate=True,lprotocol=True,overwrite=False,verbose=True)
