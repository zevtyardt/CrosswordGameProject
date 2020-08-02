from array import *
import random
import re
import argparse
import copy
import sys
from typing import List, Optional, Union
import logging
from argparse import Namespace
import tabulate
import itertools
import functools

from pprint import pprint
logging.basicConfig(format="• %(message)s", level=logging.WARN)

# decorator
def changeCurrentPos(func):
    @functools.wraps(func)
    def wrapper(self):
        row, col = func(self)
        char = self.board[row][col]
        self.start = (row, col)
    return wrapper

class parseLoc:
    def __init__(self, board: List[str], data: dict):
        self.board = board
        self.data = data
        self.empty_char = " "
        self.start = self._startPosition()

    def is_empty_char(self, char: str) -> Union[bool]:
        return char in (self.empty_char, self.empty_char * 3)

    def _startPosition(self):
        for row in range(1, len(self.board), 2):
            for col in range(1, len(self.board[row]), 2):
                char = self.board[row][col]
                if not self.is_empty_char(char):
                    return (row, col)

    @property
    def loc(self):
        row, col = self.start
        return (row, col * 2)

    @property
    def locaround(self):
        row, col = self.start
        for nrow, ncol in [
            (row - 1, col - 1),
            (row - 1, col),
            (row - 1, col + 1),
            (row, col - 1),
            (row, col + 1),
            (row + 1, col - 1),
            (row + 1, col),
            (row + 1, col + 1),
        ]:
            char = self.board[nrow][ncol]
            if ncol == col:
                ncol = ncol * 2
                if (_re := re.search(r"(\d+)(.+)", char)):
                    char = _re.group(2)
                    ncol += len(_re.group(1)) - 1
                else:
                    ncol -= 1
            else:
                ncol = ncol * 2
            yield (nrow, ncol, char)

    @changeCurrentPos
    def moveLeft(self):
        row, col = self.start
        while True:
            if col == 1:
                col = len(self.board[row]) - 2
            else:
                col -= 2
            if not self.is_empty_char(char := self.board[row][col]):
                return (row, col)

    @changeCurrentPos
    def moveRight(self):
        row, col = self.start
        while True:
            if col == len(self.board[row]) - 2:
                col = 1
            else:
                col += 2
            if not self.is_empty_char(char := self.board[row][col]):
                return (row, col)

    @changeCurrentPos
    def moveUp(self):
        row, col = self.start
        while True:
            if row == 1:
                row = len(self.board) - 2
            else:
                row -= 2
            if not self.is_empty_char(self.board[row][col]):
                return (row, col)

    @changeCurrentPos
    def moveDown(self):
        row, col = self.start
        while True:
            if row == len(self.board) - 2:
                row = 1
            else:
                row += 2
            if not self.is_empty_char(self.board[row][col]):
                return (row, col)

