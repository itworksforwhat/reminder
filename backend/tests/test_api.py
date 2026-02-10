"""API 엔드포인트 통합 테스트.

참고: 실제 DB가 필요한 테스트는 Docker로 PostgreSQL을 실행해야 합니다.
이 파일은 API 구조와 응답 형식을 검증하기 위한 테스트입니다.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import date, datetime


class TestAuthEndpoints:
    """인증 API 엔드포인트 구조 테스트."""

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
            id=uuid4(),
            email="test@example.com",
            name="테스트",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        token = TokenResponse(
            access_token="abc",
            refresh_token="def",
            user=user,
        )
        assert token.token_type == "bearer"


class TestReminderSchemas:
    """리마인더 스키마 테스트."""

    def test_create_schema(self):
        from app.schemas.reminder import ReminderCreate
        reminder = ReminderCreate(
            title="원천세 신고",
            category="원천세",
            deadline=date(2026, 1, 10),
            priority=2,
        )
        assert reminder.title == "원천세 신고"
        assert reminder.deadline == date(2026, 1, 10)

    def test_update_schema_partial(self):
        from app.schemas.reminder import ReminderUpdate
        update = ReminderUpdate(completed=True)
        data = update.model_dump(exclude_unset=True)
        assert "completed" in data
        assert "title" not in data

    def test_list_response_schema(self):
        from app.schemas.reminder import ReminderListResponse
        response = ReminderListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=0,
        )
        assert response.total == 0


class TestTemplateSchemas:
    """템플릿 스키마 테스트."""

    def test_apply_request(self):
        from app.schemas.template import TemplateApplyRequest
        request = TemplateApplyRequest(
            template_id=uuid4(),
            company_id=uuid4(),
            year=2026,
        )
        assert request.year == 2026

    def test_apply_response(self):
        from app.schemas.template import TemplateApplyResponse, GeneratedReminder
        reminder = GeneratedReminder(
            title="원천세 신고",
            category="원천세",
            deadline=date(2026, 1, 12),
            original_deadline=date(2026, 1, 10),
            priority=2,
        )
        response = TemplateApplyResponse(
            template_name="법정신고일",
            year=2026,
            generated_count=1,
            reminders=[reminder],
        )
        assert response.generated_count == 1


class TestCompanySchema:
    """회사 스키마 테스트."""

    def test_company_create(self):
        from app.schemas.user import CompanyCreate
        company = CompanyCreate(name="테스트 회사", business_number="123-45-67890")
        assert company.name == "테스트 회사"

    def test_company_create_without_business_number(self):
        from app.schemas.user import CompanyCreate
        company = CompanyCreate(name="테스트 회사")
        assert company.business_number is None
