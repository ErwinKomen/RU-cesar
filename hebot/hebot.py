"""
Convert ETCBC_2017 to hierarchical JSON

This version created by Erwin R. Komen 
Date: 9/nov/2019 
"""
import sys, getopt, os.path, importlib
import os, sys
import csv, json
import sqlite3

# Application specific
import util
from models import *

errHandle = util.ErrHandle()

BOOKNAMES = [{"mdf_book": 1 , "name": "Genesis", "abbr": "GEN"},
            {"mdf_book": 2 , "name": "Exodus", "abbr": "EXO"},
            {"mdf_book": 3 , "name": "Leviticus", "abbr": "LEV"},
            {"mdf_book": 4 , "name": "Numbers", "abbr": "NUM"},
            {"mdf_book": 5 , "name": "Deuteronomy", "abbr": "DEU"},
            {"mdf_book": 6 , "name": "Joshua", "abbr": "JOS"},
            {"mdf_book": 7 , "name": "Judges", "abbr": "JDG"},
            {"mdf_book": 8 , "name": "Ruth", "abbr": "RUT"},
            {"mdf_book": 9 , "name": "1_Samuel", "abbr": "1SA"},
            {"mdf_book": 10 , "name": "2_Samuel", "abbr": "2SA"},
            {"mdf_book": 11 , "name": "1_Kings", "abbr": "1KI"},
            {"mdf_book": 12 , "name": "2_Kings", "abbr": "2KI"},
            {"mdf_book": 13 , "name": "1_Chronicles", "abbr": "1CH"},
            {"mdf_book": 14 , "name": "2_Chronicles", "abbr": "2CH"},
            {"mdf_book": 15 , "name": "Ezra", "abbr": "EZR"},
            {"mdf_book": 16 , "name": "Nehemiah", "abbr": "NEH"},
            {"mdf_book": 17 , "name": "Esther", "abbr": "EST"},
            {"mdf_book": 18 , "name": "Job", "abbr": "JOB"},
            {"mdf_book": 19 , "name": "Psalms", "abbr": "PSA"},
            {"mdf_book": 20 , "name": "Proverbs", "abbr": "PRO"},
            {"mdf_book": 21 , "name": "Ecclesiastes", "abbr": "ECC"},
            {"mdf_book": 22 , "name": "Song_of_songs", "abbr": "SNG"},
            {"mdf_book": 23 , "name": "Isaiah", "abbr": "ISA"},
            {"mdf_book": 24 , "name": "Jeremiah", "abbr": "JER"},
            {"mdf_book": 25 , "name": "Lamentations", "abbr": "LAM"},
            {"mdf_book": 26 , "name": "Ezekiel", "abbr": "EZK"},
            {"mdf_book": 27 , "name": "Daniel", "abbr": "DAN"},
            {"mdf_book": 28 , "name": "Hosea", "abbr": "HOS"},
            {"mdf_book": 29 , "name": "Joel", "abbr": "JOL"},
            {"mdf_book": 30 , "name": "Amos", "abbr": "AMO"},
            {"mdf_book": 31 , "name": "Obadiah", "abbr": "OBA"},
            {"mdf_book": 32 , "name": "Jonah", "abbr": "JON"},
            {"mdf_book": 33 , "name": "Micah", "abbr": "MIC"},
            {"mdf_book": 34 , "name": "Nahum", "abbr": "NAH"},
            {"mdf_book": 35 , "name": "Habakkuk", "abbr": "HAB"},
            {"mdf_book": 36 , "name": "Zephaniah", "abbr": "ZEP"},
            {"mdf_book": 37 , "name": "Haggai", "abbr": "HAG"},
            {"mdf_book": 38 , "name": "Zechariah", "abbr": "ZEC"},
            {"mdf_book": 39 , "name": "Malachi", "abbr": "MAL"}]

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

def read_table(cur, field_list, **kwargs):
    table = []
    rows = cur.fetchall()
    for row in rows:
        item = {}
        for field in field_list:
            # Get the field value into the table
            item[field] = row[field]
            # Possibly translate the field value
            if len(kwargs) > 0:
                kv_obj = kwargs['kwargs']
                for k, v in kv_obj.items():
                    if k == field:
                        item[field] = v[item[field]]
        table.append(item)
    return table

def get_book_name(mdf_book, type=""):
    sBack = ""
    for bk in BOOKNAMES:
        if bk['mdf_book'] == mdf_book:
            if type == "":
                sBack = bk['name']
            elif type == "abbr":
                sBack = bk['abbr']
            break
    return sBack

