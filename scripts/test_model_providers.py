"""Tests for the model provider registry/config layer (stdlib unittest, no deps).

Run: python scripts/test_model_providers.py
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import model_config
import model_registry
from model_config import (
    add_custom_provider,
    add_fallback,
    clear_fallback,
    load_config,
    parse_selection,
    resolve_api_target,
    set_active,
    set_context_length,
)
from model_registry import load_registry, _parse_simple_yaml


class TempLoopHome(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="loop-model-test-")
        self._prev = os.environ.get("LOOP_ENGINEER_HOME")
        os.environ["LOOP_ENGINEER_HOME"] = self._tmp

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LOOP_ENGINEER_HOME", None)
        else:
            os.environ["LOOP_ENGINEER_HOME"] = self._prev
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestMiniYamlParser(unittest.TestCase):
    def test_flat_map(self) -> None:
        data = _parse_simple_yaml("a: 1\nb: two\nc: true\n")
        self.assertEqual(data, {"a": 1, "b": "two", "c": True})

    def test_nested_map(self) -> None:
        data = _parse_simple_yaml("active:\n  provider: openai\n  model: gpt-4o\n")
        self.assertEqual(data["active"], {"provider": "openai", "model": "gpt-4o"})

    def test_list_of_dicts(self) -> None:
        text = (
            "custom_providers:\n"
            "  - name: local\n"
            "    base_url: http://localhost:8080/v1\n"
            "    env_key: LOCAL_KEY\n"
            "  - name: work\n"
            "    base_url: https://gpu.internal/v1\n"
        )
        data = _parse_simple_yaml(text)
        self.assertEqual(
            data["custom_providers"],
            [
                {"name": "local", "base_url": "http://localhost:8080/v1", "env_key": "LOCAL_KEY"},
                {"name": "work", "base_url": "https://gpu.internal/v1"},
            ],
        )

    def test_empty_list(self) -> None:
        data = _parse_simple_yaml("fallback: []\n")
        self.assertEqual(data["fallback"], "[]")  # scalar text, matches save_config's own writer format


class TestRegistry(unittest.TestCase):
    def test_new_providers_present(self) -> None:
        reg = load_registry()
        for pid in (
            "together",
            "perplexity",
            "novita",
            "nvidia",
            "huggingface",
            "qwen",
            "moonshot",
            "minimax",
            "glm",
            "vllm",
            "sglang",
            "llamacpp",
            "jan",
        ):
            self.assertIn(pid, reg, f"expected provider `{pid}` in registry")

    def test_no_provider_limits_model_ids(self) -> None:
        reg = load_registry()
        for pid, meta in reg.items():
            self.assertNotIn("models", meta, f"provider `{pid}` must not carry a static model list")


class TestParseSelection(TempLoopHome):
    def test_plain_provider_uses_fallback_default(self) -> None:
        provider, model, custom_name = parse_selection("openai")
        self.assertEqual((provider, custom_name), ("openai", ""))
        self.assertTrue(model)  # falls back to registry default_model

    def test_provider_colon_model(self) -> None:
        provider, model, custom_name = parse_selection("openai:gpt-5.5")
        self.assertEqual((provider, model, custom_name), ("openai", "gpt-5.5", ""))

    def test_custom_triple_syntax(self) -> None:
        provider, model, custom_name = parse_selection("custom:local:qwen-2.5")
        self.assertEqual((provider, model, custom_name), ("custom", "qwen-2.5", "local"))


class TestNamedCustomProviders(TempLoopHome):
    def test_add_and_resolve(self) -> None:
        add_custom_provider("local", "http://localhost:8080/v1", "LOCAL_KEY")
        cfg = set_active("custom", "qwen-2.5", custom_name="local")
        self.assertEqual(cfg["active"], {"provider": "custom", "model": "qwen-2.5", "custom_name": "local"})

        target = resolve_api_target()
        self.assertEqual(target["base_url"], "http://localhost:8080/v1")
        self.assertEqual(target["env_key"], "LOCAL_KEY")
        self.assertEqual(target["label"], "custom:local")

    def test_unknown_custom_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            set_active("custom", "some-model", custom_name="does-not-exist")

    def test_roundtrip_through_disk(self) -> None:
        add_custom_provider("work", "https://gpu.internal/v1")
        set_active("custom", "llama-3", custom_name="work")
        # Force a fresh read from disk (new process would do this naturally).
        cfg = model_config.load_config()
        self.assertEqual(cfg["active"]["custom_name"], "work")
        self.assertEqual(len(cfg["custom_providers"]), 1)
        self.assertEqual(cfg["custom_providers"][0]["name"], "work")


class TestFallbackChain(TempLoopHome):
    def test_add_list_clear(self) -> None:
        add_fallback("openrouter", "anthropic/claude-sonnet-4")
        add_fallback("anthropic", "claude-sonnet-4-20250514")
        cfg = load_config()
        self.assertEqual(len(cfg["fallback"]), 2)
        self.assertEqual(cfg["fallback"][0]["provider"], "openrouter")

        clear_fallback()
        self.assertEqual(load_config()["fallback"], [])

    def test_add_is_idempotent_per_pair(self) -> None:
        add_fallback("openrouter", "anthropic/claude-sonnet-4")
        add_fallback("openrouter", "anthropic/claude-sonnet-4")
        self.assertEqual(len(load_config()["fallback"]), 1)

    def test_unknown_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            add_fallback("not-a-real-provider")


class TestContextLength(TempLoopHome):
    def test_roundtrip(self) -> None:
        set_context_length("64000")
        # The mini-YAML parser reads numeric scalars back as int, not str.
        self.assertEqual(str(load_config()["context_length"]), "64000")

    def test_overrides_registry_context_min(self) -> None:
        set_active("ollama", "qwen2.5-coder")
        set_context_length("128000")
        target = resolve_api_target()
        self.assertEqual(target["context_length"], "128000")


class TestSetActive(TempLoopHome):
    def test_unknown_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            set_active("not-a-real-provider")

    def test_known_provider_persists(self) -> None:
        set_active("openai", "gpt-5.5")
        self.assertEqual(load_config()["active"]["model"], "gpt-5.5")


if __name__ == "__main__":
    unittest.main()
