import copy
import lxml.etree as et
import os
from tqdm import tqdm


alpino_dirs = ['./data/alpino/WhatsApp2013/', './data/alpino/WhatsApp2014/',
	'./data/alpino/WhatsAppData/', './data/alpino/WhatsAppLieke/'] 
anonim_dirs = ['./data/data/WhatsApp-2013/', './data/data/WhatsApp-2014/', 
	'./data/data/WhatsApp-Data/', './data/data/WhatsApp-Lieke/']
result_dirs = ['./data/results/WhatsApp2013/', './data/results/WhatsApp2014/',
	'./data/results/WhatsAppData/', './data/results/WhatsAppLieke/']


def open_xml(filename):
	doc_string = ""
	with open(filename, 'rb') as doc:
		for x in doc.readlines():
			doc_string += x

	return et.fromstring(doc_string)


def anonimize_xml(ano_xml, alp_xml):
	alp_ano_xml = copy.deepcopy(alp_xml)

	for i in range(len(alp_xml[1])):
		alp_ano_xml[1][i] = anonimize_event(ano_xml[1][i], alp_xml[1][i])

	return alp_ano_xml


def anonimize_event(ano_event, alp_event):
	alp_ano_event = copy.deepcopy(alp_event)
 	wx = []

	# anonimize actor
	alp_ano_event.attrib['actor'] = ano_event.attrib['actor']

	# s
	words = []
	for s_i in range(1, len(alp_ano_event)):
		# w
		for w_i in range(len(alp_ano_event[s_i][2:])):
			w = alp_ano_event[s_i][w_i]
			if w.tag[-1] == 'w':
				word = w[0].text
				words.append(word)
			
	ano_words = []
	for w in words:
		if w not in ano_event[0].text and '*T*' not in w and '*ICH*' not in w:
			ano_words.append(w)
	
	for s_i in range(1, len(alp_ano_event)):		
		for w_i in range(len(alp_ano_event[s_i][2:])):
			w = alp_ano_event[s_i][w_i]
			if w.tag[-1] == 'w':
				word = w[0].text
				if word in ano_words:
					# remove word from t
					alp_ano_event[0].text = alp_ano_event[0].text.replace(word, '[REMOVED]')
					# remove word from inner t
					alp_ano_event[s_i][1].text = alp_ano_event[s_i][1].text.replace(word, '[REMOVED]')
					# replace lemma
					alp_ano_event[s_i][w_i][3].attrib['class'] = '[REMOVED]'


	string_event = et.tostring(alp_ano_event)
	for w in ano_words:
		string_event = string_event.replace('\"' + w + '\"', '\"[REMOVED]\"')
		string_event = string_event.replace('>' + w + '<', '>[REMOVED]<')
	alp_ano_event = et.fromstring(string_event)

	return alp_ano_event


for i in range(len(result_dirs)):
	for file in tqdm(os.listdir(anonim_dirs[i])):
		try:
			# open anomized file
			ano_xml = open_xml(anonim_dirs[i] + file)

			# open alpino gesprek
			alp_xml = open_xml(alpino_dirs[i] + file + '.alpinoed/' + file + '.frogged.folia.xml')
			
			# anonimize alpino
			new_alp_xml = anonimize_xml(ano_xml, alp_xml)
			
			# save anonimized alpino
			filestring = et.tostring(new_alp_xml)
			with open(result_dirs[i] + file, 'wb') as output:
				output.writelines(filestring)
		except:
			print 'failed:', file
