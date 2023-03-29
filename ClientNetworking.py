import socket
import threading
from datetime import datetime
import json


class Client:
    connected = False
    __disconnectedByCommand = False

    encoding = "utf-8"
    disconnectMessage = "!DISCONNECT"

    __recvListener = []
    __serverCloseListener = []

    def __init__(self, host: str, port: int = 5000, standartBufferSize: int = 64, messageTerminatorChar: str = "|") -> None:
        self.address = (host, port)
        self.standartBufferSize = standartBufferSize

        if not len(messageTerminatorChar) == 1:
            raise Exception(
                "messageTerminatorChar should be one char that dont ever exists in your sended messages!")

        self.messageTerminatorChar = messageTerminatorChar

        self.clientSocket = socket.socket()

    def connect(self):
        self.__logMessage(f"Connecting to {self.address}...")

        self.clientSocket.connect(self.address)
        self.connected = True

        self.__logMessage(f"Connected to {self.address}!")

        threading.Thread(target=self.__handleConnection).start()

    def disconnect(self):
        self.send(self.disconnectMessage)
        self.__disconnectedByCommand = True
        self.clientSocket.close()
        self.connected = False
        self.__fireDisconnect()

    def send(self, message: dict = {}):
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

    def __handleConnection(self):
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
        if func in self.__recvListener:
            return

        self.__recvListener.append(func)

    def __fireRecv(self, msg):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __fireRecv returns the msg
        """
        for func in self.__recvListener:
            threading.Thread(target=func, args=[msg]).start()

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
        for func in self.__serverCloseListener:
            threading.Thread(target=func).start()

    def __logMessage(self, msg):
        """
        DO NOT USE OUTSIDE OF SERVER CLASS\n
        __debugMessage print a debug message.
        """
        now = datetime.now()
        currTime = now.strftime("%Y-%m-%d, %H:%M:%S")
        print(f"[{currTime}] {msg}")
