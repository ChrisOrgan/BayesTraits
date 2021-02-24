# Import libraries
import os
import re
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, call

import numpy as np
import pandas as pd

# Wrapper for BayesTraits
execute = 'BayesTraitsV3'
intree = ' Mammal.trees'
indata = ' MammalBrainBody.txt'
commands = ' < bt_in.txt'
bt_sp = call([execute + intree + indata + commands], shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)

# Set tree and data files
data_folder = Path('./')
data_file = data_folder / indata + '.Log.txt'

def load_BTdata(data_file):
	'''
	Loads output data from a BayesTraits analysis

	Args:
		data_file (BayesTraits output log file): An output file with header (settings) information and tab-delimited results

	Returns:
		dictionary: Dictionary of settings from the header of the BayesTraits log file.
		pandas data frame: Data frame of results.
	'''

	# Setup parameters for parsing file
	header = []
	head_end = '     Sites:'
	skiprows = 0

	# Iterate over file
	with open(data_file, 'r+') as f:
		for line in f:

			line = line.rstrip()

			# Track the number of lines in the header
			skiprows += 1

			# Save header line to the header list
			header.append(line)

			# If the last line of the header is reached, exit loop
			if line.startswith('     Sites:'):
				break

	# Load data into pandas, skipping the header
	df = pd.read_csv(data_file, sep='\t', index_col=0, skiprows=skiprows)

	# Drop the last NaN column (BayesTraits may append a tab in some results)
	df= df.dropna(axis=1, how='all')

	# Set index name
	df.index.name='Iteration'

	settings = proc_settings(header)
	
	return settings, df

def proc_settings(header):
	'''
	Processes the heading of a BayesTraits output log file into a dictionary of settings

	Args:
		header (string): The heading section of the log file

	Returns:
		dictionary: Dictionary of settings from the header of the BayesTraits log file.
	'''

	# Remover 1st line of header
	header.pop(0)

	# Initialize settings dictionary and iterate over header
	settings_dict = {}
	for line in header:

		# Split line 
		setting = re.split(r'\s{2,}', line)

		# If setting is category, save it
		if len(setting) == 1:
			
			# don't save category if tab indented tags
			if not bool(re.match(pattern='^\t', string=setting[0])):
				cat = setting[0]

			if bool(re.match(pattern='^Tags:', string=setting[0])):
				setting = re.split(r'\t', line)

			# Process tags
			if bool(re.match(pattern='^\t', string=setting[0])):
				tagsplit=re.split(r'\t', setting[0])
				setting[0] = tagsplit[1]
				setting.append(tagsplit[2] + ' ' + tagsplit[3])

		# If indented, substitute setting category
		if setting[0] == '' and len(setting) == 3:

			# Process tree information
			if cat == 'Restrictions:' or cat == 'Tree Information':
				setting.pop(0)
				setting[0] = cat + ' ' + setting[0]
			else:
				setting.pop(0)
				setting[0] = cat

		elif setting[0] == '' and len(setting) == 2:
			setting[0] = cat
			
			# Process priors
			if cat == 'Prior Information:' and setting[1] != 'Priors':
				priorsplit = re.split(r' - ', setting[1])
				setting[0] = cat + ' ' + priorsplit[0]
				setting[1] = priorsplit[1]

			if cat == 'Local Rates:':
				localsplit = setting[1].split(r' Tag', 1)
				setting[0] = cat + ' ' + localsplit[0]
				setting[1] = localsplit[1]				 

		# Remove colons
		setting[0] = setting[0].replace(':','')

		# Build settings dictionary, skipping categories
		if len(setting) > 1:
			settings_dict[setting[0]] = setting[1]

	return settings_dict


settings, output = load_BTdata(data_file)

# Plot results
import matplotlib.pyplot as plt
import seaborn as sns

# Set default Seaborn style (as opposed to using Matplotlib's style)
sns.set()

# Plot the histogram
plt.hist(output['Lambda'], density=False)

# Label axes
_ = plt.xlabel('Lambda')
_ = plt.ylabel('count')

# Show histogram
plt.show()
