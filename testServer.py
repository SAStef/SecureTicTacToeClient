import socket as sock

def serverInit():
    s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    s.connect(("34302.cyberteknologi.dk", 1061))
    print(s)
    file = s.makefile('rb')
    
    
    firstLine = file.readline().strip()
    
    print(firstLine)
    
    while 1:
        
        nextLines = file.readline().strip()
        
        if nextLines != b'':
            print(nextLines.decode())
        
serverInit()

