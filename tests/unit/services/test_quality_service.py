"""Unit tests for QualityAnalysisService severity breakdown calculation."""

import pytest

from app.api.v1.schemas import QualityIssue
from app.core.services.quality_service import QualityAnalysisService


class TestSeverityBreakdownCalculation:
    """Test suite for _calculate_severity_breakdown method."""

    @pytest.fixture
    def service(self):
        """Create a QualityAnalysisService instance for testing."""
        return QualityAnalysisService()

    def test_calculate_severity_breakdown_empty(self, service):
        """Test severity breakdown with no issues."""
        breakdown = service._calculate_severity_breakdown([])

        assert breakdown == {"error": 0, "warning": 0, "info": 0}

    def test_calculate_severity_breakdown_only_errors(self, service):
        """Test severity breakdown with only error-level issues."""
        issues = [
            QualityIssue(
                file_path="test.py",
                line=1,
                severity="error",
                code="E001",
                message="Error 1",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=2,
                severity="error",
                code="E002",
                message="Error 2",
                detected_by="rule",
            ),
        ]

        breakdown = service._calculate_severity_breakdown(issues)

        assert breakdown["error"] == 2
        assert breakdown["warning"] == 0
        assert breakdown["info"] == 0

    def test_calculate_severity_breakdown_only_warnings(self, service):
        """Test severity breakdown with only warning-level issues."""
        issues = [
            QualityIssue(
                file_path="test.py",
                line=1,
                severity="warning",
                code="W001",
                message="Warning 1",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=2,
                severity="warning",
                code="W002",
                message="Warning 2",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=3,
                severity="warning",
                code="W003",
                message="Warning 3",
                detected_by="rule",
            ),
        ]

        breakdown = service._calculate_severity_breakdown(issues)

        assert breakdown["error"] == 0
        assert breakdown["warning"] == 3
        assert breakdown["info"] == 0

    def test_calculate_severity_breakdown_only_info(self, service):
        """Test severity breakdown with only info-level issues."""
        issues = [
            QualityIssue(
                file_path="test.py",
                line=1,
                severity="info",
                code="I001",
                message="Info 1",
                detected_by="rule",
            ),
        ]

        breakdown = service._calculate_severity_breakdown(issues)

        assert breakdown["error"] == 0
        assert breakdown["warning"] == 0
        assert breakdown["info"] == 1

    def test_calculate_severity_breakdown_mixed(self, service):
        """Test severity breakdown with mixed severity levels."""
        issues = [
            QualityIssue(
                file_path="test.py",
                line=1,
                severity="error",
                code="E001",
                message="Error",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=2,
                severity="error",
                code="E002",
                message="Error 2",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=3,
                severity="warning",
                code="W001",
                message="Warning",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=4,
                severity="warning",
                code="W002",
                message="Warning 2",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=5,
                severity="warning",
                code="W003",
                message="Warning 3",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test.py",
                line=6,
                severity="info",
                code="I001",
                message="Info",
                detected_by="rule",
            ),
        ]

        breakdown = service._calculate_severity_breakdown(issues)

        assert breakdown["error"] == 2
        assert breakdown["warning"] == 3
        assert breakdown["info"] == 1

    def test_calculate_severity_breakdown_realistic_distribution(self, service):
        """Test severity breakdown with realistic distribution of issues."""
        issues = [
            # 3 errors
            QualityIssue(
                file_path="test_user.py",
                line=10,
                severity="error",
                code="missing-assertion",
                message="Test has no assertions",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_user.py",
                line=20,
                severity="error",
                code="missing-assertion",
                message="Test has no assertions",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_product.py",
                line=5,
                severity="error",
                code="trivial-assertion",
                message="Assertion always passes",
                detected_by="rule",
            ),
            # 5 warnings
            QualityIssue(
                file_path="test_user.py",
                line=30,
                severity="warning",
                code="redundant-assertion",
                message="Duplicate assertion",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_user.py",
                line=40,
                severity="warning",
                code="missing-mock",
                message="External dependency not mocked",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_product.py",
                line=15,
                severity="warning",
                code="missing-mock",
                message="External dependency not mocked",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_product.py",
                line=25,
                severity="warning",
                code="redundant-assertion",
                message="Duplicate assertion",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_order.py",
                line=12,
                severity="warning",
                code="unused-fixture",
                message="Fixture not used",
                detected_by="rule",
            ),
            # 2 info
            QualityIssue(
                file_path="test_user.py",
                line=50,
                severity="info",
                code="unused-variable",
                message="Variable assigned but never used",
                detected_by="rule",
            ),
            QualityIssue(
                file_path="test_product.py",
                line=35,
                severity="info",
                code="unused-variable",
                message="Variable assigned but never used",
                detected_by="rule",
            ),
        ]

        breakdown = service._calculate_severity_breakdown(issues)

        assert breakdown["error"] == 3
        assert breakdown["warning"] == 5
        assert breakdown["info"] == 2
        assert sum(breakdown.values()) == len(issues)  # Total matches issue count
