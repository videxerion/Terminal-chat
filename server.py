import socket
import time
import rsa
import zlib
import _pickle as cPickle
from multiprocessing import Process
from multiprocessing import Manager


class Server:
    def recv(self, size, conn: socket.socket, key):
        data = conn.recv(size)
        if data != b'':
            decompressedData = zlib.decompress(data)
            deserializedData = cPickle.loads(decompressedData)
            decryptedData = rsa.decrypt(deserializedData, key)
            return decryptedData
        else:
            return False

    def __connection_loop__(self):
        ID_THREAD = 0
        manager = Manager()
        connections = manager.list()
        nicks = manager.list()

        while self.status == 'run':
            try:
                conn, addr = self.sock.accept()
            except KeyboardInterrupt:
                self.close()
                return 0
            self.logPrint(f'connected: {addr}')

            proc = Process(target=self.__connection__, args=(conn, addr, ID_THREAD, connections, nicks))
            pubkeyClient = cPickle.loads(conn.recv(2048))
            conn.send(cPickle.dumps(self.pubkey))
            connections.append(
                {
                    "ID_THREAD": ID_THREAD,
                    "DATA": {
                        'CONN': conn,
                        'ADDR': addr,
                        'OPEN_KEY': pubkeyClient
                    }
                }
            )
            proc.start()
            ID_THREAD += 1

    def __connection__(self, conn: socket.socket, addr, ID_THREAD, connections: list, nicks: list):
        while True:
            find = False
            nickname = self.recv(4096, conn, self.privkey)
            for nick in nicks:
                if nick == nickname:
                    conn.send(b'\x01')
                    find = True
            if not find:
                break

        nicks.append(nickname)
        conn.send(b'\x00')

        self.__send_msg__(f'{nickname.decode("UTF-8")} join the chat!'.encode('UTF-8'), -1, connections)
        self.logPrint(f'{addr[0]}:{addr[1]} enter to chat under the name "{nickname.decode("UTF-8")}"')
        while True:
            try:
                data = self.recv(4096, conn, self.privkey)
            except KeyboardInterrupt:
                return 0
            if data:
                self.__send_msg__(data.removesuffix(b"\n"), ID_THREAD, connections, nickname)
            else:
                for i in range(len(connections)):
                    if connections[i]["ID_THREAD"] == ID_THREAD:
                        connections.pop(i)
                        nicks.remove(nickname)
                        break
                self.__send_msg__(f'{nickname.decode("UTF-8")} leave the chat...'.encode('UTF-8'), -1, connections)
                self.logPrint(f'{addr[0]}:{addr[1]} leave chat under the name "{nickname.decode("UTF-8")}"')
                return 0

    @staticmethod
    def __send_msg__(msg, threadID, connections, nickname=b'SERVER'):
        for connect in connections:
            if connect["ID_THREAD"] != threadID:
                msgForSend = b"[" + nickname.replace(b'\n', b'') + b']' + b" " + msg
                encMsg = rsa.encrypt(msgForSend, connect['DATA']['OPEN_KEY'])
                serializeMsg = cPickle.dumps(encMsg)
                compressedMsg = zlib.compress(serializeMsg, zlib.Z_BEST_COMPRESSION)
                connect['DATA']['CONN'].send(compressedMsg)

    def __time_difference__(self):
        return format(time.time() - self.start_time, '.5f')

    @staticmethod
    def __get_current_time__():
        return time.strftime("%H:%M:%S", time.gmtime())

    def logPrint(self, message):
        print(f'[{self.__time_difference__()}]({self.__get_current_time__()})', message)

    def __init__(self, ipAndPort: tuple):
        self.ip, self.port = ipAndPort
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start_time = None
        self.status = 'stop'
        self.__loop = Process(target=self.__connection_loop__)

        self.pubkey = None
        self.privkey = None

    def bind(self):
        self.sock.bind((self.ip, self.port))

    def start(self):
        self.sock.listen(10)
        self.status = 'run'
        self.start_time = time.time()
        (pubkey, privkey) = rsa.newkeys(2048)
        self.pubkey = pubkey
        self.privkey = privkey
        self.__loop.start()
        self.logPrint('Server start!')

    def close(self):
        self.status = 'stop'
        #print(self.__loop)
        #self.__loop.terminate()
        self.sock.close()
        self.logPrint("Server close!")
        self.start_time = None
        self.privkey = None
        self.pubkey = None


srv = Server(
    ('0.0.0.0', 5005)
)

srv.bind()
srv.start()