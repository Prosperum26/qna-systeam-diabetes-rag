#!/usr/bin/env python3
"""Test script to verify relative URL handling for NIDDK."""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crawler.utils.url import normalize_url

def test_normalize_url():
    """Test URL normalization with various scenarios."""
    
    base_url = "https://www.niddk.nih.gov"
    base_full_url = "https://www.niddk.nih.gov/health-information/diabetes"
    
    test_cases = [
        # (input_url, base_url, expected_output, description)
        ("/health-information/diabetes/overview/what-is-diabetes", base_url, 
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Absolute path with domain"),
        
        ("health-information/diabetes/overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes", 
         "Relative path with domain"),
        
        ("/health-information/diabetes/overview/what-is-diabetes", base_full_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Absolute path with full URL"),
        
        ("health-information/diabetes/overview/what-is-diabetes", base_full_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Relative path with full URL"),
        
        ("https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes", base_url,
         "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes",
         "Full absolute URL"),
        
        ("", base_url, "", "Empty URL"),
        
        ("/", base_url, "https://www.niddk.nih.gov/", "Root path"),
    ]
    
    print("Testing URL normalization:")
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
    test_normalize_url()
