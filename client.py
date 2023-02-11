import socket
import rsa
import zlib
import _pickle as cPickle
from multiprocessing import Process
import curses

stdscr = curses.initscr()
stdscr.keypad(True)
curses.echo(True)
stdscr.refresh()

inputWin = curses.newwin(3, curses.COLS, curses.LINES - 3, 0)
inputWin.keypad(True)

inputWin.refresh()

chatWin = curses.newwin(curses.LINES - 2, curses.COLS, 0, 0)
chatWin.refresh()

chatWin.addstr('Generate keys......')
chatWin.refresh()
(pubkey, privkey) = rsa.newkeys(2048)


def getMessageLoop(sock: socket.socket):
    def recv(size, conn: socket.socket, key):
        data = conn.recv(size)
        if data:
            decompressedData = zlib.decompress(data)
            deserializedData = cPickle.loads(decompressedData)
            decryptedData = rsa.decrypt(deserializedData, key)
            return decryptedData
        else:
            chatWin.addstr("server error")
            chatWin.refresh()
            exit(0)

    try:
        while True:
            data = recv(4096, sock, privkey)
            chatWin.addstr(data.decode('UTF-8'))
            chatWin.refresh()
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

chatWin.clear()
chatWin.refresh()

while True:
    sendMsg(input('Enter nickname: '), pubkeyServer)
    answer = sock.recv(5)
    if answer[0] == 0x1:
        chatWin.addstr('This nickname already in use')
        chatWin.refresh()
    elif answer[0] == 0x0:
        break

chatWin.clear()
chatWin.refresh()

getLoop = Process(target=getMessageLoop, args=tuple([sock]))
getLoop.start()

try:
    while True:
        text = (inputWin.getstr()).decode(encoding='UTF-8')
        sendMsg(text, pubkeyServer)
except KeyboardInterrupt:
    curses.endwin()
    exit(0)
