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

    def test_duplicate_keys_are_rejected_before_validation(self):
        for response in ('{"a":0,"a":1}', '```json\n[{"a":0,"\\u0061":1}]\n```'):
            with self.subTest(response=response), self.assertRaisesRegex(ValidationError, "duplicate JSON key"):
                extract_json(response)

    def test_distinct_objects_can_reuse_a_key(self):
        self.assertEqual(extract_json('[{"a":0},{"a":1}]'), [{"a": 0}, {"a": 1}])

    def test_extra_fields_are_rejected(self):
        with self.assertRaisesRegex(ValidationError, "unexpected"):
            validate({"answer": "ok", "secret": "x"}, SCHEMA)


if __name__ == "__main__":
    unittest.main()
