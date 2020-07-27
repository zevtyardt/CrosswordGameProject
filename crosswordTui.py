from crosswordEngine import crosswordEngine
from typing import List, Union
import itertools
import curses
import _curses
import threading
import time
import textwrap


class Wraptext:
    def __init__(self):
        self.text = ""
        self.width = 20
        self.maxline = 3
        self.index = 0
        self.maxindex = float("inf")
        self.prevdirect = None
        self._result = []

    def update(self, text: str, width: int = None, maxline: int = None):
        if self.text != text:
            self.text = text
        if width != self.width:
            self.width = width
            self.maxindex = float("inf")
        if maxline:
            self.maxline = maxline

    def _calc(self, back=False):
        if back and self.index > 0:
            self.index -= 1
        wrapped = textwrap.wrap(self.text, self.width)
        splited = [wrapped[i + self.index: i + self.index + self.maxline]
                   for i in range(0, len(wrapped), self.maxline)]
        result = splited[0]
        if len(result) < self.maxline:
            result = wrapped
        if result[-1] == wrapped[-1]:
            self.maxindex = self.index
        if not back and self.index < self.maxindex:
            self.index += 1
        self._result = result
        return result

    def __iter__(self):
        return iter(self._result)

    @property
    def next(self):
        if self.prevdirect == "back":
            self.index += 1
        self.prevdirect = "next"
        return self._calc()

    @property
    def back(self):
        if self.prevdirect == "next" and self.index != self.maxindex:
            self.index -= 1
        self.prevdirect = "back"
        return self._calc(back=True)


class _Utils:
    def calc_center(self, texts: Union[str, list], win: _curses.window) -> tuple:
        if isinstance(texts, str):
            texts = [texts]
        longestText = max(texts)
        ltexts = len(texts)
        ltxt = len(longestText)
        height, width = map(lambda x: (x // 2), win.getmaxyx())
        return height - (ltexts // 2), width - (ltxt // 2), longestText if ltexts == 1 else texts

    def add_title(self, text: str, win: _curses.window, align: str = "center") -> None:
        if align == "alignleft":
            cw = 2
        elif align == "center":
            ch, cw, text = self.calc_center(text, win)
        elif align == "alignright":
            cw = win.getmaxyx()[1] - 2 - len(text)
        win.addstr(0, cw, f" {text.upper()} ", curses.A_BOLD)

    def refresh(self, *windows) -> None:
        self.scr.refresh()
        for win in windows:
            win.refresh()

    def runtext(self, text: str, maxwidth: int = float("inf"), delimeter: str = " " * 10) -> iter:
        if len(text) < maxwidth:
            while text:
                yield text
                time.sleep(0.5)
        else:
            text += delimeter
            ltext = len(text)
            ldelim = len(delimeter)
            for index in itertools.cycle(range(ltext)):
                line = text[index: maxwidth + index]
                if len(line) != maxwidth:
                    line += text[:index]
                yield line[:maxwidth]
                time.sleep(0.5)

    def startThread(self, name: str, func):
        if not self.activeThread.get(name):
            self.activeThread[name] = True
            th = threading.Thread(target=func)
            th.daemon = True
            th.start()


class CrosswordTui(_Utils):
    def __init__(self):
        self.question = "Lorem Ipsum adalah contoh teks atau dummy dalam industri percetakan dan penataan huruf atau typesetting. Lorem Ipsum telah menjadi standar contoh teks sejak tahun 1500an, saat seorang tukang cetak yang tidak dikenal mengambil sebuah kumpulan teks dan mengacaknya untuk menjadi sebuah buku contoh huruf. Ia tidak hanya bertahan selama 5 abad, tapi juga telah beralih ke penataan huruf elektronik, tanpa ada perubahan apapun. Ia mulai dipopulerkan pada tahun 1960 dengan diluncurkannya lembaran-lembaran Letraset yang menggunakan kalimat-kalimat dari Lorem Ipsum, dan seiring munculnya perangkat lunak Desktop Publishing seperti Aldus PageMaker juga memiliki versi Lorem Ipsum."
        self.score = float("inf")
        self.dataCrossword = None
        self.activeThread = {}

    def startWrapper(self):
        curses.wrapper(self.app)

    def define_colors(self):
        for i in range(1, curses.COLORS):
            curses.init_pair(i, i, curses.COLOR_BLACK)

    def new_window(self, *args):
        _win = curses.newwin(*args)
        _win.border(0)
        return _win

    def generateCrosswordBoard(self, mh: int, mw: int):
        def targetFunc():
            engine = crosswordEngine("ab abc abcd abcde abcdef abcdefg abcdefgh abcdefghi abcdefghij abcdefghijk".split(),
                maxheight=mh, maxwidth=mw)
            engine.compute()
            g = engine.generateBoard()
            self.dataCrossword = {"board": g.serialize(), "height": mh, "width": mw}
        self.startThread("gcb", targetFunc)

    def drawCrossword(self, win: _curses.window):
        mh, mw = win.getmaxyx()
        if not self.dataCrossword and not self.activeThread.get("gcb"):
            self.generateCrosswordBoard(mh, mw)
        if self.dataCrossword:
            if mh > self.dataCrossword["height"] or mw > self.dataCrossword["width"]:
                self.dataCrossword = None
                return
            ch, cw, board = self.calc_center(self.dataCrossword["board"], win)
            for index, line in enumerate(board, start=ch):
                win.addstr(index, cw, line, curses.A_BOLD)

    def displayHelpMenu(self, win: _curses.window):
        win.timeout(500)
        while 1:
            win.erase()
            win.border()
            self.add_title("help menu", win)
            self.drawCrossword(win)
            if win.getch() == ord("g"):
                break

    def app(self, scr):
        self.scr = scr

        self.scr.timeout(500)
        curses.curs_set(0)
        self.define_colors()

        wraptext = Wraptext()
        wraptext.update(self.question, self.scr.getmaxyx()[1] - 19, 3)
        wraptext.next

        ch = 0
        while ch != ord("q"):
            height, width = self.scr.getmaxyx()

            questScreen = self.new_window(5, width - 15, 0, 0)
            self.add_title("question", questScreen, "alignleft")
            questWidth = questScreen.getmaxyx()[1] - 4
            wraptext.update(self.question, width=questWidth)
            for index, line in enumerate(wraptext, start=1):
                questScreen.addstr(index, 2, line)

            mainScreen = self.new_window(height - 5, width, 5, 0)
            self.add_title("teka teki silang v1", mainScreen)
            mainScreen.addstr(*self.calc_center(time.strftime("%c"), mainScreen))

            #  additional
            scoreScreen = self.new_window(5, 15, 0, width - 15)
            self.add_title("score", scoreScreen, "alignleft")
            scoreScreen.addstr(*self.calc_center(
                f"{self.score}", scoreScreen), curses.color_pair(2))

            self.refresh(scoreScreen, questScreen, mainScreen)

            ch = self.scr.getch()
            if ch == ord("g"):
                self.displayHelpMenu(mainScreen)
            elif ch == curses.KEY_PPAGE:
                wraptext.back
            elif ch == curses.KEY_NPAGE:
                wraptext.next

try:
    tui = CrosswordTui()
    tui.startWrapper()
except Exception as e:
    print (e)
