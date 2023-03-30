import socket
import threading
from datetime import datetime
import json
from time import time


class Client:
    """
    Use this class to set up an client.
    """
    connected = False
    __disconnectedByCommand = False

    # standart Properties
    encoding = "utf-8"
    disconnectMessage = "!DISCONNECT"

    # all Listeners
    __onRecvListener = []
    __onConnectListener = []
    __serverCloseListener = []

    def __init__(self, host: str, port: int = 5000, standartBufferSize: int = 64, messageTerminatorChar: str = "|") -> None:
        self.address = (host, port)
        self.standartBufferSize = standartBufferSize

        # the messageTerminatorChar has to be just one char
        if not len(messageTerminatorChar) == 1:
            raise Exception(
                "messageTerminatorChar should be one char that dont ever exists in your sended messages!")

        self.messageTerminatorChar = messageTerminatorChar

    def connect(self):
        """
        Connect to the server.
        """
        self.__logMessage(f"Connecting to {self.address}...")

        # create socket and connect to server
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket.connect(self.address)
        self.connected = True

        self.__logMessage(f"Connected to {self.address}!")

        threading.Thread(target=self.__handleConnection).start()

    def disconnect(self):
        """
        Disconnect from the server.
        """
        # send the disconnect message and close connection
        self.send(self.disconnectMessage)
        self.__disconnectedByCommand = True
        self.connected = False
        t = time()
        while time() - t < 0.1:
            pass

        self.clientSocket.close()
        self.__fireDisconnect()

    def send(self, message: dict = {}):
        """
        Send a dict to the server.
        """
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

        self.clientSocket.send(sendLen)
        self.clientSocket.send(msg)

        self.__logMessage("Sended message to server!")

    def __handleConnection(self):
        """
        DO NOT USE OUTSIDE OF CLIENT CLASS\n
        __handleConnection handles the servers send messages.
        """
        # fire the onConnect event
        self.__fireOnConnect()

        while self.connected:
            try:
                msgLen = ""
                while not self.messageTerminatorChar in msgLen:
                    msgLen += self.clientSocket.recv(
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
                    f"Invalid message lenght from server!\n{msgLen}")
                continue

            try:
                msg = ""
                while not self.messageTerminatorChar in msg:
                    msg += self.clientSocket.recv(msgLen).decode(self.encoding)

                msg = msg.replace(self.messageTerminatorChar, "")
            except:
                continue

            self.__logMessage(f"Got message from server!")

            # check system commands
            if msg == self.disconnectMessage:
                self.connected = False
                continue

            try:
                msg = json.loads(msg)
            except:
                self.__logMessage(
                    f"Message from server could not be handled!\n{msg}")
                continue

            self.__fireRecv(msg)

        if self.__disconnectedByCommand:
            return

        self.clientSocket.close()
        self.__fireDisconnect()

    # decorators
    def onRecv(self, func):
        """
        This decorator returns every received message.\n
        @Client.onRecv\n
        def onRecv(message):
            # code
        """
        if func in self.__onRecvListener:
            return

        self.__onRecvListener.append(func)

    def __fireRecv(self, msg):
        """
        DO NOT USE OUTSIDE OF CLIENT CLASS\n
        __fireRecv returns the msg
        """
        for func in self.__onRecvListener:
            threading.Thread(target=func, args=[msg]).start()

    def onConnect(self, func):
        """
        Fire when the client connects to a server.\n
        @Client.onConnect\n
        def onConnect():
            # code
        """
        if func in self.__onConnectListener:
            return

        self.__onConnectListener.append(func)

    def __fireOnConnect(self):
        """
        DO NOT USE OUTSIDE OF CLIENT CLASS\n
        __fireOnConnect fires after you connect to a server.
        """
        for func in self.__onConnectListener:
            threading.Thread(target=func).start()

    def onDisconnect(self, func):
        """
        Fire when the client disconnects from the server or gets disconnected.\n
        @Client.onDisconnect\n
        def onDisconnect():
            # code
        """
        if func in self.__serverCloseListener:
            return

        self.__serverCloseListener.append(func)

    def __fireDisconnect(self):
        """
        DO NOT USE OUTSIDE OF CLIENT CLASS\n
        __fireDisconnect fires when you get diconnected or disconnect from the server.
        """
        for func in self.__serverCloseListener:
            func()

    def __logMessage(self, msg):
        """
        DO NOT USE OUTSIDE OF CLIENT CLASS\n
        __logMessage print a log message.
        """
        now = datetime.now()
        currTime = now.strftime("%Y-%m-%d, %H:%M:%S")
        print(f"[{currTime}] {msg}")
