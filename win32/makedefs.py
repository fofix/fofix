#!/usr/bin/env python
# Script to create .defs from a folder of MinGW implibs and a folder of DLLs.
# Copyright (C) 2010 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import struct
import sys
import glob
import shlex
import re
import subprocess

if len(sys.argv) != 4:
    sys.stderr.write('''Usage: %s [implib-dir] [dll-dir] [identify-cmd]
For each MinGW-style import library in implib-dir, locates the corresponding
DLL in dll-dir and creates a .def file for it in implib-dir, which MSVC
tools can be run on to create an MSVC-compatible implib.

identify-cmd is run on each implib to discover what DLL it goes with. It is
split into an argument list using sh-style rules, then the implib name is
added to the end of the argument list.

The .def files are named [whatever goes after -l to link to the lib].def
''' % sys.argv[0])
    sys.exit(1)

def make_def(file):
    f = open(file, 'rb')
    if f.read(2) != 'MZ':
        raise ValueError, 'Incorrect magic number in file.'
    f.seek(60)
    pe_header_offset = struct.unpack('<L', f.read(4))[0]
    f.seek(pe_header_offset)
    if f.read(4) != 'PE\0\0':
        raise ValueError, 'Incorrect magic number in file.'

    # Get sizes of tables we need.
    f.seek(pe_header_offset + 6)
    number_of_sections = struct.unpack('<H', f.read(2))[0]
    f.seek(pe_header_offset + 116)
    number_of_data_directory_entries = struct.unpack('<L', f.read(4))[0]
    data_directory_offset = f.tell()  # it's right after the number of entries

    # Where is the export table?
    f.seek(data_directory_offset)
    rva_of_export_table = struct.unpack('<L', f.read(4))[0]

    # Get the section ranges so we can convert RVAs to file offsets.
    f.seek(data_directory_offset + 8 * number_of_data_directory_entries)
    sections = []
    for i in range(number_of_sections):
        section_descriptor_data = f.read(40)
        name, size, va, rawsize, offset = struct.unpack('<8sLLLL', section_descriptor_data[:24])
        sections.append({'min': va, 'max': va+rawsize, 'offset': offset})

    def seek_to_rva(rva):
        for s in sections:
            if s['min'] <= rva and rva < s['max']:
                f.seek(rva - s['min'] + s['offset'])
                return
        raise ValueError, 'Could not find section for RVA.'

    # Read the relevant fields of the export directory.
    seek_to_rva(rva_of_export_table + 12)
    rva_of_dll_name = struct.unpack('<L', f.read(4))[0]
    seek_to_rva(rva_of_export_table + 24)
    number_of_names = struct.unpack('<L', f.read(4))[0]
    seek_to_rva(rva_of_export_table + 32)
    rva_of_name_array = struct.unpack('<L', f.read(4))[0]

    def read_asciiz(rva):
        seek_to_rva(rva)
        value = ''
        while True:
            c = f.read(1)
            if c in ('\0', ''):
                break
            value += c
        return value

    # Build the .def file contents with a list of all exported symbols.
    dllname = read_asciiz(rva_of_dll_name)
    def_contents = 'LIBRARY %s\nEXPORTS\n' % dllname

    seek_to_rva(rva_of_name_array)
    name_rvas = struct.unpack('<%sL' % number_of_names, f.read(4 * number_of_names))
    for name_rva in name_rvas:
        def_contents += '    %s\n' % read_asciiz(name_rva)

    return def_contents


implibs = glob.glob(os.path.join(sys.argv[1], 'lib*.a'))
dlls = os.listdir(sys.argv[2])
identify_cmd = shlex.split(sys.argv[3])

for implib in implibs:
    dash_l_name = re.match(r'^lib(.*?)(?:\.dll)?\.a$', os.path.basename(implib)).group(1)
    identify_proc = subprocess.Popen(identify_cmd + [implib], stdout=subprocess.PIPE)
    dllnames = identify_proc.stdout.readlines()
    if identify_proc.wait() != 0 or len(dllnames) != 1:
        print >>sys.stderr, 'Could not get a unique DLL name from %s.' % implib
        continue
    dllname = dllnames[0].rstrip('\n')

    for dll in dlls:
        if dll.lower() == dllname.lower():
            def_contents = make_def(os.path.join(sys.argv[2], dll))
            open(os.path.join(sys.argv[1], dash_l_name+'.def'), 'w').write(def_contents)
