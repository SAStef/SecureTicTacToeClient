import socket as sock

def serverInit():
    s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)  
    s.connect(("34302.cyberteknologi.dk", 1061))     

    
    T = s.recv(1)
    print(f'T: {T}, type: {type(T)}')
    
    
    L = s.recv(1)
    print(f'L: {L}, type: {type(L)}')

    
    num1 = s.recv(16)
    print(f'num1: {num1}, type: {type(num1)}')

    
    num2 = s.recv(16)
    print(f'num2: {num2}, type: {type(num2)}')

    
    FCS = s.recv(2)
    print(f'FCS: {FCS}, Hex: {FCS.hex()}, type: {type(FCS)}')

    
    data = T + L + num1 + num2

    
    sum1 = 0
    sum2 = 0
    N = len(data)

    for i in range(N):
        sum1 = (sum1 + data[i]) % 255
        sum2 = (sum2 + sum1) % 255

    calculated_checksum = (sum2 << 8) | sum1  
    print(f'Calculated Checksum: {calculated_checksum}, Hex: {calculated_checksum:04x}')

    
    FCS_int = int.from_bytes(FCS, byteorder='big')

    
    if calculated_checksum == FCS_int:
        print("Checksum is valid!")
    else:
        print("Checksum is INVALID!")

    s.close()

    return {
        "T": T,
        "L": L,
        "num1": num1,
        "num2": num2,
        "FCS": FCS,
        "calculated_checksum": calculated_checksum
    }

server_content = serverInit()
