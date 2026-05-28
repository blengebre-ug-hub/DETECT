#!/usr/bin/env python3
"""
Pre-deployment validation script for 3D EUS AI System
Checks for common issues before deploying to Render/Vercel
"""

import os
import sys
import json
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
CHECK = '✓'
CROSS = '✗'
WARN = '⚠'

def print_section(title):
    """Print a section header"""
    print(f"\n{BLUE}{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}{RESET}\n")

def check_file(path, required=True):
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = f"{GREEN}{CHECK}{RESET}" if exists else f"{RED}{CROSS}{RESET}"
    req_text = "(required)" if required else "(optional)"
    filename = Path(path).name
    print(f"  {status} {filename:30} {req_text}")
    return exists

def check_directory(path):
    """Check if a directory exists"""
    exists = os.path.isdir(path)
    status = f"{GREEN}{CHECK}{RESET}" if exists else f"{YELLOW}{WARN}{RESET}"
    print(f"  {status} {Path(path).name}/ (directory)")
    return exists

def check_file_contains(path, search_text):
    """Check if file contains specific text"""
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            return search_text.lower() in content.lower()
    except:
        return False

def get_file_size_mb(path):
    """Get file size in MB"""
    if os.path.exists(path):
        return os.path.getsize(path) / (1024 * 1024)
    return None

def main():
    print(f"\n{BLUE}{'*'*60}")
    print(f"3D EUS AI System - Pre-Deployment Validator")
    print(f"{'*'*60}{RESET}\n")
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    issues = []
    warnings = []
    
    # Check 1: Required Deployment Files
    print_section("1. Deployment Configuration Files")
    
    required_files = [
        'Procfile',
        'runtime.txt',
        'requirements.txt',
        '.env.example',
    ]
    
    for file in required_files:
        if not check_file(file, required=True):
            issues.append(f"Missing: {file}")
    
    # Check 2: Application Files
    print_section("2. Application Files")
    
    app_files = [
        'app.py',
        'templates/index.html',
        'static/script.js',
        'static/style.css',
        'dataset.py',
        'model.py',
        'segmentation.py',
        'explainability.py',
    ]
    
    for file in app_files:
        if not check_file(file, required=True):
            issues.append(f"Missing: {file}")
    
    # Check 3: Model Files
    print_section("3. Model Files (Required for Deployment)")
    
    model_files = [
        ('best_model.keras', True),
        ('segmentation_model.keras', True),
    ]
    
    for model_file, required in model_files:
        exists = check_file(model_file, required=required)
        if exists:
            size_mb = get_file_size_mb(model_file)
            print(f"     Size: {size_mb:.2f} MB")
            if size_mb > 500:
                warnings.append(f"{model_file} is {size_mb:.2f}MB - may require Git LFS")
        elif required:
            issues.append(f"Missing required model: {model_file}")
    
    # Check 4: Code Configuration
    print_section("4. Code Configuration Checks")
    
    checks = [
        ('app.py', 'BASE_DIR = os.path.dirname', 'BASE_DIR for model paths'),
        ('app.py', 'tempfile.gettempdir()', 'Temp file directory handling'),
        ('app.py', 'os.environ.get', 'Environment variable support'),
        ('app.py', 'from dotenv import load_dotenv', 'dotenv support'),
        ('Procfile', 'gunicorn', 'Gunicorn web server'),
        ('requirements.txt', 'gunicorn', 'gunicorn in requirements'),
        ('requirements.txt', 'python-dotenv', 'python-dotenv in requirements'),
        ('templates/index.html', 'email-input', 'Email form HTML elements'),
        ('static/script.js', 'emailInput', 'Email JavaScript elements'),
    ]
    
    for file, search, description in checks:
        found = check_file_contains(file, search)
        status = f"{GREEN}{CHECK}{RESET}" if found else f"{RED}{CROSS}{RESET}"
        print(f"  {status} {description:40} ({file})")
        if not found:
            issues.append(f"Code check failed: {description} in {file}")
    
    # Check 5: Directory Structure
    print_section("5. Directory Structure")
    
    dirs = [
        'templates',
        'static',
        'gradcam_results',
        'predictions',
    ]
    
    for dir_name in dirs:
        check_directory(dir_name)
    
    # Check 6: Python Requirements
    print_section("6. Python Requirements Analysis")
    
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            reqs = f.readlines()
            print(f"  Total packages: {len(reqs)}")
            
            # Check for heavy packages
            heavy_packages = ['tensorflow', 'opencv-python', 'torch', 'keras']
            found_heavy = [pkg for pkg in reqs if any(hp in pkg.lower() for hp in heavy_packages)]
            print(f"  Heavy packages: {len(found_heavy)}")
            for pkg in found_heavy:
                print(f"    - {pkg.strip()}")
            
            if len(found_heavy) > 0:
                warnings.append("Heavy packages detected - deployment may take time or exceed memory limits")
    
    # Check 7: Total Repository Size
    print_section("7. Repository Size")
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk('.'):
        # Skip git and venv directories
        dirnames[:] = [d for d in dirnames if d not in ['.git', 'venv', '__pycache__', '.venv']]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    
    total_size_mb = total_size / (1024 * 1024)
    print(f"  Total size: {total_size_mb:.2f} MB")
    
    if total_size_mb > 512:
        warnings.append(f"Repository size ({total_size_mb:.2f}MB) exceeds 512MB - may need Git LFS")
    elif total_size_mb > 100:
        warnings.append(f"Large repository size ({total_size_mb:.2f}MB) - deployment may be slow")
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    if not issues and not warnings:
        print(f"{GREEN}✓ All checks passed! Ready for deployment.{RESET}\n")
        return 0
    
    if issues:
        print(f"{RED}Critical Issues ({len(issues)}):{RESET}")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    
    if warnings:
        print(f"\n{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    if issues:
        print(f"\n{RED}Cannot deploy with critical issues. Please fix the above.{RESET}\n")
        return 1
    else:
        print(f"\n{YELLOW}Deployment possible but review warnings above.{RESET}\n")
        return 0

if __name__ == '__main__':
    sys.exit(main())