def read_relation(cur, obj, enum_name):
    enum_fields = ['enum_id', 'enum_name']
    enum_const_fields = ['enum_value_name', 'value']
    # Get the enum_id
    cur.execute('select * from enumerations where enum_name = ?', [enum_name])
    enum_kv_list = read_table(cur, enum_fields)
    if len(enum_kv_list) > 0:
        enum_id = enum_kv_list[0]['enum_id']
        # Now read the table
        cur.execute("select * from enumeration_constants where enum_id = ?", [str(enum_id)])
        enum_const_list = read_table(cur, enum_const_fields)
        # Transform list values to object
        for item in enum_const_list:
            key = item['value']
            value = item['enum_value_name']
            obj[key] = value

def get_text(tbl_sentence, first_monad, last_monad):
    """Read the text from first to last monad"""

    sBack = ""
    lText = []
    for row in tbl_sentence:
        if row['first_monad'] >= first_monad and row['last_monad'] <= last_monad:
            lText.append(row["mdf_g_word_utf8"])
    # Combine the words into a sentence
    sBack = " ".join(lText)
    return sBack

def get_text_as_table(cur, first_monad, last_monad, part_of_speech, state, gender):
    """Read the text from first to last monad"""

    word_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_sp', 'mdf_st', 'mdf_prs_gn', 'mdf_functional_parent',
                   'mdf_g_lex_utf8', 'mdf_g_word_utf8']
    cur.execute("select * from word_objects where (first_monad >= ? and last_monad <= ?) order by first_monad", 
                [first_monad, last_monad])
    tbl_back = read_table(cur, word_fields, 
                          kwargs = {'mdf_sp': part_of_speech, 'mdf_st': state, 'mdf_prs_gn': gender})
    return tbl_back


