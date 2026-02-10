# 개발자 가이드

> [메인 README](./README.md) | [사용자 가이드](./README_USER.md) | **개발자 가이드**

프로젝트에 기여하거나 로컬에서 개발 환경을 구축하려는 개발자를 위한 문서입니다.

---

## 1. 시스템 아키텍처

```
┌─────────────────────────────────────────────┐
│           클라이언트 레이어                  │
├──────────────┬──────────────┬───────────────┤
│  웹 (React)  │  데스크톱    │  모바일 (PWA) │
│  :3000       │  (Electron)  │               │
└──────┬───────┴──────┬───────┴───────┬───────┘
       │ HTTPS        │               │
       └──────────────┼───────────────┘
                      ↕ REST / WebSocket
┌─────────────────────────────────────────────┐
│          FastAPI (:8000)                    │
├─────────────────────────────────────────────┤
│  /api/auth/*         JWT 인증               │
│  /api/reminders/*    일정 CRUD              │
│  /api/templates/*    템플릿 관리            │
│  /api/companies/*    회사·멤버 관리         │
│  /api/notifications/* 알림 조회             │
│  /ws/{company_id}    실시간 동기화          │
└──────────┬──────────────────┬───────────────┘
           ↕                  ↕
┌──────────────────┐ ┌───────────────────────┐
│  PostgreSQL 16   │ │  Redis 7              │
│  :5432           │ │  :6379                │
│  - users         │ │  - 세션 캐시          │
│  - companies     │ │  - WebSocket 메시지   │
│  - reminders     │ │                       │
│  - templates     │ │                       │
└──────────────────┘ └───────────────────────┘
```

---

## 2. 로컬 개발 환경

### 사전 요구사항

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (또는 Docker)
- Redis 7+ (또는 Docker)

### 방법 1: Docker로 DB만 실행

```bash
# PostgreSQL + Redis만 실행
docker-compose up -d postgres redis

# 백엔드
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 프론트엔드 (별도 터미널)
cd frontend
npm install
npm run dev
```

### 방법 2: 전체 Docker Compose

```bash
docker-compose up -d
# 웹: http://localhost:3000
# API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### 환경변수 (.env)

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/reminder
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/reminder
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
DEBUG=true
```

---

## 3. 프로젝트 구조 상세

```
backend/
├── app/
│   ├── main.py                  # FastAPI 앱 진입점, lifespan, WebSocket
│   ├── config.py                # pydantic-settings 기반 설정
│   ├── database.py              # SQLAlchemy async engine (lazy init)
│   │
│   ├── api/                     # API 라우터
│   │   ├── __init__.py          # 라우터 통합 등록
│   │   ├── auth.py              # POST register/login/refresh, GET me
│   │   ├── reminders.py         # CRUD + Excel export/import
│   │   ├── templates.py         # list/get/preview/apply
│   │   ├── companies.py         # 회사 목록, 멤버 CRUD
│   │   └── notifications.py     # summary/today/overdue/upcoming
│   │
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── user.py              # User (email, password_hash, name)
│   │   ├── company.py           # Company, CompanyMember, MemberRole
│   │   ├── reminder.py          # Reminder (deadline, completed, priority)
│   │   └── template.py          # Template, TemplateItem
│   │
│   ├── schemas/                 # Pydantic v2 스키마
│   │   ├── user.py              # UserCreate/Login/Response, Token, Company
│   │   ├── reminder.py          # ReminderCreate/Update/Response/List
│   │   └── template.py          # TemplateResponse, ApplyRequest/Response
│   │
│   ├── services/                # 비즈니스 로직
│   │   ├── auth_service.py      # register, authenticate, token 관리
│   │   ├── reminder_service.py  # CRUD + 접근 권한 검증
│   │   ├── template_engine.py   # 시스템 템플릿 정의, 일정 자동 생성
│   │   ├── holiday_service.py   # 한국 공휴일/대체공휴일/영업일 계산
│   │   ├── excel_service.py     # openpyxl 기반 Excel 처리
│   │   └── notification_service.py  # D-Day 알림 조회
│   │
│   └── utils/
│       ├── security.py          # bcrypt 해싱, PyJWT 토큰, get_current_user
│       └── websocket.py         # ConnectionManager (회사별 채널)
│
├── alembic/
│   ├── env.py                   # 마이그레이션 설정
│   └── versions/
│       └── 001_initial_schema.py  # 초기 테이블 생성
│
└── tests/
    ├── test_services.py         # 공휴일·템플릿·보안 테스트 (27개)
    └── test_api.py              # 스키마 검증 테스트 (10개)

frontend/
├── public/
│   ├── manifest.json            # PWA manifest
│   ├── sw.js                    # Service Worker (캐싱, 푸시)
│   └── vite.svg                 # Favicon
├── src/
│   ├── App.tsx                  # 라우팅, 테마, 인증 가드
│   ├── index.tsx                # React DOM 진입점
│   ├── types/index.ts           # 전체 TypeScript 인터페이스
│   ├── contexts/AuthContext.tsx  # 인증 상태 (login/register/logout)
│   ├── services/
│   │   ├── api.ts               # Axios + 인터셉터 (자동 토큰 갱신)
│   │   └── websocket.ts         # WebSocket 싱글톤 (자동 재연결)
│   ├── hooks/
│   │   ├── useReminders.ts      # 리마인더 CRUD + WS 동기화
│   │   └── useTemplates.ts      # 템플릿 목록/미리보기/적용
│   ├── components/
│   │   ├── Layout.tsx            # AppBar + Drawer 네비게이션
│   │   ├── ReminderCard.tsx      # 일정 카드 (D-Day, 우선순위)
│   │   ├── ReminderDialog.tsx    # 일정 생성/수정 다이얼로그
│   │   └── TemplateApplyDialog.tsx  # 템플릿 미리보기·적용
│   └── pages/
│       ├── LoginPage.tsx         # 로그인 폼
│       ├── RegisterPage.tsx      # 2단계 회원가입 (계정 → 회사)
│       ├── DashboardPage.tsx     # 대시보드 (통계, 필터, CRUD)
│       ├── CalendarPage.tsx      # 월간 캘린더 뷰
│       └── TemplatePage.tsx      # 템플릿 목록·적용
└── vite.config.ts               # Vite (프록시, 경로 별칭)

desktop/
├── main.js                      # Electron 메인 프로세스
├── preload.js                   # Context Bridge API
└── package.json                 # electron-builder 설정
```

