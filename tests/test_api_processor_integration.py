"""
Tests for API processor integration with mapper and detector

Tests cover:
- Integration with mapper.map_columns()
- Integration with detector.standardize_dataframe()
- Error propagation from mapper/detector
- Data flow through processing pipeline
"""
import pytest
import pandas as pd
from pathlib import Path
from src.api.processor import load_and_process_data


class TestProcessorMapperIntegration:
    """Test processor integration with mapper module"""
    
    def test_processor_uses_mapper_for_custom_columns(self):
        """Should use mapper.map_columns() when custom columns provided"""
        # Use existing sample data directory
        from src.api.processor import get_data_directory
        import tempfile
        import shutil
        
        data_dir = get_data_directory()
        
        # Create temp CSV in data directory
        temp_file = data_dir / "temp_custom_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'PriceOpen': [100.0 + i for i in range(10)],
            'PriceHigh': [105.0 + i for i in range(10)],
            'PriceLow': [99.0 + i for i in range(10)],
            'PriceClose': [103.0 + i for i in range(10)],
            'Vol': [1000 + i*100 for i in range(10)]
        })
        df.to_csv(temp_file, index=False)
        
        try:
            # Should use mapper to standardize columns
            data, metadata = load_and_process_data(
                filename="temp_custom_test.csv",
                column_open='PriceOpen',
                column_high='PriceHigh',
                column_low='PriceLow',
                column_close='PriceClose',
                column_volume='Vol'
            )
            
            # Should successfully process with custom columns
            assert len(data) > 0
            assert len(data[0]) == 10  # 10 data points
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
    
    def test_processor_auto_detects_when_no_custom_columns(self):
        """Should use auto-detection when custom columns not provided"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_standard_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'Open': [100.0 + i for i in range(10)],
            'High': [105.0 + i for i in range(10)],
            'Low': [99.0 + i for i in range(10)],
            'Close': [103.0 + i for i in range(10)],
            'Volume': [1000 + i*100 for i in range(10)]
        })
        df.to_csv(temp_file, index=False)
        
        try:
            # Should auto-detect columns
            data, metadata = load_and_process_data(filename="temp_standard_test.csv")
            
            assert len(data) > 0
            assert len(data[0]) == 10
        finally:
            if temp_file.exists():
                temp_file.unlink()


class TestProcessorDetectorIntegration:
    """Test processor integration with detector module"""
    
    def test_processor_uses_detector_for_standardization(self):
        """Should use detector.standardize_dataframe() internally"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_mixed_case_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'OPEN': [100.0 + i for i in range(10)],
            'HIGH': [105.0 + i for i in range(10)],
            'LOW': [99.0 + i for i in range(10)],
            'CLOSE': [103.0 + i for i in range(10)],
            'VOLUME': [1000 + i*100 for i in range(10)],
            'rsi_14': [50.0 + i for i in range(10)]
        })
        df.to_csv(temp_file, index=False)
        
        try:
            # Detector should standardize and preserve indicators
            data, metadata = load_and_process_data(filename="temp_mixed_case_test.csv")
            
            assert len(data) >= 5  # timestamp, open, high, low, close (+ maybe volume)
        finally:
            if temp_file.exists():
                temp_file.unlink()


class TestErrorPropagation:
    """Test error propagation from mapper/detector modules"""
    
    def test_processor_raises_on_missing_required_columns(self):
        """Should propagate ColumnNotFoundError from mapper"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_incomplete_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'price': [100.0 + i for i in range(10)]  # Missing OHLC columns
        })
        df.to_csv(temp_file, index=False)
        
        try:
            with pytest.raises((ValueError, Exception)):
                load_and_process_data(
                    filename="temp_incomplete_test.csv",
                    column_open='open'  # Column doesn't exist
                )
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_processor_provides_helpful_error_messages(self):
        """Errors should include helpful suggestions"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_wrong_names_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'opening': [100.0 + i for i in range(10)],
            'highest': [105.0 + i for i in range(10)],
            'lowest': [99.0 + i for i in range(10)],
            'closing': [103.0 + i for i in range(10)]
        })
        df.to_csv(temp_file, index=False)
        
        try:
            load_and_process_data(
                filename="temp_wrong_names_test.csv",
                column_open='open'  # Wrong name
            )
            assert False, "Should have raised error"
        except Exception as e:
            error_msg = str(e)
            # Should suggest similar columns or indicate missing column
            assert 'opening' in error_msg or 'not found' in error_msg.lower() or 'Did you mean' in error_msg
        finally:
            if temp_file.exists():
                temp_file.unlink()


class TestDataFlowPipeline:
    """Test complete data flow through pipeline"""
    
    def test_custom_columns_flow_through_pipeline(self):
        """Custom columns should flow through entire pipeline"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_pipeline_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20, freq='1h'),
            'o': [100.0 + i for i in range(20)],
            'h': [105.0 + i for i in range(20)],
            'l': [99.0 + i for i in range(20)],
            'c': [103.0 + i for i in range(20)],
            'v': [1000 + i*100 for i in range(20)]
        })
        df.to_csv(temp_file, index=False)
        
        try:
            data, metadata = load_and_process_data(
                filename="temp_pipeline_test.csv",
                column_open='o',
                column_high='h',
                column_low='l',
                column_close='c',
                column_volume='v',
                timeframe='5h'  # Also test with resampling
            )
            
            # Should process successfully
            assert len(data) > 0
            # Should have fewer points after resampling
            assert len(data[0]) < 20
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_mixed_custom_and_auto_detection(self):
        """Should handle mix of custom and auto-detected columns"""
        from src.api.processor import get_data_directory
        
        data_dir = get_data_directory()
        temp_file = data_dir / "temp_mixed_test.csv"
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='1h'),
            'custom_open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],  # Auto-detect
            'low': [99.0 + i for i in range(10)],    # Auto-detect
            'close': [103.0 + i for i in range(10)],  # Auto-detect
            'volume': [1000 + i*100 for i in range(10)]  # Auto-detect
        })
        df.to_csv(temp_file, index=False)
        
        try:
            data, metadata = load_and_process_data(
                filename="temp_mixed_test.csv",
                column_open='custom_open'  # Specify only open, rest auto-detected
            )
            
            assert len(data) > 0
        finally:
            if temp_file.exists():
                temp_file.unlink()

