# -*- coding: utf8 -*-
import socket
import sys
import datetime
import select
import json

class Client:
    def __init__(self):
        self.SERVER_HOST = '127.0.0.1'
        self.SERVER_PORT = 9111
        self.connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        # 서버와의 연결을 시도
        try:
            self.connection_sock.connect((self.SERVER_HOST, self.SERVER_PORT))
            print(f"채팅서버 ({self.SERVER_HOST}:{self.SERVER_PORT})에 연결되었습니다")
            room_num = int(input("\n◽ 입장할 채팅방 번호를 입력하세요: "))
        except Exception as e:
            print(e)
            raise Exception

        while True:
            client_id = input("◽ 사용하실 아이디을 입력하세요: ")
            if ' ' in client_id:
                print("공백 없이 입력해주세요.")
                continue

            login_info = {'room_num': room_num, 'client_id': client_id}
            self.connection_sock.send(json.dumps(login_info).encode())  # 클라이언트 정보 송신
            is_authenticated = self.connection_sock.recv(1024).decode()  # 아이디 중복 여부 수신

            # 중복 아이디인 경우 overlappedError 메시지 수신
            if is_authenticated != 'Y':
                print(is_authenticated)
                continue
            # 중복 아이디가 아닌 경우 채팅방 입장
            print(f"\n  아이디[{client_id}] 생성 완료! :-)")
            s = ""
            s += "\n -----------< 추가기능 command >-----------"
            s += "\n 1. 귓속말 보내기"
            s += "\n   : !whisper [상대방 아이디] [메시지] 입력"
            s += "\n 2. 아이디 변경하기"
            s += "\n   : !change [바꿀 아이디] 입력"
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
                connection_list = [sys.stdin, self.connection_sock]
                read_sockets, _, _ = select.select(connection_list, [], [], 3)

                for sock in read_sockets:
                    # 서버에서 받은 메시지인 경우    
                    if sock == self.connection_sock:
                        data = sock.recv(4096).decode()
                        if 'changed_id' in data:    # 아이디이 바뀐 경우 {"changed_id": changed_id}의 dictionary가 전달됨
                            changed_info = json.loads(data)
                            client_id = changed_info['changed_id'].replace('\n', "")
                        else:
                            print(data)

                    # 클라이언트가 터미널에서 입력한 메시지인 경우
                    else:
                        message = sys.stdin.readline().replace('\n', '') # 클라이언트가 입력한 문자열을 읽어서
                        self.connection_sock.send(f'{client_id}{time_str}: {message}'.encode())   # 서버에 전송

            except ConnectionResetError:
                print("서버에 의해 채팅방이 종료되었습니다.")
                sys.exit()

            except KeyboardInterrupt:
                self.connection_sock.close()
                sys.exit()

            except Exception as e:
                print(type(e), e)
                self.connection_sock.close()
                sys.exit()

client = Client()
client.run()