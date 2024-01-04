class SocketRepo:
	connections_info = {}
	
	@classmethod
	def get_connections_info(cls):
		return cls.connections_info
	
	@classmethod
	def upsert_connections_info(cls, room_num, sock, client_id):
		cls.connections_info[room_num][sock] = client_id

	@classmethod
	def del_connection_info(cls, room_num, sock):
		del cls.connections_info[room_num][sock]