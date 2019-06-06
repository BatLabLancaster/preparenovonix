import preparenovonix.novonix_prep as prep

# The r" " are needed to handle Windows paths
# otherwise ' ' can be enough to include the path.
infile = r"example_data/example_data.csv"
infile = r"../batdata/novonix_data/Cell5_200cyc.csv"

prep.prepare_novonix(infile, addstate=False, lprotocol=True,
                     overwrite=False, verbose=True)
