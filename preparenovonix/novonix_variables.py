eps = 1.0e-5

# Novonix columns
col_step = "Step Number"
col_tstep = "Step Time (h)"
col_capacity = "Capacity (Ah)"

state_col = "State (0=Start 1=Regular 2=End -1=Single Measurement)"
loop_col = "Loop number"
line_col = "Protocol Line (it refers to the reduced protocol)"

# Commands in Protocols
increment1 = "Increment the cycle counter"
increment2 = "Increment cycle counter"

ignore = [
    "End storage",
    "End charge",
    "End discharge",
    "End repeat",
    increment1,
    increment2,
    "End increment",
    "Trip conditions",
    "End trip conditions",
    "Save conditions",
    "End save conditions",
    "Operating limits",
    "End operating limits",
    "Emergency limits",
    "End emergency limits",
]

com_prot = [
    "Open_circuit_storage",
    "Constant_current_charge",
    "Constant_current_discharge",
    "CC-CV_charge",
    "CC-CV_discharge",
    "Repeat",
]

# Novonix step values
OCV = 0
CCc = 1
CCd = 2  # in some cases this is also set to 1
CCCV_CCc = 7
CCCV_CVc = 8
CCCV_CCd = 9
CCCV_CVd = 10

com_val1 = [OCV, CCc, CCd, CCCV_CCc, CCCV_CCd]
com_val2 = [None, None, CCc, CCCV_CVc, CCCV_CVd]

numberstr = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-"]
