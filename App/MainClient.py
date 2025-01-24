from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout,
    QPushButton,
    QVBoxLayout,
    QLabel,
)
from PyQt6.QtCore import Qt
from ServerWorker import ServerWorker


class TicTacToe(QWidget):
    def __init__(self):
        super().__init__()
        self.board = "." * 9
        self.serverWorker = ServerWorker("34302.cyberteknologi.dk", 1063)

        self.initUI()
        self.connectSignals()

        self.serverWorker.start()

    def initUI(self):
        self.setWindowTitle("Tic Tac Toe")
        self.layout = QVBoxLayout(self)
        self.gridLayout = QGridLayout()

        self.buttons = [QPushButton(" ") for _ in range(9)]
        for i, btn in enumerate(self.buttons):
            self.gridLayout.addWidget(btn, i // 3, i % 3)
            btn.setText(" ")
            btn.setMinimumSize(100, 100)
            btn.setEnabled(True)
            btn.clicked.connect(lambda _, idx=i: self.handleButtonClick(idx))

        self.layout.addLayout(self.gridLayout)
        self.setLayout(self.layout)

        self.statusLabel = (
            QLabel()
        )  # statusLabel initialiseres. (den tekst som står ovenfor spillet som informerer spilleren om status på spillet)
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.statusLabel)
        self.layout.addLayout(self.gridLayout)

    def connectSignals(self):
        self.serverWorker.boardUpdated.connect(
            self.updateBoard
        )  # forbinder actions til dispatches
        self.serverWorker.statusUpdated.connect(self.updateStatus)
        self.serverWorker.gameEnded.connect(self.endGame)

    def handleButtonClick(self, index):
        if (
            not self.board[index] == "."
        ):  # denne logik behøves egentlig ikke fordi knapperne i forvejen bliver enabled/disabled, men bare for en sikkerhedsskyld (sanity check)
            return

        self.serverWorker.handleData(index + 1)

    def updateBoard(self, board):
        self.board = board
        for i, char in enumerate(
            board
        ):  # looper bare over board-state beskeden fra server påny
            self.buttons[i].setText(char if char != "." else " ")
            self.buttons[i].setEnabled(
                char == "."
            )  # for at kun enable de knapper som er tilladte at klikke på

    def updateStatus(self, status):
        self.statusLabel.setText(status)  # har bare valgt at tage status fra serveren

    def endGame(self, message):
        self.statusLabel.setText(message)
        for btn in self.buttons:
            btn.setEnabled(
                False
            )  # hvis nogen vinder så vil man ikke have at der stadig kan trykkes på de knapper som er tilbage.
        self.serverWorker.isRunning = (
            False  # initialiserer at tråden ikke er i gang længere
        )
        self.serverWorker.quit()  # exit even loop
        self.serverWorker.wait()  # god practice for at sikre sig at worker er stoppet med at køre og ikke er i gang under nedlukningsprocessen af main thread (hvilket ofte skaber bugs i større programmer).


if __name__ == "__main__":
    app = QApplication([])
    window = TicTacToe()
    window.setMinimumSize(500, 300)
    window.show()
    app.exec()