class GridMaker(object):
    def __init__(self, array: List[list], current_position: dict):
        assert len(array) > 0
        self.array = array
        self.current_position = current_position
        self.new_position = {"vertical": {}, "horizontal": {}}
        self.number = 1
        self.board = []

        self.cornerA = "┌"
        self.lineH = "───"
        self.centerTop = "┬"
        self.cornerB = "┐"
        self.lineV = "│"
        self.centerLeft = "├"
        self.cross = "┼"
        self.centerRight = "┤"
        self.cornerC = "└"
        self.centerBottom = "┴"
        self.cornerD = "┘"

        self.empty_char = " "

    def is_empty(self, arr: List[list]) -> Union[bool]:
        return len(arr) < 1

    def is_empty_char(self, char: str) -> Union[bool]:
        return char in (self.empty_char, self.empty_char * 3)

    def mergelines(self) -> List[str]:
        return [
            [[i for l in line for i in l]
             for line in self.board[i:i+3]]
            for i in range(0, len(self.board), 3)
        ]

    def joinlines(self) -> None:
        pair = {
            (self.cornerC, self.cornerA): self.centerLeft,
            (self.cornerD, self.cornerB): self.centerRight,
            (self.cornerC, self.cornerB): self.cross,
            (self.cornerD, self.cornerA): self.cross,
            (self.cornerD, self.centerTop): self.cross,
            (self.cornerC, self.centerTop): self.cross,
            (self.centerBottom, self.centerTop): self.cross,
            (self.centerBottom, self.cornerA): self.cross,
            (self.centerBottom, self.cornerB): self.cross,
            (self.centerBottom, self.cornerD): self.cross
        }

        board = self.mergelines()
        lboard = len(board)
        for index in range(1, lboard):
            newline = []
            for uchar, dchar in itertools.zip_longest(board[index - 1][-1], board[index][0]):
                if (nkey := pair.get((uchar, dchar))):
                    newline.append(nkey)
                else:
                    newline.append(
                        uchar if self.is_empty_char(dchar) else dchar)
            board[index - 1][-1] = newline
            board[index] = board[index][1:]
        self.board = [line for grid in board for line in grid]

    def parseline(self, array: List[str]) -> None:
        results = Namespace(upline=[], center=[], bottom=[])
        end = len(array) - 1
        for index in range(end + 1):
            char = array[index]

            upline_template = [self.empty_char,
                               self.empty_char * 3, self.empty_char]
            center_template = [self.empty_char,
                               self.empty_char * 3, self.empty_char]
            bottom_template = [self.empty_char,
                               self.empty_char * 3, self.empty_char]
            if not self.is_empty_char(char):
                upline_template[:2] = [self.cornerA, self.lineH]
                center_template[:2] = [self.lineV, f" {char} "]
                bottom_template[:2] = [self.cornerC, self.lineH]
                if index == end:
                    upline_template[2] = self.cornerB
                    center_template[2] = self.lineV
                    bottom_template[2] = self.cornerD
                else:
                    if not self.is_empty_char(array[index + 1]):
                        upline_template[2] = self.centerTop
                        bottom_template[2] = self.centerBottom
                    else:
                        upline_template[2] = self.cornerB
                        bottom_template[2] = self.cornerD
                    center_template[2] = self.lineV
                if not self.is_empty(results.upline) and results.upline[-1][-1] == self.centerTop:
                    upline_template = upline_template[1:]
                if not self.is_empty(results.bottom) and results.bottom[-1][-1] == self.centerBottom:
                    bottom_template = bottom_template[1:]
            else:
                if index != end:
                    upline_template = upline_template[:-1]
                    center_template = center_template[:-1]
                    bottom_template = bottom_template[:-1]
                if not self.is_empty(results.upline) and not self.is_empty_char(results.upline[-1][-1]):
                    upline_template = upline_template[1:]
                if not self.is_empty(results.bottom) and not self.is_empty_char(results.bottom[-1][-1]):
                    bottom_template = bottom_template[1:]
            if not self.is_empty(results.center) and results.center[-1][-1] == self.lineV:
                center_template = center_template[1:]

            results.upline.append(upline_template)
            results.center.append(center_template)
            results.bottom.append(bottom_template)

        self.board.extend(results.__dict__.values())

    def update_position(self) -> None:
        def calc(pos: tuple) -> tuple:
            return tuple(map(lambda x: (x * 2) + 1, pos))

        def add_number(pos: tuple) -> None:
            row, col = calc(pos)
            char = self.board[row - 1][col]
            if char == self.lineH:
                char = f"{{0:{self.lineH[0]}<3}}".format(self.number)
                self.number += 1
            self.board[row - 1][col] = char
            return re.search(r"(\d+)", char).group(1)

        for vertical, horizontal in itertools.zip_longest(self.current_position.vertical, self.current_position.horizontal):
            if vertical:
                pos, word = vertical
                number = add_number(pos)
                self.new_position["vertical"][word] = {
                    "number": number,
                    "loc": [calc((pos[0] + index, pos[1])) for index in range(len(word))]
                }
            if horizontal:
                pos, word = horizontal
                number = add_number(pos)
                self.new_position["horizontal"][word] = {
                    "number": number,
                    "loc": [calc((pos[0], pos[1] + index)) for index in range(len(word))]
                }

    def genClueless(self):
        board = []
        for line in self.board:
            board.append([re.sub(r"[A-Z]", " ", char) for char in line])
        self.clueless = board

    def generate(self) -> None:
        for array in self.array:
            self.parseline(array)
        self.joinlines()
        self.update_position()
        self.genClueless()

    def serialize(self, arrays: Optional[List[list]] = None) -> None:
        arrays = arrays or self.board
        return ["".join(i) for i in arrays]

