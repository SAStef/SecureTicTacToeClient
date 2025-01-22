import socket as sock

def serverInit():
    s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    s.connect(("34302.cyberteknologi.dk", 1061))    
        
servercontent = serverInit()



