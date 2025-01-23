import socket as sock
import random
import traceback             # Debugging
            
class MainClass():
    def __init__(self):
        try:
            self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)       # Vælger TCP
            self.s.connect(("34302.cyberteknologi.dk", 1063))          # Vælger host og port
            self.isRunning = True
            print("connected")

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
            self.handleServerhello(T)
        # Clienthello
        elif T == 2:
            self.handleClienthello()
        # Data
        elif T == 3:
            self.handleData(T)

    def handleServerhello(self, T):
        print(r"""
           _   _      _             _             _ 
          | | (_)    | |           | |           | |
          | |_ _  ___| |_ __ _  ___| |_ ___   ___| |
          | __| |/ __| __/ _` |/ __| __/ _ \ / _ \ |
          | |_| | (__| || (_| | (__| || (_) |  __/_|
           \__|_|\___|\__\__,_|\___|\__\___/ \___(_)
            """)
        
        
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
        b = random.getrandbits((8 * 16) - 2)    # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.

        B = pow(g, b, p)
        self.K = pow(A, b, p) # K værdi til self så den kan gives globalt

        self.sendClienthello(B)

    def handleData(self, T):        
        # print(f'    self.X: {self.X}')
        L_bytes = self.s.recv(1)
        L_int = int.from_bytes(L_bytes)                # Længden i bytes. Ex L_int = 18 => 18 bytes.

        payload = self.s.recv(L_int)

        result = self.encryptDecrypt(payload)

        # Bruger serverens sendte data til at udregne FCS osv.
        firstline_bytes = result[:-2]                         # Board state
        data = T.to_bytes(1) + L_bytes + firstline_bytes          # Skal bruges til at udregne FCS.
        recieved_FCS = int.from_bytes(result[-2:])          # Recieved FCS som en integer

        firstline = str(firstline_bytes)

        # print(f'firstline_bytes: {firstline_bytes}, type: {firstline_bytes}')
        # print(f'firstline: {firstline}, type: {type(firstline)}')
        
        serverstring = firstline[12:-2]        # Laver en string, hvor jeg slicer fra 12 og fjerner de sidste to elementer
        print(f'{serverstring}')
        
        own_FCS = self.calculateFCS(data)
        self.checkFCS(own_FCS, recieved_FCS)

        # Vælger hvad der skal ske alt efter hvad serverstring er:
        if "ILLEGAL" in serverstring:
            print("illegal move!!")
            pass

        elif "BOARD IS" in serverstring:
            self.print_board(serverstring.replace("BOARD IS ",""))
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
            self.s.send(player_move)
            

        elif "WINS" in serverstring:
            print("GGWP!")
            self.isRunning = False
            self.s.close()


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
    
    def print_board(self, board):
        boardStateParsed = board.replace(".", " ")
        print(f"""
                    1   |   2   |   3   
                        |       |
                    {boardStateParsed[-9]}   |   {boardStateParsed[-8]}   |   {boardStateParsed[-7]}   
                        |       |
                ────────┼───────┼───────
                    4   |   5   |   6   
                        |       |
                    {boardStateParsed[-6]}   |   {boardStateParsed[-5]}   |   {boardStateParsed[-4]}   
                        |       |
                ────────┼───────┼───────
                    7   |   8   |   9   
                        |       |
                    {boardStateParsed[-3]}   |   {boardStateParsed[-2]}   |   {boardStateParsed[-1]}   
                        |       |
        """)


client = MainClass()
