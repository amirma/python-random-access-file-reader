"""
General random-access file reader with very small memory overhead
Inspired by: http://stackoverflow.com/a/35785248/1857802 and http://stackoverflow.com/a/14999585/1857802

@author: Yaakov Gesher
"""

# =============
# imports
# =============

import csv
import StringIO

# ==========
# classes
# ==========


class RandomAccessReader(object):

    def __init__(self, filepath, endline_character='\n'):
        """
        :param filepath:  Absolute path to file
        :param endline_character: Delimiter for lines. Defaults to newline character (\n)
        """
        self._filepath = filepath
        self._endline = endline_character
        self._lines = self._get_line_data()

    def _get_line_data(self):
        f = open(self._filepath)
        lines = []
        start_position = 0
        has_more = True
        current_line = 0
        while has_more:
            current = f.read(1)
            if current == '':
                has_more = False
                continue

            if current == self._endline:
                # we've reached the end of the current line
                lines.append({"position": start_position, "length": current_line})
                start_position += current_line + 1
                current_line = 0
                continue

            current_line += 1
        f.close()
        return lines

    def get_line(self, line_number):
        """
        get the contents of a given line in the file
        :param line_number: 0-indexed line number
        :return: str
        """
        with open(self._filepath) as f:
            line_data = self._lines[line_number]
            f.seek(line_data['position'])
            return f.read(line_data['length'])


class CsvRandomAccessReader(RandomAccessReader):

    def __init__(self, filepath, has_header=True, endline_character='\n', values_delimiter=',', quotechar='"'):
        super(CsvRandomAccessReader, self).__init__(filepath, endline_character)
        self._headers = None
        self._delimiter = values_delimiter
        self._quotechar = quotechar
        self._has_header = has_header
        if has_header:
            reader = RandomAccessReader(filepath, endline_character)
            self._headers = self._get_line_values(reader.get_line(0))

    def set_headers(self, header_list):
        if not hasattr(header_list, '__iter__'):
            raise TypeError("Argument 'header_list' must contain an iterable")
        self._headers = tuple(header_list)

    def _get_line_values(self, line):
        """
        Splits the csv line into a list of individual values
        :param line: str
        :return: tuple of str
        """
        dialect = self.MyDialect(self._endline, self._quotechar, self._delimiter)
        b = StringIO.StringIO(line)
        r = csv.reader(b, dialect)
        values = []
        return  tuple(r.next())

    def get_line_dict(self, line_number):
        """
        gets the requested line as a dictionary (header values are the keys)
        :param line_number: requested line number, 0-indexed (disregards the header line if present)
        :return: dict
        """
        if not self._headers:
            raise ValueError("Headers must be set before requesting a line dictionary")
        if self._has_header:
            line_number += 1
        return dict(zip(self._headers, self._get_line_values(self.get_line(line_number))))

    class MyDialect(csv.Dialect):
        strict = True
        skipinitialspace = True
        quoting = csv.QUOTE_ALL
        delimiter = ','
        quotechar = '"'
        lineterminator = '\n'

        def __init__(self, terminator, quotechar, delimiter):
            csv.Dialect.__init__(self)
            self.delimiter = delimiter
            self.lineterminator = terminator
            self.quotechar = quotechar
