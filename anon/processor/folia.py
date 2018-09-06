import ntpath
import os
from pynlpl.formats import folia
from processor import Processor

class FoLiAExporter(Processor):
    def process_files(self):
        input_files = [file for file in os.listdir(self.input_path) if '~' not in file]
        output_files = []
        for file in input_files:
            print(file)
            path = os.path.join(self.input_path, file)
            filename = ntpath.basename(path)

            # Read the data
            with open(path, 'rb') as file_handle:
                data = file_handle.read().decode('utf-8-sig')

            # create a folia document with a numbered id
            docstr = filename
            doc = folia.Document(id=docstr)
            doc.declare(folia.Event, "hdl:1839/00-SCHM-0000-0000-000A-B")

            # first create an folia text opbject, then paste string into it
            text = doc.append(folia.Text)
            for messagecounter, line in enumerate(data.split("\n")):
                (date, actor, message) = line.split("\t")
                eventid = "text.%s.event.%s" % (docstr, messagecounter)
                chatevent = folia.Event(doc, id=eventid, actor=actor, cls="message", begindatetime=date, text=message)
                text.append(chatevent)

            # Store the result
            result_path = os.path.join(self.output_path, filename.replace('.txt', '.xml'))
            doc.save(result_path)
            output_files.append(result_path)

        return output_files