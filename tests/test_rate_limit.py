import time
import unittest
from unittest.mock import MagicMock, patch
from arbvantage_provider.rate_limit import (
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor,
    CustomRateLimitMonitor,
    NoRateLimitMonitor
)
from arbvantage_provider.rate_limit_provider import RateLimitProvider

class TestRateLimit(unittest.TestCase):
    """
    Unit tests for all rate limiting strategies and the RateLimitProvider.
    
    These tests verify that:
    - Each rate limit monitor enforces limits as expected
    - Configuration updates are applied correctly
    - No delays occur when using NoRateLimitMonitor
    
    Why is this important?
    -----------------------------------
    Testing rate limiting ensures that your application respects API limits,
    avoids throttling, and behaves predictably under load.
    """
    def setUp(self):
        self.mock_request = MagicMock(return_value="success")

    def test_time_based_rate_limit(self):
        monitor = TimeBasedRateLimitMonitor(
            min_delay=0.1,
            max_calls_per_second=10
        )
        
        # First request should succeed
        result = monitor.make_safe_request(self.mock_request)
        self.assertEqual(result, "success")
        
        # Second request should be rate limited
        result = monitor.make_safe_request(self.mock_request)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Rate limit exceeded")
        
        # Wait and try again
        time.sleep(0.1)
        result = monitor.make_safe_request(self.mock_request)
        self.assertEqual(result, "success")

    def test_advanced_rate_limit(self):
        monitor = AdvancedRateLimitMonitor(
            min_delay=0.1,
            max_calls_per_second=10,
            warning_threshold=0.8,
            critical_threshold=0.9
        )
        
        # Make requests up to warning threshold
        for _ in range(8):
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
            time.sleep(0.01)
        
        # Next request should trigger warning
        with patch("logging.warning") as mock_warning:
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
            mock_warning.assert_called_once()
        
        # Make requests up to critical threshold
        for _ in range(1):
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
            time.sleep(0.01)
        
        # Next request should trigger critical
        with patch("logging.error") as mock_error:
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
            mock_error.assert_called_once()

    def test_custom_rate_limit(self):
        monitor = CustomRateLimitMonitor(
            window_size=1,
            max_requests=5
        )
        
        # Make requests up to limit
        for _ in range(5):
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
        
        # Next request should be rate limited
        result = monitor.make_safe_request(self.mock_request)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Rate limit exceeded")
        
        # Wait for window to reset
        time.sleep(1)
        result = monitor.make_safe_request(self.mock_request)
        self.assertEqual(result, "success")

    def test_rate_limit_provider(self):
        provider = RateLimitProvider(
            min_delay=0.1,
            max_calls_per_second=10
        )
        
        # First request should succeed
        result = provider.make_safe_request(self.mock_request)
        self.assertEqual(result, "success")
        
        # Second request should be rate limited
        result = provider.make_safe_request(self.mock_request)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Rate limit exceeded")
        
        # Update configuration
        provider.update_config(
            min_delay=0.05,
            max_calls_per_second=20
        )
        
        # Request should succeed with new config
        time.sleep(0.05)
        result = provider.make_safe_request(self.mock_request)
        self.assertEqual(result, "success")

    def test_no_rate_limit(self):
        monitor = NoRateLimitMonitor()
        
        # Multiple requests should always succeed
        for _ in range(10):
            result = monitor.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
        
        # No delay between requests
        start_time = time.time()
        for _ in range(100):
            monitor.make_safe_request(self.mock_request)
        end_time = time.time()
        
        # Should complete quickly (less than 0.1 seconds)
        self.assertLess(end_time - start_time, 0.1)

    def test_no_rate_limit_provider(self):
        provider = RateLimitProvider(monitor_class=NoRateLimitMonitor)
        
        # Multiple requests should always succeed
        for _ in range(10):
            result = provider.make_safe_request(self.mock_request)
            self.assertEqual(result, "success")
        
        # No delay between requests
        start_time = time.time()
        for _ in range(100):
            provider.make_safe_request(self.mock_request)
        end_time = time.time()
        
        # Should complete quickly (less than 0.1 seconds)
        self.assertLess(end_time - start_time, 0.1)

if __name__ == "__main__":
    unittest.main() 