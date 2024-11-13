import socket
import threading
from datetime import datetime
import json
from time import time


class Server:
    """
    The server class.
    """
    serverActive = False

    # connectedClients model
    # {
    #   clientIpAddress: {
    #       "address": address:(ipAddress, port),
    #       "connection": connObj
    #   }
    # }
    connectedClients = {}

    # standart Properties
    encoding = "utf-8"
    disconnectMessage = "!DISCONNECT"

    # all Listeners
    __recvListener = []
    __onConnectListener = []
    __onDisconnectListener = []

    def __init__(self, host: str = socket.gethostbyname(socket.gethostname()), port: int = 5000, maxClients: int = 1, standartBufferSize: int = 64, messageTerminatorChar: str = "|"):
        # the messageTerminatorChar has to be just one char long
        if not len(messageTerminatorChar) == 1:
            raise Exception(
                "messageTerminatorChar should be one char that dont ever exists in your messages that you want to send!")

        self.address = (host, port)
        self.maxClients = maxClients
        self.standartBufferSize = standartBufferSize

        self.messageTerminatorChar = messageTerminatorChar

    def start(self) -> bool:
        """
        Start the server instance so that clients can join.

        Return true if server started successfully.
        """
        self.__logMessage("Server is starting...")

        # create the socket and make it ready to connect to
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.serverSocket.bind(self.address)
            self.serverSocket.listen(self.maxClients)

        except:
            return False

        self.serverActive = True

        threading.Thread(target=self.__handleNewConnections).start()
        self.__logMessage(f"Server is listening on {self.address}")
        return True

    def stop(self):
        """
        Stop the server and disconnect all clients.
        """
        # send the diconnect message and close connection
        self.send(self.disconnectMessage)
        self.serverActive = False

        t = time()
        while time() - t < 3:
            pass

        self.serverSocket.close()
        self.__logMessage("Server is stopped!")

    def send(self, message: dict = {}, clients: list = []):
        """
        Send a dict to the clients.

        message should be a dict.

        clients is a list of addresses to send the data. When empty then send to all clients.
        """
        if len(self.connectedClients) == 0:
            return

        # get the clients the message should be send to
        clientsToSend = []
        connectedClients = dict(self.connectedClients)
        if clients == []:
            clientsToSend = [address for address in connectedClients]
        else:
            clientsToSend = [
                address for address in connectedClients if address in clients]

        # when message type is a dict then convert to json string when it is str then it is the diconnect message
        if type(message) == dict:
            message = json.dumps(message)

        else:
            message = str(message)

        # append the messageTerminatorChar to the end
        message = f"{message}{self.messageTerminatorChar}"
        # calculate the send lenght and convert it to binary
        msg = message.encode(self.encoding)
        msgLen = len(msg)
        # append the messageTerminatorChar to the end of the message
        sendLen = f"{str(msgLen)}{self.messageTerminatorChar}".encode(
            self.encoding)
        sendLen += b' ' * (self.standartBufferSize - len(sendLen))

        # for each address that should get the message send the lenght of the message and then the message
        clientAdresses = []
        for address in clientsToSend:
            self.connectedClients[address]["connection"].send(sendLen)
            self.connectedClients[address]["connection"].send(msg)
            clientAdresses.append(address)

        self.__logMessage(f"Sended message to {clientAdresses}")

    def getAllClients(self) -> list:
        """
        Get all clients currently connected.
        """
        # copy the dict so that no error occures when writing something while iterating
        connectedClients = dict(self.connectedClients)
        # list comprehension to return all client addresses
        return [address for address in connectedClients]

    def __handleNewConnections(self):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __handleNewConnections wait for an incoming connection.
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
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __handleClient handle the client.
        """
        # add the client to the list
        self.connectedClients[address[0]] = {
            "address": address, "connection": connection}

        self.__logMessage(f"Got connection from {address}")
        self.__logMessage(f"Active connections {len(self.connectedClients)}")
        self.__fireOnConnect(address)

        while address[0] in self.connectedClients:
            # this is in try except because if client diconnects then it would throw an error but like this it obviously doesnt
            try:
                # receive the message lenght while the messageTerminatorChar is not present
                msgLen = ""
                while not self.messageTerminatorChar in msgLen:
                    msgLen += connection.recv(
                        self.standartBufferSize).decode(self.encoding)

                # remove the messageTerminatorChar
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

            # this is in try except because if client diconnects then it would throw an error but like this it obviously doesnt
            try:
                # receive the message lenght while the messageTerminatorChar is not present
                msg = ""
                while not self.messageTerminatorChar in msg:
                    msg += connection.recv(msgLen).decode(self.encoding)

                # remove the messageTerminatorChar
                msg = msg.replace(self.messageTerminatorChar, "")
            except:
                continue

            self.__logMessage(f"Got message from {address[0]}!")

            # check if message is an system message
            if msg == self.disconnectMessage:
                self.connectedClients.pop(address[0])
                continue

            # load the message to a dict
            try:
                msg = json.loads(msg)
            except:
                self.__logMessage(
                    f"Message from {address[0]} could not be handled!\n{msg}")
                continue

            self.__fireOnRecv(msg, address)

        connection.close()
        self.__fireOnDisconnect(address)
        self.__logMessage(f"{address[0]} disconnected from the server!")
        self.__logMessage(f"Active connections {len(self.connectedClients)}")

    #
    # decorators
    #
    def onRecv(self, func):
        """
        This decorator returns every received message.

        @Server.onRecv

        def onRecv(message: dict, address: tuple):
            # code
            """
        if func in self.__recvListener:
            return

        self.__recvListener.append(func)

    def __fireOnRecv(self, msg: dict, address: tuple | None = None):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __fireRecv calls every function that used the onRecv decorator and gives the msg as an argument.
        """
        for func in self.__recvListener:
            threading.Thread(target=func, args=[msg, address]).start()

    def onConnect(self, func):
        """
        This decorator calls the function when a client connects.

        @Server.onConnect

        def onConnect(address: tuple):
            # code
        """
        if func in self.__onConnectListener:
            return

        self.__onConnectListener.append(func)

    def __fireOnConnect(self, address: tuple):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __fireOnConnect calls every function that uses the onConnect decorator.
        """
        for func in self.__onConnectListener:
            threading.Thread(target=func, args=[address]).start()

    def onDisconnect(self, func):
        """
        This decorator calls the function when a client disconnects.

        @Server.onDisconnect

        def onDisconnect(address: tuple):
            # code
        """
        if func in self.__onDisconnectListener:
            return

        self.__onDisconnectListener.append(func)

    def __fireOnDisconnect(self, address: tuple):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __fireOnDisconnect calls every function that uses the onDisconnect decorator.
        """
        for func in self.__onDisconnectListener:
            threading.Thread(target=func, args=[address]).start()

    def __logMessage(self, msg):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS
        -----
        __logMessage print a log message.
        """
        now = datetime.now()
        currTime = now.strftime("%Y-%m-%d, %H:%M:%S")
        print(f"[{currTime}] {msg}")
