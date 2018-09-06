import argparse
import csv
import os
import re
from processor.folia import FoLiAExporter

# load arguments
parser = argparse.ArgumentParser(description='Convert raw WhatsApp files to the FoLiA format.')
parser.add_argument('--input', help='the path to the folder which contains the WhatsApp data.')
parser.add_argument('--output', help='the path where the output will be stored.')
args = parser.parse_args()
input_dir, output_dir = args.input, args.output

# create the output folders
def make_output_dir(folder):
    path = os.path.abspath( os.path.join(output_dir, folder))
    if not os.path.exists(path):
        os.makedirs(path)
    return path

preprocessed_output = make_output_dir('1_preprocessed')
folia_output = make_output_dir('3_folia')

# processing pipeline

print("exporting to folia...")
FoLiAExporter(preprocessed_output, folia_output).process_files()

print("done")