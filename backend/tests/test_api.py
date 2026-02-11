"""API 엔드포인트 통합 테스트.

SQLite in-memory DB와 httpx AsyncClient를 사용한 실제 엔드포인트 테스트입니다.
"""
import pytest
from uuid import uuid4
from datetime import date, datetime

pytestmark = pytest.mark.asyncio


class TestHealthCheck:
    """헬스체크 엔드포인트 테스트."""

    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """인증 API 엔드포인트 테스트."""

    async def test_register_success(self, client):
        resp = await client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "password123",
            "name": "신규유저",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["name"] == "신규유저"

    async def test_register_duplicate_email(self, client):
        # First registration
        await client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "password123",
            "name": "첫번째",
        })
        # Duplicate registration
        resp = await client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "password456",
            "name": "두번째",
        })
        assert resp.status_code == 409

    async def test_login_success(self, client):
        # Register first
        await client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "password123",
            "name": "로그인유저",
        })
        # Login
        resp = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client):
        await client.post("/api/auth/register", json={
            "email": "wrongpw@example.com",
            "password": "password123",
            "name": "유저",
        })
        resp = await client.post("/api/auth/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    async def test_refresh_token(self, client):
        # Register to get tokens
        reg_resp = await client.post("/api/auth/register", json={
            "email": "refresh@example.com",
            "password": "password123",
            "name": "리프레시유저",
        })
        refresh_token = reg_resp.json()["refresh_token"]

        # Use refresh token
        resp = await client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    async def test_get_me(self, client):
        # Register to get token
        reg_resp = await client.post("/api/auth/register", json={
            "email": "me@example.com",
            "password": "password123",
            "name": "미유저",
        })
        token = reg_resp.json()["access_token"]

        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@example.com"

    async def test_get_me_no_auth(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    async def test_create_company(self, client):
        # Register
        reg_resp = await client.post("/api/auth/register", json={
            "email": "company@example.com",
            "password": "password123",
            "name": "회사유저",
        })
        token = reg_resp.json()["access_token"]

        resp = await client.post("/api/auth/companies", json={
            "name": "테스트 주식회사",
            "business_number": "111-22-33333",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "테스트 주식회사"
        assert data["business_number"] == "111-22-33333"


class TestReminderEndpoints:
    """리마인더 API 엔드포인트 테스트."""

    async def _setup(self, client):
        """테스트 사용자와 회사를 생성하고 토큰과 company_id를 반환합니다."""
        email = f"reminder_{uuid4().hex[:8]}@example.com"
        reg = await client.post("/api/auth/register", json={
            "email": email,
            "password": "password123",
            "name": "리마인더유저",
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        company_resp = await client.post("/api/auth/companies", json={
            "name": "리마인더회사",
        }, headers=headers)
        company_id = company_resp.json()["id"]

        return headers, company_id

    async def test_create_and_list_reminders(self, client):
        headers, company_id = await self._setup(client)

        # Create
        resp = await client.post(
            f"/api/reminders?company_id={company_id}",
            json={
                "title": "원천세 신고",
                "category": "세금",
                "deadline": "2026-03-10",
                "priority": 2,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        reminder = resp.json()
        assert reminder["title"] == "원천세 신고"
        assert reminder["category"] == "세금"
        assert reminder["completed"] is False
        reminder_id = reminder["id"]

        # List
        resp = await client.get(
            f"/api/reminders?company_id={company_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == reminder_id

    async def test_get_reminder_detail(self, client):
        headers, company_id = await self._setup(client)

        create_resp = await client.post(
            f"/api/reminders?company_id={company_id}",
            json={"title": "상세조회", "category": "기타", "deadline": "2026-04-01"},
            headers=headers,
        )
        reminder_id = create_resp.json()["id"]

        resp = await client.get(f"/api/reminders/{reminder_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "상세조회"

    async def test_update_reminder(self, client):
        headers, company_id = await self._setup(client)

        create_resp = await client.post(
            f"/api/reminders?company_id={company_id}",
            json={"title": "수정전", "category": "기타", "deadline": "2026-05-01"},
            headers=headers,
        )
        reminder_id = create_resp.json()["id"]

        resp = await client.put(
            f"/api/reminders/{reminder_id}",
            json={"title": "수정후", "completed": True},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "수정후"
        assert data["completed"] is True
        assert data["completed_at"] is not None

    async def test_delete_reminder(self, client):
        headers, company_id = await self._setup(client)

        create_resp = await client.post(
            f"/api/reminders?company_id={company_id}",
            json={"title": "삭제대상", "category": "기타", "deadline": "2026-06-01"},
            headers=headers,
        )
        reminder_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/reminders/{reminder_id}", headers=headers)
        assert resp.status_code == 204

        # Verify deleted
        resp = await client.get(f"/api/reminders/{reminder_id}", headers=headers)
        assert resp.status_code == 404

    async def test_list_with_filters(self, client):
        headers, company_id = await self._setup(client)

        # Create multiple reminders
        for i in range(3):
            await client.post(
                f"/api/reminders?company_id={company_id}",
                json={"title": f"세금 {i}", "category": "세금", "deadline": f"2026-0{i+1}-10"},
                headers=headers,
            )
        await client.post(
            f"/api/reminders?company_id={company_id}",
            json={"title": "HR 업무", "category": "HR", "deadline": "2026-01-15"},
            headers=headers,
        )

        # Filter by category
        resp = await client.get(
            f"/api/reminders?company_id={company_id}&category=세금",
            headers=headers,
        )
        assert resp.json()["total"] == 3

        # Filter by year and month
        resp = await client.get(
            f"/api/reminders?company_id={company_id}&year=2026&month=1",
            headers=headers,
        )
        assert resp.json()["total"] == 2  # 세금 0 + HR 업무

    async def test_unauthorized_access(self, client):
        resp = await client.get("/api/reminders?company_id=" + str(uuid4()))
        assert resp.status_code in (401, 403)

    async def test_export_excel(self, client):
        headers, company_id = await self._setup(client)

        await client.post(
            f"/api/reminders?company_id={company_id}",
            json={"title": "엑셀테스트", "category": "기타", "deadline": "2026-01-10"},
            headers=headers,
        )

        resp = await client.get(
            f"/api/reminders/export/excel?company_id={company_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]


class TestTemplateEndpoints:
    """템플릿 API 엔드포인트 테스트."""

    async def _setup(self, client):
        email = f"tpl_{uuid4().hex[:8]}@example.com"
        reg = await client.post("/api/auth/register", json={
            "email": email, "password": "password123", "name": "템플릿유저",
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        company_resp = await client.post("/api/auth/companies", json={
            "name": "템플릿회사",
        }, headers=headers)
        company_id = company_resp.json()["id"]
        return headers, company_id

    async def test_list_templates(self, client):
        headers, _ = await self._setup(client)
        resp = await client.get("/api/templates", headers=headers)
        assert resp.status_code == 200
        templates = resp.json()
        assert len(templates) >= 3  # 최소 3개 시스템 템플릿

        # Check template structure
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "category" in t
            assert "items" in t

    async def test_get_template_detail(self, client):
        headers, _ = await self._setup(client)
        list_resp = await client.get("/api/templates", headers=headers)
        template_id = list_resp.json()[0]["id"]

        resp = await client.get(f"/api/templates/{template_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == template_id
        assert len(data["items"]) > 0

    async def test_preview_template(self, client):
        headers, company_id = await self._setup(client)
        list_resp = await client.get("/api/templates", headers=headers)
        template_id = list_resp.json()[0]["id"]

        resp = await client.post("/api/templates/preview", json={
            "template_id": template_id,
            "company_id": company_id,
            "year": 2026,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2026
        assert data["generated_count"] > 0
        assert len(data["reminders"]) == data["generated_count"]

        # Check each reminder has required fields
        for r in data["reminders"]:
            assert "title" in r
            assert "deadline" in r
            assert "category" in r

    async def test_apply_template(self, client):
        headers, company_id = await self._setup(client)
        list_resp = await client.get("/api/templates", headers=headers)
        template_id = list_resp.json()[0]["id"]

        resp = await client.post("/api/templates/apply", json={
            "template_id": template_id,
            "company_id": company_id,
            "year": 2026,
        }, headers=headers)
        assert resp.status_code == 200
        created_reminders = resp.json()
        assert isinstance(created_reminders, list)
        assert len(created_reminders) > 0

        # Verify reminders were actually created in DB
        reminders_resp = await client.get(
            f"/api/reminders?company_id={company_id}&page_size=100",
            headers=headers,
        )
        assert reminders_resp.json()["total"] == len(created_reminders)


class TestCompanyEndpoints:
    """회사 API 엔드포인트 테스트."""

    async def _setup(self, client):
        email = f"comp_{uuid4().hex[:8]}@example.com"
        reg = await client.post("/api/auth/register", json={
            "email": email, "password": "password123", "name": "회사유저",
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        company_resp = await client.post("/api/auth/companies", json={
            "name": "테스트회사",
        }, headers=headers)
        company_id = company_resp.json()["id"]
        return headers, company_id, email

    async def test_list_companies(self, client):
        headers, company_id, _ = await self._setup(client)
        resp = await client.get("/api/companies", headers=headers)
        assert resp.status_code == 200
        companies = resp.json()
        assert len(companies) >= 1
        assert any(c["id"] == company_id for c in companies)

    async def test_list_members(self, client):
        headers, company_id, email = await self._setup(client)
        resp = await client.get(f"/api/companies/{company_id}/members", headers=headers)
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) == 1
        assert members[0]["role"] == "owner"
        assert members[0]["user_email"] == email

    async def test_invite_member(self, client):
        headers, company_id, _ = await self._setup(client)

        # Register another user
        new_email = f"new_{uuid4().hex[:8]}@example.com"
        await client.post("/api/auth/register", json={
            "email": new_email, "password": "password123", "name": "새멤버",
        })

        # Invite
        resp = await client.post(
            f"/api/companies/{company_id}/members",
            json={"email": new_email, "role": "member"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_email"] == new_email
        assert data["role"] == "member"

    async def test_invite_nonexistent_user(self, client):
        headers, company_id, _ = await self._setup(client)
        resp = await client.post(
            f"/api/companies/{company_id}/members",
            json={"email": "nonexistent@example.com", "role": "member"},
            headers=headers,
        )
        assert resp.status_code == 404


class TestNotificationEndpoints:
    """알림 API 엔드포인트 테스트."""

    async def _setup(self, client):
        email = f"noti_{uuid4().hex[:8]}@example.com"
        reg = await client.post("/api/auth/register", json={
            "email": email, "password": "password123", "name": "알림유저",
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        company_resp = await client.post("/api/auth/companies", json={
            "name": "알림회사",
        }, headers=headers)
        company_id = company_resp.json()["id"]
        return headers, company_id

    async def test_notification_summary(self, client):
        headers, _ = await self._setup(client)
        resp = await client.get("/api/notifications/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "today" in data
        assert "overdue" in data
        assert "upcoming_7days" in data
        assert "total_pending" in data

    async def test_today_notifications(self, client):
        headers, _ = await self._setup(client)
        resp = await client.get("/api/notifications/today", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_overdue_notifications(self, client):
        headers, _ = await self._setup(client)
        resp = await client.get("/api/notifications/overdue", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_upcoming_notifications(self, client):
        headers, _ = await self._setup(client)
        resp = await client.get("/api/notifications/upcoming", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestSchemaValidation:
    """Pydantic 스키마 유효성 검사 테스트."""

    def test_register_schema(self):
        from app.schemas.user import UserCreate
        user = UserCreate(email="test@example.com", password="password123", name="테스트")
        assert user.email == "test@example.com"
        assert user.name == "테스트"

    def test_login_schema(self):
        from app.schemas.user import UserLogin
        login = UserLogin(email="test@example.com", password="password123")
        assert login.email == "test@example.com"

    def test_token_response_schema(self):
        from app.schemas.user import TokenResponse, UserResponse
        user = UserResponse(
            id=uuid4(), email="test@example.com", name="테스트",
            is_active=True, created_at=datetime.utcnow(),
        )
        token = TokenResponse(access_token="abc", refresh_token="def", user=user)
        assert token.token_type == "bearer"

    def test_create_reminder_schema(self):
        from app.schemas.reminder import ReminderCreate
        reminder = ReminderCreate(
            title="원천세 신고", category="원천세", deadline=date(2026, 1, 10), priority=2,
        )
        assert reminder.title == "원천세 신고"
        assert reminder.deadline == date(2026, 1, 10)

    def test_update_reminder_schema_partial(self):
        from app.schemas.reminder import ReminderUpdate
        update = ReminderUpdate(completed=True)
        data = update.model_dump(exclude_unset=True)
        assert "completed" in data
        assert "title" not in data

    def test_template_apply_request(self):
        from app.schemas.template import TemplateApplyRequest
        request = TemplateApplyRequest(template_id=uuid4(), company_id=uuid4(), year=2026)
        assert request.year == 2026

    def test_company_create(self):
        from app.schemas.user import CompanyCreate
        company = CompanyCreate(name="테스트 회사", business_number="123-45-67890")
        assert company.name == "테스트 회사"

    def test_company_create_without_business_number(self):
        from app.schemas.user import CompanyCreate
        company = CompanyCreate(name="테스트 회사")
        assert company.business_number is None
