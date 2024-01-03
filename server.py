# -*- coding: utf8 -*-
import socket
import sys
import select
import json
from messenger import Messenger
from repository import SocketRepo
from authenticator import AuthManager

class ChattingServer:
	HOST = '127.0.0.1'
	PORT = 9111
	def __init__(self):
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # AF_INET = IPv4, SOCK_STREAM = TCP 통신
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((ChattingServer.HOST, ChattingServer.PORT))
		self.server_sock.listen()
		self.messenger = Messenger()
		SocketRepo.add_connections_list(self.server_sock)

	def run(self):
		print("==============================================")
		print("채팅 서버를 시작합니다. %s 포트로 접속을 기다립니다." % str(ChattingServer.PORT))
		print("==============================================")

		while True:
			try:
				read_sockets, _, _ = select.select(SocketRepo.connections_list, [], [], 30)
				print("클라이언트 요청 대기...")
				for sock in read_sockets:
					# 클라이언트와 최초 연결 수립용 서버 소켓에 연결된 경우: connections_list에 추가  
					if sock == self.server_sock:
						client_conn, _ = self.server_sock.accept()
						SocketRepo.add_connections_list(client_conn)
					# 각 클라이언트와의 통신용으로 생성된 소켓과 연결된 경우: 해당 클라이언트가 보낸 메세지 처리
					else:
						client_conn = sock
						data = client_conn.recv(1024).decode()
						# 이미 접속한 클라이언트의 메시지 수신
						if 'room_num' not in data:
							self.messenger.process_message(client_conn, data)
						# 최초 접속한 클라이언트 로그인
						else:
							client_info = json.loads(data)
							AuthManager.authenticate(client_conn, client_info)	

			except IndexError:
				self.handle_disconnection(client_conn)

			except StopIteration:
				SocketRepo.remove_connection(client_conn)
				client_conn.close()

			except KeyboardInterrupt:
				self.server_sock.close()
				sys.exit()

			except Exception as e:
				self.server_sock.close()
				sys.exit()

	def handle_disconnection(self, disconnected_sock):
		"""
		클라이언트에 의해 연결이 소실된 소켓에 대한 graceful한 처리
		"""
		connections_info = SocketRepo.get_connections_info()
		room_num = self.messenger.find_room_num(connections_info, disconnected_sock)
		client_id = self.messenger.find_client_id(connections_info[room_num], disconnected_sock)
		SocketRepo.del_connection_info(room_num, disconnected_sock)
		SocketRepo.remove_connection(disconnected_sock)
		disconnected_sock.close()
		print(f"[INFO] [room_num_{room_num}] {client_id}님 퇴장")
		for sock in connections_info[room_num]: # 해당 room의 모든 클라이언트들에게 broadcast
			sock.send(f"[INFO] {client_id}님 퇴장".encode())

chatting_server = ChattingServer()
chatting_server.run()