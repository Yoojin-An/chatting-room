import json
import datetime
from repository import SocketRepo

class Messenger:
	def __init__(self):
		pass

	def find_conn(self, clients, client_id):
		return next(conn for conn, _client_id in clients.items() if client_id == _client_id)
		
	def find_client_id(self, clients, conn):
		return next(client_id for client_conn, client_id in clients.items() if conn == client_conn)

	def find_room_num(self, connections_info, conn):
		return next(room_num for room_num, clients in connections_info.items() if conn in clients)

	def process_message(self, conn, data):
		now = datetime.datetime.now()
		time_str=now.strftime('[%H:%M]')
		connections_info = SocketRepo.get_connections_info()
		room_num = self.find_room_num(connections_info, conn)
		clients = connections_info[room_num] # {conn1: id1, conn2: id2, conn3: id3, ...}

		if data.split(' ')[1] == '!whisper':  	# data.split(' ') = ['client_id[time]:', '!whisper', 'receiver', 'message[0]', 'message[1]' ...]
			sender_conn = conn
			receiver_id = data.split(' ')[2]
			if receiver_id in clients.values():
				receiver_conn = self.find_conn(clients, receiver_id)
				msg = data.split(' ')[3:]
				msg = ' '.join(msg)
				sender_id = self.find_client_id(clients, sender_conn) # conn으로 client_id 찾기
				receiver_conn.send(f"(귓속말){sender_id}{time_str}: {msg}".encode())
			else:
				receiver_conn.send(f"입력하신 아이디 존재하지 않습니다.".encode())

		elif data.split(' ')[1] == '!change':
			original_client_id = self.find_client_id(clients, conn) # conn으로 client_id 찾기
			new_client_id = data.split(' ')[2]
			if new_client_id not in 
			SocketRepo.upsert_connections_info(room_num, conn, new_client_id) # 새로운 client_id로 갱신
			msg = {f"[INFO] {new_client_id}로 아이디가 변경되었습니다.".encode()}
			conn.send(json.dumps(msg).encode())
			for sock in clients.keys():
				if sock != conn:   # 닉네임을 바꾼 클라이언트를 제외한 채팅방 멤버에게 메시지 전달
					sock.send(f"[INFO] {original_client_id}님이 {new_client_id}로 아이디 변경".encode())

		elif data.split(' ')[1] == '!member':
			member_list = list(clients.values())
			conn.send(f'{member_list}'.encode())

		else: 
			msg = data
			print(f'[MESSAGE] {data}')	
			for conn in clients:
				conn.send(msg.encode())