import preparenovonix.novonix_add as prep

# The r" " are needed to handle Windows paths
# otherwise ' ' can be enough to include the path.
infile = r"example_data/example_data.csv"

prep.prepare_novonix(infile, addstate=True, lprotocol=True,
                     overwrite=False, verbose=True)
