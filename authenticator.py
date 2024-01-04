from repository import SocketRepo

class OverlappedError(Exception):
	def __init__(self):
		super().__init__("\n※ 이미 사용중인 아이디입니다. 다시 입력해주세요.\n")


class AuthManager:
	@classmethod
	def authenticate(cls, conn, client_info):
		room_num = client_info['room_num']
		client_id = client_info['client_id']
		connections_info = SocketRepo.get_connections_info()  # connection_dict = {conn1:client_id1, conn2:client_id2, ...}
		if room_num not in connections_info:
			connections_info[room_num] = {}
		
		# 아이디 중복 체크
		try:
			# 중복아이디 없으면 authenticated
			if client_id not in connections_info[room_num].values():		 
				SocketRepo.upsert_connections_info(room_num, conn, client_id) # 해당 방에 {conn:client} 추가	
				conn.send('Y'.encode()) # 클라이언트에게 authenticated 메시지 전달
				print(f"[INFO] [room_num_{room_num}] {client_id}님 접속")
				for sock in connections_info[room_num]: # 해당 방의 모든 인원에게 broadcast
					if sock != conn: 
						sock.send(f"[INFO] {client_id}님 접속".encode())
			# 중복아이디 있으면 클라이언트에게 에러메시지 전달
			else:
				raise OverlappedError
		except OverlappedError as e:
			conn.send(f'{e}'.encode())