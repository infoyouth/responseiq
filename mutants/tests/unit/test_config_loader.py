import tempfile
from pathlib import Path

from responseiq.utils.config_loader import ResponseIQConfig, load_config


class TestConfigLoader:
    def test_default_ignores(self):
        """Verify default ignore sets are populated correctly."""
        config = ResponseIQConfig()

        assert ".pyc" in config.ignored_extensions
        assert ".py" in config.ignored_extensions
        assert "__pycache__" in config.ignored_dirs
        assert "node_modules" in config.ignored_dirs

    def test_load_from_valid_pyproject(self):
        """Verify loading/overriding defaults from a valid pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a pyproject.toml
            toml_content = """
            [tool.responseiq]
            ignore_extensions = [".foo", ".bar"]
            ignore_dirs = ["secret_folder"]
            """

            manifest_path = tmp_path / "pyproject.toml"
            with open(manifest_path, "w") as f:
                f.write(toml_content)

            config = ResponseIQConfig(root_path=tmp_path)

            # Should contain overrides (not standard appends based on code strategy)
            # Code strategy says: self.ignored_extensions = set(tool_config["ignore_extensions"])
            # So it REPLACES defaults.

            assert ".foo" in config.ignored_extensions
            assert ".bar" in config.ignored_extensions
            assert ".pyc" not in config.ignored_extensions  # Replaced!

            assert "secret_folder" in config.ignored_dirs
            assert "node_modules" not in config.ignored_dirs  # Replaced!

    def test_ignores_bad_toml(self):
        """Verify loader gracefully handles malformed TOML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            with open(tmp_path / "pyproject.toml", "w") as f:
                f.write("This is not TOML")

            # Should not raise exception
            config = ResponseIQConfig(root_path=tmp_path)

            # Should defaults remain
            assert ".pyc" in config.ignored_extensions

    def test_is_ignored_extensions(self):
        """Test strict extension ignoring."""
        config = ResponseIQConfig()

        # .py is ignored by default
        assert config.is_ignored(Path("script.py"))
        # .txt is not
        assert not config.is_ignored(Path("readme.txt"))

    def test_is_ignored_directories(self):
        """Test directory ignoring."""
        config = ResponseIQConfig()

        assert config.is_ignored(Path("node_modules"))
        assert config.is_ignored(Path(".git"))
        assert not config.is_ignored(Path("src"))

    def test_is_ignored_smart_heuristic_logs(self):
        """Test 'smart' relaxation for log folders."""
        config = ResponseIQConfig()

        # Normally .json is ignored
        assert config.is_ignored(Path("data.json"))

        # Inside a "logs" folder, .json SHOULD be allowed
        log_file = Path("logs/app.json")
        assert not config.is_ignored(log_file)

        # But binaries should still be blocked in logs
        assert config.is_ignored(Path("logs/binary.exe"))
        assert config.is_ignored(Path("logs/archive.whl"))

    def test_load_config_helper(self):
        """Test the helper function."""
        config = load_config()
        assert isinstance(config, ResponseIQConfig)
