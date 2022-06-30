"""
Purpose: extract free text lines as paragraphs into text file

Original created by by Erwin R. Komen 
Date: 10/may/2021
"""

# import lxml.etree as et
import xml.etree.ElementTree as et
import getopt, copy, util
import re
import json
import os, sys

# ============ SETTINGS FOR THIS INSTANCE =================
bAllowCrashing = True   # Allow program to stop upon the first error
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


def process_flextree(oArgs):
    """Process one .flextree file into on .txt file"""

    # Defaults
    flInput = ""
    flOutput = ""
    language = "en"
    count = 0
    col_offset = 3          # Number of columns that are not used for text file information
    path_list = []
    stat_list = []          # Number of occurrances per path
    text_list_list = []

    try:
        # Recover the arguments
        if "input" in oArgs: flInput = oArgs["input"]
        if "output" in oArgs: flOutput = oArgs["output"]
        if "language" in oArgs: language = oArgs['language']

        # Check input directory
        if not os.path.exists(flInput) :
            errHandle.Status("Please specify an existing input file")
            return False


        # Show where we are
        errHandle.Status("Processing file: {}".format(flInput))

        # Try to open the file
        try:
            input_file = flInput

            flex_xml, root = open_xml(input_file)
            # Keep track of the count of stories
            count += 1

            # Start a list of stories
            stories = []
            # Look for the <interlinear-text> element
            story_list = flex_xml.findall(".//interlinear-text")
            for story in story_list:
                # Get the title of the story
                titles = story.findall("./item[@type='title']")
                title = ""
                for one_title in titles:
                    if title == "":
                        title = one_title.text
                    elif one_title.attrib['lang'] == "en":
                        title = one_title.text
                # Walk the paragraphs
                paragraphs = []
                for paragraph in story.findall("./paragraphs/paragraph"):
                    sentence = []
                    # Walk all phrases in this paragraph
                    for phrase in paragraph.findall("./phrases/phrase"):
                        lines = phrase.findall("./item[@type='gls']")
                        sText = lines[0].text
                        if lines[0].attrib['lang'] != language:
                            for line in lines[1:]:
                                if line.attrib['lang'] == language:
                                    sText = line.text
                                    break
                        if sText != "" and sText != None:
                            sentence.append(sText)
                    if len(sentence) > 0:
                        paragraphs.append(sentence)
                if len(paragraphs) > 0:
                    stories.append(dict(title=title, paragraphs=paragraphs))

            # Determine the name of the output file
            output_file = flOutput

            # Convert the list of stories into the right format
            html = []
            html.append("<html><head><meta charset='UTF-8'></head><body>")
            for story in stories:
                title = story['title']
                html.append("<h2>{}</h2>".format(title))
                for paragraph in story['paragraphs']:
                    html.append("<p>")
                    for line in paragraph:
                        html.append(line)
                    html.append("</p>")

            html.append("</body></html>")
            output_text = "\n".join(html)

            # Save the sentences into the file
            with open(output_file, "w", encoding="utf-8") as fp:
                fp.write(output_text)

        except:
            sMsg = errHandle.get_error_message()
            print('failed: {}'.format(input_file))
            print("error: {}".format(get_error_message()))
            if bAllowCrashing:
                print("The program has been aborted")
                return False

        print("Stories: {}".format(count))

        print("Ready")
        return True
    except:
        sMsg = errHandle.get_error_message()
        errHandle.DoError("process_flextree")
        return False

# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 29/apr/2019    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
    flInput = ''        # input directory name
    flOutput = ""       # Output directory
    language = "en"     # Default language

    try:
        sSyntax = prgName + ' -i <input dir>' + ' -o <output dir>' + " -l <language>"
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:l:", ["-input=", "-output=", "-language="])
        except getopt.GetoptError:
            print(sSyntax)
            sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--idir"):
                flInput = arg
            elif opt in ("-o", "--odir"):
                flOutput = arg
            elif opt in ("-l", "--language"):
                language = arg
        # Check if all arguments are there
        if (flInput == ''):
            errHandle.DoError(sSyntax, True)

        # Determine what the output directory will be
        if flOutput == "":
            flOutput = flInput
        if language != "":
            flOutput = flOutput.replace(".", "_{}.".format(language))

        # Continue with the program
        errHandle.Status('Input file is "' + flInput + '"')
        errHandle.Status('Output file is "' + flOutput + '"')
        errHandle.Status('Language is "' + language + '"')

        # Call the function that does the job
        oArgs = {'input': flInput, 'output': flOutput, 'language': language}
        if (not process_flextree(oArgs)) :
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
