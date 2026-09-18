import unittest

from structured_output_guard import ValidationError, extract_json, validate


SCHEMA = {"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}, "additionalProperties": False}


class GuardTests(unittest.TestCase):
    def test_fenced_json_and_schema(self):
        value = extract_json("```json\n{\"answer\":\"ok\"}\n```")
        self.assertEqual(validate(value, SCHEMA)["answer"], "ok")

    def test_missing_required_is_rejected(self):
        with self.assertRaisesRegex(ValidationError, "missing required"):
            validate({}, SCHEMA)

    def test_extra_fields_are_rejected(self):
        with self.assertRaisesRegex(ValidationError, "unexpected"):
            validate({"answer": "ok", "secret": "x"}, SCHEMA)


if __name__ == "__main__":
    unittest.main()
