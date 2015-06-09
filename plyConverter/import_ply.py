# import_ply.py copied from blender addons io_mesh_ply
# (modified: removed last blocks after "import bpy")

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import re
import struct


class element_spec(object):
    __slots__ = ("name",
                 "count",
                 "properties",
                 )

    def __init__(self, name, count):
        self.name = name
        self.count = count
        self.properties = []

    def load(self, format, stream):
        if format == b'ascii':
            stream = stream.readline().split()
        return [x.load(format, stream) for x in self.properties]

    def index(self, name):
        for i, p in enumerate(self.properties):
            if p.name == name:
                return i
        return -1


class property_spec(object):
    __slots__ = ("name",
                 "list_type",
                 "numeric_type",
                 )

    def __init__(self, name, list_type, numeric_type):
        self.name = name
        self.list_type = list_type
        self.numeric_type = numeric_type

    def read_format(self, format, count, num_type, stream):
        if format == b'ascii':
            if num_type == 's':
                ans = []
                for i in range(count):
                    s = stream[i]
                    if len(s) < 2 or s[0] != '"' or s[-1] != '"':
                        print('Invalid string', s)
                        print('Note: ply_import.py does not handle whitespace in strings')
                        return None
                    ans.append(s[1:-1])
                stream[:count] = []
                return ans
            if num_type == 'f' or num_type == 'd':
                mapper = float
            else:
                mapper = int
            ans = [mapper(x) for x in stream[:count]]
            stream[:count] = []
            return ans
        else:
            if num_type == 's':
                ans = []
                for i in range(count):
                    fmt = format + 'i'
                    data = stream.read(struct.calcsize(fmt))
                    length = struct.unpack(fmt, data)[0]
                    fmt = '%s%is' % (format, length)
                    data = stream.read(struct.calcsize(fmt))
                    s = struct.unpack(fmt, data)[0]
                    ans.append(s[:-1])  # strip the NULL
                return ans
            else:
                fmt = '%s%i%s' % (format, count, num_type)
                data = stream.read(struct.calcsize(fmt))
                return struct.unpack(fmt, data)

    def load(self, format, stream):
        if self.list_type is not None:
            count = int(self.read_format(format, 1, self.list_type, stream)[0])
            return self.read_format(format, count, self.numeric_type, stream)
        else:
            return self.read_format(format, 1, self.numeric_type, stream)[0]


class object_spec(object):
    __slots__ = ("specs",
                )
    'A list of element_specs'
    def __init__(self):
        self.specs = []

    def load(self, format, stream):
        return dict([(i.name, [i.load(format, stream) for j in range(i.count)]) for i in self.specs])

        '''
        # Longhand for above LC
        answer = {}
        for i in self.specs:
            answer[i.name] = []
            for j in range(i.count):
                if not j % 100 and meshtools.show_progress:
                    Blender.Window.DrawProgressBar(float(j) / i.count, 'Loading ' + i.name)
                answer[i.name].append(i.load(format, stream))
        return answer
            '''


def read(filepath):
    format = b''
    texture = b''
    version = b'1.0'
    format_specs = {b'binary_little_endian': '<',
                    b'binary_big_endian': '>',
                    b'ascii': b'ascii'}
    type_specs = {b'char': 'b',
                  b'uchar': 'B',
                  b'int8': 'b',
                  b'uint8': 'B',
                  b'int16': 'h',
                  b'uint16': 'H',
                  b'ushort': 'H',
                  b'int': 'i',
                  b'int32': 'i',
                  b'uint': 'I',
                  b'uint32': 'I',
                  b'float': 'f',
                  b'float32': 'f',
                  b'float64': 'd',
                  b'double': 'd',
                  b'string': 's'}
    obj_spec = object_spec()
    invalid_ply = (None, None, None)

    with open(filepath, 'rb') as plyf:
        signature = plyf.readline()

        if not signature.startswith(b'ply'):
            print('Signature line was invalid')
            return invalid_ply

        valid_header = False
        for line in plyf:
            tokens = re.split(br'[ \r\n]+', line)

            if len(tokens) == 0:
                continue
            if tokens[0] == b'end_header':
                valid_header = True
                break
            elif tokens[0] == b'comment':
                if len(tokens) < 2:
                    continue
                elif tokens[1] == b'TextureFile':
                    if len(tokens) < 4:
                        print('Invalid texture line')
                    else:
                        texture = tokens[2]
                continue
            elif tokens[0] == b'obj_info':
                continue
            elif tokens[0] == b'format':
                if len(tokens) < 3:
                    print('Invalid format line')
                    return invalid_ply
                if tokens[1] not in format_specs:
                    print('Unknown format', tokens[1])
                    return invalid_ply
                if tokens[2] != version:
                    print('Unknown version', tokens[2])
                    return invalid_ply
                format = tokens[1]
            elif tokens[0] == b'element':
                if len(tokens) < 3:
                    print(b'Invalid element line')
                    return invalid_ply
                obj_spec.specs.append(element_spec(tokens[1], int(tokens[2])))
            elif tokens[0] == b'property':
                if not len(obj_spec.specs):
                    print('Property without element')
                    return invalid_ply
                if tokens[1] == b'list':
                    obj_spec.specs[-1].properties.append(property_spec(tokens[4], type_specs[tokens[2]], type_specs[tokens[3]]))
                else:
                    obj_spec.specs[-1].properties.append(property_spec(tokens[2], None, type_specs[tokens[1]]))
        if not valid_header:
            print("Invalid header ('end_header' line not found!)")
            return invalid_ply

        obj = obj_spec.load(format_specs[format], plyf)

    return obj_spec, obj, texture
