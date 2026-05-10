"""Preflight gate tests (G0-G5) for generate_modes_and_rules.py."""

from __future__ import annotations

import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import generate_modes_and_rules as gen

FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures"
MINIMAL_FIXTURE = FIXTURES_DIR / "minimal"


def _copy_fixture(dst: pathlib.Path) -> None:
    """Copy the minimal fixture into a temporary root directory."""
    shutil.copytree(MINIMAL_FIXTURE, dst, dirs_exist_ok=True)


class _PreflightTestBase(unittest.TestCase):
    """Base class: sets up a temp root from the minimal fixture and redirects Paths."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        _copy_fixture(self.root)
        gen.init_paths(self.root)

    def tearDown(self):
        gen.init_paths(gen._DEFAULT_ROOT)
        self.tmpdir.cleanup()

    def _profiles(self) -> list[pathlib.Path]:
        return [self.root / "stack-profile.md"]


# ---------------------------------------------------------------------------
# G0 — Infrastructure
# ---------------------------------------------------------------------------


class TestGate0Infrastructure(_PreflightTestBase):
    def test_all_present_passes(self):
        errors = gen._gate_0_infrastructure()
        self.assertEqual(errors, [])

    def test_missing_base_rule(self):
        (self.root / "aias" / ".canonical" / "rules" / "base-rule.md").unlink()
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "base rule" in e for e in errors))

    def test_missing_output_contract(self):
        (self.root / "aias" / ".canonical" / "rules" / "output-contract.md").unlink()
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "output contract" in e for e in errors))

    def test_missing_stack_fragment(self):
        (self.root / "stack-fragment.md").unlink()
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "fragment" in e.lower() for e in errors))

    def test_missing_one_mode_template(self):
        (self.root / "aias" / ".canonical" / "modes" / "planning.mdc").unlink()
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "planning" in e for e in errors))

    def test_base_rule_no_markdown_block(self):
        br = self.root / "aias" / ".canonical" / "rules" / "base-rule.md"
        br.write_text("# No code block here\nJust text.\n", encoding="utf-8")
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "markdown" in e.lower() for e in errors))

    def test_output_contract_no_markdown_block(self):
        oc = self.root / "aias" / ".canonical" / "rules" / "output-contract.md"
        oc.write_text("# No code block\nJust text.\n", encoding="utf-8")
        errors = gen._gate_0_infrastructure()
        self.assertTrue(any("[G0]" in e and "markdown" in e.lower() for e in errors))


# ---------------------------------------------------------------------------
# G1 — Profile Discovery
# ---------------------------------------------------------------------------


class TestGate1ProfileDiscovery(_PreflightTestBase):
    def test_valid_profile_passes(self):
        errors, bindings = gen._gate_1_profile_discovery(self._profiles())
        self.assertEqual(errors, [])
        self.assertEqual(len(bindings), 1)

    def test_no_profiles(self):
        errors, bindings = gen._gate_1_profile_discovery([])
        self.assertTrue(any("[G1]" in e for e in errors))
        self.assertEqual(bindings, [])

    def test_profile_not_readable(self):
        fake = self.root / "nonexistent.md"
        errors, bindings = gen._gate_1_profile_discovery([fake])
        self.assertTrue(any("[G1]" in e and "not readable" in e for e in errors))

    def test_no_bindings_in_profile(self):
        p = self.root / "stack-profile.md"
        p.write_text("# Empty profile\nNo bindings.\n", encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e for e in errors))

    def test_missing_stack_id(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "generation.stack_id" not in line
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "stack_id" in e for e in errors))

    def test_deprecated_mode_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content += "\n- `binding.generation.mode_output_dir`: `aias-config/modes`\n"
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Deprecated" in e for e in errors))

    def test_legacy_canonical_mode_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.canonical_mode_output_dir`: `aias-config/modes`",
            "- `binding.generation.canonical_mode_output_dir`: `aias/.modes`",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Legacy" in e and "canonical_mode_output_dir" in e for e in errors))

    def test_invalid_canonical_mode_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.canonical_mode_output_dir`: `aias-config/modes`",
            "- `binding.generation.canonical_mode_output_dir`: `invalid/path`",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Invalid" in e and "canonical_mode_output_dir" in e for e in errors))

    def test_missing_canonical_mode_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "canonical_mode_output_dir" not in line
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Missing" in e and "canonical_mode_output_dir" in e for e in errors))

    def test_legacy_canonical_rule_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.canonical_rule_output_dir`: `aias-config/rules`",
            "- `binding.generation.canonical_rule_output_dir`: `aias/.rules`",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Legacy" in e and "canonical_rule_output_dir" in e for e in errors))

    def test_invalid_canonical_rule_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.canonical_rule_output_dir`: `aias-config/rules`",
            "- `binding.generation.canonical_rule_output_dir`: `invalid/path`",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Invalid" in e and "canonical_rule_output_dir" in e for e in errors))

    def test_missing_canonical_rule_output_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "canonical_rule_output_dir" not in line
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Missing" in e and "canonical_rule_output_dir" in e for e in errors))

    def test_missing_tools(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "generation.tools" not in line
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "tools" in e for e in errors))

    def test_invalid_tool(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.tools`: `cursor`",
            "- `binding.generation.tools`: `vim`",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "Invalid" in e and "vim" in e for e in errors))

    def test_empty_tools(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = content.replace(
            "- `binding.generation.tools`: `cursor`",
            "- `binding.generation.tools`: ``",
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "empty" in e.lower() for e in errors))

    def test_missing_tasks_dir(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "generation.tasks_dir" not in line
        )
        p.write_text(content, encoding="utf-8")
        errors, _ = gen._gate_1_profile_discovery([p])
        self.assertTrue(any("[G1]" in e and "tasks_dir" in e for e in errors))


# ---------------------------------------------------------------------------
# G2 — Mode Bindings
# ---------------------------------------------------------------------------


class TestGate2ModeBindings(_PreflightTestBase):
    def test_all_bindings_present_passes(self):
        profiles = self._profiles()
        bindings = gen.load_bindings(profiles[0])
        errors = gen._gate_2_mode_bindings([(profiles[0], bindings)])
        self.assertEqual(errors, [])

    def test_missing_core_mode_binding(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "mode.dev.description" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_2_mode_bindings([(p, bindings)])
        self.assertTrue(any("[G2]" in e and "dev" in e and "description" in e for e in errors))

    def test_transversal_mode_defaults_pass(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "mode.delivery" not in line and "mode.devops" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_2_mode_bindings([(p, bindings)])
        delivery_errors = [e for e in errors if "delivery" in e]
        devops_errors = [e for e in errors if "devops" in e]
        self.assertEqual(delivery_errors, [])
        self.assertEqual(devops_errors, [])


# ---------------------------------------------------------------------------
# G3 — Rule Bindings
# ---------------------------------------------------------------------------


class TestGate3RuleBindings(_PreflightTestBase):
    def test_all_bindings_present_passes(self):
        profiles = self._profiles()
        bindings = gen.load_bindings(profiles[0])
        errors = gen._gate_3_rule_bindings([(profiles[0], bindings)])
        self.assertEqual(errors, [])

    def test_no_workspaces_discovered(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "rule.base." not in line or "description" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_3_rule_bindings([(p, bindings)])
        self.assertTrue(any("[G3]" in e and "No rule workspaces" in e for e in errors))

    def test_missing_base_rule_binding(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "rule.base.stubapp.role_specialty" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_3_rule_bindings([(p, bindings)])
        self.assertTrue(any("[G3]" in e and "role_specialty" in e for e in errors))

    def test_missing_output_contract_binding(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "rule.output_contract.stubapp.environment" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_3_rule_bindings([(p, bindings)])
        self.assertTrue(any("[G3]" in e and "environment" in e for e in errors))

    def test_missing_profile_binding(self):
        p = self.root / "stack-profile.md"
        content = p.read_text(encoding="utf-8")
        content = "\n".join(
            line for line in content.splitlines()
            if "output_contract.stubapp.profile" not in line
        )
        p.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(p)
        errors = gen._gate_3_rule_bindings([(p, bindings)])
        self.assertTrue(any("[G3]" in e and "profile" in e for e in errors))


# ---------------------------------------------------------------------------
# G4 — Fragment Validation
# ---------------------------------------------------------------------------


class TestGate4FragmentValidation(_PreflightTestBase):
    def test_valid_fragment_passes(self):
        errors = gen._gate_4_fragment_validation([])
        self.assertEqual(errors, [])

    def test_missing_fragment(self):
        (self.root / "stack-fragment.md").unlink()
        errors = gen._gate_4_fragment_validation([])
        self.assertTrue(any("[G4]" in e and "Missing" in e for e in errors))

    def test_empty_fragment(self):
        (self.root / "stack-fragment.md").write_text("", encoding="utf-8")
        errors = gen._gate_4_fragment_validation([])
        self.assertTrue(any("[G4]" in e and "Empty" in e for e in errors))

    def test_fragment_no_uppercase_header(self):
        (self.root / "stack-fragment.md").write_text(
            "this fragment has no uppercase header\njust lowercase.\n",
            encoding="utf-8",
        )
        errors = gen._gate_4_fragment_validation([])
        self.assertTrue(any("[G4]" in e and "header" in e.lower() for e in errors))


# ---------------------------------------------------------------------------
# G5 — Output Directories
# ---------------------------------------------------------------------------


class TestGate5OutputDirectories(_PreflightTestBase):
    def test_directories_exist_passes(self):
        errors = gen._gate_5_output_directories()
        self.assertEqual(errors, [])

    def test_directories_created(self):
        shutil.rmtree(self.root / "aias-config" / "rules", ignore_errors=True)
        shutil.rmtree(self.root / "aias-config" / "modes", ignore_errors=True)
        errors = gen._gate_5_output_directories()
        self.assertEqual(errors, [])
        self.assertTrue((self.root / "aias-config" / "rules").is_dir())
        self.assertTrue((self.root / "aias-config" / "modes").is_dir())


# ---------------------------------------------------------------------------
# Full preflight pass/fail
# ---------------------------------------------------------------------------


class TestPreflightValidation(_PreflightTestBase):
    def test_full_validation_passes(self):
        errors = gen.preflight_validation(self._profiles())
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_accumulates_multiple_errors(self):
        (self.root / "aias" / ".canonical" / "rules" / "base-rule.md").unlink()
        (self.root / "stack-fragment.md").unlink()
        errors = gen.preflight_validation(self._profiles())
        g0_errors = [e for e in errors if "[G0]" in e]
        self.assertGreaterEqual(len(g0_errors), 2)


if __name__ == "__main__":
    unittest.main()
