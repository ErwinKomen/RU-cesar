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
  flInput = ''      # input file name
  dirOutput = ''    # output directory
  dirSurface = ''   # directory for surfaced htree
  sBook = None      # Specific book

  try:
    sSyntax = prgName + ' -i <input file> -o <output directory> [-b <book abbreviation>] [-s <surface directory>]'
    # get all the arguments
    try:
      # Get arguments and options
      opts, args = getopt.getopt(argv, "hi:o:b:s:", ["-inputfile=", "-outputdir=", "-book=", "-surface="])
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
      elif opt in ("-b", "--book"):
        sBook = arg
      elif opt in ("-s", "--surface"):
        dirSurface = arg
    # Check if all arguments are there
    if (flInput == ''):
      errHandle.DoError(sSyntax)

    # Check if output directory exists
    if not os.path.exists(dirOutput):
        errHandle.DoError("Output directory does not exist", True)

    # Check if surface directory exists
    if dirSurface != "" and not os.path.exists(dirSurface):
        errHandle.DoError("Surface directory does not exist", True)

    # Continue with the program
    errHandle.Status('Input is "' + flInput + '"')
    errHandle.Status('Output is "' + dirOutput + '"')
    if sBook: errHandle.Status("Book: {}".format(sBook))
    if dirSurface != "": errHandle  .Status("Surface dir is: {}".format(dirSurface))

    # Call the function that does the job
    oArgs = {'input':   flInput,
             'output':  dirOutput,
             'surface': dirSurface,
             'book':    sBook}
    if (not etcbc_2017_convert(oArgs)) :
      errHandle.DoError("Could not complete")
      return False
    
      # All went fine  
    errHandle.Status("Ready")
  except:
    # act
    errHandle.DoError("main")
    return False

def read_table(cur, field_list, feat_list = None, **kwargs):
    table = []
    try:
        rows = cur.fetchall()
        for row in rows:
            item = {}   # main items
            feat = {}   # features
            value = ""
            for field in field_list:
                # Get the field value into the table
                item[field] = row[field]
                # Possibly translate the field value
                if len(kwargs) > 0:
                    # Get the field value into the features
                    item[field] = row[field]
                    kv_obj = kwargs['kwargs']
                    for k, v in kv_obj.items():
                        if k == field:
                            x = item[field]
                            if not isinstance(x, str) and int(x) < 0:
                                item.pop(field)
                            else:
                                value = v[item[field]]
                                vl = value.lower()
                                if vl == "unknown" or vl == "none" or vl == "n/a" or vl == "absent":
                                    # Remove from the object
                                    item.pop(field)
                                else:
                                    item[field] = value 
            if feat_list:
                for field in feat_list:
                    # Get the field value into the table
                    feat[field] = row[field]
                    # Possibly translate the field value
                    if len(kwargs) > 0:
                        # Get the field value into the features
                        feat[field] = row[field]
                        kv_obj = kwargs['kwargs']
                        for k, v in kv_obj.items():
                            if k == field:
                                x = feat[field]
                                if not isinstance(x, str) and int(x) < 0:
                                    feat.pop(field)
                                else:
                                    value = v[feat[field]]
                                    vl = value.lower()
                                    if vl == "unknown" or vl == "none" or vl == "n/a" or vl == "absent":
                                        # Remove from the object
                                        feat.pop(field)
                                    else:
                                        feat[field] = value
                features = {}
                for k,v in feat.items():
                    k_new = k.replace("mdf_", "")
                    features[k_new] = v
                item['f'] = features

            table.append(item)
        return table
    except:
        errHandle.DoError("read_table")
        return None

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

def read_relation_table(cur, obj, tbl_name):
    fields = ['id_d', 'string_value']
    # Read the table
    cur.execute('select * from {}'.format(tbl_name))
    kv_list = read_table(cur, fields)
    # Transform list values to object
    for item in kv_list:
        key = item['id_d']
        value = item['string_value']
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

