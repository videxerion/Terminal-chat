import socket
import rsa
import zlib
import _pickle as cPickle
from os import system, name
from multiprocessing import Process

print('Generate keys......')
(pubkey, privkey) = rsa.newkeys(2048)


def clear():
    # for windows
    if name == 'nt':
        system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        system('clear')


def getMessageLoop(sock: socket.socket):
    def recv(size, conn: socket.socket, key):
        data = conn.recv(size)
        if data:
            decompressedData = zlib.decompress(data)
            deserializedData = cPickle.loads(decompressedData)
            decryptedData = rsa.decrypt(deserializedData, key)
            return decryptedData
        else:
            print('Server closed')
            exit(0)
    try:
        while True:
            data = recv(4096, sock, privkey)
            print(data.decode('UTF-8'))
    except KeyboardInterrupt:
        return 0


def sendMsg(msg: str, pubkeyServer):
    byteString = msg.encode('UTF-8')
    encMsg = rsa.encrypt(byteString, pubkeyServer)
    dump = cPickle.dumps(encMsg)
    compressDump = zlib.compress(dump, zlib.Z_BEST_COMPRESSION)
    sock.send(compressDump)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # создаем сокет
sock.connect(('localhost', 5005))  # подключемся к серверному сокету

sock.send(cPickle.dumps(pubkey))
pubkeyServer = cPickle.loads(sock.recv(2048))

clear()
while True:
    sendMsg(input('Enter nickname: '), pubkeyServer)
    answer = sock.recv(5)
    if answer[0] == 0x1:
        print('This nickname already in use')
    elif answer[0] == 0x0:
        break
clear()

getLoop = Process(target=getMessageLoop, args=tuple([sock]))
getLoop.start()

try:
    while True:
        sendMsg(input(), pubkeyServer)
except KeyboardInterrupt:
    exit(0)