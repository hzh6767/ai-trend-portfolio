import unittest

from pii_redactor import redact, scan


class RedactorTests(unittest.TestCase):
    def test_redacts_multiple_classes(self):
        value, findings = redact("email alice@example.com, IP 192.168.1.4, Bearer abcdefghijklmnop")
        self.assertNotIn("alice@example.com", value)
        self.assertNotIn("192.168.1.4", value)
        self.assertEqual({item.kind for item in findings}, {"email", "ipv4", "bearer_token"})

    def test_findings_are_sorted_and_non_overlapping(self):
        findings = scan("alice@example.com")
        self.assertEqual(findings[0].start, 0)
        self.assertTrue(all(a.end <= b.start for a, b in zip(findings, findings[1:])))

    def test_plain_text_is_unchanged(self):
        self.assertEqual(redact("hello world")[0], "hello world")


if __name__ == "__main__":
    unittest.main()