class crosswordEngine:
    def __init__(self, words: List[str], *, maxloop: Optional[int] = 1, empty_cell: str = " ", maxheight: Optional[int] = None, maxwidth: Optional[int] = None):
        assert len(words) > 0, "input 'kata' tidak boleh kosong"

        self.direct = Namespace(up="UP", down="DOWN",
                                left="LEFT", right="RIGHT")

        # filter kata terlebih dahulu menggunakan :regex:
        # kriteria kata yang kita butuhkan seperti ini;
        #  - kata harus lebih dari 2 karakter
        #  - karakter yang diperbolehkan hanya alfabet dari A sampai Z
        #    huruf kecil juga termasuk
        self.words = set(word.upper() for word in words if word and re.match(
            r"^[a-zA-Z]{2,}$", word))
        self.word_used = set()

        # maksimal rekursif yang kita butuhkan, karena akan ada kondisi dimana
        # kata tidak bisa ditambahkan sebab belumb ada huruf dengan posisi yang
        # valid
        self.maxloop = maxloop
        self.registered = Namespace(horizontal=[], vertical=[])
        self.empty_cell = empty_cell

        self.maxheight = maxheight or float("inf")
        self.maxwidth = maxwidth or float("inf")
        self.nonetype = type(None)
        self.array = self.build_first_array()
        logging.info(
            f"generating crossword [{self.maxheight}, {self.maxwidth}]")
        self.logging_level = logging.getLogger().level

    def longest_word(self, *,  delitem: bool = False) -> str:
        """
           Fungsi untuk mencari kata terpanjang dari list kata yang sudah kita filter sebelumnya.
           Ini sangat penting karena dengan kata paling panjang otomatis kemungkinan
           mencari huruf yang sama juga tinggi.
        """
        longest_word_ = ""
        for word in self.words:
            if len(word) >= len(longest_word_):
                longest_word_ = word
        if delitem and longest_word_:
            self.words.remove(longest_word_)
        return longest_word_

    def next_word(self, **kwargs) -> str:
        """Fungsi wrapper dari :self.longest_word:"""
        return self.longest_word(**kwargs)

    def build_first_array(self) -> List:
        """Fungsi untuk membuat pondasi array, bisa mendatar atau menurun

        l = [
           ["L", "O", "R", "E", "M"],
           [" ", " ", "B", " ", " "],
           [" ", " ", "Z", " ", " "],
           [" ", " ", " ", " ", " "],
           [" ", " ", "X", "S", " "],
        ]
        self.registered.vertical.append(("RBZ", (0, 2)))
        self.registered.horizontal.extend([
            ("LOREM", (0, 0)),
            ("XS", (4, 2))
        ])
        """

        longest_word = self.longest_word(delitem=True)
        self.word_used.add(longest_word)
        logging.info(f"kata dasar: {longest_word}")
        if random.choice([self.direct.down, self.direct.right]) == self.direct.down:
            self.registered.vertical.append([(0, 0), longest_word])
            return [[char] for char in longest_word]
        else:
            self.registered.horizontal.append([(0, 0), longest_word])
            return [[char for char in longest_word]]

    def split_text(self, word: str, delimeter: str) -> List[tuple]:
        """
           Fungsi untuk memisahkan kata menjadi 2 bagian. sebagai contoh:

           >>> split_text("robo", "b")
           ... [("ro", "o")]
           >>> split_text("robo", "o")
           ... [("r", "bo"), ("rob", "")]
        """
        def x(y): return delimeter.join(y)

        splited = word.split(delimeter)
        if len(splited) == 2:
            return [splited]
        else:
            n = []
            for i in range(1, len(splited)):
                n.append((x(splited[:i]), x(splited[i:])))
            return n

    def find_position(self, word: str) -> dict:
        """Fungsi untuk mencari posisi huruf yang sama dalam sebuah array"""
        dict = {}
        for char in word:
            for col, arr in enumerate(self.array):
                for row, ar in enumerate(arr):
                    if char == ar and (col, row) not in dict.get(char, []):
                        dict.setdefault(char, [])
                        dict[char].append((col, row))
        return dict

    def update_registered_position(self, direction: str, newA: int) -> None:
        """
           Karena isi dari :self.array: selalu berubah-ubah maka kita
           juga akan memperbaharui posisi dari kata yang sudah terdaftar
           sebelumnya
        """
        for index, (vertical, horizontal) in enumerate(itertools.zip_longest(self.registered.vertical, self.registered.horizontal)):
            if vertical:
                (row, col), word = vertical
                if direction == "vertical":
                    row += newA
                elif direction == "horizontal":
                    col += newA
                self.registered.vertical[index] = [(row, col), word]
            if horizontal:
                (row, col), word = horizontal
                if direction == "vertical":
                    row += newA
                elif direction == "horizontal":
                    col += newA
                self.registered.horizontal[index] = [(row, col), word]

    def addWord(self, data: Namespace) -> None:
        """
           Menambahkan kata kedalam :self.array: sesuai dengan :data:
           yang diberikan
        """
        row, col = data.location
        word = data.sideA + data.char + data.sideB
        self.word_used.add(word)

        #  cek tinggi array + grid harus kurang dari :self.maxheight:
        def calcHeight():
            return (len(self.array) + data.newA + data.newB) * 2 + 1

        #  dan lebar array + grid harus kurang dari :self.maxwidth:
        def calcWidth():
            return (len(self.array[0]) + data.newA + data.newB) * 4 + 1

        template = Namespace(word=data.sideA + data.char +
                             data.sideB, row=row, col=col, cross=False)
        if calcHeight() < self.maxheight and data.direction == "vertical":
            self.registered.vertical.append(
                [(row - len(data.sideA), col), word]
            )
            row += data.newA
            if data.sideA:
                for _ in range(data.newA):
                    self.array.insert(0, [self.empty_cell]
                                      * len(self.array[0]))
                for num in range(1, len(data.sideA) + 1):
                    charA = data.sideA[-num]
                    self.array[row - num][col] = charA
            if data.sideB:
                for _ in range(data.newB):
                    self.array.append([self.empty_cell] * len(self.array[0]))
                for num, charA in enumerate(data.sideB, start=1):
                    self.array[row + num][col] = charA

        elif calcWidth() < self.maxwidth and data.direction == "horizontal":
            self.registered.horizontal.append(
                [(row, col - len(data.sideA)), word]
            )
            col += data.newA
            for n in range(len(self.array)):
                for _ in range(data.newA):
                    self.array[n].insert(0, self.empty_cell)
                for _ in range(data.newB):
                    self.array[n].append(self.empty_cell)
            if data.sideA:
                for num in range(1, len(data.sideA) + 1):
                    charB = data.sideA[-num]
                    self.array[row][col - num] = charB
            if data.sideB:
                for num, charB in enumerate(data.sideB, start=1):
                    self.array[row][col + num] = charB
        else:
            return False
        self.update_registered_position(data.direction, data.newA)
        return True

    def checkLines(self, l: List[int], direction: str) -> Optional[bool]:
        maxcon = [(c, len(list(nl))) for c, nl in itertools.groupby(l)]
        for i, (x, y) in enumerate(maxcon):
            if (i == 0 and x == 0) or isinstance(x, self.nonetype) or (x == 0 and y > 1):
                return False
        return True

    def isCellCrash(self, current_position: tuple, real_direction: str) -> Optional[bool]:
        def verify(row: int, col: int) -> Optional[bool]:
            cpositions = {
                "cur": (row, col),
                "up": (row - 1, col), "down": (row + 1, col),
                "left": (row, col - 1), "right": (row, col + 1),
            }
            return current_position in cpositions.values()

        def translate(current_position: Union[tuple, List], real_direction: str) -> tuple:
            row, col = current_position
            if real_direction in ("up.left", "down.left"):
                col += 1
            elif real_direction in ("up.right", "down.right"):
                col -= 1
            elif real_direction in ("left.up", "right.up"):
                row += 1
            elif real_direction in ("left.down", "right.down"):
                row -= 1
            return (row, col)

        currow, curcol = current_position
        rrow, rcol = translate(current_position, real_direction)

        for vertical, horizontal in itertools.zip_longest(self.registered.vertical, self.registered.horizontal):
            if vertical:
                (row, col), word = vertical
                lword = len(word) - 1
                if (verify(rrow, rcol) or verify(rrow + lword, rcol)):
                    if not any(i in range(row + 1, row + lword) for i in [rrow - 1, rrow + 1]):
                        logging.debug(
                            f"crash on position: ({rrow}, {rcol}), HORIZONTAL.{real_direction}")
                        return None

            if horizontal:
                (row, col), word = horizontal
                lword = len(word) - 1
                if (verify(rrow, rcol) or verify(rrow, rcol + lword)):
                    if not any(i in range(col + 1, col + lword) for i in [rcol - 1, rcol + 1]):
                        logging.debug(
                            f"crash on position: ({rrow}, {rcol}), VERTICAL.{real_direction}")
                        return None

        return 0 if self.array[currow][curcol] != self.empty_cell else 1

    def checkSide(self, row: int, col: int, real_direction: str) -> Optional[int]:
        if self.array[row][col] == self.empty_cell:
            return 1
        return self.isCellCrash((row, col), real_direction)

    def findPossibleDirection(self, word: str, char: str, location: tuple) -> Optional[str]:
        splited_text = self.split_text(word, char)
        row, col = location

        results = []

        # 1 artinya sel sudah ditempati
        # 0 berarti belum ditempati alias masih kosong
        lines = Namespace(
            up=Namespace(left=[], right=[]),
            down=Namespace(left=[], right=[]),
            left=Namespace(up=[], down=[]),
            right=Namespace(up=[], down=[]),
        )

        # mulai mengecek satu persatu
        for sideA, sideB in splited_text:
            local_direct = Namespace(
                up=False, down=False, left=False, right=False)

            # step 1: cek line dan sisi kiri/kanan jika
            logging.debug(f"\n{sideA  = }")
            for num in range(1, len(sideA) + 1):
                if not isinstance(local_direct.up, self.nonetype):
                    if row - num < 0:
                        if not isinstance(local_direct.up, int):
                            local_direct.up = 0
                        local_direct.up += 1
                    else:
                        previous_char = self.array[row - num][col]
                        if previous_char not in (self.empty_cell, sideA[-num]):
                            local_direct.up = None

                if not isinstance(local_direct.left, self.nonetype):
                    if col - num < 0:
                        if not isinstance(local_direct.left, int):
                            local_direct.left = 0
                        local_direct.left += 1
                    else:
                        previous_char = self.array[row][col - num]
                        if previous_char not in (self.empty_cell, sideA[-num]):
                            local_direct.left = None

                if row - num >= 0:
                    lines.up.left.append(self.checkSide(row - num, col - 1, "up.left")
                                         if col - 1 >= 0 else 1)
                    lines.up.right.append(self.checkSide(row - num, col + 1, "up.right")
                                          if col + 1 < len(self.array[row]) else 1)
                if col - num >= 0:
                    lines.left.up.append(self.checkSide(row - 1, col - num, "left.up")
                                         if row - 1 >= 0 else 1)
                    lines.left.down.append(self.checkSide(row + 1, col - num, "left.down")
                                           if row + 1 < len(self.array) else 1)

            logging.debug(f"{location} = {char}")
            logging.debug(f"{sideB  = }")

            for num, charB in enumerate(sideB, start=1):
                if not isinstance(local_direct.down, self.nonetype):
                    if row + num >= len(self.array):
                        if not isinstance(local_direct.down, int):
                            local_direct.down = 0
                        local_direct.down += 1
                    else:
                        next_char = self.array[row + num][col]
                        if next_char not in (self.empty_cell, charB):
                            local_direct.down = None

                if not isinstance(local_direct.right, self.nonetype):
                    if col + num >= len(self.array[row]):
                        if not isinstance(local_direct.right, int):
                            local_direct.right = 0
                        local_direct.right += 1
                    else:
                        next_char = self.array[row][col + num]
                        if next_char not in (self.empty_cell, charB):
                            local_direct.right = None

                if row + num < len(self.array):
                    lines.down.left.append(self.checkSide(row + num, col - 1, "down.left")
                                           if col - 1 >= 0 else 1)
                    lines.down.right.append(self.checkSide(row + num, col + 1, "down.right")
                                            if col + 1 < len(self.array[row]) else 1)
                if col + num < len(self.array[row]):
                    lines.right.up.append(self.checkSide(row - 1, col + num, "right.up")
                                          if row - 1 >= 0 else 1)
                    lines.right.down.append(self.checkSide(row + 1, col + num, "right.down")
                                            if row + 1 < len(self.array) else 1)

            logging.debug(f"{lines.up = }")
            logging.debug(f"{lines.left = }")
            logging.debug(f"{lines.down = }")
            logging.debug(f"{lines.right = }")

            # step 2: ubah value
            if local_direct.left is False and col - len(sideA) >= 0:
                local_direct.left = 0
            if local_direct.up is False and row - len(sideA) >= 0:
                local_direct.up = 0
            if local_direct.right is False and col + len(sideB) < len(self.array[row]):
                local_direct.right = 0
            if local_direct.down is False and row + len(sideB) < len(self.array):
                local_direct.down = 0

            # step 3: cek self.array[row][col] sebelum/sesudah harus kosong
            if local_direct.up is not False and row + 1 < len(self.array) and self.array[row + 1][col] != self.empty_cell:
                local_direct.down = None
            if local_direct.down is not False and row > 0 and self.array[row - 1][col] != self.empty_cell:
                local_direct.up = None
            if local_direct.right is not False and col > 0 and self.array[row][col - 1] != self.empty_cell:
                local_direct.left = None
            if local_direct.left is not False and col + 1 < len(self.array[row]) and self.array[row][col + 1] != self.empty_cell:
                local_direct.right = None

            # step 4: cek sel setelah ujung kata harus kosong
            if sideA:
                if isinstance(local_direct.up, int) and row - len(sideA) > 0 and self.array[row - len(sideA) - 1][col] != self.empty_cell:
                    local_direct.up = None
                if isinstance(local_direct.left, int) and col - len(sideA) > 0 and self.array[row][col - len(sideA) - 1] != self.empty_cell:
                    local_direct.left = None
            if sideB:
                if isinstance(local_direct.down, int) and row + len(sideB) + 1 < len(self.array) and self.array[row + len(sideB) + 1][col] != self.empty_cell:
                    local_direct.down = None
                if isinstance(local_direct.right, int) and col + len(sideB) + 1 < len(self.array[row]) and self.array[row][col + len(sideB) + 1] != self.empty_cell:
                    local_direct.right = None

            # step 5: cek sekitar line
            in_lines = Namespace(
                up=(self.checkLines(lines.up.left, "up.left") and
                    self.checkLines(lines.up.right, "up.right")
                    and bool(sideA)) or not bool(sideA),
                down=(self.checkLines(lines.down.left, "down.left") and
                      self.checkLines(lines.down.right, "down.right") and bool(
                    sideB)) or not bool(sideB),
                left=(self.checkLines(lines.left.up, "left.up") and
                      self.checkLines(lines.left.down, "left.down") and bool(
                    sideA)) or not bool(sideA),
                right=(self.checkLines(lines.right.up, "right.up") and
                       self.checkLines(lines.right.down, "right.down") and bool(
                    sideB)) or not bool(sideB)
            )

            logging.debug(f"{in_lines = }")
            logging.debug(f"{local_direct = }")

            # OK: parse final result
            if (local_direct.left is not False and local_direct.right is not False) and \
               (local_direct.left is not None and local_direct.right is not None) and \
               (local_direct.left or not (local_direct.left and sideA)) and \
               (in_lines.left and in_lines.right) and \
               (local_direct.right or not (local_direct.right and sideB)):
                results.append(Namespace(direction="horizontal", location=location, char=char, sideA=sideA, sideB=sideB,
                                         newA=local_direct.left or 0, newB=local_direct.right or 0))

            if (local_direct.up is not False and local_direct.down is not False) and \
               (local_direct.up is not None and local_direct.down is not None) and \
               (local_direct.up or not (local_direct.up and sideA)) and \
               (in_lines.up and in_lines.down) and \
               (local_direct.down or not (local_direct.down and sideB)):
                results.append(Namespace(direction="vertical", location=location, char=char, sideA=sideA, sideB=sideB,
                                         newA=local_direct.up or 0, newB=local_direct.down or 0))
        if results and self.logging_level == logging.DEBUG:
            logging.debug("results:")
            pprint(results)
        return results

    def parsePos(self, word: str, locations: List[tuple]) -> dict:
        logging.debug(f"parsing kata: {word}")
        results = []
        for char, pos in locations.items():
            for po in pos:
                if (data_results := self.findPossibleDirection(word, char, po)):
                    results.extend(data_results)
                    logging.debug(
                        f"\nterdapat {len(data_results)} kemungkinan untuk lokasi {po}\ntotal kemungkinan untuk kata {word!r}: {len(results)}\n")
        return random.choice(results or [None])

    def compute(self, loop=0, added=0) -> None:
        temp = []
        while self.words:
            next_word = self.next_word(delitem=True)
            pos = self.find_position(next_word)
            if (data := self.parsePos(next_word, pos)):
                added += 1
                logging.info(
                    f"menambahkan kata: {next_word!r} {data.location} arah {data.direction!r} {len(self.words)} kata tersisa [{len(self.array) * 2}, {len(self.array[0]) * 2}]")
                if not self.addWord(data):
                    temp = []
                    break
            else:
                logging.info(f"lewati kata: {next_word}")
                temp.append(next_word)
        if temp:
            if loop >= self.maxloop:
                logging.info(
                    f"\n{added} kata berhasil ditambahkan\n{len(temp)} kata tidak dapat ditambahkan {temp}")
                return
            self.words = set(temp)
            self.compute(loop + 1, added)
        else:
            logging.info(f"\n{added} kata berhasil ditambahkan")

    def refresh(self):
        wordUse = self.word_used
        lwordUse = len(wordUse)
        prevarray = [self.array]

        loop = 1
        while loop:
            self.__init__(wordUse, maxloop=self.maxloop, empty_cell=self.empty_cell, maxheight=self.maxheight, maxwidth=self.maxwidth)
            self.compute()
            if (len(self.word_used) == lwordUse and self.array != prevarray) or loop >= self.maxloop:
                break
            loop += 1

    def generateBoard(self) -> tuple:
        gridMaker = GridMaker(self.array, self.registered)
        gridMaker.generate()
        return gridMaker

if __name__ == "__main__":
    from cmd2 import ansi
    import shutil
    term = shutil.get_terminal_size()
    c = crosswordEngine(
        sys.argv[1:], maxheight=term.lines, maxwidth=term.columns)
    try:
        c.compute()
    except KeyboardInterrupt:
        pass
    g = c.generateBoard()
    x = g.serialize()
    print(ansi.style(
        "\n".join(x),
        bold=True
    ), "\n", "=" * 20)

    p = parseLoc(g.board, g.new_position)
    print (p.start)
    p.moveLeft()
    print (p.start)
    p.moveRight()
    print (p.start)
    p.locaround
    print (g.clueless)