---

## 4. 데이터베이스 ERD

```
users
├── id (UUID, PK)
├── email (VARCHAR 255, UNIQUE)
├── password_hash (VARCHAR 255)
├── name (VARCHAR 100)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
        │
        ├── 1:N ──→ companies (owner_id FK)
        │               ├── id (UUID, PK)
        │               ├── name (VARCHAR 200)
        │               ├── business_number (VARCHAR 20, UNIQUE)
        │               ├── created_at, updated_at
        │               │
        │               └── 1:N ──→ reminders
        │                               ├── id (UUID, PK)
        │                               ├── company_id (FK)
        │                               ├── title (VARCHAR 200)
        │                               ├── category (VARCHAR 50, INDEX)
        │                               ├── deadline (DATE, INDEX)
        │                               ├── original_deadline (DATE, NULL)
        │                               ├── completed (BOOLEAN)
        │                               ├── priority (INTEGER)
        │                               ├── template_id (FK → templates, NULL)
        │                               └── created_by (FK → users)
        │
        └── N:M ──→ company_members (user_id + company_id)
                        ├── role (ENUM: owner/admin/member/viewer)
                        └── joined_at (TIMESTAMP)

templates
├── id (UUID, PK)
├── name, description, category
├── is_system (BOOLEAN)
└── 1:N ──→ template_items
                ├── title, month, day
                ├── recurrence (once/monthly/quarterly)
                ├── adjust_for_holiday (BOOLEAN)
                └── extra_config (JSON)
```

---

## 5. API 명세

### 인증

| Method | Endpoint | Body | 응답 |
|--------|----------|------|------|
| POST | `/api/auth/register` | `{email, password, name}` | TokenResponse (access + refresh + user) |
| POST | `/api/auth/login` | `{email, password}` | TokenResponse |
| POST | `/api/auth/refresh` | `{refresh_token}` | TokenResponse |
| GET | `/api/auth/me` | — | UserResponse |
| POST | `/api/auth/companies` | `{name, business_number?}` | CompanyResponse |

### 일정 (Reminders)

| Method | Endpoint | 파라미터 | 설명 |
|--------|----------|---------|------|
| GET | `/api/reminders` | `company_id`, `page`, `page_size`, `category?`, `completed?`, `year?`, `month?` | 페이징된 일정 목록 |
| GET | `/api/reminders/{id}` | — | 일정 상세 |
| POST | `/api/reminders` | `company_id` (query), body: ReminderCreate | 일정 생성 |
| PUT | `/api/reminders/{id}` | body: ReminderUpdate | 일정 수정 |
| DELETE | `/api/reminders/{id}` | — | 일정 삭제 |
| GET | `/api/reminders/export/excel` | `company_id`, `year?`, `category?` | Excel 다운로드 |
| POST | `/api/reminders/import/excel` | `company_id`, file(multipart) | Excel 업로드 |

### 템플릿

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/templates` | 템플릿 목록 |
| GET | `/api/templates/{id}` | 템플릿 상세 (항목 포함) |
| POST | `/api/templates/preview` | 미리보기 (저장하지 않음) |
| POST | `/api/templates/apply` | 적용 → 리마인더 일괄 생성 |

### 회사·멤버

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/companies` | 내 회사 목록 |
| GET | `/api/companies/{id}/members` | 멤버 목록 |
| POST | `/api/companies/{id}/members` | 멤버 초대 (Owner/Admin만) |
| PUT | `/api/companies/{id}/members/{mid}` | 역할 변경 |
| DELETE | `/api/companies/{id}/members/{mid}` | 멤버 제거 |

