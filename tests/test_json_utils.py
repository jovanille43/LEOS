"""Tests for defensive JSON preflight helpers."""

import unittest

from leos_core.json_utils import MAX_JSON_NESTING, json_nesting_within_limit


class JsonUtilsTests(unittest.TestCase):
    def test_accepts_normal_json_and_brackets_inside_strings(self):
        self.assertTrue(json_nesting_within_limit('{"text":"[[[[ {{{ }}} ]]]]"}'))
        self.assertTrue(json_nesting_within_limit('{"items":[1,2,3]}'))

    def test_rejects_excessive_container_nesting(self):
        self.assertFalse(json_nesting_within_limit("[" * (MAX_JSON_NESTING + 1) + "0" + "]" * (MAX_JSON_NESTING + 1)))

    def test_rejects_malformed_unbalanced_nesting(self):
        self.assertFalse(json_nesting_within_limit('{"items":[1,2}'))

    def test_rejects_invalid_input_and_limits(self):
        self.assertFalse(json_nesting_within_limit(None))
        self.assertFalse(json_nesting_within_limit("[]", max_depth=-1))
        self.assertFalse(json_nesting_within_limit("[]", max_depth=True))


if __name__ == "__main__":
    unittest.main()
