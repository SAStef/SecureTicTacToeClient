import socket as sock
import random
import traceback             # Debugging
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ServerWorker(QThread):
    boardUpdated = pyqtSignal(str)
    statusUpdated = pyqtSignal(str)
    gameEnded = pyqtSignal(str) 

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.s = None
        
        self.file = None
        self.isRunning = True
        
    def run(self):
        try:
            self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.s.connect((self.host, self.port))

            self.recieveType()
            print("initiated")
            
            while self.isRunning:
                self.recieveType()
                print("while loop running fine")

        except Exception as e:
            print(f'Fejlen i __init__: {e}')
            traceback.print_exc()
        except Exception as e:
                self.statusUpdated.emit(f"Error: {e}")
        finally: # kode som skal blive kørt når try-block'en er færdig med at køre.
                if self.s:
                    self.s.close()
                
    def recieveType(self, ):
        T = self.s.recv(1)            # Recv 1 byte til Typen
        T = int.from_bytes(T)

        # Serverhello
        if T == 1:                 
            self.handleServerhello(T)
        # Clienthello
        elif T == 2:
            self.handleClienthello()
        # Data
        elif T == 3:
            self.handleData(T)

    def handleServerhello(self, T):
        L = self.s.recv(1)            # Recv 1 byte til længden, L
        L = int.from_bytes(L)


        g = self.s.recv(16)        # Recv 16 byte til tal g
        g = int.from_bytes(g)


        p = self.s.recv(16)        # Recv 16 byte til tal g
        p = int.from_bytes(p)


        A = self.s.recv(16)
        A = int.from_bytes(A)

        FCS = self.s.recv(2)          # Recv 2 bytes til Frame Check Sequence (Altid 2 bytes)
        FCS_int = int.from_bytes(FCS)

        data_byte_array = T.to_bytes(1) + L.to_bytes(1) + g.to_bytes(16) + p.to_bytes(16) + A.to_bytes(16)
        calculated_checksum = self.calculateFCS(data_byte_array)
        
        self.checkFCS(calculated_checksum, FCS_int)

        # Udregner B, ved at vælge en filfældig b-værdi.
        b = random.getrandbits((8 * 16) - 2)    # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.

        B = pow(g, b, p)
        self.K = pow(A, b, p) # K værdi til self så den kan gives globalt

        self.sendClienthello(B)

    def handleData(self, T):        
        L_bytes = self.s.recv(1)
        L_int = int.from_bytes(L_bytes)                # Længden i bytes. Ex L_int = 18 => 18 bytes.

        payload = self.s.recv(L_int)

        result = self.encryptDecrypt(payload)

        # Bruger serverens sendte data til at udregne FCS osv.
        firstline_bytes = result[:-2]                         # Board state
        data = T.to_bytes(1) + L_bytes + firstline_bytes          # Skal bruges til at udregne FCS.
        recieved_FCS = int.from_bytes(result[-2:])          # Recieved FCS som en integer

        firstline = str(firstline_bytes)
        
        serverstring = firstline[12:-2]        # Laver en string, hvor jeg slicer fra 12 og fjerner de sidste to elementer
        print(f'{serverstring}')
        
        own_FCS = self.calculateFCS(data)
        self.checkFCS(own_FCS, recieved_FCS)

        # Vælger hvad der skal ske alt efter hvad serverstring er:
        if "ILLEGAL" in serverstring:
            print("illegal move!!")
            pass

        elif "BOARD IS" in serverstring:
            print("hello :)")
            pass

        if "YOUR TURN" in serverstring:
            player_input = f"{input("Write your turn (1-9): ")}\r\n".encode()
            
            T_ = 3
            T_send = T_.to_bytes(1)
            
            player_input_send = bytearray()
            player_input_send.extend(map(ord, str(player_input.decode())))
            
            L_ = len(player_input_send) + 2
            L_send = L_.to_bytes(1)
            
            header = T_send + L_send
            
            data = header + player_input_send
            
            FCS = self.calculateFCS(data) # Denne metode returner en integer. Skal laves til et byte-array, for at kunne transmitteres
            FCS_bytes = FCS.to_bytes(2) 
            
            player_move =  header + self.encryptDecrypt(player_input_send) + self.encryptDecrypt(FCS_bytes)
            
            if self.s:
                try:
                    self.s.send(player_move)
                except Exception as e:
                    self.statusUpdated.emit(f"Error: {e}")

        elif "WINS" in serverstring:
            print("GGWP!")
            self.isRunning = False
            self.s.close()

    def sendClienthello(self, B):
        # Generate CLIENTHELLO message

        T = 2                    # Type 2 => CLIENTHELLO.
        T = T.to_bytes(1)        # Skal være 1 byte i længde.

        B = B.to_bytes(16)      # Skal være 16 byte i længde.

        L = len(B) + 2
        L = L.to_bytes(1)

        # - Calculate FCS trailer
        data = T + L + B

        FCS = self.calculateFCS(data)                  # Denne metode returner en integer. Skal laves til et byte-array, for at kunne transmitteres
        FCS_bytes = FCS.to_bytes(2)                         
        
        clienthello = data + FCS_bytes
        # test_msg = "Hello, this is a test"
        # self.s.send(test_msg.encode('utf-8'))
        self.s.send(clienthello)

    def handleClienthello(self, ):
        print(f'Serveren må ikke sende en clienthello. Lukker forbindelsen...')
        self.isRunning = False
        self.s.close()

    def calculateFCS(self, data):
            sum1 = 0
            sum2 = 0
            for i in range(len(data)):
                sum1 = (sum1 + data[i]) % 255
                sum2 = (sum2 + sum1) % 255
            calculated_checksum = (sum2 << 8) + sum1
            
            return calculated_checksum            # Returnerer en integer
            
    def checkFCS(self, calculated_FCS, recieved_FCS):
        if calculated_FCS == recieved_FCS:
                print(f'    calculated_checksum: {calculated_FCS}\n    FCS: {recieved_FCS}')
                return True
        else:
                self.isRunning == False
                print("GAME CRASHED DUE TO BITFLIP ISSUES! TRY AGAIN!")
                self.s.close()   
                return False

    def encryptDecrypt(self, data_payload):
        if not hasattr(self, 'X') or self.X is None:          # Hvis ikke klassen har self.X eller hvis self.X er None
            print(f'Initializing X the first time...')
            self.X = self.K.to_bytes(16)[13:16]                 # Skal kun initlialiseres 1 gang !!!!!!!!
            self.X = int.from_bytes(self.X)

        a = 125      # Fixed værdi
        c = 1        # Fixed værdi
        
        result = bytearray(len(data_payload))
        for i in range(len(data_payload)):
            self.X = (a * self.X + c) % (2**24)
            keybyte = self.X.to_bytes(3)[1]            # Laver self.X til 3 bytes, og udvælger den midterste
            result[i] = data_payload[i] ^ keybyte

        return result

class TicTacToe(QWidget):
    def __init__(self):
        super().__init__()
        self.board = "." * 9 
        self.serverWorker = ServerWorker("34302.cyberteknologi.dk", 1063)
        
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

        self.serverWorker.handleData(index + 1) # +1 skal huskes her da index argumentet stadig er nul-indekseret og vi skal sende et træk som ligger imellem felterne 1-9

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
