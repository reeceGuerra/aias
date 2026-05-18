"""Unit tests for generate_modes_and_rules.py — pure functions and minimal I/O."""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import generate_modes_and_rules as gen
import aias_cli


# ---------------------------------------------------------------------------
# 1a — Pure functions (no filesystem)
# ---------------------------------------------------------------------------


class TestUnescapeBinding(unittest.TestCase):
    def test_newline_escape(self):
        self.assertEqual(gen.unescape_binding("line1\\nline2"), "line1\nline2")

    def test_backtick_escape(self):
        self.assertEqual(gen.unescape_binding("use \\`code\\`"), "use `code`")

    def test_no_escapes(self):
        self.assertEqual(gen.unescape_binding("plain text"), "plain text")

    def test_multiple_escapes(self):
        self.assertEqual(
            gen.unescape_binding("a\\nb\\nc\\`d"),
            "a\nb\nc`d",
        )

    def test_empty_string(self):
        self.assertEqual(gen.unescape_binding(""), "")


class TestRenderConditionals(unittest.TestCase):
    def test_true_includes_block(self):
        content = "before{{#if flag}}included{{/if}}after"
        result = gen.render_conditionals(content, {"flag": "true"})
        self.assertEqual(result, "beforeincludedafter")

    def test_false_removes_block(self):
        content = "before{{#if flag}}removed{{/if}}after"
        result = gen.render_conditionals(content, {"flag": "false"})
        self.assertEqual(result, "beforeafter")

    def test_absent_key_removes_block(self):
        content = "before{{#if missing}}removed{{/if}}after"
        result = gen.render_conditionals(content, {})
        self.assertEqual(result, "beforeafter")

    def test_truthy_values(self):
        for val in ("true", "1", "yes", "enabled"):
            with self.subTest(val=val):
                content = "{{#if k}}yes{{/if}}"
                self.assertEqual(gen.render_conditionals(content, {"k": val}), "yes")

    def test_falsy_values(self):
        for val in ("false", "0", "no", "disabled", "anything_else"):
            with self.subTest(val=val):
                content = "{{#if k}}yes{{/if}}"
                self.assertEqual(gen.render_conditionals(content, {"k": val}), "")

    def test_nested_conditionals_loop(self):
        content = "{{#if a}}outer{{#if b}}inner{{/if}}{{/if}}"
        result = gen.render_conditionals(content, {"a": "true", "b": "true"})
        self.assertEqual(result, "outerinner")

    def test_multiline_block(self):
        content = "start\n{{#if flag}}\nline1\nline2\n{{/if}}\nend"
        result = gen.render_conditionals(content, {"flag": "true"})
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_false_multiline_no_residue(self):
        content = "start\n{{#if flag}}\nremoved\n{{/if}}\nend"
        result = gen.render_conditionals(content, {"flag": "false"})
        self.assertNotIn("removed", result)


class TestRenderPlaceholders(unittest.TestCase):
    def test_happy_path(self):
        result = gen.render_placeholders("Hello {{name}}!", {"name": "World"})
        self.assertEqual(result, "Hello World!")

    def test_missing_key_raises(self):
        with self.assertRaises(KeyError):
            gen.render_placeholders("{{missing}}", {})

    def test_skips_hash_slash_keys(self):
        content = "{{#if x}}block{{/if}} and {{name}}"
        result = gen.render_placeholders(content, {"name": "val"})
        self.assertIn("{{#if x}}", result)
        self.assertIn("{{/if}}", result)
        self.assertIn("val", result)

    def test_multiple_placeholders(self):
        result = gen.render_placeholders("{{a}} {{b}}", {"a": "1", "b": "2"})
        self.assertEqual(result, "1 2")


class TestRenderSections(unittest.TestCase):
    def test_section_present(self):
        content = "before\n{{#extra}}\nExtra: {{extra}}\n{{/extra}}\nafter"
        result = gen.render_sections(content, {"extra": "value"})
        self.assertIn("Extra: value", result)
        self.assertIn("before", result)
        self.assertIn("after", result)

    def test_section_empty_removed(self):
        content = "before\n{{#extra}}\nExtra: {{extra}}\n{{/extra}}\nafter"
        result = gen.render_sections(content, {})
        self.assertNotIn("Extra", result)
        self.assertIn("before", result)
        self.assertIn("after", result)

    def test_section_with_newlines(self):
        content = "{{#s}}\nline1\nline2\n{{/s}}"
        result = gen.render_sections(content, {"s": "val"})
        self.assertIn("line1", result)

    def test_section_with_internal_placeholder(self):
        content = "{{#name}}\nHello {{name}}\n{{/name}}"
        result = gen.render_sections(content, {"name": "World"})
        self.assertIn("Hello World", result)


class TestRenderRulePlaceholders(unittest.TestCase):
    def test_replaces_normal_keys(self):
        result = gen.render_rule_placeholders("{{key}}", {"key": "val"})
        self.assertEqual(result, "val")

    def test_skips_hash_keys(self):
        content = "{{#section}}content{{/section}}"
        result = gen.render_rule_placeholders(content, {})
        self.assertEqual(result, content)

    def test_missing_key_raises(self):
        with self.assertRaises(KeyError):
            gen.render_rule_placeholders("{{missing}}", {})


class TestStripTemplateComments(unittest.TestCase):
    def test_removes_comment_lines(self):
        content = "line1\n<!-- comment -->\nline2"
        result = gen.strip_template_comments(content)
        self.assertNotIn("comment", result)
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_no_comments(self):
        content = "line1\nline2"
        result = gen.strip_template_comments(content)
        self.assertIn("line1", result)
        self.assertIn("line2", result)

    def test_multiple_comments(self):
        content = "<!-- a -->\nkeep\n<!-- b -->"
        result = gen.strip_template_comments(content)
        self.assertIn("keep", result)
        self.assertNotIn("a", result)
        self.assertNotIn("b", result)


class TestInjectGeneratedHeader(unittest.TestCase):
    def test_with_frontmatter(self):
        content = "---\ndescription: test\n---\nBody"
        result = gen.inject_generated_header(content)
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("GENERATED — DO NOT EDIT", result)
        self.assertIn("Body", result)

    def test_without_frontmatter(self):
        content = "Just body"
        result = gen.inject_generated_header(content)
        self.assertTrue(result.startswith("GENERATED — DO NOT EDIT"))
        self.assertIn("Just body", result)

    def test_incomplete_frontmatter(self):
        content = "---\nno closing"
        result = gen.inject_generated_header(content)
        self.assertIn("GENERATED — DO NOT EDIT", result)


class TestNormalizeGlobsYaml(unittest.TestCase):
    def test_normal(self):
        result = gen.normalize_globs_yaml("*.swift, *.py")
        self.assertIn('"*.swift"', result)
        self.assertIn('"*.py"', result)

    def test_extra_spaces(self):
        result = gen.normalize_globs_yaml("  *.swift ,  *.py  ")
        self.assertIn('"*.swift"', result)
        self.assertIn('"*.py"', result)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            gen.normalize_globs_yaml("")

    def test_only_commas_raises(self):
        with self.assertRaises(ValueError):
            gen.normalize_globs_yaml(",,,")

    def test_single_glob(self):
        result = gen.normalize_globs_yaml("*.md")
        self.assertEqual(result, '  - "*.md"')

    def test_braces_pattern_splits_on_comma(self):
        result = gen.normalize_globs_yaml("**/*.{h,m}")
        self.assertIn("**/*.{h", result)
        self.assertIn("m}", result)


