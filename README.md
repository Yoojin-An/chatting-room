# I/O multiplexing chatting program

</br>
⌨️ 다중화 에코 서버와 클라이언트가 TCP/IP로 통신하는 채팅 프로그램입니다.

</br>
⚙️ 프로젝트 환경</br>
 <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=Python&logoColor=white"/>


</br>
multiplexing은 I/O model 중 Asyncrous Blocking 영역에 해당됩니다.</br>
관점의 주체에 따라 Blocking인지, Non-Blocking인지 여부가 달라지며 실제 I/O 동작은 Synchronous 방식으로 동작하기도 합니다. 
프로그램에서 여러 FD를 모니터링해서 어떤 종류의 I/O 이벤트가 일어났는지 검사하고 각각의 FD가 Ready 상태가 되었는지 인지

    * Sync: I/O를 호출한 대상이 결과까지 챙기는 경우
    * Async: 결과를 kernel로 부터 노티를 받거나 call-back 형식으로 동작하는 경우

</br>

### multiplexing 종류
 '함수 레벨'에서 완성되는 라이브러리 </br>
 관심 있는 fd를 모두 등록해놓고 무한정 loop 순환 -> 하나 이상의 fd에서 이벤트 발생 시 실제 I/O 처리
 - select
 - pselect: select의 timeout 정밀도와 signal 처리 로직이 개선된 버전
 - poll: 
 - ppoll: poll의 timeout 정밀도와 signal 처리 로직이 개선된 버전
 -------------------------------------------------------------------------------- </br>
 I/O 성능 문제를 개선하기 위해 '운영체제 레벨'에서 지원하는 라이브러리
 - epoll(Linux)
 - kqueue(OpenBSD)
 - IOCP(I/O completion port)(Windows)
 - devpoll(Solaris)

#### 본 프로젝트는 I/O system call을 select() -> kqueue()로 고도화</br>
kqueue는 select나 poll에 비해 이벤트 처리에서 효율적입니다.
이벤트 발생 시, 해당 이벤트에 접근하는 시간복잡도가 O(1)이다.
select와 poll의 경우 이벤트 발생 시 해당 이벤트에 접근하는 시간복잡도가 O(N)이나, kqueue는 발생한 이벤트를 정리하여 return해주기 때문에 O(1)로 접근 가능하다.
등록된 이벤트를 따로 관리할 필요가 없다.
select는 fd_set, poll은 poll_fd 구조체의 배열로 모니터링할 이벤트들을 사용자가 관리하고, 이를 select()나 poll()에 전달해야 하지만, kqueue의 경우 새로 등록할 이벤트, 발생한 이벤트만 관리해주면 된다. 모니터링되는 이벤트는 kqueue, 즉 커널에서 관리된다.


🔩 기능</br>

    - 귓속말
    - 아이디 변경
    - 참여 중인 멤버 목록 보기


패키지 구조</br>

    server.py
    client.py
    authenticator.py
    messenger.py
    repository.py

서버 실행

    python3 server.py --host [host] --port [port]

클라이언트 실행

    python3 client.py --host [host] --port [port]
