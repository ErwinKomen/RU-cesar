"""
Purpose: SFM clean up - create clean verse numbering and add xr correctly

Original created by by Erwin R. Komen 
Date: 22/aug/2024

DEBUG:
    -i "D:\ptx\GGT_T\94XXAGGT_T.SFM" 
    -o "D:\ptx\GGT_T\94XXAGGT_T.SFM.out"

"""

# import lxml.etree as et
import xml.etree.ElementTree as et
import getopt, copy, util
import re
import json
import os, sys

errHandle = util.ErrHandle()

def process_sfmclean(oArgs):
    """Clean up one .sfm file into an output .sfm file"""

    def get_word(sLine):
        sText = ""
        m = re.match(pat, sLine)
        if m:
            sText = m.group()
            # Get remainder of the string
            start = m.span()[1]
            sLine = sLine[start:].strip()
        return sText, sLine

    def get_sfm(sLine):
        """Get the SFM marker plus the remainder of the line"""

        sArg = ""
        sRem = ""
        sMarker = ""
        if sLine[0] == "\\":
            # Get first \s position or the end of the string
            sMarker, sRem = get_word(sLine[1:])
            if sMarker in ["v", "c", "d"]:
                sArg, sRem = get_word(sRem)
        # Return what we found
        return sMarker, sArg, sRem


    # Defaults
    pat = r'^\S*'
    flInput = ""
    flOutput = ""
    count = 0
    bResult = True
    lst_output = []

    try:
        # Recover the arguments
        if "input" in oArgs: flInput = oArgs["input"]
        if "output" in oArgs: flOutput = oArgs["output"]

        # Check input directory
        if not os.path.exists(flInput) :
            errHandle.Status("Please specify an existing input file")
            return False

        # Show where we are
        errHandle.Status("Processing file: {}".format(flInput))

        # read the SFM into a list of lines
        lines = []
        with open(flInput, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Walk the lines, figuring out which SFM (if any) this has
        iChapter = 0
        iVerse = 0
        sRefCh = "1"
        sRefVerse = "1"
        for line in lines:
            # Strip newlines
            line = line.strip('\n')
            # Is this SFM?
            if line and line[0] == "\\":
                # This is SFM
                sMarker, sArg, sRem = get_sfm(line)
                # Action depends on the marker
                if sMarker == "c":
                    # Process new chapter and start new verse
                    iChapter = int(sArg)
                    iVerse = 0
                    sRefCh = sArg
                    sRefVerse = "1"
                    # Also output
                    lst_output.append(line)

                elif sMarker == "v":
                    # Process new verse
                    iVerse += 1
                    # The argument contains the verse number for the Xref
                    if sArg and sRefVerse and int(sArg) < int(sRefVerse):
                        sRefCh = str(int(sRefCh) + 1)
                    sRefVerse = sArg
                    sRef = "\\x - \\xo {}.{} \\xt Gen {}:{}\\x*".format(iChapter, iVerse, sRefCh, sRefVerse)
                    # Output new combined verse
                    sOut = "\\v {} {}{}".format(iVerse, sRem, sRef)
                    lst_output.append(sOut)

                elif sMarker == "p" and sRem != "":
                    # This is a new paragraph, but with contents
                    lst_output.append("\\p")
                    for sPart in sRem.split("."):
                        sPart = sPart.strip()
                        if sPart != "":
                            sPart = sPart + "."
                            iVerse += 1
                            # Output new combined verse
                            sOut = "\\v {} {}".format(iVerse, sPart)
                            lst_output.append(sOut)

                elif sMarker == "d":
                    # Pick up the reference chapter
                    sRefCh = sArg
                    # NOTE: do *NOT* output this line

                else:
                    # Just copy the input to the output
                    lst_output.append(line)
            else:
                # Just copy the input to the output
                lst_output.append(line)

        # Convert output into string
        sData = "\n".join(lst_output)
        # Save the output
        with open(flOutput, "w", encoding="utf-8") as f:
            f.write(sData)

        # Finish up nicely
        print("Ready")
    except:
        sMsg = errHandle.get_error_message()
        errHandle.DoError("process_sfmclean")
        bResult = False

    return bResult


# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 29/apr/2019    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
    flInput = ''        # input file name
    flOutput = ""       # Output file

    try:
        sSyntax = prgName + ' -i <input file>' + ' -o <output file>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:", ["-input=", "-output="])
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
        # Check if all arguments are there
        if (flInput == ''):
            errHandle.DoError(sSyntax, True)

        # Determine what the output directory will be
        if flOutput == "":
            flOutput = flInput

        # Continue with the program
        errHandle.Status('Input file is "' + flInput + '"')
        errHandle.Status('Output file is "' + flOutput + '"')

        # Call the function that does the job
        oArgs = {'input': flInput, 'output': flOutput}
        if (not process_sfmclean(oArgs)) :
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

