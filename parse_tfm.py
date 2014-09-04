class CharInfoWord(object):
    def __init__(self, word):
        b1, b2, b3, b4 = (word >> 24,
                          (word & 0xff0000) >> 16,
                          (word & 0xff00) >> 8,
                          word & 0xff)

        self.width_index = b1
        self.height_index = b2 >> 4
        self.depth_index = b2 & 0x0f
        self.italic_index = (b3 & 0b11111100) >> 2
        self.tag = b3 & 0b11
        self.remainder = b4


class TfmCharMetrics(object):
    def __init__(self, width, height, depth, italic):
        self.width = width
        self.height = height
        self.depth = depth
        self.italic_correction = italic


class TfmFile(object):
    def __init__(self, start_char, end_char, char_info, width_table,
                 height_table, depth_table, italic_table):
        self.start_char = start_char
        self.end_char = end_char
        self.char_info = char_info
        self.width_table = width_table
        self.height_table = height_table
        self.depth_table = depth_table
        self.italic_table = italic_table

    def get_char_metrics(self, char_num):
        if char_num < self.start_char or char_num > self.end_char:
            raise RuntimeError("Invalid character number")

        info = self.char_info[char_num + self.start_char]

        return TfmCharMetrics(
            self.width_table[info.width_index],
            self.height_table[info.height_index],
            self.depth_table[info.depth_index],
            self.italic_table[info.italic_index])


class TfmReader(object):
    def __init__(self, f):
        self.f = f

    def read_byte(self):
        return ord(self.f.read(1))

    def read_halfword(self):
        b1 = self.read_byte()
        b2 = self.read_byte()
        return (b1 << 8) | b2

    def read_word(self):
        b1 = self.read_byte()
        b2 = self.read_byte()
        b3 = self.read_byte()
        b4 = self.read_byte()
        return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4

    def read_fixword(self):
        word = self.read_word()

        neg = False
        if word & 0x80000000:
            neg = True
            word = (-word & 0xffffffff)

        return (-1 if neg else 1) * word / float(1 << 20)

    def read_bcpl(self, length):
        str_length = self.read_byte()
        data = self.f.read(length - 1)
        return data[:str_length]


def read_tfm_file(file_name):
    with open(file_name, 'rb') as f:
        reader = TfmReader(f)

        # file_size
        reader.read_halfword()
        header_size = reader.read_halfword()

        start_char = reader.read_halfword()
        end_char = reader.read_halfword()

        width_table_size = reader.read_halfword()
        height_table_size = reader.read_halfword()
        depth_table_size = reader.read_halfword()
        italic_table_size = reader.read_halfword()

        # ligkern_table_size
        reader.read_halfword()
        # kern_table_size
        reader.read_halfword()

        # extensible_table_size
        reader.read_halfword()
        # parameter_table_size
        reader.read_halfword()

        # checksum
        reader.read_word()
        # design_size
        reader.read_fixword()

        if header_size > 2:
            # coding_scheme
            reader.read_bcpl(40)

        if header_size > 12:
            # font_family
            reader.read_bcpl(20)

        for i in range(header_size - 17):
            reader.read_word()

        char_info = []
        for i in range(start_char, end_char + 1):
            char_info.append(CharInfoWord(reader.read_word()))

        width_table = []
        for i in range(width_table_size):
            width_table.append(reader.read_fixword())

        height_table = []
        for i in range(height_table_size):
            height_table.append(reader.read_fixword())

        depth_table = []
        for i in range(depth_table_size):
            depth_table.append(reader.read_fixword())

        italic_table = []
        for i in range(italic_table_size):
            italic_table.append(reader.read_fixword())

        # There is more information, like the ligkern, kern, extensible, and
        # param table, but we don't need these for now

        return TfmFile(start_char, end_char, char_info, width_table,
                       height_table, depth_table, italic_table)