class TestModeFrontmatterFromBindings(unittest.TestCase):
    def test_core_mode_all_bindings(self):
        bindings = {
            "mode.dev.description": "Dev mode",
            "mode.dev.model": "sonnet-4",
            "mode.dev.color": "green",
            "mode.dev.globs": "*.swift",
        }
        result = gen.mode_frontmatter_from_bindings(bindings, "dev")
        self.assertEqual(result["description"], "Dev mode")
        self.assertEqual(result["model"], "sonnet-4")

    def test_transversal_mode_uses_defaults(self):
        result = gen.mode_frontmatter_from_bindings({}, "delivery")
        self.assertEqual(result["color"], "indigo")
        self.assertIn("Delivery", result["description"])

    def test_transversal_mode_override(self):
        bindings = {
            "mode.delivery.description": "Custom delivery",
            "mode.delivery.model": "opus-4",
            "mode.delivery.color": "red",
            "mode.delivery.globs": "*.md",
        }
        result = gen.mode_frontmatter_from_bindings(bindings, "delivery")
        self.assertEqual(result["description"], "Custom delivery")
        self.assertEqual(result["color"], "red")

    def test_core_mode_missing_key_raises(self):
        bindings = {"mode.dev.description": "Dev", "mode.dev.model": "sonnet-4"}
        with self.assertRaises(KeyError):
            gen.mode_frontmatter_from_bindings(bindings, "dev")


class TestDiscoverRuleWorkspaces(unittest.TestCase):
    def test_single_workspace(self):
        bindings = {"rule.base.myapp.description": "My app"}
        result = gen.discover_rule_workspaces(bindings)
        self.assertEqual(result, ["myapp"])

    def test_multiple_workspaces_sorted(self):
        bindings = {
            "rule.base.beta.description": "Beta",
            "rule.base.alpha.description": "Alpha",
        }
        result = gen.discover_rule_workspaces(bindings)
        self.assertEqual(result, ["alpha", "beta"])

    def test_skips_xctemplates_dev(self):
        bindings = {
            "rule.base.myapp.description": "App",
            "rule.base.xctemplates-dev.description": "Skip",
        }
        result = gen.discover_rule_workspaces(bindings)
        self.assertEqual(result, ["myapp"])

    def test_no_workspaces(self):
        bindings = {"mode.dev.description": "Dev"}
        result = gen.discover_rule_workspaces(bindings)
        self.assertEqual(result, [])


class TestDetectSharedPrefix(unittest.TestCase):
    def test_present(self):
        bindings = {"rule.base.ios_shared.description": "Shared"}
        result = gen.detect_shared_prefix(bindings)
        self.assertEqual(result, "ios_shared")

    def test_absent(self):
        bindings = {"rule.base.myapp.description": "App"}
        result = gen.detect_shared_prefix(bindings)
        self.assertIsNone(result)

    def test_multiple_returns_first(self):
        bindings = {
            "rule.base.abc_shared.description": "A",
            "rule.base.xyz_shared.description": "Z",
        }
        result = gen.detect_shared_prefix(bindings)
        self.assertIn("_shared", result)


class TestGetRuleBinding(unittest.TestCase):
    def test_workspace_level(self):
        bindings = {"rule.base.myapp.description": "App desc"}
        result = gen.get_rule_binding(bindings, "myapp", "base", "description")
        self.assertEqual(result, "App desc")

    def test_shared_fallback(self):
        bindings = {"rule.base.ios_shared.description": "Shared desc"}
        result = gen.get_rule_binding(
            bindings, "myapp", "base", "description", shared_prefix="ios_shared"
        )
        self.assertEqual(result, "Shared desc")

    def test_platform_fallback(self):
        bindings = {"rule.base.description": "Platform desc"}
        result = gen.get_rule_binding(bindings, "myapp", "base", "description")
        self.assertEqual(result, "Platform desc")

    def test_workspace_takes_priority(self):
        bindings = {
            "rule.base.myapp.description": "WS",
            "rule.base.ios_shared.description": "Shared",
            "rule.base.description": "Platform",
        }
        result = gen.get_rule_binding(
            bindings, "myapp", "base", "description", shared_prefix="ios_shared"
        )
        self.assertEqual(result, "WS")

    def test_absent_returns_none(self):
        result = gen.get_rule_binding({}, "myapp", "base", "description")
        self.assertIsNone(result)

    def test_unescapes_values(self):
        bindings = {"rule.base.myapp.description": "line1\\nline2"}
        result = gen.get_rule_binding(bindings, "myapp", "base", "description")
        self.assertEqual(result, "line1\nline2")


class TestBuildFileHeaderSection(unittest.TestCase):
    def test_basic(self):
        result = gen.build_file_header_section("MyApp", "John Doe")
        self.assertIn("MyApp", result)
        self.assertIn("John Doe", result)
        self.assertIn("FILENAME.swift", result)
        self.assertIn("DD/MM/YY", result)

    def test_special_characters(self):
        result = gen.build_file_header_section("My App (iOS)", "María García")
        self.assertIn("My App (iOS)", result)
        self.assertIn("María García", result)


class TestResolveTools(unittest.TestCase):
    def test_flag_overrides_binding(self):
        bindings = [(pathlib.Path("p.md"), {"generation.tools": "claude"})]
        result = gen._resolve_tools("cursor,windsurf", bindings)
        self.assertEqual(result, ["cursor", "windsurf"])

    def test_fallback_to_binding(self):
        bindings = [(pathlib.Path("p.md"), {"generation.tools": "cursor,claude"})]
        result = gen._resolve_tools(None, bindings)
        self.assertEqual(result, ["cursor", "claude"])

    def test_no_flag_no_binding_returns_all(self):
        result = gen._resolve_tools(None, [])
        self.assertEqual(result, list(gen.SUPPORTED_TOOLS))

    def test_empty_flag_returns_all(self):
        result = gen._resolve_tools("", [])
        self.assertEqual(result, list(gen.SUPPORTED_TOOLS))


class TestGeminiSupportConsistency(unittest.TestCase):
    """BL-S48b — Gemini consistency in SUPPORTED_TOOLS + TOOL_CONTEXT_MAP."""

    def test_gemini_in_supported_tools(self):
        self.assertIn("gemini", gen.SUPPORTED_TOOLS)

    def test_gemini_context_mapping(self):
        self.assertEqual(aias_cli.TOOL_CONTEXT_MAP.get("GEMINI.md"), ("gemini",))

    def test_supported_tools_single_source_of_truth(self):
        self.assertIs(aias_cli.SUPPORTED_TOOLS, gen.SUPPORTED_TOOLS)


# ---------------------------------------------------------------------------
# 1b — Functions with minimal I/O (tempfile)
# ---------------------------------------------------------------------------


