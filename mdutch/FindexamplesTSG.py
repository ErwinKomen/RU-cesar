import re
import os
import sys
import json
import csv
import pandas as pd

# Add a comment before the incorrect "corpusdirectory" path
corpusdirectory = "U:/Corpora/Middle Dutch/Compilatiecorpus Historisch Nederlands 1.0/Compilatiecorpus Historisch Nederlands 1.0/Geannoteerd deelcorpus narratieve teksten 1575_2000/"
corpusdirectory = "d:/data files/corpora/tara/PythonMiddelnederlands"

# The filename stays the same
coornhert_file = "doneholland_1585_coornhert_1.syn.txt"
result_file_json = "coornhert.json"
result_file_csv = "coornhert.csv"

# This combines the path and the filename into an absolute path, depending on which OS we are
coornhert = os.path.abspath(os.path.join(corpusdirectory, coornhert_file))
result_file_json = os.path.abspath(os.path.join(corpusdirectory, result_file_json))
result_file_csv = os.path.abspath(os.path.join(corpusdirectory, result_file_csv))

# Initializations
target = []
re_hierar = re.compile(r'(\[(?:\[??[^\[]*?\.\/\]))+')
re_number = re.compile(r'^\d+$')
re_constituents = re.compile(r'\w\/')

def status(msg):
    """Simple console status logging"""
    print(msg, file=sys.stderr)

def add_result(result=[], chunk="", head=-1, func="", number=-1, level=-1):
    """Add one result to the array"""

    # Check if there are any constituents in this
    constituents = []
    wordorder = ""
    if '/' in chunk:
        lst_func = re_constituents.findall(chunk)
        lst_cons = re_constituents.split(chunk)
        # Reduce constituents if the first one is empty
        if lst_cons[0] == "": lst_cons = lst_cons[1:]
        else: 
            lst_func.insert(0, "")
        # Store the word-order in a list
        lst_wordorder = []
        # Combine functions and constituents
        for idx, func in enumerate(lst_func):
            func = func.split("/")[0]
            cons = lst_cons[idx]
            lst_wordorder.append("0" if func == "" else func)
            constituents.append(dict(func=func, text=cons))
        # Combine word order into a list
        wordorder = "-".join(lst_wordorder)
    # Store the result
    obj = dict(num=number,
               text=chunk, 
               head=head,
               level=level,
               func=func,
               wordorder=wordorder,
               cons=constituents)
    result.append(obj)
    return True

def get_chunk_function(chunk):
    """Extract the function of the following part from the end of chunk"""
    func = ""
    if chunk[-1] == "/":
        arPart = chunk.split(" ")
        arLast = arPart[-1].split("/")
        func = arLast[0]
        num = len(arPart) - 1
        chunk = " ".join(arPart[0:num])
    # Return the result
    return func, chunk

def parse_line(s, i=0, result=[], head=-1, level=-1, number=-1):
    """Parse one line 's' into chunks that are hierarchically connected

    Each result is an object consistent of these parts:
      'num'     - the number of the line we are all part of
      'text'    - the text of this chunk
      'head'    - the index of the chunk under which it resides
      'level'   - level of embedding
      'func'    - optional 'function' of the chunk w.r.t. the head
      'number'  - the main clause number
    """
    # Note where we are starting
    iStart = i
    sentence = ""
    # Look at all the characters
    while i < len(s):
        if s[i] == "[":
            # This starts an embedding...
            # (1) Add the part we have so far to [sentence]
            if iStart >= 0 and i > iStart:
                chunk = s[iStart:i]
                func = ""
                sentence += chunk + "SUBCLAUSE"
                # See if this chunk *ends* with a /
                if chunk[-1] == "/":
                    # This means the chunk has a function within the larger whole: get that function
                    func, chunk = get_chunk_function(chunk)

            # (2) Go down and start from the next character
            i = parse_line(s, i+1, result, head=len(result)-1, level=level+1, number=number)
            iStart = i
            # Note: we continue with the sentence from this part onwards
        elif i < len(s) - 2 and s[i:i+3] == "./]":
            # This finishes an embedding
            # (1) File the result 
            if iStart >= 0 and i >= iStart:
                chunk = s[iStart:i]
                sentence += chunk
                add_result(result, sentence, head, number=number, level=level)
            # (2) Return the [i] where we are
            return i + 3
        else:
            # This is a continuation of the string
            i += 1       
    # Do we still have some string left?
    if iStart >= 0 and i > iStart:
        chunk = s[iStart:i]
        sentence += chunk
        add_result(result, sentence , head, number=number, level=level)
    # REturn the point where we ended up to the caller
    return i 

def get_line_number(text):
    """See if this text starts with a decimal line number, and return it"""

    arText = text.split(" ")
    number = -1
    if len(arText) > 1:
        if re_number.search(arText[0]):
            number = int(arText[0])
            text = " ".join(arText[1:])
    # Return what we found
    return number, text


# ==================== MAIN PROGRAM ====================================
with open(coornhert, 'rt') as file1:    #read file, loop door een map?   
    # Read through the text as a whole line by line
    # Note: one 'line' can be a number of sentences...             
    for idx, text in enumerate(file1):
        # Show where we are
        status("line {}".format(idx))

        # Zoek alles tussen [./] en voeg dat toe aan een dataframe met column Text 

        text = text.strip()
        if text != "" and '[' in text:
            # Get the line number from the text
            number, text = get_line_number(text)

            # lines = re.findall(r'\[([^]]+)\.\/\]', text) #geeft ook alles regels waar geen tekst in staat.  
            # target.append(lines)                         #dit geeft alles terug tussen [  ./], maar kan niet dealen met overlap (een subclause in een main clause, bijvoorbeeld)

            # EK: do this recursively, because of the embedding
            lines = []

            parse_line(text, 0, lines, level=0, number=number)
            # Store the results in the large list
            target.append(dict(num=number, lines=lines))
       
            #df = pd.DataFrame({'Text':target})          #Op een of andere manier blijft de df leeg
            #df.head()

            i = 1
    # Finished
    status("Finished lines")

# Now do something with the results
# (1) Write away as a JSON file
with open(result_file_json, 'w') as file2:
    json.dump(target, file2, indent=2)

# (2) Write main lines as CSV file
with open(result_file_csv, "w", encoding="utf-8", newline="") as file3:
    writer = csv.writer(file3)
    # Write the first row of headings
    writer.writerow(['sentence', 'line', 'text', 'head', 'level', 'func', 'wordorder' ])
    # Visit all target elements
    for obj in target:
        # Visit all parts in here
        number = obj['num']
        lines = obj['lines']
        for idx, line in enumerate(lines):
            # Write a row of items
            writer.writerow([number, idx, line['text'], line['head'], line['level'], line['func'], line['wordorder']])


        
# Finished
status("Results have been written")
             
     
