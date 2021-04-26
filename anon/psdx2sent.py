"""
Purpose: turn PSDX files into a list of original-language sentences without punctuation marks

Original created by by Erwin R. Komen 
Date: 13/apr/2021
"""

# import lxml.etree as et
import xml.etree.ElementTree as et
import getopt, copy, util
import re
import json
import os, sys

# ============ SETTINGS FOR THIS INSTANCE =================
bLocal = True           # Process locally 
bAllowCrashing = True   # Allow program to stop upon the first error
if bLocal:
    base_dir = "d:/etc/corpora/Chechen/xml/NMSU/Mono"
    #   Specify the result dir
    result_dir = "d:/etc/corpora/Chechen/xml/NMSU/MonoSent"
else:
    base_dir = "/vol/bigdata/corpora2/SoNaRfromTST/SoNaRCorpus_NC_1.2/SONAR500/CMDI/WR-P-P-G_newspapers/079"
    #   Specify the result dir
    result_dir = "/vol/tensusers5/ekomen/corpora/"
XSI_CMD = "http://www.clarin.eu/cmd/"
XSI_XSD = "http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1328259700943/xsd"
# =========================================================

errHandle = util.ErrHandle()

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
        return tree, root
    except:
        sMsg = get_error_message()
        print("Error in open_xml: {}".format(sMsg))

def parse_node(node, ancestor_string = "", bFirst=False, ch_num=None):
    """parse one node in an XML tree recursively"""

    # Adapt the path we are at right now
    sNodeTag = node.tag
    sNodeTag = sNodeTag.replace("{http://www.clarin.eu/cmd/}", "")
    if ch_num != None:
        sNodeTag = "{}_{}".format(sNodeTag, ch_num)
    if ancestor_string:
        node_string = ".".join([ancestor_string, sNodeTag])
    else:
        node_string = sNodeTag

    # Adapt the path list
    tag_list = [node_string]

    # Get the text of this node
    text = node.text
    if text:
        text_list = [text.strip()]
    else:
        text_list = [""]

    # for child_node in list(node):
    for ch_num, child_node in enumerate(node):
        child_tag_list, child_text_list = parse_node(child_node, ancestor_string=node_string, ch_num=ch_num)
        tag_list.extend(child_tag_list)
        text_list.extend(child_text_list)

    return tag_list, text_list


def process_psdx_directory(oArgs):
    """Process one directory of PSDX files into a list of TXT files"""

    # Defaults
    dirInput = ""
    dirOutput = ""
    col_offset = 3          # Number of columns that are not used for text file information
    path_list = []
    stat_list = []          # Number of occurrances per path
    text_list_list = []

    try:
        # Prepare regex
        nonvalidchar = re.compile('[^a-zA-Zа-яА-ЯІ\s]', re.UNICODE)
        spaces = re.compile('\s+', re.UNICODE)
        # Recover the arguments
        if "input" in oArgs: dirInput = oArgs["input"]
        if "output" in oArgs: dirOutput = oArgs["output"]

        # Check input directory
        if not os.path.exists(dirInput) or not os.path.isdir(dirInput):
            errHandle.Status("Please specify an existing input directory")
            return False

        # Signal the first file to be processed, which takes care of the list of paths
        bIsFirst = True
        count = 0
        word_count = 0
        # Process all psdx XML files in this directory
        for file in os.listdir(dirInput):
            # Check the ending of this file
            if file.endswith(".psdx"):

                # Show where we are
                errHandle.Status("Processing file: {}".format(file))

                # Try to open the file
                try:
                    input_file = os.path.abspath( os.path.join(dirInput, file))

                    psdx_xml, root = open_xml(input_file)
                    # Keep track of the count of files
                    count += 1

                    # Start a list for this file
                    sentences = []

                    # Look for all <seg> elements
                    seg_list = psdx_xml.findall(".//div[seg]")
                    for seg in seg_list:
                        if seg.attrib.get('lang') == "che":
                            # Get the text
                            one_line = seg.find("./seg").text
                            # Remove common punctuation
                            line = nonvalidchar.sub('', one_line).strip()
                            # Change multiple spaces for one space
                            word_list = spaces.split(line)
                            word_count += len(word_list)
                            # Add to the sentences
                            if len(word_list) != "":
                                sentences.append(word_list)

                    # Determine the name of the output file
                    output_file = os.path.abspath(os.path.join(dirOutput, file.replace(".psdx", ".json")))

                    # Save the sentences into the file
                    with open(output_file, "w", encoding="utf-8") as fp:
                        json.dump(sentences, fp, ensure_ascii=False, indent=2)
                except:
                    print('failed: {}'.format(file))
                    print("error: {}".format(get_error_message()))
                    if bAllowCrashing:
                        print("The program has been aborted")
                        break

        print("Files: {}, words: {}".format(count, word_count))

        print("Ready")
        return True
    except:
        sMsg = errHandle.get_error_message()
        errHandle.DoError("process_cmdi_directory")
        return False

# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 29/apr/2019    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
    dirInput = ''     # input directory name
    dirOutput = ""    # Output directory
    flOutput = ''     # output file name

    try:
        sSyntax = prgName + ' -i <input dir>' + ' -o <output dir>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:l:", ["-idir=", "-odir="])
        except getopt.GetoptError:
            print(sSyntax)
            sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--idir"):
                dirInput = arg
            elif opt in ("-o", "--odir"):
                dirOutput = arg
        # Check if all arguments are there
        if (dirInput == ''):
            errHandle.DoError(sSyntax, True)

        # Determine what the output directory will be
        if dirOutput == "":
            dirOutput = dirInput

        # Continue with the program
        errHandle.Status('Input directory is "' + dirInput + '"')
        errHandle.Status('Output directory is "' + dirOutput + '"')
        errHandle.Status("Local is {}".format(bLocal))

        # Call the function that does the job
        oArgs = {'input': dirInput, 'output': dirOutput}
        if (not process_psdx_directory(oArgs)) :
            errHandle.DoError("Could not complete")
            return False
    
            # All went fine  
        errHandle.Status("Ready")
    except:
        # act
        errHandle.DoError("main")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
  # Call the main function with two arguments: program name + remainder
  main(sys.argv[0], sys.argv[1:])