def etcbc_2017_convert(oArgs):

    # Define the fields for each type
    book_fields = ['first_monad', 'last_monad', 'mdf_book']
    chapter_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter']
    verse_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter', 'mdf_verse', 'mdf_label']
    sentence_fields = ['object_id_d', 'first_monad', 'last_monad']
    sentence_atom_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent']
    clause_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent', 'mdf_mother', 'mdf_rela', 'mdf_kind', 'mdf_typ']
    phrase_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent', 'mdf_mother', 'mdf_rela', 'mdf_function', 'mdf_typ']

    # Necessary for the interpretation of type, kind etc
    clause_constituent_relation = {}
    phrase_relation = {}
    clause_type = {}
    clause_kind = {}
    clause_atom_type = {}
    phrase_type = {}
    phrase_relation = {}
    phrase_function = {}
    subphrase_relation = {}
    part_of_speech = {}
    state = {}
    gender = {}

    # Settings
    do_sentence_atom_objects = False

    try:
        # Try open the SQL
        conn = sqlite3.connect(oArgs['input'])
        conn.row_factory = sqlite3.Row
        # Create a cursor
        cur = conn.cursor()

        # Read different relations
        read_relation(cur, clause_constituent_relation, "clause_constituent_relation_t")
        read_relation(cur, phrase_relation, "phrase_relation_t")
        read_relation(cur, clause_type, "clause_type_t")
        read_relation(cur, clause_kind, "clause_kind_t")
        read_relation(cur, clause_atom_type, "clause_atom_type_t")
        read_relation(cur, phrase_type, "phrase_type_t")
        read_relation(cur, phrase_relation, "phrase_relation_t")
        read_relation(cur, phrase_function, "phrase_function_t")
        read_relation(cur, subphrase_relation, "subphrase_relation_t")
        read_relation(cur, part_of_speech, "part_of_speech_t")
        read_relation(cur, state, "state_t")
        read_relation(cur, gender, "gender_t")

        # COllect the books
        cur.execute("select * from book_objects order by first_monad")
        books = read_table(cur, book_fields)

        # Walk through the books
        for book in books:
            # Create a name for this book
            bookname = get_book_name(book['mdf_book'])
            # Create a file name for this book
            filename = os.path.abspath( os.path.join(oArgs['output'], bookname)) + ".json"

            # COllect the chapters for this book
            cur.execute("select * from chapter_objects where mdf_book = ? order by first_monad", 
                        str(book['mdf_book']))
            chapters = read_table(cur, chapter_fields)

            # Start a list of SENTENCES in this book
            sentence_list = []

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
                    # Make sure we register the chapter and the verse number
                    ch_num = verse['mdf_chapter']
                    vs_num = verse['mdf_verse']
                    label = verse['mdf_label']

                    # Just show where we are
                    errHandle.Status("Processing: {}".format(label))

                    # Get the scope of this verse
                    vs_m_f = verse['first_monad']
                    vs_m_l = verse['last_monad']

                    # Collect the sentences in this verse
                    cur.execute("select * from sentence_objects where (first_monad >= ? and last_monad <= ?) order by first_monad", 
                                [str(vs_m_f), str(vs_m_l)])
                    sentences =  read_table(cur, sentence_fields)
                    sent_num = 0
                    for sentence in sentences:
                        sent_num += 1
                        # Get the scope of this sentence
                        s_m_f = sentence['first_monad']
                        s_m_l = sentence['last_monad']
                        # And get my ID
                        sentence_id = sentence['object_id_d']
                        # And get the text of this unit
                        sentence_table = get_text_as_table(cur, s_m_f, s_m_l, part_of_speech, state, gender)
                        sentence_txt = get_text(sentence_table, s_m_f, s_m_l)

                        # Start a hierarchical object for this sentence
                        # hier_sent = None
                        hier_sent = SentenceObj(label=label, sent=sent_num, txt=sentence_txt)

                        # Collect the atoms from this sentence
                        if do_sentence_atom_objects:
                            cur.execute("select * from sentence_atom_objects where (mdf_functional_parent = ?) order by first_monad", 
                                        [sentence_id])
                            sentence_atoms = read_table(cur, sentence_atom_fields)
                            for sentence_atom in sentence_atoms:
                                # Get the scope of this sentence
                                sa_m_f = sentence_atom['first_monad']
                                sa_m_l = sentence_atom['last_monad']
                                sentence_atom_id = sentence_atom['object_id_d']

                        # ALTERNATIVE: collect the CLAUSES under this [sentence_id]
                        cur.execute("select * from clause_objects where (mdf_functional_parent = ?) order by first_monad", 
                                    [sentence_id])
                        clauses = read_table(cur, clause_fields, 
                                             kwargs = {'mdf_rela': clause_constituent_relation,
                                              'mdf_typ': clause_type, 'mdf_kind': clause_kind})
                        for clause in clauses:
                            # Get the scope of this sentence
                            cl_m_f = clause['first_monad']
                            cl_m_l = clause['last_monad']
                            # And get my ID
                            clause_id = clause['object_id_d']
                            # And get the text of this unit
                            clause_txt = get_text(sentence_table, cl_m_f, cl_m_l)

                            # Make sure we have the clause type, clause category
                            pos_clause = clause['mdf_kind']

                            # Create a HierObj for this clause
                            # hier_clause = None
                            hier_clause = HierObj(pos=pos_clause, txt=clause_txt)
                            
                            # Read the phrases in this clause
                            cur.execute("select * from phrase_objects where (mdf_functional_parent = ?) order by first_monad", 
                                        [clause_id])
                            phrases = read_table(cur, phrase_fields, 
                                                 kwargs = {'mdf_rela': phrase_relation,
                                                           'mdf_typ': phrase_type, 'mdf_function': phrase_function})
                            # Walk the phrases
                            for phrase in phrases:
                                # Get the scope of this sentence
                                phr_m_f = phrase['first_monad']
                                phr_m_l = phrase['last_monad']
                                # And get my ID
                                phrase_id = phrase['object_id_d']
                                # And get the text of this unit
                                phrase_txt = get_text(sentence_table, phr_m_f, phr_m_l)

                                # Get the Grammatical category of this phrase
                                pos_phrase = "{}-{}".format(phrase['mdf_typ'], phrase['mdf_function'])

                                # Create a HierObj for this phrase
                                # hier_phrase = None
                                hier_phrase = HierObj(pos=pos_phrase, txt=phrase_txt)

                                # Get all the words in this phrase and read them in as end-nodes
                                for row in sentence_table:
                                    if row['first_monad'] >= phr_m_f and row['last_monad'] <= phr_m_l:
                                        # Get the features for this word
                                        feature_list = []
                                        feature_list.append({'name': 'lemma', 'value': row['mdf_g_lex_utf8']})
                                        # Add this row as end node
                                        hier_word = None
                                        hier_word = HierObj(pos=row['mdf_sp'], txt=row['mdf_g_word_utf8'])
                                        hier_word.type = "Vern"
                                        hier_word.f = feature_list
                                        hier_word.child = None
                                        # Add this word to the phrase
                                        # hier_phrase.add_child(hier_word)
                                        hier_phrase.child.append(hier_word)
                                # Add the phrase to the above
                                # hier_clause.add_child(hier_phrase)
                                hier_clause.child.append(hier_phrase)

                            # And add the clause as child under the sentence
                            # hier_sent.add_child(hier_clause)
                            hier_sent.child.append(hier_clause)

                        # Add the object to the list of sentences
                        sentence_list.append(hier_sent.get_object())

            # Create the object of this book
            book_obj = dict(sentence_list=sentence_list, name=bookname)

            # Write the object to the file
            with open(filename, "w") as f:
                json.dump(book_obj, f, indent=2)

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
