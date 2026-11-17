"""Keep runtime Python imports aligned with the immutable image package recipe."""

import ast
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PACKAGES = (
    "control_center",
    "controller_center",
    "desktop",
    "gaming",
    "launcher",
    "leos_core",
    "shop",
)
THIRD_PARTY_PACKAGES = {
    "PySide6": "python3-pyside6",
    "evdev": "python3-evdev",
    "psutil": "python3-psutil",
}


class RuntimeDependencyTests(unittest.TestCase):
    def test_runtime_third_party_imports_are_declared_in_recipe(self):
        external_imports = set()

        for package in RUNTIME_PACKAGES:
            package_path = ROOT / package
            for source in package_path.rglob("*.py"):
                tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        external_imports.update(
                            alias.name.split(".", 1)[0] for alias in node.names
                        )
                    elif isinstance(node, ast.ImportFrom):
                        if node.level or not node.module:
                            continue
                        external_imports.add(node.module.split(".", 1)[0])

        local_imports = set(RUNTIME_PACKAGES)
        external_imports.difference_update(sys.stdlib_module_names)
        external_imports.difference_update(local_imports)

        self.assertEqual(external_imports, set(THIRD_PARTY_PACKAGES))

        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        for module, package_name in THIRD_PARTY_PACKAGES.items():
            with self.subTest(module=module):
                self.assertIn(f"- {package_name}", recipe)


if __name__ == "__main__":
    unittest.main()
