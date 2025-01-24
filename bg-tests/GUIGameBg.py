import socket as sock
import random
import traceback             # Debugging

class MainClass():
    def __init__(self):
        try:
            self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)       # Vælger TCP
            self.s.connect(("34302.cyberteknologi.dk", 1063))          # Vælger host og port        

            self.isRunning = True

            self.recieveType()
            while self.isRunning:
                self.recieveType()

        except Exception as e:
            print(f'Fejlen i __init__: {e}')
            traceback.print_exc()
        
    def recieveType(self, ):
        T = self.s.recv(1)            # Recv 1 byte til Typen
        T = int.from_bytes(T)

        # Serverhello
        if T == 1:                 
            print(f'T: {T}, Header: SERVERHELLO')
            self.handleServerhello(T)
        # Clienthello
        elif T == 2:
            print(f'T: {T}, Header: CLIENTHELLO')
            self.handleClienthello()
        # Data
        elif T == 3:
            print(f'T: {T}, Header: DATA')
            self.handleData(T)

    def handleServerhello(self, T):
        L = self.s.recv(1)            # Recv 1 byte til længden, L
        L = int.from_bytes(L)
        # print(f'L: {L, type(L)}')

        g = self.s.recv(16)        # Recv 16 byte til tal g
        g = int.from_bytes(g)
        # print(f'g: {g, type(g)}')

        p = self.s.recv(16)        # Recv 16 byte til tal g
        p = int.from_bytes(p)
        # print(f'p: {p, type(p)}')

        A = self.s.recv(16)
        A = int.from_bytes(A)

        FCS = self.s.recv(2)          # Recv 2 bytes til Frame Check Sequence (Altid 2 bytes)
        FCS_int = int.from_bytes(FCS)

        data_byte_array = T.to_bytes(1) + L.to_bytes(1) + g.to_bytes(16) + p.to_bytes(16) + A.to_bytes(16)
        calculated_checksum = self.calculateFCS(data_byte_array)
        
        self.checkFCS(calculated_checksum, FCS_int)

        # Udregner B, ved at vælge en filfældig b-værdi.
        b = random.getrandbits((8 * 16) - 2)                             # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.
        # print(f'b: {b}')
        B = pow(g, b, p)
        self.K = pow(A, b, p)
        # print(f'B: {B}')

        self.sendClienthello(B)

    def handleData(self, T):        
        # print(f'    self.X: {self.X}')
        L_bytes = self.s.recv(1)
        L_int = int.from_bytes(L_bytes)                # Længden i bytes. Ex L_int = 18 => 18 bytes.

        payload = self.s.recv(L_int)

        # [print(hex(byte)+" ") for byte in X]

        result = self.encryptDecrypt(payload)
        

        # Bruger serverens sendte data til at udregne FCS osv.
        firstline_bytes = result[:-2]                         # Board state
        data = T.to_bytes(1) + L_bytes + firstline_bytes          # Skal bruges til at udregne FCS.
        recieved_FCS = int.from_bytes(result[-2:])          # Recieved FCS som en integer


        firstline = str(firstline_bytes)

        # print(f'firstline_bytes: {firstline_bytes}, type: {firstline_bytes}')
        # print(f'firstline: {firstline}, type: {type(firstline)}')
        
        serverstring = firstline[12:-2]        # Laver en string, hvor jeg slicer fra 12 og fjerne de sidste to elementer
        print(f'serverstring: {serverstring}')
        
        own_FCS = self.calculateFCS(data)
        self.checkFCS(own_FCS, recieved_FCS)


        # Vælger hvad der skal ske alt efter hvad serverstring er:
        if "ILLEGAL" in serverstring:
            pass

        elif "BOARD IS" in serverstring:
            self.boardstate = serverstring

        if "YOUR TURN" in serverstring:
            self.playerTurn()
            pass

        elif "WINS" in serverstring:
            self.isRunning = False
            self.s.close()

        # self.s.send(data)
        
        # self.isRunning = False
        # self.s.close()

    def sendClienthello(self, B):
        # print(f'Printer B fra sendClientHello: {B}')
        # Generate CLIENTHELLO message

        T = 2                    # Type 2 => CLIENTHELLO.
        T = T.to_bytes(1)        # Skal være 1 byte i længde.

        B = B.to_bytes(16)      # Skal være 16 byte i længde.

        L = len(B) + 2
        L = L.to_bytes(1)

        # - Calculate FCS trailer
        data = T + L + B
        # print(f'T: {T} L: {L}, B: {B}')         # Printer data, byte array uden FCS

        FCS = self.calculateFCS(data)                  # Denne metode returner en integer. Skal laves til et byte-array, for at kunne transmitteres
        FCS_bytes = FCS.to_bytes(2)                         
        # print(f'Calculated checksum in bytes: {FCS_bytes}')
        
        clienthello = data + FCS_bytes
        # test_msg = "Hello, this is a test"
        # self.s.send(test_msg.encode('utf-8'))
        self.s.send(clienthello)
        # print(f'Clienthello_array: {clienthello}')

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
                print('FCS is valid:')
                print(f'    calculated_checksum: {calculated_FCS}\n    FCS: {recieved_FCS}')
                return True
        else:
                self.isRunning == False
                print("GAME CRASHED DUE TO NETWORK! TRY AGAIN!")
                self.s.close()   
                return False

    def encryptDecrypt(self, data_payload):
        if not hasattr(self, 'X') or self.X == None:          # Hvis ikke klassen har self.X eller hvis self.X er None
            print(f'Initializing X the first time...')
            self.X = self.K.to_bytes(16)[13:16]                 # Skal kun initlialiseres 1 gang !!!!!!!! Tager de 24 mindst betydende bits
            self.X = int.from_bytes(self.X)                     # Skal være en integer for at kunne fungere i loopet

        a = 125      # Fixed værdi
        c = 1        # Fixed værdi
        
        result = bytearray(len(data_payload))
        for i in range(len(data_payload)):
            self.X = (a * self.X + c) % (2**24)
            keybyte = self.X.to_bytes(3)[1]            # Laver self.X til 3 bytes, og udvælger den midterste
            result[i] = data_payload[i] ^ keybyte

        return result

    def playerTurn(self, ):
        print(f'Skriv dit træk:')
        playerinput = f'{input()}\r\n'
        
        chosen_move = bytearray()      # Tomt bytearray
        chosen_move.extend(map(ord, playerinput))      # Fundet på stackoverflow: https://stackoverflow.com/questions/11624190/how-to-convert-string-to-byte-array-in-python
        # playerinput.encode('utf-8')
        print(playerinput, chosen_move)

        T = 3                         # Typen er af data
        T_bytes = T.to_bytes(1)       #
        L = len(playerinput) + 2
        L_bytes = L.to_bytes(1)

        data = T_bytes + L_bytes + chosen_move
        FCS = self.calculateFCS(data)
        FCS_bytes = FCS.to_bytes(2)

        til_krypt = chosen_move + FCS_bytes

        encrypted_payload = self.encryptDecrypt(til_krypt)

        til_send = T_bytes + L_bytes + encrypted_payload

        # data_sent = data + FCS_bytes
        self.s.send(til_send)
        
        # self.isRunning = False
        # self.s.close()

client = MainClass()
# client.recieveType()
# client.s.close()