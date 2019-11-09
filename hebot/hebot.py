"""
Convert ETCBC_2017 to hierarchical JSON

This version created by Erwin R. Komen 
Date: 9/nov/2019 
"""
import sys, getopt, os.path, importlib
import os, sys
import util, csv, json
import sqlite3

errHandle = util.ErrHandle()

# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 19/dec/2018    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
  flInput = ''        # input file name
  dirOutput = ''        # output directory

  try:
    sSyntax = prgName + ' -i <input file> -o <output directory>'
    # get all the arguments
    try:
      # Get arguments and options
      opts, args = getopt.getopt(argv, "hi:o:", ["-inputfile=", "-outputdir="])
    except getopt.GetoptError:
      print(sSyntax)
      sys.exit(2)
    # Walk all the arguments
    for opt, arg in opts:
      if opt in ("-h", "--help"):
        print(sSyntax)
        sys.exit(0)
      elif opt in ("-i", "--inputfile"):
        flInput = arg
      elif opt in ("-o", "--outputdir"):
        dirOutput = arg
    # Check if all arguments are there
    if (flInput == ''):
      errHandle.DoError(sSyntax)

    # Check if output directory exists
    if not os.path.exists(dirOutput):
        errHandle.DoError("Output directory does not exist", True)

    # Continue with the program
    errHandle.Status('Input is "' + flInput + '"')
    errHandle.Status('Output is "' + dirOutput + '"')

    # Call the function that does the job
    oArgs = {'input': flInput,
             'output': dirOutput}
    if (not etcbc_2017_convert(oArgs)) :
      errHandle.DoError("Could not complete")
      return False
    
      # All went fine  
    errHandle.Status("Ready")
  except:
    # act
    errHandle.DoError("main")
    return False

def etcbc_2017_convert(oArgs):

    try:
        # Try open the SQL
        conn = sqlite3.connect(oArgs['input'])
        conn.row_factory = sqlite3.Row
        # Create a cursor
        cur = conn.cursor()

        # Start at the sentence level
        cur.execute("select * from sentence_objects order by first_monad")
        for row in cur:
            # Check the scope of this sentence
            first_monad = row['first_monad']
            last_monad = row['last_monad']

        return True
    except:
        errHandle.DoError("main")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
