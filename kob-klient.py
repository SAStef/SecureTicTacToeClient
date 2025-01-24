"""
Kryds og bolle opgave
gruppemedlemmer: 
  Andreas Stefan Bjørn Bundgaard
  David Aaskov Tofft
  Victor Møgelvang Wandahl
"""

# ----------- Importerer biblioteker -----------
import socket as s
from os import system, name  # Skal bruges til at clear screen.

# -------- Definerer socket og connect --------
host = "34302.cyberteknologi.dk"
port = 1060
sock = s.socket(s.AF_INET, s.SOCK_STREAM)  # Definerer IPv4 TCP
sock.connect((host, port))  # Forbind til host og port via sock

# --- Lav fil læser og fil skriver ---
fileReader = sock.makefile("r")
fileWriter = sock.makefile("w")


# ---------- Funktioner ----------
def clear():
    """
    Denne funkion rydder terminalen
    tyv stjålet fra: https://www.geeksforgeeks.org/clear-screen-python/
    """

    # Hvis terminalen er Windows
    if name == "nt":
        _ = system("cls")

    # Hvis terminalen er Mac eller Linux (here, os.name is 'posix')
    else:
        _ = system("clear")


def printBoardState(boardString: str, player: str):
    """
    Denne funktion printer boardet ud i et brugervenligt format.
    Den kræver en board for at fungere
    """

    def printLine():
        """
        Laver linjen mellem cellerne
        """
        print("+--------" * størelsePåBoard + "+")

    størelsePåBoard = 3

    Xlist = ["#   #", " # # ", "  #  ", " # # ", "#   #"]
    Olist = [" ### ", "#   #", "#   #", "#   #", " ### "]
    emptyList = ["     ", "     ", "     ", "     ", "     "]
    # printer spillerens tegn
    print(player)

    for lines in range(størelsePåBoard):
        printLine()

        for cellLinje in range(5):

            for cellKolonne in range(størelsePåBoard):

                print(
                    "|", end=""
                )  # Vi printer den venstre væg i en celle på den nuværende linje
                # Vi tilføjer end="", fordi vores print statements ikke skal lave en ny linje.

                # hvis førstelinje i en celle så skriv tallet i venstre hjørne
                if cellLinje == 0:
                    print(f"{1+lines*3+cellKolonne} ", end="")
                else:
                    print("  ", end="")

                # nu skriver vi en linje af den relavnate karakter ind i ccellen

                if (
                    boardString[lines * 3 + cellKolonne] == "X"
                ):  # hvis den nuværende celle indholder X
                    print(Xlist[cellLinje], end="")

                elif (
                    boardString[lines * 3 + cellKolonne] == "O"
                ):  # hvis den nuværende celle indholder O
                    print(Olist[cellLinje], end="")

                else:  # hvis den nuværende celle indholder .
                    print(emptyList[cellLinje], end="")

                # ekstra mellemrum til højre i hver celle
                print(" ", end="")

            # lave den højre væg
            print("|")

    # lav den nederste linje
    printLine()


# ---- Start Serverens Protokol ----
startMessage = (
    fileReader.readline().strip()
)  # Læser den første linje og fjerner newline fra slutningen af strengen
print(startMessage)
playerIs = "Player is: " + str(startMessage[-1])

# ----------- Primære løkke ----------
gameActive = True
while gameActive:
    # Serveren returner 2 linjer
    linje1 = (
        fileReader.readline()
    )  # Definerer den første linje som vi modtager fra serveren.
    linje2 = fileReader.readline()  # Samme, men næste linje

    # Giver "illegal move" eller "illegal input" hvis spilleren giver et tegn serveren ikke kan forstå
    if "ILLEGAL" in linje1:  # Undersøger om ILLEGAL er i serverbeskeden
        printBoardState(
            newestBoard, playerIs
        )  # Newestboard er den nyese board state som serveren returnerer. Den Defineres på linje 129.
        print(linje1.strip())

    # Tager det nye board serveren giver, og sætter det op på en visuel format
    elif "BOARD IS" in linje1:
        newestBoard = linje1.strip()[
            -9:
        ]  # Er spillets board state, hvor strip() fjerne eventuelle \n, og giver os de 9 sidste elementer i vores string.
        printBoardState(newestBoard, playerIs)

    # Når serveren sender "YOUR TURN" venter klienten på indput fra spilleren som den
    if "YOUR TURN" in linje2:
        fileWriter.write(f"{input()}\r\n")  # Brugerens input gemmes i vores filewriter
        fileWriter.flush()  # Fjerner alt indhold i filen efter vi har sendt linjen
        clear()  # Rydder terminalen

    # Afslutter spillet når serveren siger hvem vinder
    elif "WINS" in linje2:
        print(linje2)
        gameActive = False  # Sætter vores gameActive til False, som ender løkken.

print("programmet lukkes")
sock.close()
