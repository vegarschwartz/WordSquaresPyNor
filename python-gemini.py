import os
import csv
import time

# Constants (equivalent to #defines in C++)
DICTIONARY = "ordliste.txt"
FREQ_FILTER = "frequency.csv"
SIZE_W = 5
SIZE_H = 5
MIN_FREQ_W = 20000
MIN_FREQ_H = 20000
UNIQUE = True
DIAGONALS = False
NUM_LETTERS = 32 #changed to 32, added more letters.

VTRIE_SIZE = (SIZE_W + 2 if DIAGONALS else SIZE_W)
BANNED = set()  # Equivalent to std::unordered_set<std::string> banned

# Global variables (equivalent to C++ global variables)
g_freqs = {}  # Equivalent to std::unordered_map<std::string, uint32_t>
g_charToIndex = {} #Add char to index
g_trie_w = None
g_trie_h = None
g_words = [''] * (SIZE_H * SIZE_W)  # Equivalent to char g_words[SIZE_H * SIZE_W]

def initialize_char_to_index():
    index = 0
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅ":
      g_charToIndex[c] = index
      index += 1
    
    # Add the lowercase letters, mapping them to the same indexes as their uppercase counterparts
    for c in "abcdefghijklmnopqrstuvwxyzæøå":
        g_charToIndex[c] = g_charToIndex[c.upper()]
    

class Trie:
    class Iter:
        def __init__(self, nodes, charToIndex):
            self.n = nodes
            self.ix = -1
            self.charToIndex = charToIndex

        def getIx(self):
            return self.ix

        def getLetter(self):
            for c, i in self.charToIndex.items():
                if i == self.ix:
                    return c
            return '?'

        def get(self):
            return self.n[self.ix]

        def next(self):
            while True:
                self.ix += 1
                if self.ix >= len(self.charToIndex):
                    return False
                if self.n[self.ix] is not None:
                    return True

    def __init__(self, charToIndex):
        self.nodes = [None] * len(charToIndex)
        self.charToIndex = charToIndex

    def add(self, string):
        ptr = self
        for c in string:
            if c not in self.charToIndex:
                raise ValueError(f"Invalid Character {c}")
            ix = self.charToIndex[c]
            if not (0 <= ix < len(self.charToIndex)):
                raise ValueError("Character not in charToIndex range")
            if ptr.nodes[ix] is None:
                ptr.nodes[ix] = Trie(self.charToIndex)
            ptr = ptr.nodes[ix]

    def has(self, string):
        ptr = self
        for c in string:
            if c not in self.charToIndex:
                return False
            ix = self.charToIndex[c]
            if not (0 <= ix < len(self.charToIndex)):
                raise ValueError("Character not in charToIndex range")
            if ptr.nodes[ix] is None:
                return False
            else:
                ptr = ptr.nodes[ix]
        return True

    def hasIx(self, ix):
        return self.nodes[ix] is not None
    
    def hasLetter(self, c):
      if c not in self.charToIndex: return False
      return self.nodes[self.charToIndex[c]] is not None

    def decend(self, ix):
        return self.nodes[ix]

    def iter(self):
        return self.Iter(self.nodes, self.charToIndex)


def load_dictionary(fname, length, trie, min_freq):
    print(f"Loading Dictionary {fname}...")
    num_words = 0
    try:
        with open(fname, 'r', encoding="utf-8") as fin:
            for line in fin:
                line = line.strip().upper()
                if len(line) != length:
                    continue
                if g_freqs and min_freq > 0:
                    freq = g_freqs.get(line, None)
                    if freq is None or freq > min_freq:
                        continue
                if line in BANNED:
                    continue
                try:
                  trie.add(line)
                  num_words += 1
                except ValueError as e:
                  print(f"Error in line: {line}: {e}")
    except UnicodeDecodeError as e:
        print(f"Error: {e}")
    
    print(f"Loaded {num_words} words.")


def load_freq(fname):
    print(f"Loading Frequency List {fname}...")
    num_words = 0
    try:
        with open(fname, 'r', encoding="utf-8") as fin:
            reader = csv.reader(fin)
            next(reader, None) # skip header
            for row in reader:
                word = row[0].upper()
                g_freqs[word] = num_words
                num_words += 1
    except UnicodeDecodeError as e:
        print(f"Error: {e}")
    print(f"Loaded {num_words} words.")


def print_box(words):
    if UNIQUE and SIZE_H == SIZE_W:
        for i in range(SIZE_H):
            num_same = 0
            for j in range(SIZE_W):
                if words[i * SIZE_W + j] == words[j * SIZE_W + i]:
                    num_same += 1
            if num_same == SIZE_W:
                return
    for h in range(SIZE_H):
        for w in range(SIZE_W):
            print(words[h * SIZE_W + w], end="")
        print()
    print()


def box_search(trie, vtries, pos):
    v_ix = pos % SIZE_W
    if v_ix == 0:
        if pos == SIZE_H * SIZE_W:
            print_box(g_words)
            return
        trie = g_trie_w
    
    it = trie.iter()
    while it.next():
        if not vtries[v_ix].hasIx(it.getIx()):
            continue
        if pos == 0:
            print(f"=== [{it.getLetter()}] ===")
        
        h_ix = pos // SIZE_W
        if DIAGONALS:
            if h_ix == v_ix and not vtries[VTRIE_SIZE - 2].hasIx(it.getIx()):
                continue
            if h_ix == SIZE_W - v_ix - 1 and not vtries[VTRIE_SIZE - 1].hasIx(it.getIx()):
                continue
                
        g_words[pos] = it.getLetter()
        backup_vtrie = vtries[v_ix]
        vtries[v_ix] = vtries[v_ix].decend(it.getIx())

        if DIAGONALS:
            backup_dtrie1 = vtries[VTRIE_SIZE - 2]
            backup_dtrie2 = vtries[VTRIE_SIZE - 1]
            if h_ix == v_ix:
                vtries[VTRIE_SIZE - 2] = vtries[VTRIE_SIZE-2].decend(it.getIx())
            if h_ix == SIZE_W - v_ix - 1:
                vtries[VTRIE_SIZE - 1] = vtries[VTRIE_SIZE-1].decend(it.getIx())

        box_search(it.get(), vtries, pos + 1)

        vtries[v_ix] = backup_vtrie
        if DIAGONALS:
            vtries[VTRIE_SIZE - 2] = backup_dtrie1
            vtries[VTRIE_SIZE - 1] = backup_dtrie2


def main():
    global g_trie_w, g_trie_h

    initialize_char_to_index()
    load_freq(FREQ_FILTER)

    g_trie_w = Trie(g_charToIndex)
    load_dictionary(DICTIONARY, SIZE_W, g_trie_w, MIN_FREQ_W)
    trie_h = g_trie_w
    if SIZE_W != SIZE_H:
        g_trie_h = Trie(g_charToIndex)
        load_dictionary(DICTIONARY, SIZE_H, g_trie_h, MIN_FREQ_H)
        trie_h = g_trie_h

    vtries = [trie_h] * VTRIE_SIZE
    start_time = time.time()
    box_search(None, vtries, 0)
    end_time = time.time()
    print(f"Done. Search took {end_time-start_time} seconds")


if __name__ == "__main__":
    main()