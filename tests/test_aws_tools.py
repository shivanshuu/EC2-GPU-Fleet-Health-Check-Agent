import unittest

from app.aws_tools import _efa_check, _parse_probe_output, infer_gpu_count
from app.models import CheckStatus


class AwsToolsTests(unittest.TestCase):
    def test_infers_g5_gpu_counts(self) -> None:
        self.assertEqual(infer_gpu_count("g5.xlarge"), 1)
        self.assertEqual(infer_gpu_count("g5.12xlarge"), 4)
        self.assertEqual(infer_gpu_count("g5.48xlarge"), 8)

    def test_unknown_instance_type_returns_none(self) -> None:
        self.assertIsNone(infer_gpu_count("c7i.large"))

    def test_parses_probe_output(self) -> None:
        output = "\n".join(
            [
                "NVIDIA_SMI=present",
                "GPU_COUNT=1",
                "EFA_STATUS=available",
                "RECENT_XID_COUNT=0",
            ]
        )

        self.assertEqual(
            _parse_probe_output(output),
            {
                "NVIDIA_SMI": "present",
                "GPU_COUNT": "1",
                "EFA_STATUS": "available",
                "RECENT_XID_COUNT": "0",
            },
        )

    def test_efa_check_fails_without_efa_nic(self) -> None:
        result = _efa_check(
            "i-test",
            {"NetworkInterfaces": [{"InterfaceType": "interface"}]},
            {"EFA_STATUS": "available"},
        )

        self.assertEqual(result.status, CheckStatus.FAIL)
        self.assertEqual(result.observed, "missing")

    def test_efa_check_warns_when_attached_but_unprobed(self) -> None:
        result = _efa_check(
            "i-test",
            {"NetworkInterfaces": [{"InterfaceType": "efa"}]},
            None,
        )

        self.assertEqual(result.status, CheckStatus.WARN)
        self.assertIn("not functionally probed", result.observed)

    def test_efa_check_passes_when_fi_info_succeeds(self) -> None:
        result = _efa_check(
            "i-test",
            {"NetworkInterfaces": [{"InterfaceType": "efa"}]},
            {"EFA_STATUS": "available"},
        )

        self.assertEqual(result.status, CheckStatus.PASS)
        self.assertEqual(result.observed, "available")


if __name__ == "__main__":
    unittest.main()
