import argparse
import csv
import os
import re
from processor.preprocess import Preprocessor
from processor.anonymizer import Anonymizer 
from processor.folia import FoLiAExporter


# load arguments
parser = argparse.ArgumentParser(description='Convert raw WhatsApp files to the FoLiA format.')
parser.add_argument('--input', help='the path to the folder which contains the WhatsApp data.')
parser.add_argument('--output', help='the path where the output will be stored.')
args = parser.parse_args()
input_dir, output_dir = args.input, args.output


# create the output folders
def make_output_dir(folder):
    path = os.path.join(output_dir, folder)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

preprocessed_output = make_output_dir('1_preprocessed')
anonymized_output = make_output_dir('2_anonymized')
folia_output = make_output_dir('3_folia')


# processing pipeline
print("preprocessing...")
preprocessor = Preprocessor(input_dir, preprocessed_output)
preprocessor.format_filenames()
preprocessor.process_files()

print("anonymizing...")
anonymizer = Anonymizer(preprocessed_output, anonymized_output)
anonymizer.create_entity_mapping()
anonymizer.process_files()

print("exporting to folia...")
FoLiAExporter(anonymized_output, folia_output).process_files()


# write participants file
with open(os.path.join(output_dir, 'participants.csv'), 'w') as file:
    writer = csv.writer(file)
    for code, entity in anonymizer.participants.items():
        writer.writerow([code, entity])

# write entities file
with open(os.path.join(output_dir, 'entities.csv'), 'w') as file:
    writer = csv.writer(file)
    for replacer, replacement in anonymizer.replaced.items():
        writer.writerow([replacer, replacement])

print("done")