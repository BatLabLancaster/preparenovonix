import sys, os.path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import preparenovonix.novonix_variables as nv
from preparenovonix.novonix_io import read_column
from preparenovonix.novonix_io import after_file_name
from preparenovonix.novonix_io import icolumn


def plot_vct(before_file, first_loop=0, plot_type="pdf", plot_show=False):
    """
    Given two Novonix data files, pre and post-processing
    with preparenovonix, plot toghether their 
    Voltage, Capacity, Step Number and Loop number versus time

    Parameters
    -----------
    before_file : string
        Name of the pre-processed file

    first_loop : int
        Value for the Loop Number to start showing data

    plot_type : string
        'pdf', 'png', 'jpg' for the format of the saved file

    plot_show : boolean
        True to show the plot.

    Notes
    -----
    This code returns a plot.

    Examples
    ---------
    >>>> from preparenovonix.compare import plot_vct

    >>>> plot_vct('example_data/example_data.csv','example_data/example_data_prep.csv',first_loop=0,plot_type='pdf',plot_show=True)
    """

    after_file = after_file_name(before_file)
    dirname, fname = os.path.split(os.path.abspath(after_file))
    figname = os.path.join(dirname, "compare_vct." + plot_type)

    # Value of the loop to start the plot from
    val = first_loop

    ### Read the voltage, step number and loop number from
    # the processed file

    a_t = read_column(after_file, nv.col_t, outtype="float")
    a_v = read_column(after_file, nv.col_v, outtype="float")
    a_c = read_column(after_file, nv.col_c, outtype="float")
    a_s = read_column(after_file, nv.col_step, outtype="int")
    a_l = read_column(after_file, nv.loop_col, outtype="int")

    # Find the column positions in the file
    icol_t = icolumn(after_file, nv.col_t)
    icol_v = icolumn(after_file, nv.col_v)
    icol_c = icolumn(after_file, nv.col_c)
    icol_step = icolumn(after_file, nv.col_step)

    ### Read the voltage and step number from the original file
    # Since there are failed tests, these need to be jumped
    data = "[Data]"
    ntests = 0  # Count the number of failed tests
    with open(before_file, "r") as ff:
        for line in ff:
            if line.strip():  # Jump empty lines
                if data in line:
                    # Count failed tests for each start of file
                    ntests += 1
                    idata = 0

    vv = []
    ss = []
    tt = []
    cc = []
    with open(before_file, "r") as ff:
        for line in ff:
            if line.strip():  # Jump empty lines
                if data in line:
                    # Count failed tests for each start of file
                    idata += 1
                    if idata == ntests:
                        # Read the header
                        ff.readline()
                        break
        for line in ff:
            tt.append(line.split(",")[icol_t])
            vv.append(line.split(",")[icol_v])
            cc.append(line.split(",")[icol_c])
            ss.append(line.split(",")[icol_step])

    b_t = np.asarray(tt, dtype=np.float64)
    b_v = np.asarray(vv, dtype=np.float64)
    b_c = np.asarray(cc, dtype=np.float64)
    b_s = np.asarray(ss, dtype=int)

    # Plot
    cols = ["darkred", "salmon", "cornflowerblue", "navy"]
    plt.figure(figsize=(8.0, 11.0))
    gs = gridspec.GridSpec(4, 1)
    gs.update(wspace=0.0, hspace=0.0)
    fs = 15

    # Plot only when the loop starts to be biggeer than val
    ind = np.where(a_l > val)
    if np.shape(ind)[1] < 1:
        print("WARNING compare.plot_vct: not enough data to be plotted")
        return

    astart = ind[0][0]
    first_a_t = a_t[astart]
    ind = np.where(b_t >= first_a_t)
    bstart = ind[0][0]

    # Loop number
    axl = plt.subplot(gs[3, :])
    axl.set_xlabel(nv.col_t, fontsize=fs)
    axl.set_ylabel(nv.loop_col, fontsize=fs)

    axl.plot(a_t[astart::], a_l[astart::], cols[2], label="Loop number after")

    # Steps
    axs = plt.subplot(gs[2, :], sharex=axl)
    plt.setp(axs.get_xticklabels(), visible=False)
    axs.set_ylabel(nv.col_step, fontsize=fs)

    axs.plot(a_t[astart::], a_s[astart::], cols[2], label="After")
    axs.plot(b_t[bstart::], b_s[bstart::], cols[0], linestyle="--", label="Before")

    # Voltage and capacity vs. time
    axv = plt.subplot(gs[:-2, :], sharex=axl)
    plt.setp(axv.get_xticklabels(), visible=False)
    axv.set_ylabel(nv.col_v, fontsize=fs)

    axv.plot(a_t[astart::], a_v[astart::], cols[2], label="Potential after")
    axv.plot(
        b_t[bstart::], b_v[bstart::], cols[0], linestyle="--", label="Potential before"
    )

    leg = axv.legend(loc=2, fontsize=fs - 2)
    ii = 0
    for text in leg.get_texts():
        text.set_color(cols[ii])
        ii = ii + 2
        leg.draw_frame(False)

    axc = axv.twinx()
    axc.set_ylabel(nv.col_c, fontsize=fs)
    axc.plot(b_t[bstart::], b_c[bstart::], cols[1], label="Capacity before")
    axc.plot(
        a_t[astart::], a_c[astart::], cols[3], linestyle="--", label="Capacity after"
    )

    leg = axc.legend(loc=4, fontsize=fs - 2)
    ii = 1
    for text in leg.get_texts():
        text.set_color(cols[ii])
        ii = ii + 2
    leg.draw_frame(False)

    plt.savefig(figname)

    if plot_show:
        plt.show()

    print("Plot: {}".format(figname))
