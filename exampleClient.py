from ClientNetworking import Client
from socket import gethostbyname, gethostname
from time import time

# gethostbyname(gethostname()) gets the current address
client = Client(gethostbyname(gethostname()))

gotMsg = False


@client.onRecv
def onRecv(msg):
    global gotMsg
    gotMsg = True
    print(msg)


@client.onConnect
def onConnect():
    print("Connected!")


@client.onDisconnect
def onDisconnect():
    print("Disconnected!")


client.connect()

while client.connected:
    while not gotMsg:
        pass

    startTime = time()
    while time() - startTime < 3:
        pass

    playerPos = {"player2": (360, 100)}
    client.send(playerPos)

    startTime = time()
    while time() - startTime < 3:
        pass

    client.disconnect()
