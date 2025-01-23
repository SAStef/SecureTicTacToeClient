# Stefan Artur Stefirta og Andreas Bundgaard

import socket as sock
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ServerWorker(QThread): # hele opgavens løsning er gennemtænkt således at man har en worker klasse som egentlig bare skal initialiseres og derefter instansieres ud fra initialiseringen, hvilket gør at man kan opnå multithreading. Dette er fordi vi gerne vil køre init af gui samtidigt med håndtering af logik.
    boardUpdated = pyqtSignal(str)
    statusUpdated = pyqtSignal(str) # pyqtSignal fungerer lidt som en dispatch-funktion inden for webudvikling - for at forbinde backend logik og frontend event handling skal man emit et dispatch i frontend som man dermed kan bruge til at håndtere state som i dette tilfælde er vores GUI i PyQt6.
    gameEnded = pyqtSignal(str) 

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.s = None # sætter default værdier til attributterne til at starte med. Vi behøver egentlig ikke at initialisere "s" og "file" attributterne men det gør det bare til cleaner code og det er better practice ift. at deklarere sine attributter i init-funktionen som man vil bruge i sine method functions
        self.file = None
        self.running = True # initialiserer at tråden er i gang.

    def run(self):
        try:
            # vi initialiserer ud fra self denne gang, da vi arbejder ud fra Object Oriented Programming og skal manipulere ud fra self argumentet fra init
            self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.s.connect((self.host, self.port))
            self.file = self.s.makefile("r") # koden i try-block'en er sådan set samme simple logik som fra opgaven med terminal som UI, bare lidt ændret for at gøre det lidt kortere + sat emitters på for at implementere state handling til vores GUI.

            yourMarker = self.file.readline().strip()
            print(f"Your marker: {yourMarker}")

            while self.running:
                rawBoardResponse = self.file.readline().strip()
                if not rawBoardResponse:
                    continue 

                boardResponse = rawBoardResponse[-9:]
                self.boardUpdated.emit(boardResponse) 

                textResponse = self.file.readline().strip()
                print(f"Server response: {textResponse}")
                self.statusUpdated.emit(textResponse)

                if any(
                    end_condition in textResponse
                    for end_condition in ["PLAYER WINS", "COMPUTER WINS", "NOBODY WINS"]
                ):
                    self.gameEnded.emit(textResponse) 
                    self.running = False
        except Exception as e:
            self.statusUpdated.emit(f"Error: {e}")
        finally: # kode som skal blive kørt når try-block'en er færdig med at køre.
            if self.s:
                self.s.close()

    def sendMove(self, move):
        if self.s:
            try:
                self.s.send(f"{move}\r\n".encode())
            except Exception as e:
                self.statusUpdated.emit(f"Error: {e}")

class TicTacToe(QWidget):
    def __init__(self):
        super().__init__()
        self.board = "." * 9 
        self.serverWorker = ServerWorker("34302.cyberteknologi.dk", 1060)

        self.init_ui()
        self.connectSignals()

        self.serverWorker.start()

    def init_ui(self):
        self.setWindowTitle("Tic Tac Toe")
        self.layout = QVBoxLayout(self)
        self.gridLayout = QGridLayout()

        self.buttons = [QPushButton() for _ in range(9)]
        for i, btn in enumerate(self.buttons):
            row = i // 3
            col = i % 3
            self.gridLayout.addWidget(btn, row, col)
            btn.setText(" ")
            btn.clicked.connect(lambda _, idx=i: self.handleButtonClick(idx)) # "lambda _, idx=i:" fanger den instans af loopets index-værdi således at man kan pass den bestemte trykkede knap ned til handleButtonClick funktionen. Dette er for at undgå at skulle have 9 if statements ud fra sender() i handlerfunktionen istedetfor.

        self.statusLabel = QLabel() # statusLabel initialiseres. (den tekst som står ovenfor spillet som informerer spilleren om status på spillet)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.statusLabel)
        self.layout.addLayout(self.gridLayout)

    def connectSignals(self):
        self.serverWorker.boardUpdated.connect(self.updateBoard) # forbinder actions til dispatches
        self.serverWorker.statusUpdated.connect(self.updateStatus)
        self.serverWorker.gameEnded.connect(self.endGame)

    def handleButtonClick(self, index):
        if not self.board[index] == ".": #denne logik behøves egentlig ikke fordi knapperne i forvejen bliver enabled/disabled, men bare for en sikkerhedsskyld (sanity check)
            return

        self.serverWorker.sendMove(index + 1) # +1 skal huskes her da index argumentet stadig er nul-indekseret og vi skal sende et træk som ligger imellem felterne 1-9

    def updateBoard(self, board):
        self.board = board
        for i, char in enumerate(board): # looper bare over board-state beskeden fra server påny
            self.buttons[i].setText(char if char != "." else " ")
            self.buttons[i].setEnabled(char == ".") # for at kun enable de knapper som er tilladte at klikke på

    def updateStatus(self, status):
        self.statusLabel.setText(status) # har bare valgt at tage status fra serveren

    def endGame(self, message):
        self.statusLabel.setText(message)
        for btn in self.buttons:
            btn.setEnabled(False) # hvis nogen vinder så vil man ikke have at der stadig kan trykkes på de knapper som er tilbage.
        self.serverWorker.running = False # initialiserer at tråden ikke er i gang længere
        self.serverWorker.quit() # exit even loop
        self.serverWorker.wait() # god practice for at sikre sig at worker er stoppet med at køre og ikke er i gang under nedlukningsprocessen af main thread (hvilket ofte skaber bugs i større programmer).

if __name__ == "__main__":
    app = QApplication([])
    gui = TicTacToe()
    gui.setWindowTitle("Tutorial 2 - Tic Tac Toe GUI")
    gui.setMinimumSize(350, 175)
    gui.show()
    app.exec()
