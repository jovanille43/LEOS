"""Tests for robust XDG directory resolution."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from leos_core.paths import config_home, data_home, state_home


class XdgPathTests(unittest.TestCase):
    def test_defaults_are_used_when_environment_variables_are_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict(os.environ, {"HOME": str(home)}, clear=True):
                self.assertEqual(config_home(), home / ".config")
                self.assertEqual(data_home(), home / ".local" / "share")
                self.assertEqual(state_home(), home / ".local" / "state")

    def test_empty_and_relative_xdg_values_fall_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            environment = {
                "HOME": str(home),
                "XDG_CONFIG_HOME": "",
                "XDG_DATA_HOME": "relative/data",
                "XDG_STATE_HOME": "relative/state",
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(config_home(), home / ".config")
                self.assertEqual(data_home(), home / ".local" / "share")
                self.assertEqual(state_home(), home / ".local" / "state")

    def test_absolute_xdg_values_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = {
                "XDG_CONFIG_HOME": str(root / "cfg"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_STATE_HOME": str(root / "state"),
            }
            with patch.dict(os.environ, environment, clear=True):
                self.assertEqual(config_home(), root / "cfg")
                self.assertEqual(data_home(), root / "data")
                self.assertEqual(state_home(), root / "state")

    def test_tilde_is_expanded_before_absolute_path_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.dict(os.environ, {"HOME": str(home), "XDG_CONFIG_HOME": "~/leos-config"}, clear=True):
                self.assertEqual(config_home(), home / "leos-config")


if __name__ == "__main__":
    unittest.main()