class TestLoadBindings(unittest.TestCase):
    def _write_temp(self, content: str) -> pathlib.Path:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        self.addCleanup(lambda: os.unlink(f.name))
        return pathlib.Path(f.name)

    def test_happy_path(self):
        path = self._write_temp(
            "# Profile\n\n- `binding.generation.stack_id`: `my-stack`\n"
        )
        result = gen.load_bindings(path)
        self.assertEqual(result["generation.stack_id"], "my-stack")

    def test_lines_without_binding_ignored(self):
        path = self._write_temp(
            "# Title\n\nSome text\n\n- `binding.key`: `val`\n"
        )
        result = gen.load_bindings(path)
        self.assertEqual(len(result), 1)
        self.assertEqual(result["key"], "val")

    def test_no_bindings_raises(self):
        path = self._write_temp("# Profile\n\nNo bindings here.\n")
        with self.assertRaises(ValueError):
            gen.load_bindings(path)

    def test_multiple_bindings(self):
        path = self._write_temp(
            "- `binding.a`: `1`\n- `binding.b`: `2`\n- `binding.c`: `3`\n"
        )
        result = gen.load_bindings(path)
        self.assertEqual(len(result), 3)

    def test_backtick_in_value(self):
        path = self._write_temp("- `binding.code`: `use \\`foo\\``\n")
        result = gen.load_bindings(path)
        self.assertEqual(result["code"], "use \\`foo\\`")


class TestExtractTemplateContent(unittest.TestCase):
    def _write_temp(self, content: str) -> pathlib.Path:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        self.addCleanup(lambda: os.unlink(f.name))
        return pathlib.Path(f.name)

    def test_happy_path(self):
        path = self._write_temp("# Template\n\n```markdown\nContent here\n```\n")
        result = gen.extract_template_content(path)
        self.assertEqual(result, "Content here\n")

    def test_no_block_raises(self):
        path = self._write_temp("# No markdown block here\n")
        with self.assertRaises(ValueError):
            gen.extract_template_content(path)


class TestExtractDescription(unittest.TestCase):
    def _write_temp(self, content: str) -> pathlib.Path:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".mdc", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        self.addCleanup(lambda: os.unlink(f.name))
        return pathlib.Path(f.name)

    def test_with_frontmatter(self):
        path = self._write_temp("---\ndescription: My mode\n---\nBody")
        result = gen._extract_description(path)
        self.assertEqual(result, "My mode")

    def test_without_frontmatter(self):
        path = self._write_temp("No frontmatter here")
        result = gen._extract_description(path)
        self.assertEqual(result, "")

    def test_long_description_truncates(self):
        long_desc = "A" * 150
        path = self._write_temp(f"---\ndescription: {long_desc}\n---\nBody")
        result = gen._extract_description(path)
        self.assertEqual(len(result), 120)
        self.assertTrue(result.endswith("..."))

    def test_no_description_field(self):
        path = self._write_temp("---\nother: value\n---\nBody")
        result = gen._extract_description(path)
        self.assertEqual(result, "")

    def test_nonexistent_file(self):
        result = gen._extract_description(pathlib.Path("/nonexistent/file.mdc"))
        self.assertEqual(result, "")


class TestCreateSymlink(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_create_new(self):
        target = self.root / "target.txt"
        target.write_text("content")
        link = self.root / "link.txt"
        gen._create_symlink(link, target)
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.read_text(), "content")

    def test_overwrite_existing_file(self):
        target = self.root / "target.txt"
        target.write_text("new")
        link = self.root / "link.txt"
        link.write_text("old")
        gen._create_symlink(link, target)
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.read_text(), "new")

    def test_overwrite_broken_symlink(self):
        target = self.root / "target.txt"
        target.write_text("content")
        link = self.root / "link.txt"
        link.symlink_to("/nonexistent/path")
        gen._create_symlink(link, target)
        self.assertTrue(link.is_symlink())
        self.assertTrue(link.exists())

    def test_creates_parent_directories(self):
        target = self.root / "target.txt"
        target.write_text("content")
        link = self.root / "sub" / "dir" / "link.txt"
        gen._create_symlink(link, target)
        self.assertTrue(link.is_symlink())


class TestDiscoverProfiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        self._orig_root = gen.Paths.root
        gen.init_paths(self.root)

    def tearDown(self):
        gen.init_paths(self._orig_root)
        self.tmpdir.cleanup()

    def test_profile_exists(self):
        (self.root / "stack-profile.md").write_text("- `binding.x`: `y`\n")
        result = gen.discover_profiles()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "stack-profile.md")

    def test_profile_missing_raises(self):
        with self.assertRaises(ValueError):
            gen.discover_profiles()


# ---------------------------------------------------------------------------
# _validate_sections (aias_cli)
# ---------------------------------------------------------------------------

class TestValidateSections(unittest.TestCase):
    """Tests for aias_cli._validate_sections (pure, no filesystem)."""

    CONFLUENCE_MANDATORY = aias_cli.EXPECTED_SECTIONS["confluence-config.md"]["mandatory"]
    CONFLUENCE_OPTIONAL = aias_cli.EXPECTED_SECTIONS["confluence-config.md"]["optional"]

    def _make_content(self, headings, body=""):
        return "\n".join(f"## {h}" for h in headings) + "\n" + body

    def test_all_mandatory_present(self):
        content = self._make_content(self.CONFLUENCE_MANDATORY)
        missing, inconsistencies = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, [])
        self.assertEqual(inconsistencies, [])

    def test_missing_mandatory_section(self):
        headings = [h for h in self.CONFLUENCE_MANDATORY if h != "Rules"]
        content = self._make_content(headings)
        missing, _ = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, ["Rules"])

    def test_heading_normalization(self):
        headings = [
            "Space", "Publishing Hierarchy", "TECH Resolution (priority order)",
            "Date Resolution", "Navigation Algorithm (find-or-create)",
            "Rules", "Example",
        ]
        content = self._make_content(headings)
        missing, _ = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, [])

    def test_optional_section_absent_no_error(self):
        content = self._make_content(self.CONFLUENCE_MANDATORY)
        missing, inconsistencies = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, [])
        self.assertEqual(inconsistencies, [])

    def test_toc_cross_reference_inconsistency(self):
        content = self._make_content(
            self.CONFLUENCE_MANDATORY,
            body="call injectTocIfMissing(cloudId, pageId)")
        missing, inconsistencies = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, [])
        self.assertEqual(len(inconsistencies), 1)
        self.assertEqual(inconsistencies[0][0], "cross-reference")

    def test_toc_present_no_inconsistency(self):
        headings = self.CONFLUENCE_MANDATORY + ["Table of Contents"]
        content = self._make_content(
            headings, body="call injectTocIfMissing(cloudId, pageId)")
        missing, inconsistencies = aias_cli._validate_sections(
            content, self.CONFLUENCE_MANDATORY, self.CONFLUENCE_OPTIONAL,
            filename="confluence-config.md")
        self.assertEqual(missing, [])
        self.assertEqual(inconsistencies, [])

    def test_all_three_file_types(self):
        for fname, schema in aias_cli.EXPECTED_SECTIONS.items():
            content = self._make_content(schema["mandatory"])
            missing, inconsistencies = aias_cli._validate_sections(
                content, schema["mandatory"], schema["optional"], filename=fname)
            self.assertEqual(missing, [], f"Unexpected missing for {fname}")
            self.assertEqual(inconsistencies, [], f"Unexpected inconsistency for {fname}")


class TestShortcutRuntimeIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        self.orig_root = aias_cli.ROOT
        aias_cli.ROOT = self.root

    def tearDown(self):
        aias_cli.ROOT = self.orig_root
        self.tmpdir.cleanup()

    def _run_checks(self, selected_tools):
        results = []
        aias_cli._check_shortcut_runtime_integrity(selected_tools, results)
        return {name: (status, detail) for name, status, detail in results}

    def test_ok_empty_dirs(self):
        (self.root / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "agents").mkdir(parents=True, exist_ok=True)

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Shortcut dirs"][0], "OK")
        self.assertEqual(checks["Shortcut symlinks"][0], "OK")
        self.assertEqual(checks["Shortcut boundary"][0], "OK")
        self.assertEqual(checks["Shortcut content refs"][0], "OK")

    def test_broken_symlink_detected(self):
        rules_dir = self.root / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        (rules_dir / "broken.mdc").symlink_to("missing-target.mdc")

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Shortcut symlinks"][0], "FAIL")

    def test_out_of_bounds_symlink_detected(self):
        rules_dir = self.root / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        outside = self.root / "outside.mdc"
        outside.write_text("x", encoding="utf-8")
        (rules_dir / "bad-boundary.mdc").symlink_to(os.path.relpath(outside, rules_dir))

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Shortcut boundary"][0], "FAIL")

    def test_within_boundary_ok(self):
        rules_dir = self.root / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        canonical_dir = self.root / "aias-config" / "rules"
        canonical_dir.mkdir(parents=True, exist_ok=True)
        canonical_file = canonical_dir / "base.mdc"
        canonical_file.write_text("ok", encoding="utf-8")
        (rules_dir / "base.mdc").symlink_to(os.path.relpath(canonical_file, rules_dir))

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Shortcut boundary"][0], "OK")

    def test_missing_enriched_text_ref(self):
        rules_dir = self.root / ".claude" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (self.root / ".claude" / "commands").mkdir(parents=True, exist_ok=True)
        (rules_dir / "base.md").write_text(
            "Read and follow aias-config/rules/nonexistent.mdc",
            encoding="utf-8",
        )

        checks = self._run_checks(["claude"])
        self.assertEqual(checks["Shortcut content refs"][0], "WARN")

    def test_missing_dir_warns(self):
        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Shortcut dirs"][0], "WARN")

    def test_gemini_skipped(self):
        results = []
        aias_cli._check_shortcut_runtime_integrity(["gemini"], results)
        self.assertEqual(results, [])


