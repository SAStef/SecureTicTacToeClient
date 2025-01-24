from PyQt6.QtCore import QThread, pyqtSignal
import random
import traceback  # Debugging
import socket as sock



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
        self.testNumber = 4

    def run(self):
        try:
            self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self.s.connect((self.host, self.port))

            self.initCryptHandshake() # initialiserer two-way handshake og enkryption mellem klient og server

            while self.isRunning:
                self.handleData() #derefter kører handleData som enten sender data eller modtager, hvorledes T=3

        except Exception as e:
            print(f"Fejlen i __init__: {e}")
            traceback.print_exc() # printer fejlen
        except Exception as e:
            self.statusUpdated.emit(f"Error: {e}") # for at fejlen kan komme op på QLabel
        finally:
            if self.s:
                self.s.close() #afslut efter processen er done (hvis man lukker siden osv.)

    def initCryptHandshake(self):  # modtager hello (1st hand in handshake) fra server
        T = self.s.recv(1)
        T = int.from_bytes(T)

        L = self.s.recv(1)
        L = int.from_bytes(L)

        g = self.s.recv(16)
        g = int.from_bytes(g)

        p = self.s.recv(16)
        p = int.from_bytes(p)

        A = self.s.recv(16)
        A = int.from_bytes(A)

        FCS = self.s.recv(2)
        FCS_int = int.from_bytes(FCS)

        data_byte_array = ( 
            T.to_bytes(1)
            + L.to_bytes(1)
            + g.to_bytes(16)
            + p.to_bytes(16)
            + A.to_bytes(16)
        )
        calculated_checksum = self.calculateFCS(data_byte_array)

        self.checkFCS(calculated_checksum, FCS_int)

        b = random.getrandbits((8 * 16) - 2)
        B = pow(g, b, p)
        self.K = pow(A, b, p)

        self.sendClientHello(B)

    def sendClientHello(self, B):  # sender hello (2nd hand in handshake) fra klient
        T = 2
        T = T.to_bytes(1)
        B = B.to_bytes(16)
        L = len(B) + 2
        L = L.to_bytes(1)
        data = T + L + B
        FCS = self.calculateFCS(data)
        FCS_bytes = FCS.to_bytes(2)
        clienthello = data + FCS_bytes
        self.s.send(clienthello)

    def handleData(self, move=None):
        serverResponse = ""

        if move is None:
            T = self.s.recv(1)

            L_bytes = self.s.recv(1)
            L_int = int.from_bytes(L_bytes)
            payload = self.s.recv(L_int)

            result = self.encryptDecrypt(payload)

            firstline_bytes = result[:-2]
            data = T + L_bytes + firstline_bytes
            recieved_FCS = int.from_bytes(result[-2:])

            firstline = str(firstline_bytes)
            serverResponse = firstline[12:-2]

            own_FCS = self.calculateFCS(data)
            self.checkFCS(own_FCS, recieved_FCS)
        if "WELCOME" in serverResponse:
            self.statusUpdated.emit(serverResponse)
            pass
        elif "ILLEGAL" in serverResponse:
            self.statusUpdated.emit(serverResponse)
            pass
        elif "BOARD IS" in serverResponse:

            boardResponse = serverResponse[-9:]
            self.boardUpdated.emit(boardResponse)

        elif any(
            end_condition in serverResponse
            for end_condition in ["PLAYER WINS", "COMPUTER WINS", "NOBODY WINS"]
        ):
            self.gameEnded.emit(serverResponse)
            self.running = False

        if (
            move is not None
        ):  # implementeres her fordi tanken er at handleData både bruges til at modtage og sende data for at simplificere projektet. (ville havde gjort det på en anden måde hvis det var et større projekt hvor man havde hver handler til data in/out)

            T = 3
            T_send = T.to_bytes(1)

            player_input_send = bytearray()
            player_input_send.extend(map(ord, str(move))) # laver bytearray for at kunne sende string
            L = len(player_input_send) + 2
            L_send = L.to_bytes(1)

            header = T_send + L_send

            data = header + player_input_send

            FCS = self.calculateFCS(data)
            FCS_bytes = FCS.to_bytes(2)

            player_move = (
                header
                + self.encryptDecrypt(player_input_send)
                + self.encryptDecrypt(FCS_bytes)
            )

            if self.s:
                try:
                    self.s.send(player_move)
                except Exception as e:
                    self.statusUpdated.emit(f"Error: {e}")

        elif "WINS" in serverResponse:
            print("GGWP!")
            self.isRunning = False
            self.s.close()

    def calculateFCS(self, data):
        sum1 = 0
        sum2 = 0
        for i in range(len(data)):
            sum1 = (sum1 + data[i]) % 255
            sum2 = (sum2 + sum1) % 255
        return (sum2 << 8) + sum1

    def checkFCS(self, calculated_FCS, recieved_FCS):
        if calculated_FCS == recieved_FCS:
            return self.isRunning == True
        else:
            self.isRunning == False
            print(
                'GAME CRASHED DUE TO BITFLIP ISSUES AND THE DEVELOPERS HAVEN\'T IMPLEMENTED "7, 4 HAMMING" BECAUSE THEY WERE LAZY! TRY AGAIN!'
            )
            self.s.close()
            return False

    def encryptDecrypt(self, data_payload):
        if not hasattr(self, "X") or self.X is None:
            self.X = self.K.to_bytes(16)[13:16]
            self.X = int.from_bytes(self.X)
        a = 125
        c = 1
        result = bytearray(len(data_payload))
        for i in range(len(data_payload)):
            self.X = (a * self.X + c) % (2**24)
            keybyte = self.X.to_bytes(3)[1]
            result[i] = data_payload[i] ^ keybyte
        return result
