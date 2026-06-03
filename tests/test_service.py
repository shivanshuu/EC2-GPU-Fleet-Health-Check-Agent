import tempfile
import unittest

from app.models import Decision, PreflightRequest
from app.service import run_preflight


class PreflightServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_preflight_returns_fail_and_report_uri(self) -> None:
        with tempfile.TemporaryDirectory() as report_dir:
            decision = await run_preflight(
                PreflightRequest(
                    job_id="test-001",
                    profile="distributed-gpu",
                    instance_ids=["i-good001", "i-badgpu123"],
                ),
                report_dir=report_dir,
            )

        self.assertEqual(decision.decision, Decision.FAIL)
        self.assertIn("failed pre-flight", decision.summary)
        self.assertIsNotNone(decision.report_uri)


if __name__ == "__main__":
    unittest.main()