def get_text_as_table(cur, first_monad, last_monad, part_of_speech, state, gender, number, 
                      person, verbal_stem, verbal_tense, lexical_set,
                      uvf, pfm, vbs, vbe, prs, language):
    """Read the text from first to last monad"""

    word_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_sp',
                   'mdf_functional_parent', 'mdf_g_lex_utf8', 'mdf_g_word_utf8']
    feat_fields = ['mdf_st', 'mdf_prs_gn', 
                   'mdf_pdp', 'mdf_sp', 'mdf_st', 
                   'mdf_suffix_gender', 'mdf_gn', 'mdf_prs_gn', 
                   'mdf_suffix_number', 'mdf_nu', 'mdf_prs_nu',
                   'mdf_suffix_person', 'mdf_ps', 'mdf_prs_ps',
                   'mdf_vt', 'mdf_ls', 'mdf_language',
                   'mdf_uvf', 'mdf_pfm', 'mdf_vbs', 'mdf_vbe', 'mdf_prs']
    cur.execute("select * from word_objects where (first_monad >= ? and last_monad <= ?) order by first_monad", 
                [first_monad, last_monad])
    tbl_back = read_table(cur, word_fields, feat_fields,
                          kwargs = {'mdf_sp': part_of_speech, 'mdf_pdp': part_of_speech, 'mdf_st': state, 
                                    'mdf_suffix_gender': gender, 'mdf_gn': gender, 'mdf_prs_gn': gender,
                                    'mdf_suffix_number': number, 'mdf_nu': number, 'mdf_prs_nu': number,
                                    'mdf_suffix_person': person, 'mdf_ps': person, 'mdf_prs_ps': person,
                                    'mdf_vt': verbal_tense, 'mdf_vs': verbal_stem, 'mdf_ls': lexical_set,
                                    'mdf_uvf': uvf, 'mdf_pfm': pfm, 'mdf_vbs': vbs, 'mdf_vbe': vbe, 'mdf_prs': prs,
                                    'mdf_language': language})
    return tbl_back

def get_hier_word(hier_obj, first_monad):
    """Look (recursively) in hier_obj to check if there is a WORD with first_monad"""

    # Validate
    if not hier_obj:
        return None
    # Look at this level
    if hier_obj.type and hier_obj.n and hier_obj.n == first_monad:
        return hier_obj
    elif hier_obj.child:
        # Visit all children
        for hier_child in hier_obj.child:
            oChild = get_hier_word(hier_child, first_monad)
            if oChild: 
                return oChild
    else:
        return None
    # REturn empty
    return None

