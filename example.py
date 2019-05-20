import pycode.novonix_add as prep

infile = 'example_data/example_data.csv'

prep.prepare_novonix(infile, addstate=True, lprotocol=True,
                     overwrite=False, verbose= True)
