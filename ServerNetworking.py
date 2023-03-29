import socket
import threading
from datetime import datetime
import json


class Server:
    """
    Use this class to set up an server.
    """
    serverActive = False

    # connectedClients model
    # {
    #   clientIpAddress: {
    #       "connection": connObj
    #   }
    # }
    connectedClients = {}

    encoding = "utf-8"
    disconnectMessage = "!DISCONNECT"

    __recvListener = []

    def __init__(self, host: str = socket.gethostbyname(socket.gethostname()), port: int = 5000, maxClients: int = 1, standartBufferSize: int = 64, messageTerminatorChar: str = "|") -> None:
        if not len(messageTerminatorChar) == 1:
            raise Exception(
                "messageTerminatorChar should be one char that dont ever exists in your sended messages!")

        self.address = (host, port)
        self.maxClients = maxClients
        self.standartBufferSize = standartBufferSize

        self.messageTerminatorChar = messageTerminatorChar

    def start(self) -> None:
        """
        Start the server instance so that clients can join.
        """
        self.__logMessage("Server is starting...")

        # create the socket and make it ready to connect to
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind(self.address)
        self.serverSocket.listen(self.maxClients)

        self.serverActive = True

        self.__logMessage(f"Server is listening on {self.address}")
        threading.Thread(target=self.__handleNewConnections).start()

    def stop(self):
        """
        Stop the server and disconnect all clients.
        """
        self.send(self.disconnectMessage)
        self.serverActive = False
        self.serverSocket.close()

    def send(self, message: dict = {}, clients: list = []):
        clientsToSend = []
        if clients == []:
            clientsToSend = [address for address in self.connectedClients]
        else:
            clientsToSend = [
                address for address in self.connectedClients if address in clients]

        if type(message) == dict:
            message = json.dumps(message)

        else:
            message = str(message)

        message = f"{message}{self.messageTerminatorChar}"
        msg = message.encode(self.encoding)
        msgLen = len(msg)
        sendLen = f"{str(msgLen)}{self.messageTerminatorChar}".encode(
            self.encoding)
        sendLen += b' ' * (self.standartBufferSize - len(sendLen))

        clientAdresses = []
        for address in clientsToSend:
            self.connectedClients[address]["connection"].send(sendLen)
            self.connectedClients[address]["connection"].send(msg)
            clientAdresses.append(address)

        self.__logMessage(f"Send message to {clientAdresses}")

    def getAllClients(self) -> list:
        return [address for address in self.connectedClients]

    def __handleNewConnections(self):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __handleNewConnections wait for an incoming connection
        """
        while self.serverActive:
            try:
                conn, address = self.serverSocket.accept()
            except:
                continue

            threading.Thread(target=self.__handleClient,
                             args=(conn, address)).start()

    def __handleClient(self, connection: socket.socket, address):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __handleClient wait for incoming message from the client
        """
        self.connectedClients[address[0]] = {
            "address": address, "connection": connection}

        self.__logMessage(f"Got connection from {address}")
        self.__logMessage(f"Active connections {len(self.connectedClients)}")

        while address[0] in self.connectedClients:
            try:
                msgLen = ""
                while not self.messageTerminatorChar in msgLen:
                    msgLen += connection.recv(
                        self.standartBufferSize).decode(self.encoding)

                msgLen = msgLen.replace(self.messageTerminatorChar, "")
            except:
                continue

            if msgLen == "":
                continue

            try:
                msgLen = int(msgLen)
            except:
                self.__logMessage(
                    f"Invalid message lenght from {address[0]}!\n{msgLen}")
                continue

            try:
                msg = ""
                while not self.messageTerminatorChar in msg:
                    msg += connection.recv(msgLen).decode(self.encoding)

                msg = msg.replace(self.messageTerminatorChar, "")
            except:
                continue

            self.__logMessage(f"Got message from {address[0]}!")

            if msg == self.disconnectMessage:
                self.connectedClients.pop(address[0])
                continue

            try:
                msg = json.loads(msg)
            except:
                self.__logMessage(
                    f"Message from {address[0]} could not be handled!\n{msg}")
                continue

            self.__fireRecv(msg)

        connection.close()
        self.__logMessage(f"{address[0]} disconnected from the server!")
        self.__logMessage(f"Active connections {len(self.connectedClients)}")

    #
    # decorators
    #
    def onRecv(self, func):
        """
        This decorator returns every received message.\n
        @Server.onRecv\n
        def onRecv(message):
            # code
        """
        if func in self.__recvListener:
            return

        self.__recvListener.append(func)

    def __fireRecv(self, msg: dict):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __fireRecv returns the msg
        """
        for func in self.__recvListener:
            threading.Thread(target=func, args=[msg]).start()

    def __logMessage(self, msg):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __debugMessage print a debug message.
        """
        now = datetime.now()
        currTime = now.strftime("%Y-%m-%d, %H:%M:%S")
        print(f"[{currTime}] {msg}")