class TestNestedContextHelpers(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        self.orig_root = aias_cli.ROOT
        aias_cli.ROOT = self.root

    def tearDown(self):
        aias_cli.ROOT = self.orig_root
        self.tmpdir.cleanup()

    def test_parse_max_depth(self):
        self.assertEqual(aias_cli._parse_max_depth(["--max-depth", "5"]), 5)
        self.assertEqual(aias_cli._parse_max_depth([], default=0), 0)
        with self.assertRaises(ValueError):
            aias_cli._parse_max_depth(["--max-depth", "-1"])

    def test_discover_rhoaias_files_with_depth(self):
        (self.root / "RHOAIAS.md").write_text("root", encoding="utf-8")
        nested = self.root / "packages" / "mobile"
        nested.mkdir(parents=True, exist_ok=True)
        (nested / "RHOAIAS.md").write_text("nested", encoding="utf-8")

        depth0 = aias_cli._discover_rhoaias_files(max_depth=0)
        depth5 = aias_cli._discover_rhoaias_files(max_depth=5)

        self.assertEqual(len(depth0), 1)
        self.assertEqual(len(depth5), 2)

    def test_ensure_context_symlinks_for_nested_rhoaias(self):
        (self.root / "RHOAIAS.md").write_text("root", encoding="utf-8")
        nested_dir = self.root / "packages" / "mobile"
        nested_dir.mkdir(parents=True, exist_ok=True)
        nested_ctx = nested_dir / "RHOAIAS.md"
        nested_ctx.write_text("nested", encoding="utf-8")

        created = aias_cli._ensure_context_symlinks_for_rhoaias(
            [nested_ctx], ["cursor", "claude", "codex", "gemini"]
        )
        self.assertGreaterEqual(created, 1)
        self.assertTrue((nested_dir / "AGENTS.md").is_symlink())
        self.assertTrue((nested_dir / "CLAUDE.md").is_symlink())
        self.assertTrue((nested_dir / "codex.md").is_symlink())
        self.assertTrue((nested_dir / "GEMINI.md").is_symlink())

    def test_ensure_context_symlinks_replaces_stale_symlink(self):
        stale_target = self.root / "old" / "RHOAIAS.md"
        stale_target.parent.mkdir(parents=True, exist_ok=True)
        stale_target.write_text("old", encoding="utf-8")

        nested_dir = self.root / "packages" / "mobile"
        nested_dir.mkdir(parents=True, exist_ok=True)
        nested_ctx = nested_dir / "RHOAIAS.md"
        nested_ctx.write_text("nested", encoding="utf-8")

        link_path = nested_dir / "AGENTS.md"
        link_path.symlink_to(os.path.relpath(stale_target, nested_dir))

        created = aias_cli._ensure_context_symlinks_for_rhoaias(
            [nested_ctx], ["cursor"]
        )

        self.assertEqual(created, 1)
        self.assertTrue(link_path.is_symlink())
        self.assertEqual(
            (link_path.parent / os.readlink(link_path)).resolve(),
            nested_ctx.resolve(),
        )


class TestCommandSkillFrontmatter(unittest.TestCase):
    """BL-S36: advisory/operative skills are correctly identified as command-shaped."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.skill_dir = pathlib.Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_skill(self, category: str, dmi: str) -> pathlib.Path:
        d = self.skill_dir / f"skill-{category}"
        d.mkdir()
        (d / "SKILL.md").write_text(
            f"---\nname: test\ncategory: {category}\ndisable-model-invocation: {dmi}\n---\n",
            encoding="utf-8",
        )
        return d

    def test_advisory_is_command_skill(self):
        d = self._make_skill("advisory", "true")
        self.assertTrue(gen._is_command_skill(d))

    def test_operative_is_command_skill(self):
        d = self._make_skill("operative", "true")
        self.assertTrue(gen._is_command_skill(d))

    def test_mcp_not_command_skill(self):
        d = self._make_skill("mcp", "false")
        self.assertFalse(gen._is_command_skill(d))

    def test_knowledge_not_command_skill(self):
        d = self._make_skill("knowledge", "false")
        self.assertFalse(gen._is_command_skill(d))

    def test_advisory_with_dmi_false_not_command_skill(self):
        d = self._make_skill("advisory", "false")
        self.assertFalse(gen._is_command_skill(d))

    def test_read_skill_frontmatter_parses_fields(self):
        d = self._make_skill("operative", "true")
        fm = gen._read_skill_frontmatter(d / "SKILL.md")
        self.assertEqual(fm.get("category"), "operative")
        self.assertEqual(fm.get("disable-model-invocation"), "true")

    def test_missing_skill_md_returns_empty(self):
        d = self.skill_dir / "empty-dir"
        d.mkdir()
        self.assertFalse(gen._is_command_skill(d))


class TestLegacyCommandShortcutDetection(unittest.TestCase):
    """BL-S36: aias health detects shortcuts still pointing to retired aias/.commands/."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        self.orig_root = aias_cli.ROOT
        aias_cli.ROOT = self.root

    def tearDown(self):
        aias_cli.ROOT = self.orig_root
        self.tmpdir.cleanup()

    def _run_checks(self, selected_tools):
        results = []
        aias_cli._check_shortcut_runtime_integrity(selected_tools, results)
        return {name: (status, detail) for name, status, detail in results}

    def test_no_legacy_shortcuts_ok(self):
        (self.root / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Legacy command shortcuts"][0], "OK")

    def test_legacy_shortcut_detected(self):
        """Legacy shortcut in .cursor/skills/ pointing to retired aias/.commands/ is detected."""
        legacy_dir = self.root / "aias" / ".commands"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "blueprint.md"
        legacy_file.write_text("legacy", encoding="utf-8")

        # Shortcuts now live in .cursor/skills/ — place the legacy symlink there.
        skills_dir = self.root / ".cursor" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        rel = os.path.relpath(legacy_file, skills_dir)
        (skills_dir / "blueprint.md").symlink_to(rel)

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Legacy command shortcuts"][0], "WARN")
        self.assertIn("aias/.commands", checks["Legacy command shortcuts"][1])

    def test_stale_cursor_commands_dir_warns(self):
        """Stale .cursor/commands/ directory with content emits a WARN."""
        (self.root / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        stale_dir = self.root / ".cursor" / "commands"
        stale_dir.mkdir(parents=True, exist_ok=True)
        (stale_dir / "old-command.md").write_text("stale", encoding="utf-8")

        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Stale .cursor/commands/"][0], "WARN")
        self.assertIn("old-command.md", checks["Stale .cursor/commands/"][1])

    def test_absent_cursor_commands_dir_ok(self):
        """Absent .cursor/commands/ directory reports OK for the stale check."""
        (self.root / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)
        (self.root / ".cursor" / "skills").mkdir(parents=True, exist_ok=True)
        checks = self._run_checks(["cursor"])
        self.assertEqual(checks["Stale .cursor/commands/"][0], "OK")


class TestReviewSubagentIntegrity(unittest.TestCase):
    """BL-S53: aias health validates the three-tier sub-agent chain.

    Three-tier model:
      aias/.canonical/subagents/ (framework canonical, read-only)
      → aias-config/subagents/  (project-owned copies)
      → .cursor/agents/         (tool-specific symlinks)
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmpdir.name)
        self.orig_root = aias_cli.ROOT
        self.orig_subagents_output = aias_cli.SUBAGENTS_OUTPUT_DIR
        aias_cli.ROOT = self.root
        # aias/.canonical/subagents/ — framework canonical
        self.fw_agents = self.root / "aias" / ".canonical" / "subagents"
        self.fw_agents.mkdir(parents=True, exist_ok=True)
        # aias-config/subagents/ — project-owned copies
        self.config_agents = self.root / "aias-config" / "subagents"
        self.config_agents.mkdir(parents=True, exist_ok=True)
        aias_cli.SUBAGENTS_OUTPUT_DIR = self.config_agents
        # .cursor/agents/ — tool-specific symlinks
        self.cursor_agents = self.root / ".cursor" / "agents"
        self.cursor_agents.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        aias_cli.ROOT = self.orig_root
        aias_cli.SUBAGENTS_OUTPUT_DIR = self.orig_subagents_output
        self.tmpdir.cleanup()

    def _write_config_agent(self, name: str, readonly: str = "true", is_background: str = "false") -> None:
        """Write a sub-agent file to aias-config/subagents/ (tier 2)."""
        content = (
            f"---\nname: {name}\nreadonly: {readonly}\nis_background: {is_background}\n---\n"
            f"# {name}\n"
        )
        (self.config_agents / name).write_text(content, encoding="utf-8")

    def _add_cursor_symlink(self, name: str) -> None:
        """Create a .cursor/agents/ symlink pointing to aias-config/subagents/ (tier 3)."""
        src = self.config_agents / name
        rel = os.path.relpath(src, self.cursor_agents)
        link = self.cursor_agents / name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(rel)

    def _run_checks(self):
        results = []
        aias_cli._check_review_subagent_integrity(results)
        return {name: (status, detail) for name, status, detail in results}

    def test_all_present_and_valid(self):
        """Full three-tier chain present and valid."""
        for agent_name in aias_cli.REVIEW_SUBAGENTS:
            self._write_config_agent(agent_name)
            self._add_cursor_symlink(agent_name)
        checks = self._run_checks()
        self.assertEqual(checks["Review sub-agents (config)"][0], "OK")
        self.assertEqual(checks["Review sub-agents (shortcuts)"][0], "OK")
        self.assertEqual(checks["Review sub-agents invariants"][0], "OK")
        self.assertNotIn("Review sub-agents (legacy)", checks)

    def test_missing_config_subagent_warns(self):
        """Missing aias-config/subagents/ file emits WARN."""
        for agent_name in list(aias_cli.REVIEW_SUBAGENTS)[:-1]:
            self._write_config_agent(agent_name)
            self._add_cursor_symlink(agent_name)
        checks = self._run_checks()
        self.assertEqual(checks["Review sub-agents (config)"][0], "WARN")

    def test_missing_cursor_symlink_warns(self):
        """Missing .cursor/agents/ symlink emits WARN for shortcuts."""
        for agent_name in aias_cli.REVIEW_SUBAGENTS:
            self._write_config_agent(agent_name)
        # No symlinks created
        checks = self._run_checks()
        self.assertEqual(checks["Review sub-agents (shortcuts)"][0], "WARN")

    def test_wrong_readonly_fails_invariant(self):
        for agent_name in aias_cli.REVIEW_SUBAGENTS:
            self._write_config_agent(agent_name, readonly="false")
            self._add_cursor_symlink(agent_name)
        checks = self._run_checks()
        self.assertEqual(checks["Review sub-agents invariants"][0], "FAIL")
        self.assertIn("readonly", checks["Review sub-agents invariants"][1])

    def test_wrong_is_background_fails_invariant(self):
        for agent_name in aias_cli.REVIEW_SUBAGENTS:
            self._write_config_agent(agent_name, is_background="true")
            self._add_cursor_symlink(agent_name)
        checks = self._run_checks()
        self.assertEqual(checks["Review sub-agents invariants"][0], "FAIL")
        self.assertIn("is_background", checks["Review sub-agents invariants"][1])

    def test_legacy_symlink_target_warns(self):
        """Symlinks pointing to old aias/.cursor/agents/ location emit legacy WARN."""
        old_fw = self.root / "aias" / ".cursor" / "agents"
        old_fw.mkdir(parents=True, exist_ok=True)
        for agent_name in aias_cli.REVIEW_SUBAGENTS:
            # Write file at old location (not in aias-config/subagents/)
            src = old_fw / agent_name
            src.write_text(
                f"---\nname: {agent_name}\nreadonly: true\nis_background: false\n---\n",
                encoding="utf-8",
            )
            rel = os.path.relpath(src, self.cursor_agents)
            (self.cursor_agents / agent_name).symlink_to(rel)
        checks = self._run_checks()
        self.assertIn("Review sub-agents (legacy)", checks)
        self.assertEqual(checks["Review sub-agents (legacy)"][0], "WARN")


# ---------------------------------------------------------------------------
# Phase 9 (v9.4 + v9.5) — Contract invariants on canonical sources
#
# These tests validate canonical source-of-truth files (sub-agents, skills,
# contracts) rather than pure code paths. They guard against regressions in
# the invariants introduced by BL-S73, BL-S74, BL-S77, and BL-S79.
# ---------------------------------------------------------------------------


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


def _read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


class TestSubagentToolBoundary(unittest.TestCase):
    """BL-S74 — every canonical sub-agent declares Tool Boundary in body.

    Sub-agents MUST NOT invoke tool runtimes. The contract is enforced
    textually: each canonical sub-agent file MUST contain a body section
    that mentions Tool Boundary AND prohibits tool calls AND points at the
    Context Gap escape hatch.
    """

    CANONICAL_DIR = REPO_ROOT / "aias" / ".canonical" / "subagents"
    REQUIRED_AGENTS = (
        "aias-architecture-reviewer.md",
        "aias-correctness-reviewer.md",
        "aias-quality-reviewer.md",
        "aias-reflector.md",
        "aias-security-auditor.md",
        "aias-test-auditor.md",
    )

    def test_all_canonical_files_present(self):
        for name in self.REQUIRED_AGENTS:
            path = self.CANONICAL_DIR / name
            self.assertTrue(path.exists(), f"missing canonical sub-agent: {path}")

    def test_tool_boundary_heading_present(self):
        for name in self.REQUIRED_AGENTS:
            with self.subTest(agent=name):
                body = _read_text(self.CANONICAL_DIR / name)
                self.assertIn(
                    "Tool Boundary",
                    body,
                    f"{name} body must include a 'Tool Boundary' section",
                )

    def test_tool_boundary_prohibits_tool_calls(self):
        for name in self.REQUIRED_AGENTS:
            with self.subTest(agent=name):
                body = _read_text(self.CANONICAL_DIR / name).lower()
                self.assertIn("must not", body, f"{name} must include MUST NOT directive")
                self.assertTrue(
                    any(kw in body for kw in ("invoke", "tool", "mcp")),
                    f"{name} Tool Boundary must reference tool invocation prohibition",
                )

    def test_context_gap_escape_documented(self):
        for name in self.REQUIRED_AGENTS:
            with self.subTest(agent=name):
                body = _read_text(self.CANONICAL_DIR / name)
                self.assertIn(
                    "Context Gap",
                    body,
                    f"{name} must document the [Context Gap] finding escape hatch",
                )

    def test_frontmatter_invariants_unchanged(self):
        """BL-S74 must not relax readonly/is_background invariants."""
        for name in self.REQUIRED_AGENTS:
            with self.subTest(agent=name):
                body = _read_text(self.CANONICAL_DIR / name)
                self.assertIn("readonly: true", body)
                self.assertIn("is_background: false", body)


class TestDispatchesSchema(unittest.TestCase):
    """BL-S73 — readme-multi-agent-review v1.2 documents dispatches[] schema.

    The contract MUST describe the host-owned telemetry schema with all
    required fields (subagent, started_at, ended_at) and clarify that
    /peer-review writes no telemetry.
    """

    CONTRACT = REPO_ROOT / "aias" / "contracts" / "readme-multi-agent-review.md"
    REFERENCE = REPO_ROOT / "aias" / ".skills" / "rho-aias" / "reference.md"

    def test_contract_declares_v1_2(self):
        body = _read_text(self.CONTRACT)
        self.assertRegex(
            body,
            r"^# Multi-Agent Review Contract \(v1\.\d+\)",
            "readme-multi-agent-review header must declare MAJOR v1",
        )

    def test_contract_documents_dispatches_section(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("Dispatch Telemetry", body)
        for field in ("subagent", "started_at", "ended_at"):
            with self.subTest(field=field):
                self.assertIn(field, body, f"dispatches[] schema must mention '{field}'")

    def test_contract_clarifies_self_review_only(self):
        body = _read_text(self.CONTRACT).lower()
        self.assertIn("self-review", body)
        self.assertIn("peer-review", body)

    def test_reference_extends_command_log_schema(self):
        body = _read_text(self.REFERENCE)
        self.assertIn("dispatches", body)


class TestCanonicalSectionTitles(unittest.TestCase):
    """BL-S77 — producer skills MUST NOT bleed internal category labels.

    The invariant: `## Category N: <title>` is an internal data-collection
    label and MUST NOT appear as a heading in produced artifacts. The skill
    must declare its canonical artifact heading explicitly.
    """

    SKILLS_DIR = REPO_ROOT / "aias" / ".skills"
    PRODUCERS = (
        "blueprint",
        "enrich",
        "charter",
        "issue",
        "fix",
        "trace",
        "assessment",
        "report",
    )
    CONTRACT = REPO_ROOT / "aias" / "contracts" / "readme-artifact.md"

    def test_contract_declares_canonical_section_titles(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("Canonical Section Titles", body)
        self.assertRegex(
            body,
            r"^# Artifact Contract.*\(v2\.\d+\)",
            "readme-artifact header must declare MAJOR v2",
        )

    def test_producers_reference_canonical_heading_rule(self):
        for skill in self.PRODUCERS:
            with self.subTest(skill=skill):
                path = self.SKILLS_DIR / skill / "SKILL.md"
                self.assertTrue(path.exists(), f"missing skill: {path}")
                body = _read_text(path)
                self.assertIn(
                    "Canonical",
                    body,
                    f"{skill} must declare Canonical headings explicitly",
                )

    def test_blueprint_does_not_emit_category_prefix_in_output(self):
        """Producer guidance must not instruct emitting '## Category N: …' as an artifact heading.

        We allow internal data-collection labels (### Category N: in skill body)
        but the skill MUST flag them as internal-only.
        """
        path = self.SKILLS_DIR / "blueprint" / "SKILL.md"
        body = _read_text(path)
        # The skill MUST contain the anti-pattern guidance.
        self.assertIn("Canonical artifact heading", body)


class TestKindEnumSchema(unittest.TestCase):
    """BL-S79 — TODO kind enum is a closed set: validation | amendment_dor | amendment_dod.

    Backward compatibility: absent `kind` is treated as `validation`.
    """

    REFERENCE = REPO_ROOT / "aias" / ".skills" / "rho-aias" / "reference.md"
    CONTRACT = REPO_ROOT / "aias" / "contracts" / "readme-artifact.md"
    VALID_KINDS = ("validation", "amendment_dor", "amendment_dod")

    def test_reference_declares_kind_enum(self):
        body = _read_text(self.REFERENCE)
        self.assertIn("kind", body)
        for kind in self.VALID_KINDS:
            with self.subTest(kind=kind):
                self.assertIn(kind, body, f"reference must document '{kind}'")

    def test_reference_documents_backward_compat(self):
        body = _read_text(self.REFERENCE).lower()
        self.assertIn("backward", body)
        self.assertIn("validation", body)

    def test_contract_extends_todo_ownership(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("amendment_dor", body)
        self.assertIn("amendment_dod", body)


class TestLegacySingleBlockHardFail(unittest.TestCase):
    """BL-S79 — /validate-plan v2.0 MUST hard-fail on legacy combined section.

    The legacy `## Proposed DoR/DoD Amendments` block is FORBIDDEN. The skill
    body must document the hard-fail mechanism and point to QUICKSTART.
    """

    VALIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "validate-plan" / "SKILL.md"
    QUICKSTART = REPO_ROOT / "aias" / "docs" / "QUICKSTART.md"

    def test_validate_plan_documents_hard_fail(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("Proposed DoR/DoD Amendments", body)
        self.assertTrue(
            "hard-fail" in body.lower() or "hard fail" in body.lower(),
            "validate-plan must document the hard-fail behaviour",
        )

    def test_validate_plan_references_split_sections(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("Proposed DoR Amendments", body)
        self.assertIn("Proposed DoD Amendments", body)

    def test_validate_plan_is_major_v2(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertRegex(body, r"version:\s*2\.\d+\.\d+", "validate-plan must be v2.x (MAJOR)")

    def test_quickstart_documents_migration(self):
        body = _read_text(self.QUICKSTART)
        self.assertIn("Upgrading from v9.4 to v9.5", body)
        self.assertIn("Proposed DoR/DoD Amendments", body)


class TestAmendmentRoutingInvariant(unittest.TestCase):
    """BL-S79 — consolidate-plan v2.0 routes by kind with strict targeting.

    - kind: validation     → named artifact (e.g., technical.plan.md)
    - kind: amendment_dor  → dor.plan.md (only)
    - kind: amendment_dod  → dod.plan.md (only)
    """

    CONSOLIDATE = REPO_ROOT / "aias" / ".skills" / "consolidate-plan" / "SKILL.md"
    RHO_AIAS = REPO_ROOT / "aias" / ".skills" / "rho-aias" / "SKILL.md"

    def test_consolidate_plan_is_major_v2(self):
        body = _read_text(self.CONSOLIDATE)
        self.assertRegex(body, r"version:\s*2\.\d+\.\d+", "consolidate-plan must be v2.x (MAJOR)")

    def test_consolidate_plan_routes_each_kind(self):
        body = _read_text(self.CONSOLIDATE)
        for kind in ("amendment_dor", "amendment_dod", "validation"):
            with self.subTest(kind=kind):
                self.assertIn(kind, body, f"consolidate-plan must route '{kind}'")

    def test_consolidate_plan_targets_correct_artifacts(self):
        body = _read_text(self.CONSOLIDATE)
        self.assertIn("dor.plan.md", body)
        self.assertIn("dod.plan.md", body)

    def test_rho_aias_documents_routing_invariant(self):
        body = _read_text(self.RHO_AIAS)
        self.assertIn("Amendment routing invariant", body)


class TestProposedBlockSplit(unittest.TestCase):
    """BL-S79 — blueprint emits two separate sections, never single-block.

    The skill body must declare both canonical Proposed sections AND must
    forbid the combined section.
    """

    BLUEPRINT = REPO_ROOT / "aias" / ".skills" / "blueprint" / "SKILL.md"
    VALIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "validate-plan" / "SKILL.md"

    def test_blueprint_declares_two_sections(self):
        body = _read_text(self.BLUEPRINT)
        self.assertIn("Proposed DoR Amendments", body)
        self.assertIn("Proposed DoD Amendments", body)

    def test_blueprint_forbids_combined_section(self):
        body = _read_text(self.BLUEPRINT)
        self.assertIn("Proposed DoR/DoD Amendments", body)
        self.assertTrue(
            "FORBIDDEN" in body or "forbidden" in body.lower(),
            "blueprint must explicitly forbid the legacy combined section",
        )

    def test_blueprint_documents_inline_capture_not_modification(self):
        """v9.6+ — blueprint MUST document inline capture as Proposed bullet sub-field,
        NOT inline modification of dor.plan.md / dod.plan.md."""
        body = _read_text(self.BLUEPRINT)
        self.assertIn(
            "Inline confirmation",
            body,
            "blueprint must document the **Inline confirmation**: sub-field marker (v9.6+)",
        )
        self.assertNotIn(
            "Resolution Log",
            body,
            "blueprint must not reference the deprecated Resolution Log section (removed in v9.6)",
        )
        self.assertNotIn(
            "Path A",
            body,
            "blueprint must not reference Path A — Inline UNKNOWN resolution (removed in v9.6)",
        )

    def test_validate_plan_aligns_split_invariant(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("Proposed DoR Amendments", body)
        self.assertIn("Proposed DoD Amendments", body)


class TestRefinementArtifactImmutability(unittest.TestCase):
    """v9.6+ — blueprint MUST NOT modify dor.plan.md / dod.plan.md; only enrich
    and consolidate-plan are authorized mutators per readme-artifact.md v2.3."""

    BLUEPRINT = REPO_ROOT / "aias" / ".skills" / "blueprint" / "SKILL.md"
    CONTRACT = REPO_ROOT / "aias" / "contracts" / "readme-artifact.md"

    def test_contract_documents_mutation_invariant(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("Refinement Artifact Mutation Invariant", body)
        self.assertIn("v2.3", body)

    def test_contract_lists_authorized_modifiers(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("/enrich --refresh", body)
        self.assertIn("/consolidate-plan", body)

    def test_blueprint_non_goals_forbid_direct_modification(self):
        body = _read_text(self.BLUEPRINT)
        forbid_section_idx = body.find("Non-Goals")
        self.assertGreater(forbid_section_idx, -1)
        non_goals = body[forbid_section_idx:]
        self.assertIn("Modify `dor.plan.md`", non_goals)
        self.assertTrue(
            "under ANY circumstance" in non_goals or "under any circumstance" in non_goals,
            "blueprint Non-Goals must forbid DoR/DoD modification unconditionally (v9.6+)",
        )

    def test_blueprint_phase_0_bug_exception_create_only(self):
        body = _read_text(self.BLUEPRINT)
        self.assertIn("bug exception", body.lower())
        self.assertIn("profile is NOT", body)


class TestInlineConfirmationMarkerConsistency(unittest.TestCase):
    """v9.6+ — the **Inline confirmation**: sub-field marker must be documented
    consistently across blueprint, validate-plan, consolidate-plan, contract."""

    BLUEPRINT = REPO_ROOT / "aias" / ".skills" / "blueprint" / "SKILL.md"
    VALIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "validate-plan" / "SKILL.md"
    CONSOLIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "consolidate-plan" / "SKILL.md"
    CONTRACT = REPO_ROOT / "aias" / "contracts" / "readme-artifact.md"

    def test_blueprint_documents_marker(self):
        body = _read_text(self.BLUEPRINT)
        self.assertIn("**Inline confirmation**", body)
        self.assertIn("(YYYY-MM-DD)", body)

    def test_validate_plan_documents_marker_parsing(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("**Inline confirmation**", body)
        self.assertIn("multi-line", body.lower())

    def test_consolidate_plan_documents_marker_default(self):
        body = _read_text(self.CONSOLIDATE_PLAN)
        self.assertIn("**Inline confirmation**", body)
        self.assertIn("default", body.lower())

    def test_contract_documents_canonical_regex(self):
        body = _read_text(self.CONTRACT)
        self.assertIn("Inline confirmation", body)
        self.assertIn(r"\d{4}-\d{2}-\d{2}", body)


class TestEnrichRefreshFlag(unittest.TestCase):
    """BL-S81 — enrich must document --refresh flag, Phase 1b, and the two
    governance gates."""

    ENRICH = REPO_ROOT / "aias" / ".skills" / "enrich" / "SKILL.md"

    def test_enrich_version_bumped(self):
        body = _read_text(self.ENRICH)
        self.assertIn("version: 1.3.0", body)

    def test_enrich_documents_refresh_flag(self):
        body = _read_text(self.ENRICH)
        self.assertIn("--refresh", body)

    def test_enrich_documents_phase_1b(self):
        body = _read_text(self.ENRICH)
        self.assertIn("Phase 1b", body)

    def test_enrich_documents_refresh_approval_gate(self):
        body = _read_text(self.ENRICH)
        self.assertIn("Gate: Refresh Approval", body)

    def test_enrich_documents_amendment_reconciliation_subgate(self):
        body = _read_text(self.ENRICH)
        self.assertIn("Sub-Gate: Amendment Reconciliation", body)

    def test_enrich_documents_case_a_b_c(self):
        body = _read_text(self.ENRICH)
        self.assertIn("Case A", body)
        self.assertIn("Case B", body)
        self.assertIn("Case C", body)


class TestStatusMdRefreshField(unittest.TestCase):
    """BL-S81 — status.md Format must declare last_refreshed_at as an optional
    field (v9.6+)."""

    REFERENCE = REPO_ROOT / "aias" / ".skills" / "rho-aias" / "reference.md"

    def test_status_md_documents_last_refreshed_at(self):
        body = _read_text(self.REFERENCE)
        self.assertIn("last_refreshed_at", body)

    def test_status_md_describes_refresh_semantics(self):
        body = _read_text(self.REFERENCE)
        self.assertIn("UTC ISO8601", body)
        self.assertIn("/enrich --refresh", body)

    def test_status_md_treats_absent_as_null(self):
        body = _read_text(self.REFERENCE)
        self.assertTrue(
            "absent and `null` identically" in body or "absent" in body.lower(),
            "reference.md must clarify that absent last_refreshed_at == null",
        )


class TestValidatePlanMultilineParsing(unittest.TestCase):
    """BL-S82 — validate-plan v2.1.0 must document multi-line bullet parsing
    + backward compatibility with v9.5 single-line bullets."""

    VALIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "validate-plan" / "SKILL.md"

    def test_version_bumped_to_2_1_0(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("version: 2.1.0", body)

    def test_documents_multiline_parsing(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("multi-line", body.lower())
        self.assertIn("Bullet parsing", body)

    def test_documents_backward_compatibility(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertIn("Backward compatibility", body)
        self.assertIn("single-line", body.lower())

    def test_content_field_captures_parent_only(self):
        body = _read_text(self.VALIDATE_PLAN)
        self.assertTrue(
            "parent line only" in body or "parent line" in body,
            "validate-plan must state TODO content captures parent line only",
        )


class TestConsolidatePlanMarkerParser(unittest.TestCase):
    """BL-S82 — consolidate-plan v2.1.0 must parse **Inline confirmation**:
    marker and use it as Update Approval default."""

    CONSOLIDATE_PLAN = REPO_ROOT / "aias" / ".skills" / "consolidate-plan" / "SKILL.md"

    def test_version_bumped_to_2_1_0(self):
        body = _read_text(self.CONSOLIDATE_PLAN)
        self.assertIn("version: 2.1.0", body)

    def test_documents_marker_parser(self):
        body = _read_text(self.CONSOLIDATE_PLAN)
        self.assertIn("Inline confirmation marker", body)

    def test_documents_discretion_clarifications(self):
        body = _read_text(self.CONSOLIDATE_PLAN)
        self.assertIn("Team notification is dev discretion", body)
        self.assertIn("Tracker freshness is dev discretion", body)

    def test_removes_entire_multiline_bullet(self):
        body = _read_text(self.CONSOLIDATE_PLAN)
        self.assertIn("entire multi-line bullet", body)


class TestExpandStringNotation(unittest.TestCase):
    """BL-S83 — expand parameter must be documented as a comma-separated string
    (not an array) in all skills that call Atlassian MCP."""

    ATLASSIAN = REPO_ROOT / "aias" / ".skills" / "atlassian-mcp" / "SKILL.md"
    ENRICH = REPO_ROOT / "aias" / ".skills" / "enrich" / "SKILL.md"
    REPORT = REPO_ROOT / "aias" / ".skills" / "report" / "SKILL.md"

    def test_atlassian_uses_string_expand(self):
        body = _read_text(self.ATLASSIAN)
        self.assertIn("expand='renderedFields,names,schema'", body)
        self.assertNotIn("expand=['renderedFields', 'names', 'schema']", body)

    def test_atlassian_documents_comments_expand(self):
        body = _read_text(self.ATLASSIAN)
        self.assertIn("expand='renderedFields,names,schema,comment'", body)

    def test_enrich_uses_string_expand(self):
        body = _read_text(self.ENRICH)
        self.assertIn("expand='renderedFields,names,schema'", body)
        self.assertNotIn("expand=['renderedFields', 'names', 'schema']", body)

    def test_report_uses_string_expand(self):
        body = _read_text(self.REPORT)
        self.assertIn("expand='renderedFields,names,schema'", body)
        self.assertNotIn("expand=['renderedFields', 'names', 'schema']", body)


class TestV96DocsConsistency(unittest.TestCase):
    """Wave 4 — CHANGELOG records v9.6 entry; user-facing docs reference the
    v9.6 mechanisms."""

    CHANGELOG = REPO_ROOT / "aias" / "CHANGELOG.md"
    ARCHITECTURE = REPO_ROOT / "aias" / "docs" / "ARCHITECTURE.md"
    QUICKSTART = REPO_ROOT / "aias" / "docs" / "QUICKSTART.md"

    def test_changelog_has_v96_entry(self):
        body = _read_text(self.CHANGELOG)
        self.assertIn("v9.6", body)
        self.assertIn("Refinement Contract Hardening", body)

    def test_architecture_mentions_refresh(self):
        body = _read_text(self.ARCHITECTURE)
        self.assertIn("--refresh", body)

    def test_quickstart_documents_v95_to_v96_upgrade(self):
        body = _read_text(self.QUICKSTART)
        self.assertIn("v9.5 to v9.6", body)


if __name__ == "__main__":
    unittest.main()
