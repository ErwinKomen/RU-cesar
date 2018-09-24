"""
Original created by Patrick 
This version emended by Erwin R. Komen 
Date: 11/sep/2018 
"""

import copy
import lxml.etree as et
import os, sys
from tqdm import tqdm

# ============ SETTINGS FOR THIS INSTANCE =================
bLocal = False          # Process locally 
bPatrick = False
bAllowCrashing = True   # Allow program to stop upon the first error
if bLocal:
    base_dir = "/etc/corpora/tmp/"
else:
    base_dir = "/vol/tensusers/ekomen/corpora/acad/remainder/lieke/"
# =========================================================

if bPatrick:
    alpino_dirs = ['./data/alpino/WhatsApp2013/', './data/alpino/WhatsApp2014/',
	    './data/alpino/WhatsAppData/', './data/alpino/WhatsAppLieke/'] 
    anonim_dirs = ['./data/data/WhatsApp-2013/', './data/data/WhatsApp-2014/', 
	    './data/data/WhatsApp-Data/', './data/data/WhatsApp-Lieke/']
    result_dirs = ['./data/results/WhatsApp2013/', './data/results/WhatsApp2014/',
	    './data/results/WhatsAppData/', './data/results/WhatsAppLieke/']
else:
    alpino_dirs = ["5_alpino/"]
    anonim_dirs = ["6_oldano/"]
    result_dirs = ["7_result/"]


def get_error_message():
    arInfo = sys.exc_info()
    if len(arInfo) == 3:
        sMsg = str(arInfo[1])
        if arInfo[2] != None:
            sMsg += " at line " + str(arInfo[2].tb_lineno)
        return sMsg
    else:
        return ""

def open_xml(filename):
    doc_string = b""
    sMethod = "onego"

    try:
        if sMethod == "onego":
            with open(filename, "rb") as doc:
                doc_string = doc.read()
        else:
            with open(filename, 'rb') as doc:
                for x in doc.readlines():
                    doc_string += x

        return et.fromstring(doc_string)
    except:
        sMsg = get_error_message()
        print("Error in open_xml: {}".format(sMsg))


def anonimize_xml(ano_xml, alp_xml):

    alp_ano_xml = copy.deepcopy(alp_xml)

    try:
        for i in range(len(alp_xml[1])):
            alp_ano_xml[1][i] = anonimize_event(ano_xml[1][i], alp_xml[1][i])

    except:
        sMsg = get_error_message()
        print("Error in anonimize_xml: {}".format(sMsg))

    return alp_ano_xml


def anonimize_event(ano_event, alp_event):
    alp_ano_event = copy.deepcopy(alp_event)
    try:
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

        # Python3: convert bytes into string
        string_event_s = string_event.decode("utf-8")
        for w in ano_words:
            string_event_s = string_event_s.replace('\"' + w + '\"', '\"[REMOVED]\"')
            string_event_s = string_event_s.replace('>' + w + '<', '>[REMOVED]<')
        # Pythong3: convert string to bytes back
        string_event = string_event_s.encode("utf-8")
        alp_ano_event = et.fromstring(string_event)

    except:
        sMsg = get_error_message()
        print("Error in anonimize_event: {}".format(sMsg))

    return alp_ano_event



for i in range(len(result_dirs)):
    print("Processing directory {}".format(i+1))

    # make sure base-dir gets added if needed
    if not bPatrick:
        result_dirs[i] = base_dir + result_dirs[i]
        anonim_dirs[i] = base_dir + anonim_dirs[i]
        alpino_dirs[i] = base_dir + alpino_dirs[i]

    for file in tqdm(os.listdir(anonim_dirs[i])):
        # Make sure the filename is readable, even though it contains unicode characters
        #file = file.encode('utf8')
        print("Re-anonimizing file {}".format(file.encode("utf8")))

        try:
            # open anomized file
            ano_xml = open_xml(anonim_dirs[i] + file)

            if bPatrick:
                # Determine folia target
                target = file

                # open alpino gesprek
                alp_xml = open_xml(alpino_dirs[i] + file + '.alpinoed/' + file + '.frogged.folia.xml')

            else:
                # Determine folia target
                target = file.replace(".xml.frogged", "")

                # open alpino gesprek
                alp_xml = open_xml(alpino_dirs[i] + target)

            # anonimize alpino
            new_alp_xml = anonimize_xml(ano_xml, alp_xml)


            # save anonimized alpino
            filestring = et.tostring(new_alp_xml)
            with open(result_dirs[i] + target, 'wb') as output:
                output.write(filestring)
                # output.writelines(filestring)

        except:
            print('failed: {}'.format(file))
            print("error: {}".format(get_error_message()))
            if bAllowCrashing:
                print("The program has been aborted")
                break

print("Ready")
