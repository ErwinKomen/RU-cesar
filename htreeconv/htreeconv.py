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
from views import ConvertHtreePsdx, ConvertHtreeFolia, ConvertHtreeLowfat,\
                  ConvertLowfatHtree, ConvertFoliaHtree, ConvertPsdxHtree,\
                  ConvertHtreeSurface, ConvertSurfaceHtree, ConvertPsdHtree
from hebviews import etcbc_2017_convert
                  

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
    l_div = -1
    l_par = -1
    l_sen = -1
    location = None
    sBook = None    # Possible book
    bForce = False  # Force means: overwrite
    bCmdi = False   # Add CMDI file
    oConv = None    # Conversion object
    debug = None    # Debugging
    conv_type = [
        {'type': 'lowfat-htree', 'src': '.xml', 'dst': '.json'},
        {'type': 'psd-htree', 'src': '.psd', 'dst': '.json'},
        {'type': 'htree-psdx', 'src': '.json', 'dst': '.psdx'},
        {'type': 'htree-folia', 'src': '.json', 'dst': '.folia.xml'},
        {'type': 'htree-lowfat', 'src': '.json', 'dst': '.xml'},
        {'type': 'htree-surface', 'src': '.json', 'dst': '.json'}
        ]

    try:
        sSyntax = prgName + ' -i <input file> -o <output directory> -t <type of conversion> [-f] [-b <book>] [-l <d.N.p.M.s.P>] [-d <level>]'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:t:fcb:d:l:", ["-inputdir=", "-outputdir=", "-type=", "-force", "-cmdi", "-book=", "-debug="])
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
            elif opt in ("-b", "--book"):
                sBook = arg
            elif opt in ("-l", "--location"):
                location = arg
            elif opt in ("-d", "--debug"):
                try:
                    debug = int(arg)
                except:
                    debug = 10
            elif opt in ("-t", "--type"):
                sType = arg
                for item in conv_type: 
                    if item['type'] == sType:
                        oConv = item ; break
            elif opt in ("-f", "--force"):
                bForce = True
            elif opt in ("-c", "--cmdi"):
                bCmdi = True

        # Check if all arguments are there
        if (dirInput == '' or dirOutput == "" or oConv == None):
            errHandle.DoError(sSyntax)
            return False

        # Check if directories exists
        if not os.path.exists(dirInput):
            errHandle.DoError("Input directory does not exist", True)
        if not os.path.exists(dirOutput):
            errHandle.DoError("Output directory does not exist", True)

        # Possibly read the location
        if location and location != "":
            arLoc = location.split(".")
            idx = 0
            while idx * 2 < len(arLoc):
                part = arLoc[idx*2]
                number = arLoc[idx*2+1]
                idx += 1
                if part == "d":
                    l_div = int(number)
                elif part == "p":
                    l_par = int(number)
                elif part == "s":
                    l_sen = int(number)

        # Continue with the program
        errHandle.Status('Input is "' + dirInput + '"')
        errHandle.Status('Output is "' + dirOutput + '"')
        if sType: errHandle.Status("Conversion type: {}".format(oConv['type']))

        # Call the function that does the job
        oArgs = {'input': dirInput,
                 'output': dirOutput,
                 'force': bForce,
                 'cmdi': bCmdi,
                 'book': sBook, 
                 'debug': debug,
                 'conv': oConv}
        if l_div >=0: oArgs['div'] = l_div
        if l_par >=0: oArgs['par'] = l_par
        if l_sen >=0: oArgs['sen'] = l_sen
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

    oToHtree = {'lowfat': ConvertLowfatHtree, 
                'folia': ConvertFoliaHtree,
                'psd': ConvertPsdHtree,
                'psdx': ConvertPsdxHtree}
    oFromHtree = {'lowfat': ConvertHtreeLowfat,
                  'folia': ConvertHtreeFolia,
                  'psdx': ConvertHtreePsdx}

    try:
        # Figure out which stages there are in conversion
        oConv = oArgs['conv']
        arConvType = oConv['type'].split("-")
        bForce = oArgs['force']
        bCmdi = oArgs['cmdi']
        sBook = oArgs['book']
        debug = oArgs['debug']

        if arConvType[0] == "surface":
            # Convert 'surfaced' Htree into 'plain' Htree (not taking word order in account)
            oConvert = ConvertSurfaceHtree(oArgs['input'])
            oConvert.do_htree_htree(oArgs['output'], bForce, sBook=sBook, debug=debug)
        elif arConvType[1] == "surface":
            # Convert un-ordered Htree into 'surfaced' Htree
            oConvert = ConvertHtreeSurface(oArgs['input'])
            oConvert.do_htree_htree(oArgs['output'], bForce, sBook=sBook, debug=debug)
        elif arConvType[0] == "htree":
            # Create XML from htree
            cls = oFromHtree[arConvType[1]]
            oConvert = cls(oArgs['input'])
            oConvert.do_htree_xml(oArgs['output'], bForce, sBook=sBook, cmdi=bCmdi, debug=debug)
        elif arConvType[1] == "htree":
            if arConvType[0] == "etcbc":
                # Convert from Hebrew ETCBC2017 to Htree
                response = etcbc_2017_convert(oArgs)
            elif arConvType[0] == "psd":
                # Convert from bracketed labelling to Htree
                cls = oToHtree[arConvType[0]]
                oConvert = cls(oArgs['input'])
                oConvert.do_xml_htree(oArgs['output'], bForce, sBook=sBook, psd=True, debug=debug)
            else:
                # Create htree from XML
                cls = oToHtree[arConvType[0]]
                oConvert = cls(oArgs['input'])
                oConvert.do_xml_htree(oArgs['output'], bForce, sBook=sBook, debug=debug)
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
