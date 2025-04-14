<a name="top"></a>
[![Legacy project](![lawmang](https://github.com/user-attachments/assets/89d9e9ef-fea7-48ea-a545-15ef7f3d0b5b)
)]

![JavaScript Badge](https://img.shields.io/badge/JavaScript-ES6+-yellow?logo=javascript&logoColor=white&style=flat)
![Python Badge](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white&style=flat)
![OS](https://img.shields.io/badge/OS-ubuntu%2C%20windows-0078D4)
![Deployment](https://img.shields.io/badge/Deployment-AWS%20%2B%20Vercel-orange?logo=amazonaws&logoColor=white&style=flat)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue?logo=postgresql&logoColor=white&style=flat)
![API](https://img.shields.io/badge/API-Google%20Maps-4285F4?logo=googlemaps&logoColor=white&style=flat)
![Environment](https://img.shields.io/badge/Environment-Anaconda-yellowgreen?logo=anaconda&logoColor=white&style=flat)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Redux%20%2B%20TailwindCSS-blue?logo=react&logoColor=white&style=flat)
![Backend](https://img.shields.io/badge/Backend-Node.js%20%2B%20Express-green?logo=nodedotjs&logoColor=white&style=flat)
![IDE](https://img.shields.io/badge/IDE-VS%20Code%20%2B%20Cursor.ai-blue?logo=visualstudiocode&logoColor=white&style=flat)
![GitHub](https://img.shields.io/badge/Version%20Control-GitHub-black?logo=github&logoColor=white&style=flat)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=githubactions&logoColor=white&style=flat)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-GPT--4o-brightgreen.svg?logo=OpenAI&logoColor=white)](https://openai.com/)

## 목차

- [설명](#-설명)
- [구성](#-구성)
- [개발환경](#-개발환경설정)
- [개발로그](#-개발로그)
- [디버깅로그](#-디버깅로그)
- [랭체인 구성](#-랭체인)
- [자료](#-자료)
- [연락처](#%EF%B8%8F-연락처)

## 🏛️ 설명

**유산지기**: 국가 문화재,행사 알림 서비스

- **구글 맵 지원**:사용자 위치 기반 문화재 정보 제공
- **챗봇**:  사용자 질문에 실시간으로 응답하고, 관심 있는 문화재 정보를 제공,
  문화재 검색 및 행사 일정 알림
- **데이터관리**: 문화재 및 행사 데이터의 효율적 저장 및 업데이트
- **유지보수**: 시스템 안정성 확보 및 정기적 업데이트를 통한 최적화

## 🎓 구성

| **기능**            | **설명**                                  | **주요 파일**                                                             |
|---------------------|------------------------------------------|---------------------------------------------------------------------------|
| **챗봇**            | 챗봇 기능 제공 및 벡터 캐시 관리          | `Chatbot.py`, `Vector_cache`                                             |
| **컨트롤러**        | 계정 및 행사/문화재 관련 비즈니스 로직관리 | `accountController.js`, `eventController.js`                             |
| **데이터베이스**    | 데이터베이스 연결 및 설정 관리            | `Database.js`                                                            |
| **라우트**          | 계정, 행사/문화재, 데이터베이스 라우팅 처리| `accountRoutes.js`, `eventRoutes.js`, `postgresSQLRoutes.js`             |
| **유틸리티**        | 공통 유틸리티 함수 및 인증 처리           | `apiUtils.js`, `Authenticate.js`                                         |

## 💻 개발환경설정

```shell
# 터미널 열기(Command Prompt or PowerShell for Windows, Terminal for macOS or Linux)

# Git 클론
git clone https://github.com/noseunghyeon/test_front.git front
git clone https://github.com/noseunghyeon/test_back.git back

# back/front터미널 npm install
cd front
npm install
cd back
npm install

#posgresql 연결 확인 (.env체크)

#conda 환경 체크(requirements.txt 참조)

conda create -n chat_env python=3.8 -y
conda activate chat_env
conda install pip
pip install -r requirements.txt
python -c "import openai; print('Environment is ready.')"

# frontend backend 구동
npm start
```

## 📝 개발로그

## 노승현

### 2024-11-23

- Google Maps API 연동 완료
  - 지도 기본 기능 구현
  - API 키 설정 및 초기 세팅

### 2024-11-28

- Heritage 위치 정보 시스템 구현 완료
  - 문화유산 위치 데이터 통합
  - 지도상 문화유산 마커 표시 기능

### 2024-12-03

- 모달-지도 연동 기능 구현 완료
  - 모달 클릭 시 해당 위치로 지도 이동 기능 추가
  - 사용자 인터페이스 개선

### 2024-12-17

- Chatbot 기능 구현 완료
  - 사용자 질문-응답 시스템 구축
  - 대화형 인터페이스 개발

## 박준호

### 2024-11-27
- Backend 개발용 엔드포인트 작성
  - 외부 API 활용 개발용 엔드포인트 작성
    
### 2024-12-03

- Backend 외부 API 연동 완료
  - 외부 서비스 연동
  - API 통신 로직 구현
  - 데이터 처리 파이프라인 구축

### 2024-12-06

- 사용자 인증 시스템 구현 완료
  - 계정 관리 기능 구현
  - 보안 강화 작업 완료
  - 사용자 권한 관리 시스템 구축(SQL)

### 2024-12-13

- 데이터베이스 구조 설계 및 구현 완료
  - ERD 설계 완료
  - REST API 엔드포인트 정의
  - SQL 쿼리 작성 완료 및 데이터 관리 시스템 구축(외부 API -> SQL관리)

### 2024-12-24

- Backend 서버 배포 및 운영 환경 구축 완료
  - Cloud 서버 배포 완료
  - 서버 성능 최적화

## 천서영

### 2024-11-26

- Search Bar 구현 완료
  - 검색창 UI 설계
  - 검색 기능 로직 구현
  - 자동완성 기능 추가

### 2024-11-29

- 검색 결과 모달 구현 완료
  - 검색 결과 표시 UI 설계
  - 모달 인터페이스 구현
  - 검색 결과 출력 로직 구현

### 2024-12-12

- 즐겨찾기 기능 구현 완료
  - 문화유산 즐겨찾기 추가/제거 기능
  - 즐겨찾기 목록 관리 시스템

### 2024-12-28

- 마이페이지 기능 구현 완료
  - 사용자 프로필 페이지 설계
  - 개인화 설정 기능 구현
  - 사용자 활동 내역 조회 기능

## 정지원

### 2024-11-27

- 행사일정 UI 설계 완료
  - 사용자 친화적 인터페이스 구현

### 2024-11-28

- 캘린더 작업 완료
  - 행사 일정 표시 및 관리 기능 구현

### 2024-12-02

- Event Modal 구현 완료
  - 행사 상세 정보 표시 기능
- Regions Button 구현 완료
  - 지역별 필터링 기능 추가

### 2024-12-13

- 즐겨찾기 기능 구현 완료
  - 사용자 맞춤 행사 저장 기능

## 윤금조

### 2024-11-25

- Nav Bar UI 설계 완료
  - 메인 네비게이션 구조 구현

### 2024-11-27

- Swiper Slide 설계 완료
  - 메인 페이지 슬라이드 기능 구현

### 2024-11-28

- ScrollToTop 버튼 설계 완료
  - 페이지 상단 이동 기능 구현

### 2024-12-02

- Chat bot 이동 버튼 설계 완료
  - 챗봇 접근성 개선

### 2024-12-19

- RecentItems 설계 완료
  - 최근 조회 항목 표시 기능

## 설송이

### 2024-12-02

- 로그인 기능 구현 완료
  - 사용자 인증 시스템 구축
- 회원가입 기능 구현 완료
  - 신규 사용자 등록 시스템 구현

### 2024-12-04

- My Page 회원 정보 기능 구현 완료
  - 사용자 프로필 관리 기능
  - 개인정보 수정 기능

## 📚 디버깅로그

```
(python 환경)
2024-12-24 11:58:33.085 [info] [Info  - 11:58:33 AM] (7832) Assuming Python version 3.12.7.final.0
2024-12-24 11:58:33.426 [info] [Error - 11:58:33 AM] (7832) File or directory "<default workspace root>" does not exist.
2024-12-24 11:58:33.426 [info] [Info  - 11:58:33 AM] (7832) No source files found.
----------------------------------------------------------------
(github action)
Run eval "$($HOME/miniconda/bin/conda shell.bash hook)"
  eval "$($HOME/miniconda/bin/conda shell.bash hook)"
  conda activate myenv
  if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
  shell: /usr/bin/bash -e {0}
EnvironmentNameNotFound: Could not find conda environment: myenv
You can list all discoverable environments with `conda info --envs`.
----------------------------------------------------------------
```

## **EC2에서 Miniconda 확인하기 (1. myenv 확인, 2.Windows에서 Linux로 전환 체크)**

1. **Miniconda 환경설정**:

   - SSH를 통해 EC2 서버에 접속 후 다음 명령 실행:
     conda info --envs

   
     결과: 없음

     conda create -n myenv python=3.12.7 (나중에는 워크플로 수정)

     
     결과: myenv 생성

2.  라우팅 Linux화 
   ```javascript
   // Python 경로 및 스크립트 경로 설정
   const pythonPath = path.join(
   "/home/ubuntu/miniconda",
   "envs",
   "myenv",
   "bin",
   "python3"
   );
   const scriptPath = path.join(__dirname, "chatbot", "chatbot.py");

   let answer = "";
```
  *결과: chatbot 연결 확인*


```yaml
    - name: Create Conda Environment
  run: |
    eval "$($HOME/miniconda/bin/conda shell.bash hook)"
    conda create -n myenv python=3.12.7 || echo "Environment already exists."

```
 *문제해결: 다른환경에도 작동하게 Github Actions yml 에 myenv 생성 명령어 추가* 

## 🦜 랭체인

## RAG 체인 구현
```python
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```
- retriever: 벡터 데이터베이스에서 관련 컨텍스트를 검색.
- RunnablePassthrough: 사용자의 질문을 체인에 전달.
- prompt: 검색된 컨텍스트와 질문을 결합하여 모델 입력 생성.
- llm: GPT 모델을 통해 답변 생성.
- StrOutputParser: 생성된 응답을 문자열 형태로 반환.

```
## 사용된 기술
# LangChain: RAG 체인을 구축하고 실행하기 위한 라이브러리.
# OpenAI GPT-3.5: 자연어 이해 및 응답 생성.
# FAISS 벡터 데이터베이스: 빠르고 효율적인 문서 검색.
# Python 3.x: 애플리케이션 개발 언어.
```

## 📃 자료

- [PPT자료](https://github.com/user-attachments/files/18289140/PPT.pptx)
- [erd클라우드](https://www.erdcloud.com/d/x7FB5qMQ6fxk5oGMv/)
- [(개인 보고서)시스템 목적 및 기술적 구현.docx](https://github.com/user-attachments/files/18248740/default.docx)


## 🗨️ 연락처

Legacy Project와 관련된 문의, 서비스, 정보에 대해 더 알고 싶으시면 언제든지 저희에게 문의하세요. 지원을 제공하고 모든 질문에 답변드릴 준비가 되어 있습니다. 아래는 저희 팀과 연락할 수 있는 방법입니다:

- **이메일**: 문의/지원 [support@legacy.com](mailto:qkrwns982@gmail.com).
- **웹사이트**: 유산사이트(https://test-front-lovat.vercel.app).
- **기타문의**: 카카오 플러스

[Back to top](#top)
