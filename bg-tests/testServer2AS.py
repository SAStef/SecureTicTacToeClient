import socket as sock
import random

class MainClass():
    def __init__(self):
        self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)  
        try:
            self.s.connect(("34302.cyberteknologi.dk", 1063))          # Vælger host og port        

            self.isRunning = True
            self.counter = 0
            
            self.recieveType()
            while self.isRunning:
                self.recieveType()

        except Exception as e:
            print(f'Fejlen i __init__: {e}')
        
    def recieveType(self):
        T_bytes = self.s.recv(1)            # Recv 1 byte til Typen
        T = int.from_bytes(T_bytes)

        # Serverhello
        if T == 1:                 
            self.handleServerhello(T)
        # Clienthello
        elif T == 2:
            self.handleClienthello()
            print(f'T: {T}, Type: {type(T)}')
        # Data
        elif T == 3:
            self.handleData()
            print(f'T: {T}, Type: {type(T)}')

    def handleServerhello(self, T):
        L_bytes = self.s.recv(1)            # Recv 1 byte til længden, L
        L = int.from_bytes(L_bytes)
        # print(f'L: {L, type(L)}')

        g_bytes = self.s.recv(16)        # Recv 16 byte til tal g
        g = int.from_bytes(g_bytes)
        # print(f'g: {g, type(g)}')
        print("________")
        print(g)

        p_bytes = self.s.recv(16)        # Recv 16 byte til tal g
        p = int.from_bytes(p_bytes)
        # print(f'p: {p, type(p)}')
        print(p)

        A_bytes = self.s.recv(16)
        A = int.from_bytes(A_bytes)
        print(A)

        FCS_bytes = self.s.recv(2)          # Recv 2 bytes til Frame Check Sequence (Altid 2 bytes)
        FCS = int.from_bytes(FCS_bytes)

        data_byte_array = T.to_bytes(1) + L.to_bytes(1) + g.to_bytes(16) + p.to_bytes(16) + A.to_bytes(16)
        calculated_checksum = self.calculateFCS(data_byte_array)
        
        self.checkFCS(calculated_checksum, FCS)

        # Udregner B, ved at vælge en filfældig b-værdi.
        b = random.getrandbits((8 * 16) - 2)                             # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.
        B = pow(g, b, p)
        K = pow(g, A*b, p)
        
        print(f"K VÆRDIEN ER::::______  _ __ _ {K}")
        
        print(f'B: {B}')
        self.sendClienthello(B)
        
        return K

    def handleClienthello(self, ):
        print(f'Serveren må ikke sende en clienthello. Lukker forbindelsen...')
        self.isRunning = False
        self.s.close()

    def handleData(self, ):
        L_bytes = self.s.recv(1)
        L = int.from_bytes(L_bytes)
        print("aflæser data")
        print("header (total length) sendt fra server:", L)
        payload = self.s.recv(L - 2)
        print(payload.decode('utf-8'))
        
        print("checksum fra server:", int.from_bytes(self.s.recv(2)))
        


    def sendClienthello(self, B):
        # print(f'Printer B fra sendClientHello: {B}')
        # Generate CLIENTHELLO message

        T_bytes = 2                    # Type 2 => CLIENTHELLO.
        T = T_bytes.to_bytes(1)        # Skal være 1 byte i længde.

        B_bytes = B.to_bytes(16)      # Skal være 16 byte i længde.

        L_bytes = len(B_bytes) + 2
        L = L_bytes.to_bytes(1)

        # - Calculate FCS trailer
        data = T + L + B_bytes

        FCS = self.calculateFCS(data)                  # Denne metode returner en integer. Skal laves til et byte-array, for at kunne transmitteres
        FCS_bytes = FCS.to_bytes(2)                         
        
        clienthello = data + FCS_bytes

        self.s.send(clienthello)

    def calculateFCS(self, data):
            sum1 = 0
            sum2 = 0
            for i in range(len(data)):
                sum1 = (sum1 + data[i]) % 255
                sum2 = (sum2 + sum1) % 255
            calculated_checksum = (sum2 << 8) + sum1
            
            return calculated_checksum
            
    def checkFCS(self, calculated_FCS, recieved_FCS):
        if calculated_FCS == recieved_FCS:
                print('FCS is valid')
                return True
        else:
                self.isRunning == False
                print("GAME CRASHED DUE TO NETWORK PROBLEMS! TRY AGAIN!")
                self.s.close()   
                return False

client = MainClass()
