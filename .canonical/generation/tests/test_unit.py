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


if __name__ == "__main__":
    unittest.main()
