"""
Purpose: add a publiction date (a year) to the CMDI metadata file

Original created by by Erwin R. Komen 
Date: 8/oct/2018 
"""

# import lxml.etree as et
from xml.dom import minidom
import xml.etree.ElementTree as et
import copy
import os, sys

# ============ SETTINGS FOR THIS INSTANCE =================
bLocal = False          # Process locally 
bAllowCrashing = True   # Allow program to stop upon the first error
if bLocal:
    base_dir = "/etc/corpora/tmp/lieke"
else:
    base_dir = "/vol/tensusers/ekomen/corpora/acad/whatsapp/manon_all"
# Specify the result dir
result_dir = base_dir + "/9_result"
XSI_CMD = "http://www.clarin.eu/cmd/"
XSI_XSD = "http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1328259700943/xsd"
# =========================================================

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
    sMethod = "traditional" # "onego"

    try:
        tree = et.parse(filename)
        root = tree.getroot()
        return root
    except:
        sMsg = get_error_message()
        print("Error in open_xml: {}".format(sMsg))

def get_year(oXml):
    """Assuming this is a folia.xml, get the first <event> with a year"""

    try:
        ns = {'folia': "http://ilk.uvt.nl/folia" }

        # Find the first <event> tag
        event = oXml.find(".//folia:event", ns)
        if event == None:
            sYear = "2010"
        else:
            sBeginTime = event.get("begindatetime")
            sYear = sBeginTime[:4]
            print("year={}".format(sYear))

        # Return the year
        return sYear
    except:
        sMsg = get_error_message()
        print("Error in get_year: {}".format(sMsg))


def add_metadate(oXml, sYear):
    """Add publication date"""
    
    back_xml = copy.deepcopy(oXml)
    lSubPub = ['Published', 'PublicationName', 'PublicationPlace', 'PublicationDate', 'PublicationTime', 'PublicationVolume',
               'PublicationNumber', 'PublicationNumber', 'PublicationIssue', 'PublicationSection', 'PublicationSubSection',
               'PublicationPage', 'PublicationId', 'PublicationLanguage', 'PublicationScope', 'PublicationGenre']
    # Local variables

    try:
        # Set the namespace
        ns_string = 'http://www.clarin.eu/cmd/'
        ns = {'df': ns_string}

        # Use the correct top components
        topattributes = {'xmlns': "http://www.clarin.eu/cmd/" ,
                    'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance/",
                    'xsi:schemaLocation': XSI_CMD + " " + XSI_XSD,
                    'CMDVersion':'1.1'}

        # Find the <Source> tag
        # root = back_xml.getroot()
        for source in back_xml.findall(".//xmlns:Source", topattributes):
            # See if there is a Publication child
            pub_children = source.findall("./xmlns:Publication", topattributes)
            if len(pub_children) == 0:
                # Add a child
                pub_root = et.SubElement(source, "Publication")
                # Add children
                for child in lSubPub:
                    newChild = et.SubElement(pub_root, child)
                    # Check if this is the date
                    if child == "PublicationDate":
                        # Set the text value
                        newChild.text = sYear
                    # Add the child
                    #ch_this = pub_root.append(newChild)
    except:
        sMsg = get_error_message()
        print("Error in add_metadate: {}".format(sMsg))

    return back_xml



# Process all cmdi.xml files in this directory
sYear = "2012"
for file in os.listdir(base_dir):
    # Check the ending of this file
    if ".cmdi.xml" in file:
        print("Processing metadata of file {}".format(file.encode("utf8")))

        # Try to open the file
        try:
            input_file = os.path.abspath( os.path.join(base_dir, file))
            output_file = os.path.abspath(os.path.join(result_dir, file))

            folia_file = os.path.abspath(os.path.join(base_dir, file.replace(".cmdi.xml", ".folia.xml")))

            folia_xml = open_xml(folia_file)
            sYear = get_year(folia_xml)

            # open anomized file
            input_xml = open_xml(input_file)

            # Add the date
            output_xml = add_metadate(input_xml, sYear)

            # Save the file
            filestring = et.tostring(output_xml, encoding='utf-8').decode('utf-8').replace("ns0:", "").encode('utf-8')
            # success = et.ElementTree.write(output_xml, output_file, encoding='utf-8')

            with open(output_file, 'wb') as output:
                output.write(filestring)

        except:
            print('failed: {}'.format(file))
            print("error: {}".format(get_error_message()))
            if bAllowCrashing:
                print("The program has been aborted")
                break
print("Ready")
