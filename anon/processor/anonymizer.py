import csv
import datetime
import json
from pynlpl.clients.frogclient import FrogClient
import os
import re
import sys

from processor import Processor


class Anonymizer(Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replacements = {}
        self.participants = {}
        self.replaced = {}
        self.postag_file = os.path.join(os.path.dirname(self.output_path), 'pos_tags.txt')
        self.entmap_file =  os.path.join(os.path.dirname(self.output_path), 'entity_mapping.csv')
        self.metafile = './data/MetadataWhatsapp.csv'
        self.unkown_participants = 0

    def process_data(self, data):
        # load the entity mapping
        if self.entmap_file is not None and os.path.exists(self.entmap_file):
            with open(self.entmap_file, 'r') as file:
                for row in csv.reader(file):
                    self.replacements[row[0]] = row[2]

        # anonimize data
        return self.anonymize(data)

    def anonymize(self, data):
        # read metafile participants
        participants = {}
        if self.metafile is not None and os.path.exists(self.metafile):
            with open(self.metafile, 'r') as file:
                rows = csv.reader(file)
                for row in rows:
                    participants[row[3]] = row

        # anonymize the data
        rep = []
        new_lines = []
        index = 0
        
        for line in data.split("\n"):
            fields = line.split("\t")
            
            if len(fields) == 3:
                if fields[1] in self.participants:
                    fields[1] = self.participants[fields[1]]
                else:
                    if fields[1] in participants:
                        self.participants[fields[1]] = '[' + participants[fields[1]][0] + ']'
                    else:
                        self.unkown_participants += 1
                        self.participants[fields[1]] = '[user?' + str(self.unkown_participants) + ']'
                    fields[1] = self.participants[fields[1]]

                # Add a surrounding space for easier replacements at boundary positions
                x = ' ' + fields[2] + ' '
                replacers = {}
                
                # Do some special replacements for variable entities                    
                pattern = re.compile('([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]')
                x = re.sub(pattern, '[time]', x)

                pattern = re.compile('[0-9]+,[0-9]+|[0-9]+')
                x = re.sub(pattern, '[numerical_value]', x)

                pattern = re.compile('[s, S][0-9]+')
                x = re.sub(pattern, '[student_number]', x)

                pattern = re.compile('[0-9]{4,}[ ]+[a-zA-Z]{2}[^a-zA-Z]{1,}')
                x = re.sub(pattern, '[postal_code]', x)

                pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
                x = re.sub(pattern, '[website]', x)

                pattern = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                                    "{|}~-]+)*(@|\sat\s)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                                    "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))
                x = re.sub(pattern, '[email]', x)

                date_delimiters = ['-/']
                for date_delimiter in date_delimiters:
                    pattern = re.compile('[0-9]{1,4}[' + date_delimiter + ']{1}[0-9]{1,4}[' + date_delimiter + ']{1}[0-9]{1,4}')
                    x = re.sub(pattern, '[date]', x)

                # Replacing Entity -> [[[VAR<number>]]] -> Replaced Entity
                # The intermediate step is required for replacing multiple entities on the same line
                for replacer in self.replacements:
                    if replacer in x:
                        self.replaced[replacer] = self.replacements[replacer]
                        if replacer not in replacers:
                            variable = '[[[VAR%d]]]' % index
                            replacers[self.replacements[replacer]] = variable
                            index += 1
                            rep.append(replacer)
                        else:
                            variable = replacers[self.replacements[replacer]]
                        x = x.replace(' ' + replacer + ' ', ' ' + variable + ' ')
                        pattern = re.compile('([^a-zA-Z])' + replacer + '([^a-zA-Z])')
                        x = re.sub(pattern, '\g<1>' + variable + '\g<2>', x)
                
                # Replace the field containing the message if something was changed
                if x != fields[2]:
                    fields[2] = x
                new_lines.append("\t".join(fields))
        
		# read general replacement file
        repx = []
        if os.path.isfile("replaced.txt"): 
            file = open("replaced.txt", 'rb')
            repx = file.readlines()
            file.close()

        # merge replacements
        tofile = []
        for w in set(repx + rep):
            try:
                w = w.decode('utf-8')
            except:
                pass
            if not "\n" in w:
                w += "\n"
            tofile.append(w)

        # write new replacement file
        file = open("replaced.txt", 'w')
        for w in sorted(tofile):
            file.write(w)
        file.close()

        return "\n".join(new_lines)

    def create_entity_mapping(self):
        # only extract pos-tags when not already done
        if not os.path.exists(self.postag_file):
            self.extract_pos_tags()
        if not os.path.exists(self.entmap_file):
            self.extract_entities()

    def extract_pos_tags(self):
        # create frogclient
        bLocal = False
        if bLocal:
            port = 8080
            frogclient = FrogClient("localhost", port, returnall=True)
        else:
            port = 443
            frogClient = FrogClient("https://languagemachines.github.io/frog", port, returnall=True)

        # create wordstream
        wordstream = ''
        for file in os.listdir(self.input_path):
            path = os.path.join(self.input_path, file)
            with open(path, 'rb') as reader:
                data = reader.read().decode('utf-8-sig')
                data = [line.split("\t")[-1] for line in data.split("\n")]
                wordstream += ' '.join(data)

        # extract pos tags
        window_size = 250
        window_shift = 50
        index = 0
        with open(self.postag_file, 'w') as file:
            while index + window_size < len(wordstream):
                substream = wordstream[index:index + window_size]
                for data in frogclient.process(substream):
                    sys.stdout.write('\r')
                    percentage = round(100 * index / float(len(wordstream)), 2)
                    sys.stdout.write(str(percentage) + '%')
                    sys.stdout.flush()
                    file.write(json.dumps(data) + "\n")
                index += window_shift

    def extract_entities(self):
        names = set()
        with open(self.postag_file, 'r') as file:
            data = file.read()
            for line_index, line in enumerate(data.split("\n")):
                try:
                    parsed_line = json.loads(line)
                except Exception:
                    continue
                parsed_line = [item if item is not None else '' for item in parsed_line]
                
                item = parsed_line[0]
                pos_tag = parsed_line[3]
                bio_tag = parsed_line[4]

                if pos_tag == 'SPEC(deeleigen)' and '-PER' in bio_tag:
                    names.add(item)
                elif pos_tag == 'SPEC(deeleigen)' and '-LOC' in bio_tag:
                    names.add(item)

        new_rows = []
        names_found = set()
        
        if os.path.exists(self.entmap_file):
            with open(self.entmap_file, 'r') as file:
                rows = csv.reader(file)
                for row in rows:
                    names_found.add(row[0])
                    new_rows.append(row)

        for name in names - names_found:
            new_rows.append([name, True, '', datetime.datetime.now()])

        with open(self.entmap_file, 'w') as file:
            writer = csv.writer(file)
            for row in new_rows:
                writer.writerow(row)