### 알림

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/notifications/summary` | 오늘/지연/7일이내 요약 |
| GET | `/api/notifications/today` | 오늘 마감 목록 |
| GET | `/api/notifications/overdue` | 지연 일정 목록 |
| GET | `/api/notifications/upcoming?days=7` | N일 이내 마감 목록 |

### WebSocket

```
ws://localhost:8000/ws/{company_id}?token={access_token}
```

수신 메시지 형식:
```json
{
  "event": "created|updated|deleted|bulk_created",
  "entity": "reminder",
  "id": "uuid-or-null",
  "data": null
}
```

---

## 6. 핵심 비즈니스 로직

### 공휴일 계산 (`holiday_service.py`)

```python
# 양력 공휴일: 신정, 삼일절, 어린이날, 현충일, 광복절, 개천절, 한글날, 크리스마스
# 음력 공휴일: 설날(음력 1/1 ±1일), 부처님오신날(음력 4/8), 추석(음력 8/15 ±1일)
# 대체공휴일: 설날/추석 일요일 겹침, 어린이날 주말/공휴일 겹침, 삼일절/광복절/개천절/한글날(2021~)

get_korean_holidays(2026)  # → {date: name} dict (캐싱됨)
next_business_day(date)    # → 주말/공휴일이면 다음 영업일
last_business_day_of_month(2026, 1)  # → 1월 마지막 영업일
```

### 템플릿 엔진 (`template_engine.py`)

```python
SYSTEM_TEMPLATES = [
    {"name": "법정신고일", "items": [
        {"title": "1월분 원천세 신고·납부", "month": 2, "day": 10, "adjust_for_holiday": True},
        # ... 총 33개 항목
    ]},
    {"name": "급여 처리", "items": [...]},  # 24개 항목
    {"name": "HR 업무", "items": [...]},     # 17개 항목
]

generate_reminders_from_template(template_data, year=2026)
# → [{"title": "...", "deadline": date, "original_deadline": date|None, ...}]
```

### 인증 흐름

```
[클라이언트]                    [서버]
    │                              │
    ├── POST /auth/login ─────────→│ password 검증 → JWT 발급
    │← access(15min)+refresh(7d) ──┤
    │                              │
    ├── GET /reminders ────────────→│ Bearer token 검증
    │   Authorization: Bearer xxx  │
    │← 200 OK ─────────────────────┤
    │                              │
    ├── (15분 후 만료)             │
    ├── GET /reminders ────────────→│ 401 Unauthorized
    │← 401 ───────────────────────┤
    │                              │
    ├── POST /auth/refresh ────────→│ refresh token 검증
    │← 새 access + refresh ────────┤
    │                              │
    └── (Axios 인터셉터가 자동 처리)
```

---

## 7. 테스트

```bash
cd backend
pytest tests/ -v          # 전체 37개 테스트
pytest tests/ -v -k holiday  # 공휴일 테스트만
pytest tests/ -v -k template # 템플릿 테스트만
```

### 테스트 구성

| 파일 | 테스트 수 | 범위 |
|------|----------|------|
| `test_services.py` | 27 | 공휴일 계산(18), 템플릿 생성(7), 비밀번호 해싱(2) |
| `test_api.py` | 10 | Pydantic 스키마 검증 |

---

## 8. DB 마이그레이션

```bash
# 마이그레이션 적용
cd backend
alembic upgrade head

# 새 마이그레이션 생성
alembic revision --autogenerate -m "add_new_column"

# 롤백
alembic downgrade -1
```

초기 마이그레이션: `alembic/versions/001_initial_schema.py`

---

## 9. 배포

### Docker 빌드

```bash
# 백엔드
docker build -t reminder-backend ./backend

# 프론트엔드
docker build -t reminder-frontend ./frontend
```

### Electron 데스크톱

```bash
cd desktop
npm install
npm run build           # 현재 OS
npm run build:win       # Windows .exe
npm run build:mac       # macOS .dmg
npm run build:linux     # Linux .AppImage
```

### 환경별 주의사항

| 환경 | 주의 |
|------|------|
| Production | `SECRET_KEY` 반드시 변경, `DEBUG=false`, HTTPS 적용 |
| Database | `DATABASE_URL`에 connection pool 설정 고려 |
| Redis | 비밀번호 설정, persistence 활성화 |
| CORS | `CORS_ORIGINS`에 실제 도메인만 허용 |

---

## 10. 코드 컨벤션

- **Backend**: Python 3.11+ 타입 힌트, async/await, Pydantic v2 `model_validate`
- **Frontend**: TypeScript strict mode, 함수 컴포넌트 + Hooks, MUI sx prop
- **커밋**: conventional commits (feat/fix/docs/refactor)
- **시간대**: DB는 UTC 저장, 프론트엔드에서 KST 변환 (`date-fns` + `ko` locale)
