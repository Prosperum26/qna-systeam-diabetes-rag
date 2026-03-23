#!/usr/bin/env python3
"""Test script to verify smart relative URL handling (Option 3)."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crawler.utils.url import normalize_url

def test_smart_normalize_url():
    """Test smart URL normalization with various scenarios."""
    
    base_url = "https://www.niddk.nih.gov/health-information/diabetes"
    
    test_cases = [
        # (input_url, base_url, expected_output, description)
        ("/health-information/diabetes/overview/what-is-diabetes", base_url, 
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Absolute path - already contains base_path (should NOT duplicate)"),
        
        ("/overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/overview/what-is-diabetes",
         "Absolute path - different from base_path"),
        
        ("health-information/diabetes/overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Relative path - already contains base_path components"),
        
        ("overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Relative path - doesn't contain base_path components"),
        
        ("prevention/type1-prevention", base_url,
         "https://www.niddk.nih.gov/health-information/diabetes/prevention/type1-prevention",
         "Relative path - different topic"),
        
        ("https://www.niddk.nih.gov/overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/overview/what-is-diabetes",
         "Full absolute URL"),
        
        ("", base_url, "", "Empty URL"),
        
        ("/", base_url, "https://www.niddk.nih.gov/", "Root path"),
    ]
    
    print("Testing Smart URL Normalization (Option 3):")
    print("=" * 80)
    
    all_passed = True
    for input_url, base_url_param, expected, description in test_cases:
        result = normalize_url(input_url, base_url_param)
        passed = result == expected
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} {description}")
        print(f"  Input:    '{input_url}'")
        print(f"  Base:     '{base_url_param}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        
        if not passed:
            all_passed = False
        print()
    
    print("=" * 80)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_smart_normalize_url()
