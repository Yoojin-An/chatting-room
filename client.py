# -*- coding: utf8 -*-
import socket
import sys
import datetime
import select
import json

HOST = '127.0.0.1'
PORT = 9111
ADDR = (HOST, PORT)

# socket 객체 생성
connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 서버와의 연결을 시도
try:
    connection_sock.connect(ADDR)
except Exception as e:
    print(e)
print("채팅서버 (%s: %s)에 연결되었습니다" %ADDR)

room_num = int(input("\n◽ 입장할 채팅방 번호를 입력하세요: "))

while True:
    client_nick = input("◽ 사용하실 닉네임을 입력하세요: ")
    if ' ' in client_nick:
        print("공백 없이 입력해주세요.")
        continue

    login_info = {'room_num': room_num, 'client_nick': client_nick}
    connection_sock.send(json.dumps(login_info).encode())  # 클라이언트 정보 송신
    is_possible_nick = connection_sock.recv(1024).decode()  # 닉네임 중복 여부 수신

    if is_possible_nick != 'Y':  # 중복 닉네임인 경우 overlappedError 메시지 수신
        continue
    else:                       # 중복닉네임이 아닌 경우 채팅방 입장
        print(f"\n  닉네임[{client_nick}] 생성 완료! :-)")
        s = ""
        s += "\n -----------< 추가기능 command >-----------"
        s += "\n 1. 귓속말 보내기"
        s += "\n   : !whisper [상대방 닉네임] [메시지] 입력"
        s += "\n 2. 닉네임 변경하기"
        s += "\n   : !change_nick [바꿀 닉네임] 입력"
        s += "\n 3. 참여 중인 멤버 목록 보기"
        s += "\n   : !member 입력"
        s += "\n -----------------------------------------"
        s+="\n"
        print(s)
        break

while True:
    now = datetime.datetime.now()
    time_str=now.strftime('[%H:%M]')
    
    try:
        # 클라이언트의 IN 동작을 파악할 수 있도록 read_sockets에 sys.stdin도 포함 
        connection_list = [sys.stdin, connection_sock]
        read_sockets, write_sockets, error_sockets = select.select(connection_list, [], [], 3)

        for sock in read_sockets:
            # 서버에서 받은 메시지인 경우    
            if sock == connection_sock:
                data = sock.recv(4096).decode()
                if 'changed_nick' in data:    # 닉네임이 바뀐 경우 {"changed_nick": changed_nick}의 dictionary가 전달됨
                    changed_info = json.loads(data)
                    client_nick = changed_info['changed_nick'].replace('\n', "")
                else:
                    print(data)

            # 클라이언트가 터미널에서 입력한 메시지인 경우
            else:
                message = sys.stdin.readline()  # 클라이언트가 입력한 문자열을 읽어서
                message = message.replace('\n', '')
                message    
                connection_sock.send(f'{client_nick}{time_str}: {message}'.encode())   # 서버에 전송

    except Exception as e:
        print(e)
        connection_sock.close()
        sys.exit()