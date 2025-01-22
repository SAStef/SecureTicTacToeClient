import socket as sock
import random

class MainClass():
    def __init__(self):
        self.s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)       # Vælger TCP
        self.s.connect(("34302.cyberteknologi.dk", 1063))          # Vælger host og port        
        
        self.isRunning = True
        
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
        elif T == 3:
            pass

    def handleServerhello(self, T):
        L_bytes = self.s.recv(1)            # Recv 1 byte til længden, L
        L = int.from_bytes(L_bytes)
        # print(f'L: {L, type(L)}')

        g_bytes = self.s.recv(16)        # Recv 16 byte til tal g
        g = int.from_bytes(g_bytes)
        # print(f'g: {g, type(g)}')

        p_bytes = self.s.recv(16)        # Recv 16 byte til tal g
        p = int.from_bytes(p_bytes)
        # print(f'p: {p, type(p)}')

        A_bytes = self.s.recv(16)
        A = int.from_bytes(A_bytes)

        FCS_bytes = self.s.recv(2)          # Recv 2 bytes til Frame Check Sequence (Altid 2 bytes)
        FCS = int.from_bytes(FCS_bytes)

        data_byte_array = T.to_bytes(1) + L.to_bytes(1) + g.to_bytes(16) + p.to_bytes(16) + A.to_bytes(16)
        calculated_checksum = self.calculateFCS(data_byte_array)
        
        self.checkFCS(calculated_checksum, FCS)

        # Udregner B, ved at vælge en filfældig b-værdi.
        b = random.getrandbits((8 * 16) - 2)                             # Denne funktion angiver nogle tilfældige bits. Derfor (8 * 16)-2, da det tilfældige tal skal være 2 lavere.
        # print(f'b: {b}')
        B_bytes = pow(g, b, p)
        # print(f'B: {B}')
        self.sendClienthello(B_bytes)

    def handleClienthello(self, ):
        pass

    def handleData(self, ):
        pass

    def sendClienthello(self, B_bytes):
        # print(f'Printer B fra sendClientHello: {B}')
        # Generate CLIENTHELLO message

        T_bytes = 2                    # Type 2 => CLIENTHELLO.
        T = T_bytes.to_bytes(1)        # Skal være 1 byte i længde.

        B = B_bytes.to_bytes(16)      # Skal være 16 byte i længde.

        L_bytes = len(B) + 2
        L = L_bytes.to_bytes(1)

        # - Calculate FCS trailer
        data = T + L + B
        print(f'T: {T} L: {L}, B: {B}')         # Printer data, byte array uden FCS

        FCS = self.calculateFCS(data)                  # Denne metode returner en integer. Skal laves til et byte-array, for at kunne transmitteres
        FCS_bytes = FCS.to_bytes(2)                         
        print(f'Calculated checksum in bytes: {FCS_bytes}')
        
        clienthello = data + FCS_bytes
        print(f'Clienthello_array: {clienthello}')

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
                print('FCS is valid:')
                print(f'    calculated_checksum: {calculated_FCS}\n    FCS: {recieved_FCS}')
                return True
        else:
                self.isRunning == False
                print("GAME CRASHED DUE TO NETWORK! TRY AGAIN!")
                self.s.close()   
                return False

client = MainClass()
client.recieveType()
client.s.close()
