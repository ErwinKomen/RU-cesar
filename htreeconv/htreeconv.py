"""
Convert from and to 'htree', the hierarchical tree

This version created by Erwin R. Komen 
Date: 9/nov/2019 
"""
import sys, getopt, os.path, importlib
import os, sys
import csv, json

# Application specific
import util                 # This allows using ErrHandle
from models import *        # This imports HierObj
from views import ConvertHtreePsdx

errHandle = util.ErrHandle()

# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 19/dec/2018    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv):
    dirInput = ''   # input directory
    dirOutput = ''  # output directory
    sType = ""      # the type of conversion
    bForce = False  # Force means: overwrite
    oConv = None    # Conversion object
    conv_type = [
        {'type': 'htree-psdx', 'src': '.json', 'dst': '.psdx'},
        {'type': 'htree-folia', 'src': '.json', 'dst': '.folia.xml'}
        ]

    try:
        sSyntax = prgName + ' -i <input file> -o <output directory> -t <type of conversion> [-f]'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:t:f", ["-inputdir=", "-outputdir=", "-type=", "-force"])
        except getopt.GetoptError:
            print(sSyntax)
            sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--inputdir"):
                dirInput = arg
            elif opt in ("-o", "--outputdir"):
                dirOutput = arg
            elif opt in ("-t", "--type"):
                sType = arg
                for item in conv_type: 
                    if item['type'] == sType:
                        oConv = item ; break
            elif opt in ("-f", "--force"):
                bForce = True

        # Check if all arguments are there
        if (dirInput == '' or dirOutput == "" or oConv == None):
            errHandle.DoError(sSyntax)
            return False

        # Check if directories exists
        if not os.path.exists(dirInput):
            errHandle.DoError("Input directory does not exist", True)
        if not os.path.exists(dirOutput):
            errHandle.DoError("Output directory does not exist", True)

        # Continue with the program
        errHandle.Status('Input is "' + dirInput + '"')
        errHandle.Status('Output is "' + dirOutput + '"')
        if sType: errHandle.Status("Conversion type: {}".format(oConv['type']))

        # Call the function that does the job
        oArgs = {'input': dirInput,
                 'output': dirOutput,
                 'force': bForce,
                 'conv': oConv}
        if (not htree_convert(oArgs)) :
            errHandle.DoError("Could not complete")
            return False
    
            # All went fine  
        errHandle.Status("Ready")
        return True
    except:
        # act
        errHandle.DoError("main")
        return False

def htree_convert(oArgs):
    """a"""

    try:
        # Figure out which stages there are in conversion
        oConv = oArgs['conv']
        arConvType = oConv['type'].split("-")
        bForce = oArgs['force']

        if arConvType[0] == "htree":
            # Create htree
            oConvert = ConvertHtreePsdx(oArgs['input'])
            oConvert.do_convert(oArgs['output'], bForce)
        elif arConvType[1] == "htree":
            # Stage 1: convert to htree
            arDstFile = do_convert_to_htree(arSourceFile, arConvType[0], oConv['src'])
        else:
            # Stage 1: convert to htree
            arHtreeFile = do_convert_to_htree(arSourceFile, arConvType[0], oConv['src'])
            # Stage 2: convert from htree
            arDstFile = do_convert_from_htree(arHtreeFile, arConvType[1], oConv['dst'])

        return True
    except:
        errHandle.DoError("htree_convert")
        return False

# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
