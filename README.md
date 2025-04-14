<a name="top"></a>
![lawmang](https://github.com/user-attachments/assets/bf5ca45e-9eb9-4aef-9109-fc353d6f5808)

![Python Badge](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white&style=flat)
![OS](https://img.shields.io/badge/OS-ubuntu%2C%20windows-0078D4)
![Deployment](https://img.shields.io/badge/Deployment-AWS%20%2B%20Vercel-orange?logo=amazonaws&logoColor=white&style=flat)
![Uvicorn](https://img.shields.io/badge/Server-uvicorn-%2337c2b1?logo=fastapi&logoColor=white&style=flat)
![LangChain](https://img.shields.io/badge/Framework-LangChain-%231a73e8?logo=langchain&logoColor=white&style=flat)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Elasticsearch-blue?logo=postgresql&logoColor=white&style=flat)
![API](https://img.shields.io/badge/API-Tavily%20%26%20Firecrawl-orange?logo=api&logoColor=white&style=flat)
![Environment](https://img.shields.io/badge/Environment-Anaconda-yellowgreen?logo=anaconda&logoColor=white&style=flat)
![IDE](https://img.shields.io/badge/IDE-VS%20Code%20%2B%20Cursor.ai-blue?logo=visualstudiocode&logoColor=white&style=flat)
![GitHub](https://img.shields.io/badge/Version%20Control-GitHub-black?logo=github&logoColor=white&style=flat)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=githubactions&logoColor=white&style=flat)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-GPT--3.5turbo-brightgreen.svg?logo=OpenAI&logoColor=white)](https://openai.com/)

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

**Lawmang**: AI 변호사 서비스

- **딥 리서치**: 나도 모르겠음 다른사람이 작성 
- **변호사 상담 챗봇**: Re-act적인 3.5turbo 로 탄탄한 plan 을 가지고 상담을 하는 AI 변호사   
- **데이터연결**:  API firecrawl/ tavily_search +  SQL_trgm + NOSQL Elastic_search + 자체 훈련 faiss   
- **유지보수**: 정기적인 업데이트 실시, 점검

## 🎓 구성

| **기능**            | **설명**                                  | **주요 파일**                                                             |
|---------------------|------------------------------------------|---------------------------------------------------------------------------|
| **AI 어시스턴스**   | 사이트 주력 AI 서비스들                   | `Chatbot`,`Chatbot_term`, `deepresearch`,                                |
| **데이터베이스**    | 데이터베이스 연결 및 설정 관리            | `core/database.py`, `services/*.py`                                        |
| **라우트**          | 계정, 라우팅 처리| `accountRoutes.js`, `eventRoutes.js`, `postgresSQLRoutes.js`             |

## 💻 개발환경설정

```shell
# Git 클론
- Lawmag > backend > 안 쪽에 가상환경 설정
conda create --prefix C:/conda_envs/lawmang_env python=3.11

- 가상환경 활성화
conda activate C:/conda_envs/lawmang_env

- 패키지 설치
pip install -r requirements.txt

# FastAPI 터미널에서 실행 (uvicorn 사용)
uvicorn app.main:app --reload

# 기본 api 확인
localhost:8000
```

## 📝 개발로그

## 개인이 알아서 추가 

## 📚개발 플로우 

## 이따가 추가 


## 🦜 랭체인

## RAG 체인 구현

## 📃 자료

- [PPT자료]()
- [erd클라우드]()
- [(개인 보고서)시스템 목적 및 기술적 구현.docx]()


## 🗨️ 연락처

Lawmang service와 관련된 문의, 서비스, 정보에 대해 더 알고 싶으시면 언제든지 저희에게 문의하세요. 지원을 제공하고 모든 질문에 답변드릴 준비가 되어 있습니다. 아래는 저희 팀과 연락할 수 있는 방법입니다:

- **이메일**: 문의/지원 [support@legacy.com](mailto:qkrwns982@gmail.com).
- **웹사이트**: 유산사이트().
- **기타문의**: 카카오 플러스

[Back to top](#top)
