# -*- coding: utf8 -*-
import socket
import sys
import selectors
import json
import argparse
import datetime
import io

parser = argparse.ArgumentParser(description='TCP Client')
parser.add_argument('-host', '--hostname', default='localhost', help="서버 호스트")
parser.add_argument('-port', '--portnum', default=9993, help="서버 포트")
argument = parser.parse_args()
host = argument.hostname
port = int(argument.portnum)

class Client:
    def __init__(self):
        self.client_id = None
        self.sel = selectors.KqueueSelector()
        self.connection_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sel.register(self.connection_sock, selectors.EVENT_READ, self.read)
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.read)
        # self.connection_sock.setblocking(False) # TODO: 왜 블로킹 해제하면 안 될까?

    def connect_to_server(self):
        try:
            self.connection_sock.connect((host, port))
            print(f"채팅서버({host}:{port})에 연결되었습니다!")
        except Exception as e:
            print(e, type(e))
            print(f"채팅서버({host}:{port}) 주소가 맞는지 확인하세요👀")
            raise Exception

    def enter_chat_room(self):
        while True:
            try: 
                room_num = int(input("\n◽ 입장할 채팅방 번호를 입력하세요: "))
                break
            except ValueError:
                print("숫자를 입력해주세요.")
        
        while True:
            self.client_id = input("◽ 사용하실 아이디를 입력하세요: ")
            if ' ' in self.client_id:
                print("공백 없이 입력해주세요👀")
                continue

            login_info = {"room_num": room_num, "client_id": self.client_id}
            self.connection_sock.send(json.dumps(login_info).encode())  # 클라이언트 정보 송신
            is_authenticated = self.connection_sock.recv(1024).decode()  # 아이디 중복 여부 수신
            # 중복 아이디인 경우 overlappedError 메시지 수신
            if is_authenticated != 'Y':
                print(is_authenticated)
                continue
            
            print(f"\n  아이디[{self.client_id}] 생성 완료! :-)")
            break

    def print_commands(self):
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

    def read(self, conn, mask):
        now = datetime.datetime.now()
        time_str=now.strftime('[%H:%M]')
        # 서버로부터 메세지 수신 시
        if conn == self.connection_sock:
            data = conn.recv(4096).decode()
            if 'changed_id' not in data:
                print(data)
            else: # 아이디가 바뀐 경우
                changed_info = json.loads(data)
                self.client_id = changed_info['changed_id'].replace('\n', "")
                print(f"[INFO] {self.client_id}(으)로 아이디가 변경되었습니다.")

        # 표준입력(stdin) 시
        else:
            message = sys.stdin.readline().replace('\n', '') # 표준입력된 문자열을 읽어서
            self.connection_sock.send(f'{self.client_id}{time_str}: {message}'.encode()) # 서버에 전송

    def run(self):
        self.connect_to_server()
        self.enter_chat_room()
        self.print_commands()

        while True:
            try:
                events = self.sel.select()
                for key, mask in events:
                    callback = key.data
                    conn = key.fileobj # stdin 또는 socket
                    callback(conn, mask)

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

if __name__ == '__main__':
    client = Client()
    client.run()