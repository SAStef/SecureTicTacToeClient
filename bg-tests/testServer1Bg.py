import socket as sock


def serverInit():
    s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)  # Vælger TCP
    s.connect(("34302.cyberteknologi.dk", 1061))  # Vælger host og port

    T = s.recv(1)  # Recv 1 byte til Typen
    T = int.from_bytes(T)
    print(f"T: {T, type(T)}")

    L = s.recv(1)  # Recv 1 byte til længden
    L = int.from_bytes(L)
    print(f"L: {L, type(L)}")

    num1 = s.recv(16)  # Recv 16 byte til tal 1
    num1 = int.from_bytes(num1)
    print(f"num1: {num1, type(num1)}")

    num2 = s.recv(16)  # Recv 16 byte til tal 2
    num2 = int.from_bytes(num2)
    print(f"num2: {num2, type(num2)}")

    FCS = s.recv(2)  # Recv 2 bytes til Frame Check Sequence (Altid 2 bytes)
    FCS = int.from_bytes(FCS)
    print(f"FCS: {FCS, type(FCS)},\nFCS: {hex(FCS)}, type {type(hex(FCS))}")


def placeholder():
    pass

    # file = s.makefile('rb')
    # firstline = file.readline().strip()                # .strip() fjerner escape-chars
    # firstline_int = int.from_bytes(firstline)
    # firstline_byte_string = bin(firstline_int)[2:]
    # print(f'{firstline}\n')
    # print(f'{firstline_byte_string}\n')                       # Printer serverens byte-array som en string
    # print(firstline_int.bit_length())                  # Printer længden af serverens svar


servercontent = serverInit()
