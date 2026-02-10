# 경리 업무 리마인더

**클라우드 동기화 기반 자동 일정 관리 시스템**

세무사, 경리, HR 담당자를 위한 법정 신고일·급여·인사 업무 리마인더입니다.
템플릿 선택만으로 연간 일정이 자동 생성되며, 공휴일·대체공휴일·주말을 자동 조정합니다.

> **다른 문서 보기**
> - [사용자 가이드 (README_USER.md)](./README_USER.md) — 설치 없이 바로 사용하는 방법, 화면별 기능 설명
> - [개발자 가이드 (README_DEV.md)](./README_DEV.md) — 아키텍처, API 명세, 로컬 개발 환경 구축

---

## 이 프로젝트는 무엇인가요?

매월 반복되는 경리·세무·HR 업무 일정을 **수동으로 관리하지 않아도** 되는 시스템입니다.

- 연간 법정신고일(원천세, 4대보험, 부가세, 법인세 등)을 **한 번의 클릭**으로 자동 생성
- 마감일이 공휴일·주말이면 **다음 영업일로 자동 조정**
- 웹·데스크톱·모바일(PWA) 어디서든 접근 가능
- 팀원 간 일정을 **실시간 공유**

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **템플릿 자동 생성** | 법정신고일, 급여 처리, HR 업무 등 사전 정의된 템플릿 선택 → 연간 일정 일괄 생성 |
| **공휴일 자동 조정** | 한국 공휴일·대체공휴일·설날·추석(음력) 포함, 주말/공휴일 마감일 → 다음 영업일 자동 이동 |
| **실시간 동기화** | WebSocket 기반 — 한 기기에서 수정하면 모든 기기에 즉시 반영 |
| **Excel 연동** | 일정 데이터를 Excel로 내보내기/가져오기 (서식·색상 포함) |
| **알림** | D-Day 알림, 마감 임박 경고, 지연 일정 알림 |
| **팀 협업** | 회사별 멤버 초대, 역할(Owner/Admin/Member/Viewer) 기반 권한 관리 |
| **PWA 지원** | 모바일 홈 화면 추가, 오프라인 캐싱, 푸시 알림 |

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Redis 7 |
| Frontend | React 18 · TypeScript 5 · Material-UI 5 · Vite |
| Desktop | Electron 28 |
| Mobile | PWA (Service Worker · Web Push) |
| Infra | Docker Compose · Nginx |

---

## 빠른 시작

### Docker Compose (가장 간단)

```bash
git clone <repository-url>
cd reminder
docker-compose up -d
```

| 서비스 | URL |
|--------|-----|
| 웹 앱 | http://localhost:3000 |
| API 서버 | http://localhost:8000 |
| API 문서 (Swagger) | http://localhost:8000/docs |

### 로컬 개발

```bash
# 백엔드
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# 프론트엔드
cd frontend
npm install
npm run dev
```

자세한 설정은 [개발자 가이드](./README_DEV.md)를 참고하세요.

---

## 프로젝트 구조

```
├── backend/                # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # REST API 라우터
│   │   ├── models/         # SQLAlchemy ORM 모델
│   │   ├── schemas/        # Pydantic 요청/응답 스키마
│   │   ├── services/       # 비즈니스 로직 (템플릿 엔진, 공휴일, Excel, 알림)
│   │   └── utils/          # 보안(JWT), WebSocket 관리
│   ├── alembic/            # DB 마이그레이션
│   └── tests/              # 단위 테스트 (37개)
├── frontend/               # React + TypeScript + MUI
│   ├── public/             # PWA (manifest, service worker)
│   └── src/
│       ├── components/     # 재사용 UI 컴포넌트
│       ├── pages/          # 페이지 (대시보드, 캘린더, 템플릿)
│       ├── services/       # API·WebSocket 클라이언트
│       ├── hooks/          # 커스텀 React 훅
│       └── contexts/       # 전역 상태 (인증)
├── desktop/                # Electron 데스크톱 앱
├── shared/                 # 공통 상수
└── docker-compose.yml      # 전체 스택 실행
```

---

## 시스템 템플릿

### 법정신고일 (33건/연)
원천세(매월 10일), 4대보험(매월 15일), 부가세(분기 25일), 법인세(3/31), 종합소득세(5/31), 지방소득세, 연말정산

### 급여 처리 (24건/연)
급여 지급(매월 마지막 영업일), 급여 확정(지급 3영업일 전)

### HR 업무 (17건/연)
4대보험 취득/상실(매월), 연차 점검(분기별), 근로계약 갱신(12월)

---

## 라이선스

MIT License
