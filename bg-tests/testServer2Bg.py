import socket as sock
import random

class MainClass():
    def __init__(self):
        self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)       # Vælger TCP
        self.s.connect(("34302.cyberteknologi.dk", 1062))          # Vælger host og port        
        
        self.checkSumValid = True
        
    def recieveType(self, ):
        T = self.s.recv(1)            # Recv 1 byte til Typen
        T = int.from_bytes(T)

        # Serverhello
        if T == 1:                 
            self.handleServerhello(T)
        # Clienthello
        elif T == 2:
            pass
        # Data
        elif T== 3:
            pass

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
        FCSr = int.from_bytes(FCS)

        data_byte_array = T.to_bytes(1) + L.to_bytes(1) + g.to_bytes(16) + p.to_bytes(16) + A.to_bytes(16)
        calculated_checksum = self.calculateFCS(data_byte_array)
        
        self.checkFCS(calculated_checksum, FCSr)

        # Udregner B, ved at vælge en filfældig b-værdi.
        b = random.getrandbits((8 * 16) - 2)                             # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.
        # print(f'b: {b}')
        B = pow(g, b, p)
        # print(f'B: {B}')
        self.sendClienthello(B)

    def handleClienthello(self, ):
        pass

    def handleData(self, ):
        pass

    def sendClienthello(self, B):
        # print(f'Printer B fra sendClientHello: {B}')
        # Generate CLIENTHELLO message

        T = 2                    # Type 2 => CLIENTHELLO.
        T = T.to_bytes(1)        # Skal være 1 byte i længde.

        b = B.to_bytes(16)      # Skal være 16 byte i længde.

        L = len(b) + 2
        L = L.to_bytes(1)

        print(f'L: {L}, B: {b}, L: {L}')
        # - Calculate FCS trailer
        clienthello = T + L + b
        print(f'CLIENTHELLO_ARRAY: {clienthello}')
        FCS = self.calculateFCS(clienthello)
        FCSr = FCS.to_bytes(2)
        print(f'Calculated checksum: {FCSr}')

    def calculateFCS(self, data):
            sum1 = 0
            sum2 = 0
            for i in range(len(data)):
                sum1 = (sum1 + data[i]) % 255
                sum2 = (sum2 + sum1) % 255
            calculated_checksum = (sum2 << 8) + sum1
            
            return calculated_checksum
            
    def checkFCS(self, calculated_checksum, FCS):
        if calculated_checksum == FCS:
                print('FCS is valid:')
                print(f'own_FCS: {calculated_checksum}\nFCS: {FCS}')
        else:
                self.checkSumValid == False
                print("GAME CRASHED DUE TO NETWORK! TRY AGAIN!")
                self.s.close()   
        
        


    def isFCSValid(self, ):
        pass

client = MainClass()
client.recieveType()
client.s.close()