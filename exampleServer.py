from ServerNetworking import Server
from time import time

server = Server()


gotMsg = False


@server.onRecv
def onRecv(msg, address):
    global gotMsg
    gotMsg = True
    print(msg)


@server.onConnect
def onConnect(address):
    print(f"{address} has connected!")


@server.onDisconnect
def onDisconnect(address):
    print(f"{address} disconnected!")


server.start()

while server.serverActive:
    while len(server.getAllClients()) == 0:
        pass

    startTime = time()
    while time() - startTime < 1:
        pass

    playerPos = {"player": {"player1": (500, 30), "player2": (352, 103)}}
    # you can also send the data to selected client only server.send(playerPos, listOfAddresses)
    server.send(playerPos)

    while not gotMsg:
        pass

    while not len(server.getAllClients()) == 0:
        pass

    server.stop()
