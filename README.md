# I/O multiplexing chatting program

#### 하나의 다중화 서버에서 다수의 클라이언트가 TCP로 통신할 수 있는 1:N 채팅 프로그램입니다. </br>초기 모델은 서버 다중화(multiplexing)를 위한 I/O system call로 select를 사용했으며, 이벤트 처리 효율 개선을 위해 kqueue로 고도화 했습니다.</br>
</br>

### ⚙️ 프로젝트 환경</br>

<img src="https://img.shields.io/badge/macOS-000000?style=flat&logo=macOS&logoColor=white"> </br>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=Python&logoColor=white"> 3.11.6</br>
<img src="https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=MySQL&logoColor=white"> 8.1.0</br>


</br>

### 💻 프로그램 실행 방법
1개의 server.py 파일과 N개의 client.py 파일을 실행시킵니다.</br> host와 port는 실행 인자로 전달함으로써 지정 가능합니다. (생략 시 default값: '127.0.0.1', 9993) 


    python3 server.py --host [서버 호스트 아이피] --port [서버 포트]
</br>

    python3 client.py --host [서버 호스트 아이피] --port [서버 포트]

</br></br>

### 📌 프로그램 기능</br>
* 클라이언트는 서버에 접속하여 클라이언트간의 메세지를 공유할 수 있음
* 클라이언트 최초 접속 시 입장할 채팅방 번호와 아이디를 입력. 아이디 중복 체크 후 통과하면 해당 채팅방에 접속
* 클라이언트의 아이디는 변경 가능
* 클라이언트는 같은 채팅방 안의 다른 클라이언트에게 귓속말을 할 수 있음
* 해당 채팅방 안의 모든 인원을 확인할 수 있음
* 채팅방 접속 시 접속 날짜에 해당하는 전체 채팅 내역을 확인할 수 있음</br>
&nbsp;&nbsp;단, 기존 이용자가 재 입장하는 경우라면 귓속말 내역까지 함께 출력

</br></br>

### 📝 프로젝트 관련 지식

#### I/O 모델 종류: 작업 순서(Sync/Async)와 작업 완료 대기 여부(Blocking/Non-Blocking)로 구분 </br>

'작업 순서'와 '대기 여부' 두 가지 특성은 독립적이므로 I/O 모델에는 Syncronous-Blocking, Syncronous-NonBlocking, Asyncronous-Blocking, Asyncronous-NonBlocing 4 종류가 존재합니다. </br>

* 작업 순서에 따른 구분
    * Sync: 작업 순서를 보장합니다. user space에서 작업 완료를 판단하므로 현재 작업에 대한 응답 시점과 다음 작업을 요청하는 시점이 일치합니다. 
    * Async: 작업 순서를 보장하지 않습니다. kernel의 작업이 완료되는 순서대로 call back 형식으로 동작합니다.

* 대기 여부에 따른 구분
    * Blocking: 요청한 I/O 작업에 대한 완료 시그널을 kernel로부터 받기 전까지 다른 작업을 하지 않고 기다립니다.
    * Non-Blocking: kernel에 I/O 작업을 요청한 후 기다리지 않고 다른 작업을 합니다. (polling으로 대기 중에 작업 상태 확인은 가능).
    
    </br></br>

#### multiplexing은 Asyncronous - Blocking 영역에 해당됨</br>

💡 system call의 실제적인 이벤트 처리에 있어서는 하나의 FD의 I/O 작업이 완료되어야 다음 FD의 작업으로 넘어가기 때문에 동기적으로 동작(Syncronous)합니다. 또한 user space에서의 I/O 작업 자체는 Block되지 않으므로 multiplexing을 무조건 Asyncronous - Blocking 모델이라고 단정지을 수는 없습니다. 하지만 큰 틀에서 보면 예측 불가능하게 인입되는 다수의 클라이언트의 요청을 '비동기적'으로(Asyncronous) 수행하며, I/O system call에 대한 kernel의 응답은 'Block'됩니다.

</br></br>

#### multiplexing 종류: FD 관리 방법 및 관리 주체에 따라 크게 두 가지로 구분 </br>

① select, pselect, poll, ppoll</br>
user 레벨에서 FD 상태를 감시하는 라이브러리이며 관심 있는 FD를 모두 관리 대상으로 등록해놓습니다. 이벤트 발생 시 해당 FD를 찾기 위해 loop를 순환합니다.</br> 
    ∴ 시간복잡도는 O(n) 입니다. </br> 

- select: 이벤트 발생 시마다 관리하는 모든 FD를 검사하는 원초적 방식, 최대로 관리 가능한 FD의 개수는 1024개
- pselect: select의 timeout 정밀도와 signal 처리 로직이 개선된 버전
- poll: 이벤트 발생한 FD의 개수만큼만 검사, select는 하나의 이벤트 처리에 3bit를 사용하는 반면 poll은 64bit를 사용하므로 FD 수가 많아질수록 select보다 비효율적, 관리 가능한 FD 개수는 무제한
- ppoll: poll의 timeout 정밀도와 signal 처리 로직이 개선된 버전 </br>  </br> 


② epoll, kqueue, IOCP, devpoll </br>
I/O 성능 문제를 개선하기 위해 FD 상태를 kernel 레벨에서 관리합니다. 운영체제에서 상태 변경을 감지하는 라이브러리이기 때문에 운영체제별로 사용할 수 있는 라이브러리가 정해져 있습니다. I/O system call 반환값으로 이벤트가 발생한 FD리스트를 받을 수 있습니다. </br> 
    ∴ 시간복잡도가 O(1)로 줄어듭니다. </br> 

- epoll(Linux)
- kqueue(OpenBSD)
- IOCP(I/O completion port)(Windows)
- devpoll(Solaris)
