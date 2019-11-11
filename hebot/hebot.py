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

def read_table(cur, field_list):
    table = []
    for row in cur:
        item = {}
        for field in field_list:
            item[field] = row[field]
        table.append(item)
    return table

def etcbc_2017_convert(oArgs):
    book_fields = ['first_monad', 'last_monad', 'mdf_book']
    chapter_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter']
    verse_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter', 'mdf_verse']
    sentence_fields = ['object_id_d', 'first_monad', 'last_monad']
    sentence_atom_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent']

    try:
        # Try open the SQL
        conn = sqlite3.connect(oArgs['input'])
        conn.row_factory = sqlite3.Row
        # Create a cursor
        cur = conn.cursor()

        # COllect the books
        cur.execute("select * from book_objects order by first_monad")
        books = read_table(cur, book_fields)

        # Walk through the books
        for book in books:
            # COllect the chapters for this book
            cur.execute("select * from chapter_objects where mdf_book = ? order by first_monad", 
                        str(book['mdf_book']))
            chapters = read_table(cur, chapter_fields)

            # Walk through the chapters
            for chapter in chapters:
                # Get the scope of this chapter
                ch_m_f = chapter['first_monad']
                ch_m_l = chapter['last_monad']

                # Collect the verses of this chapter
                cur.execute("select * from verse_objects where (mdf_book = ? and mdf_chapter = ?) order by first_monad", 
                            [str(book['mdf_book']), str(chapter['mdf_chapter'])])
                verses =  read_table(cur, verse_fields)

                # Walk the verses
                for verse in verses:
                    # Get the scope of this verse
                    vs_m_f = verse['first_monad']
                    vs_m_l = verse['last_monad']

                    # Collect the sentences in this verse
                    cur.execute("select * from sentence_objects where (first_monad >= ? and last_monad <= ?) order by first_monad", 
                                [str(vs_m_f), str(vs_m_l)])
                    sentences =  read_table(cur, sentence_fields)
                    for sentence in sentences:
                        # Get the scope of this sentence
                        s_m_f = sentence['first_monad']
                        s_m_l = sentence['last_monad']
                        # And get my ID
                        sentence_id = sentence['object_id_d']

                        # ALTERNATIVE: collect the CLAUSES under this [sentence_id]

                        # Collect the atoms from this sentence
                        cur.execute("select * from sentence_atom_objects where (mdf_functional_parent = ?) order by first_monad", 
                                    [sentence_id])
                        sentence_atoms = read_table(cur, sentence_atom_fields)
                        for sentence_atom in sentence_atoms:
                            # Get the scope of this sentence
                            sa_m_f = sentence_atom['first_monad']
                            sa_m_l = sentence_atom['last_monad']
                            sentence_atom_id = sentence_atom['object_id_d']


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
