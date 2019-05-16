### novonix_add.py 

Contains the functions:

* **prepare_novonix** Reads a csv file produced by Novonix cyclers, cleans it and add additional colums: State, Loop Number, Protocol Line, and adds in the header a reduced protocol. 

* **select_com_val** Establish the selection statement for one or two possible step values.

* **isnovonix** Given a data file, check if it exists and if looks like a Novonix file

* **iscolum** Given a Novonix data file, find the column position of the given column_name

* **read_column** Given a Novonix data file, read a column as an array of the type given in the variable astype.

* **cleannovonix** Given a Novonix file remove blank lines, correct the header and remove failed tests if needed.

* **novonix_add_state** Given a cleaned Novonix data file and adds a 'State' column with the following values: 0= Start of the measurement, 1= Measuring, 2= End of mesurement. The input file is replaced by the new one with the extra column (after passing several tests).

* **novonix_add_loopnr** Given a cleaned Novonix data file, it adds a 'LoopNr' column, with monotonically increasing numbers and the protocol line corresponding to a given measurement. This makes use of the function all the other functions defined in this module.
