# -*- coding: utf8 -*-
import socket
from sre_constants import SUCCESS
import sys
import select
import datetime
import json
import mysql.connector

class overlappedError(Exception):
	def __init__(self):
		super().__init__("\n※ 이미 사용중인 닉네임입니다. 다시 입력해주세요.\n")

def find_conn(connection_dict, nick_val):
	return next(conn for conn, nick in connection_dict.items() if nick_val == nick)
	
def find_nick(connection_dict, conn_val):
	return next(nick for conn, nick in connection_dict.items() if conn_val == conn)

def find_room_num(connection_status, conn_val):
	return next(room_num for room_num, connection_dict in connection_status.items() if conn_val in connection_dict)

def messageManage(data):
	global connectionStatus
	room_num = find_room_num(connectionStatus, conn)
	connection_dict = connectionStatus[room_num]

	if data.split(' ')[1] == '!whisper':  	# data.split(' ') = ['nick[time]:', '!whisper', 'receiver', 'message[0]', 'message[1]' ...]
		sender_conn = conn
		receiver = data.split(' ')[2]
		if receiver in connection_dict.values():
			receiver_conn = find_conn(connection_dict, receiver)
			msg = data.split(' ')[3:]
			msg = ' '.join(msg)
			sender_nick = find_nick(connection_dict, sender_conn)  # conn으로 nick 찾기
			receiver_conn.send(f"(귓속말){sender_nick}{time_str}: {msg}".encode())
		else:
			receiver_conn.send(f"입력하신 닉네임은 존재하지 않습니다.".encode())

	elif data.split(' ')[1] == '!change_nick':
		changed_nick = data.split(' ')[2]
		original_conn = conn
		original_nick = find_nick(connection_dict, original_conn)  # conn으로 nick 찾기
		connection_dict[original_conn] = changed_nick  # conn의 value에 새로운 nick로 갱신
		msg = {'changed_nick': changed_nick}
		original_conn.send(json.dumps(msg).encode())
		for sock in connection_dict.keys():
			if sock != original_conn:   # 닉네임을 바꾼 클라이언트를 제외한 채팅방 멤버에게 메시지 전달
				sock.send(f"[INFO] {original_nick}님이 {changed_nick}로 닉네임 변경".encode())

	elif data.split(' ')[1] == '!member':
		member_list = list(connection_dict.values())
		conn.send(f'{member_list}'.encode())

	else: 
		msg = data
		for sock in connection_dict:
			sock.send(msg.encode())
			print(f'[MESSAGE] {data}')	

class chatRoom():
	global connectionStatus

	def clientInfo(self, conn, data):
		self.nickname = data['client_nick']
		self.room_num = data['room_num']

		if self.room_num not in connectionStatus:  						# 최초의 채팅방이라면
			connection_dict = {}								    # connection_dict = {conn1:nick1, conn2:nick2, conn3:nick3...}
			connectionStatus[self.room_num] = connection_dict		# connectionStatus 안에 클라이언트가 입력한 채팅방을 key, 빈 딕셔너리를 value로 하는 딕셔너리 생성
			connectionStatus[self.room_num][conn] = self.nickname				# 입력한 채팅방의 value로 conn과 nick을 각각 key와 value로 갖는 딕셔너리 추가
			conn.send('Y'.encode())										# 클라이언트에게 닉네임 등록 메시지 전달
			print(f"[INFO] [room_num_{self.room_num}] {self.nickname}님 접속")
			for sock in connectionStatus[self.room_num]:
				if sock != conn: 
					sock.send(f"[INFO] {self.nickname}님 접속".encode())
		else:  															# 기존에 있는 채팅방에 들어간다면
			try:														# 같은 채팅방 안에 중복 닉네임이 있는지 여부 판단
				if self.nickname not in connectionStatus[self.room_num].values(): # 중복닉네임 없으면 		
					connectionStatus[self.room_num][conn] = self.nickname			# 입력한 채팅방의 value로 conn과 nick을 각각 key와 value로 갖는 딕셔너리 추가
					conn.send('Y'.encode())									# 클라이언트에게 닉네임 등록 메시지 전달
					print(f"[INFO] [room_num_{self.room_num}] {self.nickname}님 접속")
					for sock in connectionStatus[self.room_num]:
						if sock != conn: 
							sock.send(f"[INFO] {self.nickname}님 접속".encode())
				else:
					raise overlappedError									# 중복닉네임 있으면 에러메시지 전달
			except overlappedError as e:
				conn.send(f'{e}'.encode())


HOST = '127.0.0.1'
PORT = 9111
ADDR = (HOST, PORT)

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # AF_INET = IPv4, SOCK_STREAM = TCP 통신
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind(ADDR)

server_sock.listen()


print("==============================================")
print("채팅 서버를 시작합니다. %s 포트로 접속을 기다립니다." % str(PORT))
print("==============================================")


connectionStatus = {}  # 채팅방별 클라이언트 소켓, 닉네임 저장  ex) {1: {conn1: nick1, conn2: nick2, ...}, 2: {conn1: nick1, conn2:nick2, ...}, ...}

chat_room = chatRoom()

connection_list = [server_sock]

while True:
	now = datetime.datetime.now()
	time_str = now.strftime('[%H:%M]')
	try:
		read_sockets, write_sockets, error_sockets = select.select(connection_list, [], [], 30)
		print("클라이언트 요청 대기...")
		for sock in read_sockets:
			if sock == server_sock:   # 새로운 클라이언트의 소켓이라면 connection_list에 추가
				newsock, addr = server_sock.accept()
				connection_list.append(newsock)
			else:    # 이미 접속한 클라이언트의 소켓이라면 클라이언트가 보낸 메시지 수신
				conn = sock
				data = conn.recv(1024).decode()

				if 'room_num' not in data:  # 이미 접속한 클라이언트의 "메시지" 수신
					try:
						messageManage(data)  # 클라이언트의 메시지에 command가 있으면 해당 내용 수행, 없으면 메시지 자체를 broadcast
					except Exception as e:
						print(f"[messageManage] {e} by {data}")

				else:  						# "최초" 접속한 클라이언트의 정보 수신
					login_info = json.loads(data)  # json 문자열인 data를 -> json.loads(data) -> 파이썬 객체(dict)
					try:
						chat_room.clientInfo(conn, login_info)
					except Exception as e:
						print(e)

	except Exception as e:
		print(e)
		server_sock.close()
		sys.exit()

