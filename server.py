import socket
import time
from multiprocessing import Process
from multiprocessing import Manager


class Server:
    def __connection_loop__(self):
        ID_THREAD = 0
        manager = Manager()
        connections = manager.list()

        while self.status == 'run':
            conn, addr = self.sock.accept()
            self.logPrint(f'connected: {addr}')
            proc = Process(target=self.__connection__, args=(conn, addr, ID_THREAD, connections))
            connections.append(
                {
                    "ID_THREAD": ID_THREAD,
                    "DATA": {
                        'CONN': conn,
                        'ADDR': addr
                    }
                }
            )
            proc.start()
            ID_THREAD += 1

    def __connection__(self, conn: socket.socket, addr, ID_THREAD, connections: list):
        nickname = conn.recv(1024).removesuffix(b"\n")
        self.__send_msg__(f'{nickname.decode("UTF-8")} join the chat!'.encode('UTF-8'), -1, connections)
        self.logPrint(f'{addr[0]}:{addr[1]} enter to chat under the name "{nickname.decode("UTF-8")}"')
        while True:
            data = conn.recv(1024)
            if data:
                self.__send_msg__(data.removesuffix(b"\n"), ID_THREAD, connections, nickname)
            else:
                for i in range(len(connections)):
                    if connections[i]["ID_THREAD"] == ID_THREAD:
                        connections.pop(i)
                        break
                self.__send_msg__(f'{nickname.decode("UTF-8")} leave the chat...'.encode('UTF-8'), -1, connections)
                self.logPrint(f'{addr[0]}:{addr[1]} leave chat under the name "{nickname.decode("UTF-8")}"')
                return 0

    @staticmethod
    def __send_msg__(msg, threadID, connections, nickname=b'SERVER'):
        for connect in connections:
            if connect["ID_THREAD"] != threadID:
                connect['DATA']['CONN'].send(b"[" + nickname.replace(b'\n', b'') + b']' + b" " + msg + b'\n')

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

    def bind(self):
        self.sock.bind((self.ip, self.port))

    def start(self):
        self.sock.listen(10)
        self.status = 'run'
        self.start_time = time.time()
        self.__loop.start()
        self.logPrint('Server start!')

    def close(self):
        self.status = 'stop'
        self.__loop.terminate()
        self.sock.close()
        self.logPrint("Server close!")
        self.start_time = None


srv = Server(
    ('0.0.0.0', 5005)
)

srv.bind()
srv.start()
