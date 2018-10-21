import heapq
import os
from collections import Counter


class HeapNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __eq__(self, other):
        return HeapNode.__check(other) and (self.freq == other.freq)

    def __ne__(self, other):
        return HeapNode.__check(other) and (self.freq != other.freq)

    def __lt__(self, other):
        return HeapNode.__check(other) and (self.freq < other.freq)

    def __le__(self, other):
        return HeapNode.__check(other) and (self.freq <= other.freq)

    def __gt__(self, other):
        return HeapNode.__check(other) and (self.freq > other.freq)

    def __ge__(self, other):
        return HeapNode.__check(other) and (self.freq >= other.freq)

    @staticmethod
    def __check(other):
        if other is None:
            return False
        if not isinstance(other, HeapNode):
            return False
        return True

    def __repr__(self):
        return "Char[%s]->Freq[%s]" % (self.c, self.freq)


def _apply_merge(heap):
    n1 = heapq.heappop(heap)
    n2 = heapq.heappop(heap)
    merged = HeapNode(None, n1.freq + n2.freq)
    merged.left = n1
    merged.right = n2
    heapq.heappush(heap, merged)


def _conform_heap(d):
    heap = []
    for k, v in d.items():
        heapq.heappush(heap, HeapNode(k, v))
    return heap


def _codify(codes, reverse_mapping, root, current=''):
    if root is not None:
        if root.char is not None:
            codes[root.char] = current
            reverse_mapping[current] = root.char
            return
        _codify(codes, reverse_mapping, root.left, current + "0")
        _codify(codes, reverse_mapping, root.right, current + "1")


def _padding(enc_text):
    extra_pad = 8 - len(enc_text) % 8
    pad_info = "{0:08b}".format(extra_pad)
    return pad_info + enc_text + ''.join(["0"] * extra_pad)


class HuffmanCoding:
    def __init__(self, path):
        self.path = path
        self.heap = []
        self.codes = {}
        self.reverse_mapping = {}

    # functions for compression:

    def get_byte_array(self, padded_encoded_text):
        if len(padded_encoded_text) % 8 != 0:
            print("Encoded text not padded properly")
            exit(0)

        b = bytearray()
        for i in range(0, len(padded_encoded_text), 8):
            byte = padded_encoded_text[i:i + 8]
            b.append(int(byte, 2))
        return b

    def compress(self):
        filename, file_extension = os.path.splitext(self.path)
        output_path = filename + ".bin"

        with open(self.path, 'r+') as file, open(output_path, 'wb') as output:
            text = file.read()
            text = text.rstrip()

            self.heap = _conform_heap(Counter(text))
            while len(self.heap) > 1:
                _apply_merge(self.heap)

            _codify(self.codes, self.reverse_mapping, heapq.heappop(self.heap))

            encoded_text = ''.join([self.codes[c] for c in text])
            padded_encoded_text = _padding(encoded_text)

            output.write(bytes(self.get_byte_array(padded_encoded_text)))

        print("Compressed")
        return output_path

    """ functions for decompression: """

    def remove_padding(self, padded_encoded_text):
        padded_info = padded_encoded_text[:8]
        extra_padding = int(padded_info, 2)

        padded_encoded_text = padded_encoded_text[8:]
        encoded_text = padded_encoded_text[:-1 * extra_padding]

        return encoded_text

    def decode_text(self, encoded_text):
        current_code = ""
        decoded_text = ""

        for bit in encoded_text:
            current_code += bit
            if (current_code in self.reverse_mapping):
                character = self.reverse_mapping[current_code]
                decoded_text += character
                current_code = ""

        return decoded_text

    def decompress(self, input_path):
        filename, file_extension = os.path.splitext(self.path)
        output_path = filename + "_decompressed" + ".txt"

        with open(input_path, 'rb') as file, open(output_path, 'w') as output:
            bit_string = ""

            byte = file.read(1)
            while (byte != ""):
                byte = ord(byte)
                bits = bin(byte)[2:].rjust(8, '0')
                bit_string += bits
                byte = file.read(1)

            encoded_text = self.remove_padding(bit_string)

            decompressed_text = self.decode_text(encoded_text)
            output.write(decompressed_text)

        print("Decompressed")
        return output_path
