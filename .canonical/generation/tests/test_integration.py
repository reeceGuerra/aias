"""Integration tests — full pipeline with stub fixtures, idempotency, and shortcuts."""

from __future__ import annotations

import filecmp
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


class _IntegrationTestBase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        _copy_fixture(self.root)
        gen.init_paths(self.root)

    def tearDown(self):
        gen.init_paths(gen._DEFAULT_ROOT)
        self.tmpdir.cleanup()


# ---------------------------------------------------------------------------
# Happy path — full generation pipeline
# ---------------------------------------------------------------------------


class TestHappyPathGeneration(_IntegrationTestBase):
    def test_modes_generated(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        stack_id, mode_names = gen.generate_modes_for_profile(profile, bindings)
        self.assertEqual(stack_id, "stub-stack")
        self.assertEqual(len(mode_names), 9)
        for mode in gen.MODE_NAMES:
            output = gen.Paths.modes_output / f"{mode}.mdc"
            self.assertTrue(output.is_file(), f"Missing mode: {mode}")
            content = output.read_text(encoding="utf-8")
            self.assertIn("GENERATED — DO NOT EDIT", content)

    def test_rules_generated(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        ws_ids = gen.generate_rules_for_profile(profile, bindings)
        self.assertEqual(ws_ids, ["stubapp"])
        base = gen.Paths.rules_output / "base.mdc"
        oc = gen.Paths.rules_output / "output-contract.mdc"
        self.assertTrue(base.is_file())
        self.assertTrue(oc.is_file())
        self.assertIn("GENERATED — DO NOT EDIT", base.read_text(encoding="utf-8"))
        self.assertIn("GENERATED — DO NOT EDIT", oc.read_text(encoding="utf-8"))

    def test_mode_content_has_placeholders_resolved(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_modes_for_profile(profile, bindings)
        planning = gen.Paths.modes_output / "planning.mdc"
        content = planning.read_text(encoding="utf-8")
        self.assertNotIn("{{description}}", content)
        self.assertIn("Planning mode for stub stack", content)

    def test_rule_content_has_bindings_resolved(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_rules_for_profile(profile, bindings)
        base = gen.Paths.rules_output / "base.mdc"
        content = base.read_text(encoding="utf-8")
        self.assertNotIn("{{description}}", content)
        self.assertIn("Stub base rule", content)
        self.assertIn("You are a stub specialist.", content)

    def test_output_contract_has_fragment(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_rules_for_profile(profile, bindings)
        oc = gen.Paths.rules_output / "output-contract.mdc"
        content = oc.read_text(encoding="utf-8")
        self.assertIn("BUILD SYSTEM", content)
        self.assertIn("GitHub Actions", content)

    def test_transversal_rules_copied(self):
        gen.Paths.rules_output.mkdir(parents=True, exist_ok=True)
        for tr in gen.TRANSVERSAL_RULES:
            src = gen.Paths.canonical_dir / f"{tr}.mdc"
            if src.is_file():
                dst = gen.Paths.rules_output / f"{tr}.mdc"
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        ci = gen.Paths.rules_output / "continuous-improvement.mdc"
        self.assertTrue(ci.is_file())
        self.assertIn("CONTINUOUS IMPROVEMENT", ci.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency(_IntegrationTestBase):
    def _generate_all(self):
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_modes_for_profile(profile, bindings)
        gen.generate_rules_for_profile(profile, bindings)

    def test_generation_is_idempotent(self):
        self._generate_all()
        backup = pathlib.Path(self.tmpdir.name + "-backup")
        backup.mkdir()
        for f in gen.Paths.modes_output.glob("*.mdc"):
            shutil.copy2(f, backup / f"mode-{f.name}")
        for f in gen.Paths.rules_output.glob("*.mdc"):
            shutil.copy2(f, backup / f"rule-{f.name}")

        self._generate_all()

        for f in gen.Paths.modes_output.glob("*.mdc"):
            backup_f = backup / f"mode-{f.name}"
            self.assertTrue(
                filecmp.cmp(f, backup_f, shallow=False),
                f"Idempotency broken for mode: {f.name}",
            )
        for f in gen.Paths.rules_output.glob("*.mdc"):
            backup_f = backup / f"rule-{f.name}"
            self.assertTrue(
                filecmp.cmp(f, backup_f, shallow=False),
                f"Idempotency broken for rule: {f.name}",
            )
        shutil.rmtree(backup)


# ---------------------------------------------------------------------------
# Shortcut generation per tool
# ---------------------------------------------------------------------------


class TestShortcutsPerTool(_IntegrationTestBase):
    def setUp(self):
        super().setUp()
        profile = self.root / "stack-profile.md"
        self.bindings = gen.load_bindings(profile)
        self.stack_id, self.mode_names = gen.generate_modes_for_profile(profile, self.bindings)
        gen.generate_rules_for_profile(profile, self.bindings)
        for tr in gen.TRANSVERSAL_RULES:
            src = gen.Paths.canonical_dir / f"{tr}.mdc"
            if src.is_file():
                dst = gen.Paths.rules_output / f"{tr}.mdc"
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def _all_bindings(self):
        return [(self.root / "stack-profile.md", self.bindings)]

    def test_cursor_shortcuts(self):
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), ["cursor"])
        self.assertGreater(counts["cursor"], 0)
        self.assertTrue((self.root / ".cursor" / "rules" / "base.mdc").exists())
        self.assertTrue((self.root / ".cursor" / "rules" / "planning.mdc").exists())
        self.assertTrue((self.root / ".cursor" / "commands" / "stub-command.md").exists())

    def test_claude_shortcuts(self):
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), ["claude"])
        self.assertGreater(counts["claude"], 0)
        self.assertTrue((self.root / ".claude" / "rules" / "base.md").is_file())
        self.assertTrue((self.root / ".claude" / "rules" / "planning.md").is_file())

    def test_windsurf_shortcuts(self):
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), ["windsurf"])
        self.assertGreater(counts["windsurf"], 0)
        self.assertTrue((self.root / ".windsurf" / "rules" / "base.md").is_file())

    def test_copilot_shortcuts(self):
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), ["copilot"])
        self.assertGreater(counts["copilot"], 0)
        self.assertTrue((self.root / ".github" / "copilot-instructions.md").is_file())
        self.assertTrue((self.root / ".github" / "instructions" / "planning.instructions.md").is_file())

    def test_codex_shortcuts(self):
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), ["codex"])
        self.assertGreater(counts["codex"], 0)
        self.assertTrue((self.root / ".codex" / "commands" / "stub-command.md").exists())

    def test_multi_tool_shortcuts(self):
        all_tools = list(gen.SUPPORTED_TOOLS)
        counts = gen.generate_shortcuts(self.mode_names, self._all_bindings(), all_tools)
        for tool in all_tools:
            if tool == "gemini":
                # Gemini is context-only (GEMINI.md symlink via CLI init), no shortcuts here.
                self.assertEqual(counts[tool], 0)
                continue
            self.assertGreater(counts[tool], 0, f"No shortcuts for {tool}")
        self.assertTrue((self.root / ".cursor" / "rules" / "base.mdc").exists())
        self.assertTrue((self.root / ".claude" / "rules" / "base.md").is_file())
        self.assertTrue((self.root / ".windsurf" / "rules" / "base.md").is_file())
        self.assertTrue((self.root / ".github" / "copilot-instructions.md").is_file())
        self.assertTrue((self.root / ".codex" / "commands" / "stub-command.md").exists())


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestMultiWorkspaceLastWins(_IntegrationTestBase):
    def test_last_workspace_wins(self):
        profile_path = FIXTURES_DIR / "profiles" / "multi-workspace.md"
        shutil.copy2(profile_path, self.root / "stack-profile.md")
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        ws_ids = gen.generate_rules_for_profile(profile, bindings)
        self.assertEqual(len(ws_ids), 2)
        base = gen.Paths.rules_output / "base.mdc"
        content = base.read_text(encoding="utf-8")
        self.assertIn("specialist two", content)

    def test_xctemplates_dev_skipped(self):
        profile = self.root / "stack-profile.md"
        content = profile.read_text(encoding="utf-8")
        content += "\n- `binding.rule.base.xctemplates-dev.description`: `Should be skipped`\n"
        profile.write_text(content, encoding="utf-8")
        bindings = gen.load_bindings(profile)
        ws_ids = gen.discover_rule_workspaces(bindings)
        self.assertNotIn("xctemplates-dev", ws_ids)


