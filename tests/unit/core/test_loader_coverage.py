"""
Additional tests to improve coverage for adri.core.loader module.

These tests target specific uncovered lines to reach 90%+ coverage.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pandas as pd
import pytest

from adri.core.loader import DataLoader, detect_format, load_data


class TestDataLoaderCoverage:
    """Tests targeting specific uncovered lines in DataLoader."""

    def test_load_csv_exception_handling(self):
        """Test exception handling in load_csv method (lines 68-70)."""
        loader = DataLoader()
        
        # Create a real file but mock pandas.read_csv to raise an exception
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name\n1,test")
            csv_path = f.name

        try:
            with patch('pandas.read_csv', side_effect=RuntimeError("CSV loading failed")):
                with pytest.raises(RuntimeError):
                    loader.load_csv(csv_path)
        finally:
            os.unlink(csv_path)

    def test_load_json_manual_fallback(self):
        """Test manual JSON loading fallback (lines 105-119)."""
        loader = DataLoader()
        
        # Create a JSON file with a single dict (not list of dicts)
        test_data = {"id": 1, "name": "Alice", "score": 85.5}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_path = f.name

        try:
            # Mock pandas.read_json to raise ValueError, forcing manual fallback
            with patch('pandas.read_json', side_effect=ValueError("pandas can't handle this")):
                df = loader.load_json(json_path)
                
                # Should successfully load via manual method
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 1  # Single record (the whole dict)
                assert "id" in df.columns
                assert "name" in df.columns
                assert "score" in df.columns
        finally:
            os.unlink(json_path)

    def test_load_json_dict_of_lists(self):
        """Test JSON loading with dict of lists structure (lines 105-119)."""
        loader = DataLoader()
        
        # Create JSON with dict of lists structure
        test_data = {
            "ids": [1, 2, 3],
            "names": ["Alice", "Bob", "Charlie"],
            "scores": [85.5, 92.0, 78.3]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_path = f.name

        try:
            # Mock pandas.read_json to fail, forcing manual loading
            with patch('pandas.read_json', side_effect=ValueError("pandas failure")):
                df = loader.load_json(json_path)
                
                assert isinstance(df, pd.DataFrame)
                assert len(df) == 3  # 3 rows
                assert "ids" in df.columns
                assert "names" in df.columns
                assert "scores" in df.columns
        finally:
            os.unlink(json_path)

    def test_load_json_unsupported_structure(self):
        """Test JSON loading with unsupported structure (lines 105-119)."""
        loader = DataLoader()
        
        # Create JSON with unsupported structure (not dict or list)
        test_data = "just a string"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            json_path = f.name

        try:
            # Mock pandas.read_json to fail, forcing manual loading
            with patch('pandas.read_json', side_effect=ValueError("pandas failure")):
                with pytest.raises(ValueError, match="Unsupported JSON structure"):
                    loader.load_json(json_path)
        finally:
            os.unlink(json_path)

    def test_load_json_exception_handling(self):
        """Test exception handling in load_json method (lines 124-126)."""
        loader = DataLoader()
        
        # Create a file that will cause general exception during manual loading
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"valid": "json"}')
            json_path = f.name

        try:
            # Mock both pandas.read_json and open to cause exceptions
            with patch('pandas.read_json', side_effect=ValueError("pandas failure")):
                with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                    with pytest.raises(PermissionError):
                        loader.load_json(json_path)
        finally:
            os.unlink(json_path)

    def test_load_dataframe_type_error(self):
        """Test TypeError handling in load_dataframe (line 141)."""
        loader = DataLoader()
        
        # Create an object that has len() and columns attributes but isn't a DataFrame
        class FakeDataFrame:
            def __len__(self):
                return 5
            
            @property
            def columns(self):
                return ["col1", "col2"]
        
        fake_df = FakeDataFrame()
        
        # This should pass the logging line but fail the isinstance check
        with pytest.raises(TypeError, match="Expected pandas DataFrame, got"):
            loader.load_dataframe(fake_df)

    def test_load_from_dict_empty_list(self):
        """Test loading from empty list (line 167)."""
        loader = DataLoader()
        
        # Test empty list
        df = loader.load_from_dict([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert len(df.columns) == 0

    def test_load_from_dict_list_of_values(self):
        """Test loading from list of values (lines 173-178)."""
        loader = DataLoader()
        
        # Test list of simple values
        data = [1, 2, 3, 4, 5]
        df = loader.load_from_dict(data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert "value" in df.columns
        assert df["value"].tolist() == [1, 2, 3, 4, 5]

    def test_load_from_dict_list_of_dicts(self):
        """Test loading from list of dicts (line 106)."""
        loader = DataLoader()
        
        # Test list of dictionaries - this should trigger line 106: df = pd.DataFrame(data)
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"}
        ]
        df = loader.load_from_dict(data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "id" in df.columns
        assert "name" in df.columns
        assert df["id"].tolist() == [1, 2, 3]

    def test_load_from_dict_single_dict(self):
        """Test loading from single dict (line 176)."""
        loader = DataLoader()
        
        # Test single dictionary - this should trigger line 176: df = pd.DataFrame([data])
        data = {"id": 1, "name": "Alice", "score": 95.5}
        df = loader.load_from_dict(data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "id" in df.columns
        assert "name" in df.columns
        assert "score" in df.columns
        assert df.iloc[0]["id"] == 1
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["score"] == 95.5

    def test_load_from_dict_exception_handling(self):
        """Test exception handling in load_from_dict (lines 183-185)."""
        loader = DataLoader()
        
        # Create a scenario that will cause an exception during DataFrame creation
        # Mock pandas.DataFrame to raise an exception
        with patch('pandas.DataFrame', side_effect=RuntimeError("DataFrame creation failed")):
            with pytest.raises(RuntimeError):
                loader.load_from_dict([{"id": 1, "name": "test"}])


class TestFormatDetectionCoverage:
    """Tests targeting uncovered lines in format detection."""

    def test_detect_format_file_not_found(self):
        """Test file not found handling in detect_format."""
        with pytest.raises(ValueError, match="File not found"):
            detect_format("nonexistent_file.csv")

    def test_detect_format_unsupported_extension(self):
        """Test unsupported file extension in detect_format (line 222)."""
        # Create a file with unsupported extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("some content")
            xyz_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                detect_format(xyz_path)
        finally:
            os.unlink(xyz_path)

    def test_detect_format_unsupported_type(self):
        """Test unsupported data type in detect_format."""
        with pytest.raises(ValueError, match="Cannot detect format for data type"):
            detect_format(12345)  # Integer is not supported


class TestLoadDataCoverage:
    """Tests targeting uncovered lines in load_data function."""

    def test_load_data_exception_handling(self):
        """Test exception handling in load_data (lines 259-263)."""
        # Test with data that will cause detect_format to fail
        with pytest.raises(ValueError):
            load_data(12345)  # Unsupported type

    def test_load_data_unsupported_format(self):
        """Test unsupported format handling in load_data."""
        # Mock detect_format to return unsupported format
        with patch('adri.core.loader.detect_format', return_value="unsupported"):
            with pytest.raises(ValueError, match="Unsupported format"):
                load_data("dummy_data")

    def test_load_data_loader_exception(self):
        """Test exception propagation from specific loaders."""
        # Create a file that exists but will cause loading to fail
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv\ncontent,with,too,many,columns")
            csv_path = f.name

        try:
            # Mock the CSV loader to raise an exception
            with patch.object(DataLoader, 'load_csv', side_effect=RuntimeError("CSV loading failed")):
                with pytest.raises(RuntimeError):
                    load_data(csv_path)
        finally:
            os.unlink(csv_path)


class TestEdgeCases:
    """Additional edge case tests to improve coverage."""

    def test_load_json_with_json_decode_error(self):
        """Test JSON decode error handling."""
        loader = DataLoader()
        
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Missing quotes around json
            json_path = f.name

        try:
            # Mock pandas.read_json to fail, forcing manual loading
            with patch('pandas.read_json', side_effect=ValueError("pandas failure")):
                with pytest.raises(json.JSONDecodeError):
                    loader.load_json(json_path)
        finally:
            os.unlink(json_path)

    def test_load_from_dict_unsupported_type(self):
        """Test unsupported data type in load_from_dict."""
        loader = DataLoader()
        
        # Test with unsupported data type
        with pytest.raises(ValueError, match="Unsupported data type"):
            loader.load_from_dict(12345)  # Integer is not supported

    def test_detect_format_with_pathlib_path(self):
        """Test detect_format with pathlib.Path object."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name\n1,test")
            csv_path = f.name

        try:
            # Test with Path object
            path_obj = Path(csv_path)
            format_type = detect_format(path_obj)
            assert format_type == "csv"
        finally:
            os.unlink(csv_path)

    def test_load_csv_with_kwargs(self):
        """Test load_csv with additional kwargs."""
        loader = DataLoader()
        
        # Create a CSV file with custom separator
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id;name\n1;Alice\n2;Bob")
            csv_path = f.name

        try:
            # Load with custom separator
            df = loader.load_csv(csv_path, sep=';')
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "id" in df.columns
            assert "name" in df.columns
        finally:
            os.unlink(csv_path)

    def test_load_json_with_kwargs(self):
        """Test load_json with additional kwargs."""
        loader = DataLoader()
        
        # Create a JSON lines file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}')
            json_path = f.name

        try:
            # Load with lines=True parameter
            df = loader.load_json(json_path, lines=True)
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "id" in df.columns
            assert "name" in df.columns
        finally:
            os.unlink(json_path)
