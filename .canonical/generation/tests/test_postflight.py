"""Postflight gate tests (G6-G7) for generate_modes_and_rules.py."""

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
    shutil.copytree(MINIMAL_FIXTURE, dst, dirs_exist_ok=True)


class _PostflightTestBase(unittest.TestCase):
    """Sets up a temp root with generated canonical + shortcut outputs."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        _copy_fixture(self.root)
        gen.init_paths(self.root)
        self._generate_canonical_outputs()

    def tearDown(self):
        gen.init_paths(gen._DEFAULT_ROOT)
        self.tmpdir.cleanup()

    def _generate_canonical_outputs(self):
        """Generate canonical mode/rule files so shortcuts can reference them."""
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        self.bindings = bindings
        self.stack_id, self.mode_names = gen.generate_modes_for_profile(profile, bindings)
        gen.generate_rules_for_profile(profile, bindings)
        for tr in gen.TRANSVERSAL_RULES:
            src = gen.Paths.canonical_dir / f"{tr}.mdc"
            if src.is_file():
                dst = gen.Paths.rules_output / f"{tr}.mdc"
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


# ---------------------------------------------------------------------------
# G6 — Shortcut Consistency
# ---------------------------------------------------------------------------


class TestGate6ShortcutConsistency(_PostflightTestBase):
    def _generate_shortcuts(self, tools: list[str]):
        gen.generate_shortcuts(
            self.mode_names,
            [(self.root / "stack-profile.md", self.bindings)],
            tools,
        )

    def test_cursor_shortcuts_pass(self):
        self._generate_shortcuts(["cursor"])
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["cursor"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_cursor_missing_rule_shortcut(self):
        self._generate_shortcuts(["cursor"])
        (self.root / ".cursor" / "rules" / "base.mdc").unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["cursor"])
        self.assertTrue(any("[G6]" in e and "base" in e for e in errors))

    def test_cursor_missing_mode_shortcut(self):
        self._generate_shortcuts(["cursor"])
        (self.root / ".cursor" / "rules" / "planning.mdc").unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["cursor"])
        self.assertTrue(any("[G6]" in e and "planning" in e for e in errors))

    def test_cursor_broken_symlink(self):
        self._generate_shortcuts(["cursor"])
        link = self.root / ".cursor" / "rules" / "base.mdc"
        link.unlink()
        link.symlink_to("/nonexistent/path")
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["cursor"])
        self.assertTrue(any("[G6]" in e and "Broken symlink" in e for e in errors))

    def test_claude_shortcuts_pass(self):
        self._generate_shortcuts(["claude"])
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["claude"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_claude_missing_rule(self):
        self._generate_shortcuts(["claude"])
        (self.root / ".claude" / "rules" / "base.md").unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["claude"])
        self.assertTrue(any("[G6]" in e and "base" in e for e in errors))

    def test_copilot_shortcuts_pass(self):
        self._generate_shortcuts(["copilot"])
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["copilot"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_copilot_missing_instructions(self):
        self._generate_shortcuts(["copilot"])
        (self.root / ".github" / "copilot-instructions.md").unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["copilot"])
        self.assertTrue(any("[G6]" in e and "copilot-instructions" in e for e in errors))

    def test_copilot_missing_mode(self):
        self._generate_shortcuts(["copilot"])
        (self.root / ".github" / "instructions" / "planning.instructions.md").unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["copilot"])
        self.assertTrue(any("[G6]" in e and "planning" in e for e in errors))

    def test_codex_missing_command(self):
        self._generate_shortcuts(["codex"])
        codex_cmds = self.root / ".codex" / "commands"
        if codex_cmds.is_dir():
            for f in codex_cmds.iterdir():
                f.unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["codex"])
        self.assertTrue(any("[G6]" in e and "Codex command" in e for e in errors))

    def test_cursor_does_not_create_commands_dir(self):
        """Cursor no longer uses .cursor/commands/ — command-shaped skills go to .cursor/skills/."""
        self._generate_shortcuts(["cursor"])
        cursor_cmds = self.root / ".cursor" / "commands"
        self.assertFalse(cursor_cmds.is_dir(),
                         ".cursor/commands/ must not be created for Cursor (skills only)")

    def test_cursor_missing_skill_shortcut(self):
        self._generate_shortcuts(["cursor"])
        skill_link = self.root / ".cursor" / "skills" / "stub-skill" / "SKILL.md"
        if skill_link.exists() or skill_link.is_symlink():
            skill_link.unlink()
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["cursor"])
        self.assertTrue(any("[G6]" in e and "skill" in e.lower() for e in errors))

    def test_windsurf_shortcuts_pass(self):
        self._generate_shortcuts(["windsurf"])
        errors = gen._gate_6_shortcut_consistency(self.mode_names, ["windsurf"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")


# ---------------------------------------------------------------------------
# G7 — Size Limits
# ---------------------------------------------------------------------------


class TestGate7SizeLimits(_PostflightTestBase):
    def _generate_shortcuts(self, tools: list[str]):
        gen.generate_shortcuts(
            self.mode_names,
            [(self.root / "stack-profile.md", self.bindings)],
            tools,
        )

    def test_normal_shortcuts_pass(self):
        self._generate_shortcuts(["cursor", "claude", "windsurf", "copilot", "codex"])
        errors = gen._gate_7_no_duplication(["cursor", "claude", "windsurf", "copilot", "codex"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_enriched_text_too_large(self):
        self._generate_shortcuts(["claude"])
        large_file = self.root / ".claude" / "rules" / "base.md"
        large_file.write_text("X" * (gen.SHORTCUT_MAX_LEN + 100), encoding="utf-8")
        errors = gen._gate_7_no_duplication(["claude"])
        self.assertTrue(any("[G7]" in e and "too large" in e for e in errors))

    def test_aggregated_file_too_large(self):
        self._generate_shortcuts(["copilot"])
        copilot_instr = self.root / ".github" / "copilot-instructions.md"
        copilot_instr.write_text("X" * (gen.SHORTCUT_MAX_LEN * 3 + 100), encoding="utf-8")
        errors = gen._gate_7_no_duplication(["copilot"])
        self.assertTrue(any("[G7]" in e and "Aggregated" in e for e in errors))

    def test_symlinks_exempt_from_size_check(self):
        self._generate_shortcuts(["cursor"])
        cursor_rules = self.root / ".cursor" / "rules"
        for f in cursor_rules.iterdir():
            if f.is_symlink():
                target = f.resolve()
                if target.is_file():
                    target.write_text("X" * (gen.SHORTCUT_MAX_LEN + 500), encoding="utf-8")
        errors = gen._gate_7_no_duplication(["cursor"])
        symlink_errors = [e for e in errors if "[G7]" in e and ".cursor" in e]
        self.assertEqual(symlink_errors, [])

    def test_mdc_enriched_too_large(self):
        self._generate_shortcuts(["cursor"])
        cursor_rules = self.root / ".cursor" / "rules"
        non_symlink = cursor_rules / "test-oversized.mdc"
        non_symlink.write_text("X" * (gen.SHORTCUT_MAX_LEN + 100), encoding="utf-8")
        errors = gen._gate_7_no_duplication(["cursor"])
        self.assertTrue(any("[G7]" in e and "test-oversized" in e for e in errors))


# ---------------------------------------------------------------------------
# Full postflight pass/fail
# ---------------------------------------------------------------------------


class TestPostflightValidation(_PostflightTestBase):
    def test_full_postflight_passes(self):
        gen.generate_shortcuts(
            self.mode_names,
            [(self.root / "stack-profile.md", self.bindings)],
            ["cursor"],
        )
        errors = gen.postflight_validation(self.mode_names, ["cursor"])
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_postflight_accumulates_errors(self):
        errors = gen.postflight_validation(self.mode_names, ["cursor"])
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