class TestTransversalModeDefaults(_IntegrationTestBase):
    def test_delivery_uses_defaults(self):
        profile_path = FIXTURES_DIR / "profiles" / "transversal-defaults-only.md"
        shutil.copy2(profile_path, self.root / "stack-profile.md")
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_modes_for_profile(profile, bindings)
        delivery = gen.Paths.modes_output / "delivery.mdc"
        content = delivery.read_text(encoding="utf-8")
        self.assertIn("indigo", content)

    def test_devops_uses_defaults(self):
        profile_path = FIXTURES_DIR / "profiles" / "transversal-defaults-only.md"
        shutil.copy2(profile_path, self.root / "stack-profile.md")
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_modes_for_profile(profile, bindings)
        devops = gen.Paths.modes_output / "devops.mdc"
        content = devops.read_text(encoding="utf-8")
        self.assertIn("slate", content)


class TestSharedPrefixResolution(_IntegrationTestBase):
    def test_shared_prefix_fallback(self):
        profile_path = FIXTURES_DIR / "profiles" / "shared-prefix.md"
        shutil.copy2(profile_path, self.root / "stack-profile.md")
        profile = self.root / "stack-profile.md"
        bindings = gen.load_bindings(profile)
        gen.generate_rules_for_profile(profile, bindings)
        base = gen.Paths.rules_output / "base.mdc"
        content = base.read_text(encoding="utf-8")
        self.assertIn("Workspace-specific override", content)
        self.assertIn("Shared specialist.", content)


if __name__ == "__main__":
    unittest.main()
