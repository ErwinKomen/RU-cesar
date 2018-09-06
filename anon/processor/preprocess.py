from collections import Counter
import os
import re

from processor import Processor


class Preprocessor(Processor):
    def process_data(self, data):
        data = self.remove_blank_lines(data)
        data = self.normalize_field_separator(data)

        # for line in data.split("\n"):
        #     print(line)
        # input('...')

        data = self.normalize_datetime(data)

        return data

    def format_filenames(self):
        input_files = os.listdir(self.input_path)
        for file in input_files:
            # replace all spaces with hyphens (-)
            newfile = file.replace(" ", "-")

            # replace all brackets
            newfile = newfile.replace("[", "")
            newfile = newfile.replace("]", "")
            newfile = newfile.replace("(", "")
            newfile = newfile.replace(")", "")

            # actually rename the file
            if not newfile == file:
                os.rename(os.path.join(self.input_path, file), \
                    os.path.join(self.input_path, newfile))

    def remove_blank_lines(self, data):
        """
        Remove blank lines from text data.

        :param data: text data
        :return: data where \r is replaced by \n and all blank lines are removed
        """
        output = data.replace("\r", "\n").replace("\t", "")
        output = [line for line in output.split("\n") if len(line.strip()) > 0]
        # Concatenate messages which contain newlines
        redo = True
        while redo:
            redo = False
            for index in range(len(output) - 1):
                if index < len(output) - 1 and ': ' in output[index] and ': ' not in output[index + 1]:
                    output = output[:index - 1] + [output[index] + ' ' + output[index + 1]] + output[index + 2:]
                    redo = True
        return "\n".join(output)


    def normalize_field_separator(self, data):
        """
        Normalize field separators.

        :param data: text data without \t
        :return: data with normalized field separators (\t)
        """
        if "\t" in data:
            raise ValueError("normalize_field_separator: there exists a tab character in the data.")
        lines = data.split("\n")
        
        # Check whether " - " is present in all lines
        has_dash_separator = True
        for line in lines:
            if ' - ' not in line:
                has_dash_separator = False
        # Check for the " : " separator
        has_colon_separator = True
        for line in lines:
            if ' : ' not in line:
                has_colon_separator = False

        # Normalize the first field separator in all the lines
        if has_dash_separator:
            # " - " is used as separator
            lines = [line.split(' - ') for line in lines]
            lines = [field[0] + "\t" + ' - '.join(field[1:]) for field in lines]
        elif has_colon_separator:
            # " : " is used as separator
            lines = [line.split(' : ') for line in lines]            
            lines = [field[0] + "\t" + ' : '.join(field[1:]) for field in lines]
        else:
            # ": " is used as separator
            lines = [line.split(': ') for line in lines]
            lines = [field[0] + "\t" + ': '.join(field[1:]) for field in lines]
            
        if not has_colon_separator:
            # Now normalize the field separator between the person and the actual message
            lines = [line.split(': ') for line in lines]
            lines = [field[0] + "\t" + ': '.join(field[1:]) for field in lines]
        
        return "\n".join(lines)


    def normalize_datetime(self, data):
        """
        Normalize datetime fields.

        :param data: data with normalized field separators
        :return: data with normalized datetime fields
        """
        months = ['*', 'jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']
        lines = data.split("\n")
        last_parsed_year = None
        last_parsed_month = None
        new_lines = []

        for line in lines:
            fields = line.split("\t")
            fields = [field for field in fields if len(field) > 0]
            parsed_month, parsed_day, parsed_year, parsed_hour, parsed_minutes = '1', '1', '2012', '0', '0'
            if len(fields) == 2:
                fields = [''] + fields
            else:
                if len(fields) != 3:
                    raise ValueError("normalize_datetime: number of fields should equal 3")
                raw_date = fields[0]

                for month, label in enumerate(months):
                    if label in raw_date.lower():
                        parsed_month = month

                # Parse the time field
                parts = raw_date.split(' ')
                for part in parts:
                    if ':' in part:
                        timeparts = part.split(':')
                        if len(timeparts) < 2:
                            raise ValueError('normalize_datetime: invalid timefield found')
                        parsed_hour, parsed_minutes = timeparts[0], timeparts[1]
                    if len(part) == 4 and part.isdigit():
                        parsed_year = part
                    if len(part) <= 2 and parsed_month is not None:
                        parsed_day = part
                    if len(part) > 4 and ':' not in part:
                        # A date
                        part = part.replace('/', '-').split('-')
                        if len(part) != 3:
                            parsed_day, parsed_month, parsed_year = '1', '1', '2012'
                        else:
                            parsed_day, parsed_month, parsed_year = part
                        if len(parsed_year) < 4:
                            parsed_year = int(parsed_year)
                            parsed_year = 1900 + parsed_year if parsed_year >= 70 else 2000 + parsed_year

                if parsed_year is None and last_parsed_year is not None:
                    parsed_year = int(last_parsed_year)
                    if parsed_month < last_parsed_month:
                        parsed_year += 1

                # Substitute the year if no year could be infered
                if parsed_year is None:
                    parsed_year = 2012

            # Add zeros to the beginning of the strings
            date = (str(parsed_year).zfill(4), str(parsed_month).zfill(2), str(parsed_day).zfill(2), str(parsed_hour).zfill(2), str(parsed_minutes).zfill(2))
            # Format the date
            date = '%s-%s-%sT%s:%s' % date

            # Remember the last year and month
            if parsed_year is not None:
                last_parsed_year = parsed_year
            if parsed_month is not None:
                last_parsed_month = parsed_month

            new_lines.append("\t".join([date] + fields[1:]))

        return "\n".join(new_lines)
