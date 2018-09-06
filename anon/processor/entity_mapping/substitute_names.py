import argparse
import csv
from random import choice


def main():
    parser = argparse.ArgumentParser(description='Substitute names in an entity mapping CSV file.')
    parser.add_argument('input_file', help='The entity mapping CSV file')
    parser.add_argument('output_file', help='The entity mapping CSV file')
    parser.add_argument('female_names', help='A CSV file containing female names')
    parser.add_argument('male_names', help='A CSV file containing male names')
    parser.add_argument('last_names', help='A CSV file containing last names')
    args = parser.parse_args()

    female_names, male_names, last_names = [], [], []

    # Read female names
    with open(args.female_names, 'r') as input_file:
        reader = csv.reader(input_file)
        for row in reader:
            name = row[0].replace(' (V)', '')
            if len(name) > 0:
                female_names.append(name.strip())

    # Read male names
    with open(args.male_names, 'r') as input_file:
        reader = csv.reader(input_file)
        for row in reader:
            name = row[0].replace(' (M)', '')
            if len(name) > 0:
                male_names.append(name.strip())

    # Read last names
    with open(args.last_names, 'r') as input_file:
        reader = csv.reader(input_file)
        for row in reader:
            names = row[0]
            for item in names.split(','):
                item = item.strip()
                if len(item) > 0:
                    last_names.append(item)

    # Read the input
    with open(args.output_file, 'w') as output_file:
        writer = csv.writer(output_file)
        with open(args.input_file, 'r') as input_file:
            reader = csv.reader(input_file)
            for row in reader:
                if row[1] == 'True':
                    substitution = []
                    for item in list(row[2]):
                        if item == 'M':
                            substitution += [choice(male_names)]
                        elif item == 'V':
                            substitution += [choice(female_names)]
                        elif item == 'A':
                            substitution += [choice(last_names)]
                    row[3] = ' '.join(substitution)
                    writer.writerow(row)


if __name__ == '__main__':
    main()
