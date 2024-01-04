# -*- coding: utf8 -*-
import socket
import sys
import selectors
import json
from time import time
from messenger import Messenger
from repository import SocketRepo
from authenticator import AuthManager

class ChattingServer:
   HOST = '127.0.0.1'
   PORT = 9111
   def __init__(self):
      self.sel = selectors.KqueueSelector()
      self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.server_sock.bind((ChattingServer.HOST, ChattingServer.PORT))
      self.server_sock.listen(100) # 서버가 동시 처리할 수 있는 연결 요청의 최대 큐 크기(default = 5)
      self.server_sock.setblocking(False)
      self.sel.register(self.server_sock, selectors.EVENT_READ, self.accept)
      self.messenger = Messenger()

   def read(self, client_conn, mask):
      data = client_conn.recv(1024).decode()
      if data:
         # 최초 접속한 클라이언트 로그인
         if 'room_num' in data:
            client_info = json.loads(data)
            AuthManager.authenticate(client_conn, client_info)   
         # 이미 접속한 클라이언트의 메시지 수신
         else:
            self.messenger.process_message(client_conn, data)
      else:
         # selectors에서 해당 클라이언트 커넥션 등록 해제
         self.sel.unregister(client_conn)
         # SocketRepo.connections_info에서 해당 클라이언트 커넥션 정보 삭제
         connections_info = SocketRepo.get_connections_info()
         room_num = self.messenger.find_room_num(connections_info, client_conn)
         client_id = self.messenger.find_client_id(connections_info[room_num], client_conn)
         SocketRepo.del_connection_info(room_num, client_conn)
         # 해당 클라이언트 커넥션용 소켓 close
         client_conn.close()
         print(f"[INFO] [room_num_{room_num}] {client_id}님 퇴장")
         # 해당 room의 모든 클라이언트들에게 broadcast
         for sock in connections_info[room_num]:
            sock.send(f"[INFO] {client_id}님 퇴장".encode())

   def accept(self, sock, mask):
      client_conn, _ = sock.accept()
      client_conn.setblocking(False)
      self.sel.register(client_conn, selectors.EVENT_READ, self.read)

   def run(self):
      print("==============================================")
      print("채팅 서버를 시작합니다. %s 포트로 접속을 기다립니다." % str(ChattingServer.PORT))
      print("==============================================")

      while True:
         try:
            events = self.sel.select()
            start = time()
            for key, mask in events:
               callback = key.data
               client_conn = key.fileobj
               callback(client_conn, mask)
            end = time()
            print(end - start)

         except StopIteration:
            client_conn.close()

         except KeyboardInterrupt:
            self.server_sock.close()
            sys.exit()

         except Exception as e:
            self.server_sock.close()
            sys.exit()

chatting_server = ChattingServer()
chatting_server.run()