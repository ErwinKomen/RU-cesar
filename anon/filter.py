import csv
import os


# obtain all replaced words
entmaps = [
	'./data/OutputWhatsApp2013/entity_mapping.csv',
	'./data/OutputWhatsApp2014/entity_mapping.csv',
	'./data/OutputWhatsAppData/entity_mapping.csv',
	'./data/OutputLieke/entity_mapping.csv']
thelist = []
for entmap in entmaps:
	with open(entmap, 'rt') as csvfile:
		csvreader = csv.reader(csvfile)
		for row in csvreader:
			if row[0] not in thelist:
				thelist.append(row[0])
thelist = sorted(thelist)

# read existing remove file
remove = []
if os.path.isfile("remove.txt"): 
    file = open("remove.txt", 'rb')
    for w in file.readlines():
    	try:
    		remove.append(w[:-2].decode('utf-8'))
    	except:
    		pass
    file.close()

# remove words from the list
for w in remove:
	if w in thelist:
		thelist.remove(w)

# manualy filter words
n = len(thelist)
i = 0
while(i < len(thelist)):
	# obtain word
	w = thelist[i]

	# ask delete
	inp = input(str(i+1) + "/" + str(n) + " " + w + " ")

	# remove word
	if inp == 'd':
		remove.append(w)

	# go back and restore
	if inp == 'b':
		bw = thelist[i-1]
		if bw in remove:
			remove.remove(bw)
		print('restored:', bw)
		# set back counter
		i -= 2

	# stop operations
	if inp == 'stop':
		break

	# raise counter
	i += 1


# update entitiy mappings
for entmap in entmaps:
	# the new file
	new_file = []

	with open(entmap, 'rt') as csvfile:
		csvreader = csv.reader(csvfile)
		for row in csvreader:
			if row[0] not in remove:
				new_file.append(row)

	with open(entmap, 'wt') as csvfile:
		csvwriter = csv.writer(csvfile)
		for row in new_file:
			csvwriter.writerow(row)

# print number of removed words
print('removed ' + str(len(remove)) + ' word(s)')

# update remove file
file = open("remove.txt", 'w')
for w in sorted(remove):
    file.write(w + "\n")
file.close()

print('updated remove.txt')