def etcbc_2017_convert(oArgs):

    # Define the fields for each type
    book_fields = ['first_monad', 'last_monad', 'mdf_book']
    chapter_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter']
    verse_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_book', 'mdf_chapter', 'mdf_verse', 'mdf_label']
    sentence_fields = ['object_id_d', 'first_monad', 'last_monad']
    sentence_atom_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent']
    clause_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent', 'mdf_mother', 'mdf_rela', 'mdf_kind', 'mdf_typ']
    phrase_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent', 'mdf_mother', 'mdf_rela', 'mdf_function', 'mdf_typ']
    phrase_atom_fields = ['object_id_d', 'first_monad', 'last_monad', 'mdf_functional_parent', 'mdf_mother', 'mdf_rela', 'mdf_typ']

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
    phrase_atom_relation = {}
    part_of_speech = {}
    state = {}
    gender = {}
    number = {}
    person = {}
    verbal_tense = {}
    verbal_stem = {}
    lexical_set = {}
    uvf = {}
    pfm = {}
    vbs = {}
    vbe = {}    # verbal ending
    prs = {}    # pronominal suffix
    language = {1: "heb", 2: "tmr"}

    # Settings
    do_sentence_atom_objects = False    # Now extinct
    do_hier_word_check = False          # Still valid...

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
        read_relation(cur, phrase_atom_relation, "phrase_atom_relation_t")
        read_relation(cur, part_of_speech, "part_of_speech_t")
        read_relation(cur, state, "state_t")
        read_relation(cur, gender, "gender_t")
        read_relation(cur, number, "number_t")
        read_relation(cur, person, "person_t")
        read_relation(cur, verbal_tense, "verbal_tense_t")
        read_relation(cur, verbal_stem, "verbal_stem_t")
        read_relation(cur, lexical_set, "lexical_set_t")
        read_relation_table(cur, uvf, "word_mdf_uvf_set")
        read_relation_table(cur, pfm, "word_mdf_pfm_set")
        read_relation_table(cur, vbs, "word_mdf_vbs_set")
        read_relation_table(cur, vbe, "word_mdf_vbe_set")
        read_relation_table(cur, prs, "word_mdf_prs_set")

        # COllect the books
        cur.execute("select * from book_objects order by first_monad")
        books = read_table(cur, book_fields)

        # Possibly get the mdf_book of the book
        sBook = oArgs['book']
        mdf_book = None
        if sBook:
            mdf_book = next( item['mdf_book'] for item in BOOKNAMES if item['abbr'] == sBook)

        # Walk through the books
        for book in books:
            # Do we process this book?
            if mdf_book == None or book['mdf_book'] == mdf_book:

                # Create a name for this book
                booknum = book['mdf_book']
                bookname = get_book_name(booknum)
                # Create a file name for this book
                filename = os.path.abspath( os.path.join(oArgs['output'], bookname)) + ".json"
                fsurface = None

                # Are we doing surfacing?
                dirsurface = oArgs['surface']
                if dirsurface != "":
                    # Create a file name for this book's surface output
                    fsurface = os.path.abspath( os.path.join(dirsurface, bookname)) + ".json"

                # COllect the chapters for this book
                cur.execute("select * from chapter_objects where mdf_book = ? order by first_monad", (str(book['mdf_book']),))
                chapters = read_table(cur, chapter_fields)

                # Start a list of SENTENCES in this book
                sentence_list = []
                surface_list = []

                # Walk through the chapters
                for chapter in chapters:
                    # Get the scope of this chapter
                    ch_m_f = chapter['first_monad']
                    ch_m_l = chapter['last_monad']
                    chapter_num = chapter['mdf_chapter']

                    # Collect the verses of this chapter
                    cur.execute("select * from verse_objects where (mdf_book = ? and mdf_chapter = ?) order by first_monad", 
                                [str(booknum), str(chapter_num)])
                    verses =  read_table(cur, verse_fields)

                    # Walk the verses
                    for verse in verses:
                        # Make sure we register the chapter and the verse number
                        ch_num = verse['mdf_chapter']
                        vs_num = verse['mdf_verse']
                        label = verse['mdf_label'].strip()

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
                            # Just show where we are
                            errHandle.Status("Processing: {} - d.{}.p.{}.s.{}".format(label, ch_num, vs_num, sent_num))

                            # Get the scope of this sentence
                            s_m_f = sentence['first_monad']
                            s_m_l = sentence['last_monad']
                            # And get my ID
                            sentence_id = sentence['object_id_d']
                            # And get the text of this unit
                            sentence_table = get_text_as_table(cur, s_m_f, s_m_l, 
                                part_of_speech, state, gender, number, person, verbal_stem, verbal_tense, lexical_set,
                                uvf, pfm, vbs, vbe, prs, language)
                            sentence_txt = get_text(sentence_table, s_m_f, s_m_l)

                            # Start a list of child-mother connections that need to be made after the clauses have been done
                            child_to_mother = []

                            # Start a hierarchical object for this sentence
                            hier_sent = SentenceObj(label=label, sent=sent_num, txt=sentence_txt, div=ch_num, divpar=vs_num)

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

                                # Check out the mdf_mother
                                clause_mother = clause['mdf_mother']

                                # Make sure we have the clause type, clause category
                                pos_clause = clause['mdf_kind']

                                # Create a HierObj for this clause
                                hier_clause = HierObj(hier_sent, pos=pos_clause, txt=clause_txt, parent=hier_sent, id=clause_id)
                            
                                # Read the phrases in this clause
                                cur.execute("select * from phrase_objects where (mdf_functional_parent = ?) order by first_monad", 
                                            [clause_id])
                                phrases = read_table(cur, phrase_fields, 
                                                     kwargs = {'mdf_rela': phrase_relation,
                                                               'mdf_typ': phrase_type, 'mdf_function': phrase_function})
                                # Walk the phrases
                                for phrase in phrases:
                                    # Get the scope of this phrase
                                    phr_m_f = phrase['first_monad']
                                    phr_m_l = phrase['last_monad']
                                    # Get my ID
                                    phrase_id = phrase['object_id_d']
                                    # Get the text of this unit
                                    phrase_txt = get_text(sentence_table, phr_m_f, phr_m_l)

                                    # Check out the mdf_mother
                                    phrase_mother = phrase['mdf_mother']

                                    # Get the Grammatical category of this phrase
                                    pos_phrase = "{}-{}".format(phrase['mdf_typ'], phrase['mdf_function'])

                                    # Create a HierObj for this phrase
                                    hier_phrase = HierObj(hier_sent, pos=pos_phrase, txt=phrase_txt, parent=hier_clause, id=phrase_id)

                                    # Read the phrase-atoms in this phrase
                                    cur.execute("select * from phrase_atom_objects where (mdf_functional_parent = ?) order by first_monad", 
                                                [phrase_id])
                                    try:
                                        phrase_atoms = read_table(cur, phrase_atom_fields, 
                                                             kwargs = {'mdf_rela': phrase_atom_relation,
                                                                       'mdf_typ': phrase_type})
                                    except:
                                        msg = errHandle.get_error_message()
                                        iStop = 1

                                    # Walk the phrase-atoms
                                    for phrase_atom in phrase_atoms:
                                        # Get the scope of this phrase_atom
                                        phra_m_f = phrase_atom['first_monad']
                                        phra_m_l = phrase_atom['last_monad']
                                        # Get my ID
                                        phrase_atom_id = phrase_atom['object_id_d']
                                        # Get the text of this unit
                                        phrase_atom_txt = get_text(sentence_table, phra_m_f, phra_m_l)

                                        # Check out the mdf_mother
                                        phrase_atom_mother = phrase_atom['mdf_mother']

                                        # Get the Grammatical category of this phrase
                                        pos_phrase_atom = "{}".format(phrase_atom['mdf_typ'])

                                        # Create a HierObj for this phrase_atom
                                        hier_phrase_atom = HierObj(hier_sent, pos=pos_phrase_atom, txt=phrase_atom_txt, parent=hier_phrase, id=phrase_atom_id)

                                        # Get all the words in this phrase_atom and read them in as end-nodes
                                        for row in sentence_table:
                                            first_monad = row['first_monad']
                                            if first_monad >= phra_m_f and row['last_monad'] <= phra_m_l:

                                                # Only do checking if this is intentional
                                                if do_hier_word_check:
                                                    # Check if this word has already been attached somewhere else in [hier_sent]
                                                    hier_word = get_hier_word(hier_sent, first_monad)

                                                    if hier_word:
                                                        # Remove it from its current parent
                                                        hier_parent = hier_word.parent
                                                        hier_parent.child.remove(hier_word)
                                                        hier_word.parent = hier_phrase_atom
                                                        iStop = 1

                                                # Get the features for this word
                                                feature_list = []
                                                feature_list.append({'name': 'lemma', 'value': row['mdf_g_lex_utf8']})
                                                for k, v in row['f'].items():
                                                    feature_list.append(dict(name=k, value=v))

                                                # Add this row as end node
                                                hier_word = None
                                                hier_word = HierObj(hier_sent, pos=row['mdf_sp'], txt=row['mdf_g_word_utf8'], id=row['object_id_d'])
                                                hier_word.type = "Vern"
                                                hier_word.f = feature_list
                                                hier_word.child = None
                                                hier_word.n = first_monad
                                                hier_word.parent = hier_phrase_atom

                                                # Add this word to the phrase
                                                hier_phrase_atom.child.append(hier_word)

                                        # Add the phrase_atom to the above
                                        if phrase_atom_mother == 0:
                                            hier_phrase.child.append(hier_phrase_atom)
                                        else:
                                            # add to the list
                                            child_to_mother.append(dict(obj=hier_phrase_atom, id=phrase_atom_mother))

                                    # Add the phrase to the above
                                    if phrase_mother == 0:
                                        hier_clause.child.append(hier_phrase)
                                    else:
                                        # add to the list
                                        child_to_mother.append(dict(obj=hier_phrase, id=phrase_mother))

                                # And add the clause as child under the sentence
                                if clause_mother == 0:
                                    hier_sent.child.append(hier_clause)
                                else:
                                    # add to the list
                                    child_to_mother.append(dict(obj=hier_clause, id=clause_mother))

                            # Check the child-to-mother relations
                            for relation in child_to_mother:
                                id = relation['id']
                                obj = relation['obj']
                                mother = hier_sent.find(id)
                                if not mother:
                                    iStop = 1
                                if not mother.child:
                                    mother = mother.parent
                                mother.child.append(obj)
                                obj.parent = mother

                            # Simplification of the tree
                            hier_sent.simplify()

                            # Add the object to the list of sentences
                            sentence_list.append(hier_sent.get_object())

                            # Do we do surfacing?
                            if fsurface:
                                # Get a surface representation of the sentence
                                surface_sent = hier_sent.copy_surface()
                                # Append it to the surface list
                                surface_list.append(surface_sent.get_object())

                # Create the object of this book
                book_obj = dict(sentence_list=sentence_list, name=bookname)

                # Write the object to the file
                with open(filename, "w") as f:
                    json.dump(book_obj, f, indent=2)

                if fsurface:
                    # Make an object for the book as a whole
                    book_obj_surface = dict(sentence_list=surface_list, name=bookname)
                    # Write the surface output
                    with open(fsurface, "w") as f:
                        json.dump(book_obj_surface, f, indent=2)

        return True
    except:
        errHandle.DoError("etcbc_2017_convert")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
