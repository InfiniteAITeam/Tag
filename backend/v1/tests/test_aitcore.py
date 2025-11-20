"""
Unit tests for AIT core modules.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Test fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def config():
    """Get test configuration."""
    from aitcore.v1.config import get_config
    return get_config()


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfiguration:
    """Test configuration management."""
    
    def test_config_initialization(self, config):
        """Test that config initializes with required paths."""
        assert config.outputs_dir.exists()
        assert config.logs_dir.exists()
        assert config.clone_base_dir.exists()
    
    def test_config_get_output_file(self, config):
        """Test output file path generation."""
        path = config.get_output_file("test.json")
        assert path.suffix == ".json"
        assert path.parent == config.outputs_dir
    
    def test_config_to_dict(self, config):
        """Test config serialization."""
        config_dict = config.to_dict()
        assert "outputs_dir" in config_dict
        assert "clone_base_dir" in config_dict
        assert "use_llm" in config_dict


# ============================================================================
# FILE HANDLER TESTS
# ============================================================================

class TestFileHandler:
    """Test file handling operations."""
    
    def test_read_write_file(self, temp_dir):
        """Test reading and writing files."""
        from aitcore.v1.tools import FileHandler
        
        test_file = temp_dir / "test.txt"
        content = "Test content"
        
        FileHandler.write_file(test_file, content)
        read_content = FileHandler.read_file(test_file)
        
        assert read_content == content
    
    def test_json_operations(self, temp_dir):
        """Test JSON read/write."""
        from aitcore.v1.tools import FileHandler
        
        test_file = temp_dir / "test.json"
        data = {"key": "value", "number": 42}
        
        FileHandler.write_json(test_file, data)
        read_data = FileHandler.read_json(test_file)
        
        assert read_data == data
    
    def test_find_react_files(self, temp_dir):
        """Test finding React files."""
        from aitcore.v1.tools import FileHandler
        
        # Create test React files
        (temp_dir / "Home.jsx").touch()
        (temp_dir / "App.js").touch()
        (temp_dir / "index.tsx").touch()
        (temp_dir / "utils.ts").touch()
        
        files = FileHandler.find_react_files(temp_dir)
        
        assert len(files) >= 3  # At least jsx, js, tsx


# ============================================================================
# BACKUP MANAGER TESTS
# ============================================================================

class TestBackupManager:
    """Test backup operations."""
    
    def test_create_backup(self, temp_dir):
        """Test backup creation."""
        from aitcore.v1.tools import BackupManager, FileHandler
        
        test_file = temp_dir / "test.js"
        FileHandler.write_file(test_file, "original content")
        
        backup_path = BackupManager.create_backup(test_file)
        
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
    
    def test_restore_from_backup(self, temp_dir):
        """Test backup restoration."""
        from aitcore.v1.tools import BackupManager, FileHandler
        
        test_file = temp_dir / "test.js"
        FileHandler.write_file(test_file, "original")
        backup_path = BackupManager.create_backup(test_file)
        
        # Modify original
        FileHandler.write_file(test_file, "modified")
        
        # Restore
        BackupManager.restore_from_backup(backup_path, test_file)
        
        assert FileHandler.read_file(test_file) == "original"


# ============================================================================
# DATA MODELS TESTS
# ============================================================================

class TestDataModels:
    """Test data model serialization."""
    
    def test_techspec_serialization(self):
        """Test TechSpec model serialization."""
        from aitcore.v1.models import TechSpec, SpecItem, AdobeConfig
        
        item = SpecItem(
            sheet="Test",
            row_index=1,
            description="Test item",
            action="click",
        )
        
        spec = TechSpec(
            file_path="test.xlsx",
            generated_at=datetime.now(),
            items=[item],
            sheets_parsed=["Test"]
        )
        
        spec_dict = spec.to_dict()
        assert spec_dict["item_count"] == 1
        assert "Test" in spec_dict["sheets_parsed"]
    
    def test_apply_report_calculations(self):
        """Test ApplyReport calculations."""
        from aitcore.v1.models.tagging import ApplyReport, ApplyResult, ApplyStatus
        
        report = ApplyReport(
            run_id="test",
            repo_path="/test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            results=[
                ApplyResult(file_path="a.js", status=ApplyStatus.SUCCESS, lines_added=5),
                ApplyResult(file_path="b.js", status=ApplyStatus.FAILED),
                ApplyResult(file_path="c.js", status=ApplyStatus.SUCCESS, lines_added=3),
            ]
        )
        
        assert report.success_count() == 2
        assert report.failed_count() == 1
        assert report.total_lines_added() == 8


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

class TestWorkflow:
    """Test workflow orchestration."""
    
    def test_workflow_step_execution(self):
        """Test basic step execution."""
        from aitcore.v1.workflow import BaseStep, StepResult, StepStatus
        
        class TestStep(BaseStep):
            def validate_input(self, data):
                return True
            
            def execute(self, data):
                return {"result": "success"}
        
        step = TestStep("TestStep")
        result = step.run({"test": "data"})
        
        assert result.status == StepStatus.COMPLETED
        assert result.output["result"] == "success"
    
    def test_workflow_orchestrator(self):
        """Test workflow orchestration."""
        from aitcore.v1.workflow import WorkflowOrchestrator, BaseStep
        
        class DummyStep(BaseStep):
            def validate_input(self, data):
                return True
            
            def execute(self, data):
                return data
        
        orchestrator = WorkflowOrchestrator("test_workflow")
        orchestrator.add_step(DummyStep("Step1"))
        orchestrator.add_step(DummyStep("Step2"))
        
        result = orchestrator.execute({"initial": "data"})
        
        assert result.success
        assert len(result.steps) == 2


# ============================================================================
# VALIDATOR TESTS
# ============================================================================

class TestValidators:
    """Test input validators."""
    
    def test_validate_non_empty_string(self):
        """Test string validation."""
        from aitcore.v1.utils.validators import validate_non_empty_string
        
        assert validate_non_empty_string("valid")
        
        with pytest.raises(ValueError):
            validate_non_empty_string("")
    
    def test_validate_positive_int(self):
        """Test integer validation."""
        from aitcore.v1.utils.validators import validate_positive_int
        
        assert validate_positive_int(42)
        
        with pytest.raises(ValueError):
            validate_positive_int(-1)
    
    def test_validate_dict_keys(self):
        """Test dictionary key validation."""
        from aitcore.v1.utils.validators import validate_dict_keys
        
        data = {"key1": "value1", "key2": "value2"}
        assert validate_dict_keys(data, ["key1", "key2"])
        
        with pytest.raises(ValueError):
            validate_dict_keys(data, ["key1", "key3"])


# ============================================================================
# FORMATTER TESTS
# ============================================================================

class TestFormatters:
    """Test output formatters."""
    
    def test_format_json(self):
        """Test JSON formatting."""
        from aitcore.v1.utils.formatters import format_json
        
        data = {"key": "value", "nested": {"inner": "data"}}
        result = format_json(data)
        
        assert '"key"' in result
        assert '"value"' in result
    
    def test_format_markdown_heading(self):
        """Test Markdown heading formatting."""
        from aitcore.v1.utils.formatters import format_markdown_heading
        
        h1 = format_markdown_heading("Title", 1)
        h2 = format_markdown_heading("Subtitle", 2)
        
        assert h1.startswith("# ")
        assert h2.startswith("## ")
    
    def test_format_markdown_list(self):
        """Test Markdown list formatting."""
        from aitcore.v1.utils.formatters import format_markdown_list
        
        items = ["Item 1", "Item 2", "Item 3"]
        result = format_markdown_list(items)
        
        assert "- Item 1" in result
        assert "- Item 2" in result


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Test custom exceptions."""
    
    def test_ait_exception_hierarchy(self):
        """Test exception hierarchy."""
        from aitcore.v1.exceptions import (
            AITException,
            FileOperationError,
            BackupError,
        )
        
        # Test that exceptions inherit properly
        assert issubclass(FileOperationError, AITException)
        assert issubclass(BackupError, AITException)
        
        # Test raising exceptions
        with pytest.raises(AITException):
            raise FileOperationError("Test error")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_file_workflow(self, temp_dir):
        """Test complete file handling workflow."""
        from aitcore.v1.tools import FileHandler, BackupManager, DiffGenerator
        
        # Create original file
        test_file = temp_dir / "component.js"
        original = "const Component = () => <div>Hello</div>;"
        FileHandler.write_file(test_file, original)
        
        # Create backup
        backup = BackupManager.create_backup(test_file)
        
        # Modify file
        modified = "const Component = () => <div>Hello World</div>;"
        FileHandler.write_file(test_file, modified)
        
        # Generate diff
        diff = DiffGenerator.generate_unified_diff(
            str(backup),
            str(test_file)
        )
        
        assert "-Hello</div>" in diff or "Hello" in diff
        assert "+Hello World</div>" in diff or "Hello World" in diff
    
    @patch('aitcore.v1.tools.openai_client.OpenAI')
    def test_llm_client_integration(self, mock_openai):
        """Test LLM client integration."""
        from aitcore.v1.tools import OpenAIClient
        
        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"code": "test"}'
        
        with patch.object(OpenAIClient, 'call_chat', return_value='{"code": "test"}'):
            client = OpenAIClient()
            result = client.extract_json('{"code": "test"}')
            
            assert "code" in result


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and load tests."""
    
    def test_large_file_handling(self, temp_dir):
        """Test handling of large files."""
        from aitcore.v1.tools import FileHandler
        
        large_file = temp_dir / "large.js"
        large_content = "const x = " + str(list(range(10000))) + ";"
        
        FileHandler.write_file(large_file, large_content)
        read_content = FileHandler.read_file(large_file)
        
        assert len(read_content) > 50000
    
    def test_many_backups(self, temp_dir):
        """Test handling many backup files."""
        from aitcore.v1.tools import BackupManager, FileHandler
        
        test_file = temp_dir / "test.js"
        
        # Create multiple backups
        for i in range(10):
            FileHandler.write_file(test_file, f"version {i}")
            BackupManager.create_backup(test_file)
        
        backups = BackupManager.find_backups(temp_dir)
        assert len(backups) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
