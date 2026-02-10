# 경리 업무 리마인더

클라우드 동기화 기반 자동 일정 관리 시스템

세무사, 경리, HR 담당자를 위한 법정 신고일·급여·인사 업무 리마인더입니다.
템플릿 선택만으로 연간 일정이 자동 생성되며, 공휴일·대체공휴일·주말을 자동 조정합니다.

## 주요 기능

- **템플릿 자동 생성**: 법정신고일(원천세·4대보험·부가세·법인세 등), 급여 처리, HR 업무 템플릿
- **공휴일 자동 조정**: 한국 공휴일·대체공휴일·주말 → 다음 영업일로 마감일 자동 이동
- **실시간 동기화**: WebSocket 기반 다중 클라이언트 동기화
- **Excel 연동**: 일정 데이터 Excel 가져오기/내보내기
- **JWT 인증**: Access Token(15분) + Refresh Token(7일) 기반 보안

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 16, Redis 7 |
| Frontend | React 18, TypeScript 5, Material-UI 5, Vite |
| Desktop | Electron |
| Infra | Docker Compose, Nginx |

## 프로젝트 구조

```
├── backend/           # FastAPI 백엔드
│   ├── app/
│   │   ├── api/       # API 라우터 (auth, reminders, templates)
│   │   ├── models/    # SQLAlchemy 모델
│   │   ├── schemas/   # Pydantic 스키마
│   │   ├── services/  # 비즈니스 로직
│   │   └── utils/     # 보안, WebSocket
│   ├── alembic/       # DB 마이그레이션
│   └── tests/         # 테스트 (37개)
├── frontend/          # React + TypeScript
│   └── src/
│       ├── components/  # Layout, ReminderCard, Dialog 등
│       ├── pages/       # Dashboard, Calendar, Template
│       ├── services/    # API, WebSocket 클라이언트
│       ├── hooks/       # useReminders, useTemplates
│       └── contexts/    # AuthContext
├── desktop/           # Electron 데스크톱 앱
├── shared/            # 공통 상수
└── docker-compose.yml
```

## 빠른 시작

### Docker Compose (권장)

```bash
docker-compose up -d
```

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 로컬 개발

**백엔드:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 환경변수 설정
uvicorn app.main:app --reload
```

**프론트엔드:**
```bash
cd frontend
npm install
npm run dev
```

**테스트:**
```bash
cd backend
pytest tests/ -v
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| POST | /api/auth/refresh | 토큰 갱신 |
| GET | /api/reminders | 일정 목록 (필터, 페이징) |
| POST | /api/reminders | 일정 생성 |
| PUT | /api/reminders/{id} | 일정 수정 |
| DELETE | /api/reminders/{id} | 일정 삭제 |
| GET | /api/templates | 템플릿 목록 |
| POST | /api/templates/preview | 템플릿 미리보기 |
| POST | /api/templates/apply | 템플릿 적용 (일정 자동 생성) |
| GET | /api/reminders/export/excel | Excel 내보내기 |
| POST | /api/reminders/import/excel | Excel 가져오기 |
| WS | /ws/{company_id} | 실시간 동기화 |

## 시스템 템플릿

### 법정신고일
원천세(매월 10일), 4대보험(매월 15일), 부가세(분기), 법인세(3/31), 종합소득세(5/31) 등 — 공휴일 자동 조정

### 급여 처리
급여 지급(매월 마지막 영업일), 급여 확정(지급 3영업일 전)

### HR 업무
4대보험 취득/상실(매월 15일), 연차 점검(분기별), 근로계약 갱신(12월)

## 환경변수

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/reminder
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```
