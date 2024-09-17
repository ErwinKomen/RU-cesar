"""
Purpose: extract free text lines as paragraphs into text file

Original created by by Erwin R. Komen 
Date: 10/may/2021
"""

import getopt, copy, util
import re
import json
import os, sys

errHandle = util.ErrHandle()

def process_verses(oArgs):
    """Process one .txt file from PTX with verses"""

    # Defaults
    flInput = ""
    flOutput = ""
    count = 0

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

        # compile recognition expression
        r_ref = re.compile(r'\s(\d+)\.\s+')

        # Read the file
        lst_data = []
        with open(flInput, "r", encoding="utf-8") as f:
            lst_data = f.readlines()
        lst_out = []

        # Process the data
        for line in lst_data:
            if r_ref.search(line):
                # Start verse numbering
                vsnum = 1
                pos_start = 0
                pos_end = None
                lst_line = []
                # Visit all matches
                for m in r_ref.finditer(line):
                    pos_m = m.span()
                    if pos_end is None:
                        # Save whatever can be done
                        # lst_line.append(line[pos_start:pos_m[0]])
                        # Only store the pos_end and the original verse
                        pos_end = pos_m[0]
                        vs_org = m.groups()[0]
                    else:
                        #pos_start = pos_end
                        #pos_end = pos_m[0]
                        # output verse number
                        lst_line.append("\\v {} ".format(vsnum))
                        # Output previous partition
                        lst_line.append(line[pos_start:pos_end])
                        # Add the XREF
                        xref = "\\x - \\xo 1.{} \\xt Gen 1:{}\\x*".format(vsnum, vs_org)
                        lst_line.append(xref)
                        sLine = " ".join(lst_line)
                        lst_data.append(sLine)
                        # Make ready for the next batch...
                        pos_end = pos_m[0]
                        # Note the pos_start
                        pos_start = pos_m[1]
                        vs_org = m.groups()[0]
                        vsnum += 1
                # We still have brushing up to do
                # output verse number
                lst_line.append("\\v {} ".format(vsnum))
                # Output last partition
                lst_line.append(line[pos_start:pos_end])
                # Add the XREF
                xref = "\\x - \\xo 1.{} \\xt Gen 1:{}\\x*".format(vsnum, vs_org)
                lst_line.append(xref)
                sLine = " ".join(lst_line)
                lst_data.append(sLine)
            else:
                lst_out.append(line)
        # Combine the output        
        data = "\n".join(lst_out)
        # Save the output
        with open(fileout, "w", encoding="utf-8") as f:
            f.write(data)
        print("Ready")
    except:
        sMsg = errHandle.get_error_message()
        errHandle.DoError("process_verses")
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

    try:
        sSyntax = prgName + ' -i <input dir>' + ' -o <output dir>' 
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
        if (not process_verses(oArgs)) :
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
