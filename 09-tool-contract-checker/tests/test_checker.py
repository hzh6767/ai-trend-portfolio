import unittest

from tool_contract_checker import ToolContract, check_invocation, validate_contract


CONTRACT = ToolContract(
    "read_report",
    "Read a report",
    {"path": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1}, "format": {"type": "string", "enum": ["csv", "json"]}},
    ("path",),
)


class ToolContractTests(unittest.TestCase):
    def test_valid_invocation(self):
        result = check_invocation(CONTRACT, {"path": "reports/today.csv", "limit": 10})
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, ())

    def test_shape_and_type_errors(self):
        result = check_invocation(CONTRACT, {"limit": "many", "extra": True})
        self.assertFalse(result.valid)
        self.assertIn("missing required parameter: path", result.errors)
        self.assertIn("limit: expected integer", result.errors)
        self.assertIn("unknown parameter: extra", result.errors)

    def test_safety_warnings_are_reported(self):
        result = check_invocation(CONTRACT, {"path": "../secret.csv;cat /etc/passwd"})
        self.assertTrue(result.valid)
        self.assertTrue(any("path traversal" in warning for warning in result.warnings))
        self.assertTrue(any("shell metacharacters" in warning for warning in result.warnings))

    def test_invalid_contract(self):
        bad = ToolContract("", "", {"x": {"type": "unsupported"}}, ("missing",))
        errors = validate_contract(bad)
        self.assertGreaterEqual(len(errors), 3)

    def test_real_nul_byte_is_flagged_as_shell_metacharacter(self):
        result = check_invocation(CONTRACT, {"path": "a\x00b"})
        self.assertTrue(any("shell metacharacters" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
