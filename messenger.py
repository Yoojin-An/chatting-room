import json
import socket
import datetime
from repository import SocketRepo

class Messenger:
	def __init__(self):
		pass
	
	def find_conn(self, room_num, client_id) -> socket.socket:
		clients = SocketRepo.connections_info[room_num]
		flipped_clients = {client_id: client_conn for client_conn, client_id in clients.items()}
		return flipped_clients.get(client_id)

	def find_client_id(self, room_num, conn) -> str:
		clients = SocketRepo.connections_info[room_num]
		return clients.get(conn)

	def find_room_num(self, conn) -> int:
		connections_info = SocketRepo.connections_info
		return next(room_num for room_num, clients in connections_info.items() if conn in clients)
    
	def find_clients(self, room_num) -> dict:
		"""
		room_num에 해당하는 모든 커넥션 정보
		SocketRepo.connections_info[room_num] = {conn1: id1, conn2: id2, ...} 
		"""
		connections_info = SocketRepo.get_connections_info() # room_num별 conn: id 딕셔너리
		return connections_info[room_num]

	def process_message(self, conn, data):
		now = datetime.datetime.now()
		time_str=now.strftime('[%H:%M]')
		room_num = self.find_room_num(conn)
		clients = self.find_clients(room_num)

		if data.split(' ')[1] == '!whisper':  	# data.split(' ') = ['client_id[time]:', '!whisper', 'receiver', 'message[0]', 'message[1]' ...]
			sender_conn = conn
			receiver_id = data.split(' ')[2]
			if receiver_id in clients.values():
				receiver_conn = self.find_conn(room_num, receiver_id)
				msg = data.split(' ')[3:]
				msg = ' '.join(msg)
				sender_id = self.find_client_id(room_num, sender_conn) # conn으로 client_id 찾기
				receiver_conn.send(f"(귓속말){sender_id}{time_str}: {msg}".encode())
			else:
				receiver_conn.send(f"입력하신 아이디는 존재하지 않습니다.".encode())

		elif data.split(' ')[1] == '!change':
			try:
				original_client_id = self.find_client_id(room_num, conn) # conn으로 client_id 찾기
				new_client_id = data.split(' ')[2]
				if new_client_id not in clients.values():
					SocketRepo.upsert_connections_info(room_num, conn, new_client_id) # 새로운 client_id로 갱신
				msg = {"changed_id": new_client_id}
				conn.send(json.dumps(msg).encode())
				for sock in clients.keys():
					if sock != conn:   # 닉네임을 바꾼 클라이언트를 제외한 채팅방 멤버에게 메시지 전달
						sock.send(f"[INFO] {original_client_id}님이 {new_client_id}로 아이디 변경".encode())
			except Exception as e:
				print(type(e), e)

		elif data.split(' ')[1] == '!member':
			member_list = list(clients.values())
			conn.send(f'{member_list}'.encode())

		else: 
			msg = data
			print(f'[MESSAGE] {data}')	
			for conn in clients:
				conn.send(msg.encode())