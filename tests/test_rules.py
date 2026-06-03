import unittest

from app.mock_collectors import collect_mock_checks
from app.models import Decision, JobProfile, RiskLevel
from app.rules import aggregate, classify_instance


class RuleEngineTests(unittest.TestCase):
    def test_healthy_instances_aggregate_to_go(self) -> None:
        profile = JobProfile()
        reports = [
            classify_instance("i-good001", collect_mock_checks("i-good001", profile)),
            classify_instance("i-good002", collect_mock_checks("i-good002", profile)),
        ]

        decision, counts = aggregate(reports)

        self.assertEqual(decision, Decision.GO)
        self.assertEqual(counts.passed, 2)
        self.assertEqual(counts.failed, 0)

    def test_missing_gpu_fails_job(self) -> None:
        profile = JobProfile(expected_gpu_count=8)
        reports = [
            classify_instance("i-good001", collect_mock_checks("i-good001", profile)),
            classify_instance("i-badgpu123", collect_mock_checks("i-badgpu123", profile)),
        ]

        decision, counts = aggregate(reports)

        self.assertEqual(decision, Decision.FAIL)
        self.assertEqual(counts.failed, 1)

    def test_warning_without_failure_warns_job(self) -> None:
        profile = JobProfile()
        reports = [
            classify_instance(
                "i-warn001",
                collect_mock_checks("i-warn001", profile),
                RiskLevel.MEDIUM,
            )
        ]

        decision, counts = aggregate(reports)

        self.assertEqual(decision, Decision.WARN)
        self.assertEqual(counts.warned, 1)


if __name__ == "__main__":
    unittest.main()
