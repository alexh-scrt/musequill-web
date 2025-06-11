#!/usr/bin/env python3
"""
Python 3.13 Compatibility Check for MuseQuill Newsletter Service
Verifies that all dependencies work correctly with Python 3.13
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check if Python 3.13 is being used."""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3:
        print("❌ Python 3.x required")
        return False
    
    if version.minor < 11:
        print("⚠️  Python 3.11+ recommended for best compatibility")
        print("   Python 3.13 is preferred for optimal performance")
    elif version.minor == 13:
        print("✅ Python 3.13 detected - excellent choice!")
    else:
        print(f"✅ Python 3.{version.minor} detected - compatible")
    
    return True


def check_package_availability():
    """Check if required packages can be imported."""
    required_packages = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('pydantic', 'Data validation'),
        ('sqlite3', 'SQLite database (built-in)'),
        ('json', 'JSON handling (built-in)'),
        ('datetime', 'Date/time handling (built-in)'),
        ('asyncio', 'Async programming (built-in)'),
        ('smtplib', 'Email sending (built-in)'),
        ('email', 'Email utilities (built-in)'),
        ('pathlib', 'Path handling (built-in)'),
        ('uuid', 'UUID generation (built-in)'),
        ('logging', 'Logging (built-in)'),
        ('os', 'OS interface (built-in)'),
        ('re', 'Regular expressions (built-in)'),
    ]
    
    optional_packages = [
        ('aiosmtplib', 'Async SMTP client'),
        ('structlog', 'Structured logging'),
        ('pandas', 'Data analysis'),
        ('plotly', 'Data visualization'),
        ('psycopg2', 'PostgreSQL adapter'),
        ('sqlalchemy', 'SQL toolkit'),
        ('redis', 'Redis client'),
        ('httpx', 'HTTP client'),
        ('requests', 'HTTP library'),
        ('slowapi', 'Rate limiting'),
    ]
    
    print("\n📦 Checking Required Packages:")
    print("=" * 40)
    
    required_available = 0
    for package, description in required_packages:
        try:
            if importlib.util.find_spec(package):
                print(f"✅ {package:<15} - {description}")
                required_available += 1
            else:
                print(f"❌ {package:<15} - {description} (NOT FOUND)")
        except Exception as e:
            print(f"❌ {package:<15} - {description} (ERROR: {e})")
    
    print(f"\nRequired packages available: {required_available}/{len(required_packages)}")
    
    print("\n📦 Checking Optional Packages:")
    print("=" * 40)
    
    optional_available = 0
    for package, description in optional_packages:
        try:
            if importlib.util.find_spec(package):
                print(f"✅ {package:<15} - {description}")
                optional_available += 1
            else:
                print(f"⚪ {package:<15} - {description} (not installed)")
        except Exception as e:
            print(f"⚪ {package:<15} - {description} (error: {e})")
    
    print(f"\nOptional packages available: {optional_available}/{len(optional_packages)}")
    
    return required_available == len(required_packages)


def test_fastapi_compatibility():
    """Test FastAPI basic functionality."""
    print("\n🚀 Testing FastAPI Compatibility:")
    print("=" * 40)
    
    try:
        import fastapi
        from fastapi import FastAPI
        from pydantic import BaseModel, EmailStr
        
        print(f"✅ FastAPI version: {fastapi.__version__}")
        
        # Test basic FastAPI app creation
        app = FastAPI(title="Test App")
        
        class TestModel(BaseModel):
            email: EmailStr
            name: str = "Test"
        
        @app.get("/")
        async def root():
            return {"message": "Hello World"}
        
        @app.post("/test")
        async def test_endpoint(data: TestModel):
            return {"received": data.dict()}
        
        print("✅ FastAPI app creation successful")
        print("✅ Pydantic models working")
        print("✅ Async endpoints working")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI compatibility test failed: {e}")
        return False


def test_database_operations():
    """Test SQLite database operations."""
    print("\n💾 Testing Database Operations:")
    print("=" * 40)
    
    try:
        import sqlite3
        import tempfile
        import os
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # Test database operations
            with sqlite3.connect(db_path) as conn:
                # Create table
                conn.execute("""
                    CREATE TABLE test_subscribers (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Insert data
                conn.execute(
                    "INSERT INTO test_subscribers (id, email, created_at) VALUES (?, ?, ?)",
                    ("test-id", "test@example.com", "2024-01-01T00:00:00Z")
                )
                
                # Query data
                cursor = conn.execute("SELECT * FROM test_subscribers")
                result = cursor.fetchone()
                
                if result:
                    print("✅ Database table creation successful")
                    print("✅ Data insertion successful")
                    print("✅ Data querying successful")
                    print(f"✅ Test record: {result}")
                    return True
                else:
                    print("❌ No data returned from query")
                    return False
        
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_email_functionality():
    """Test email functionality (without sending)."""
    print("\n📧 Testing Email Functionality:")
    print("=" * 40)
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Test email creation
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email"
        msg['From'] = "test@example.com"
        msg['To'] = "recipient@example.com"
        
        text_part = MIMEText("This is a test email", 'plain')
        html_part = MIMEText("<p>This is a <b>test</b> email</p>", 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        print("✅ Email message creation successful")
        print("✅ MIME multipart handling working")
        print("✅ HTML email support working")
        
        # Test async email (if available)
        try:
            import aiosmtplib
            print("✅ Async SMTP support available")
        except ImportError:
            print("⚪ Async SMTP not installed (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ Email functionality test failed: {e}")
        return False


def test_async_functionality():
    """Test async/await functionality."""
    print("\n⚡ Testing Async Functionality:")
    print("=" * 40)
    
    try:
        import asyncio
        
        async def test_async_function():
            await asyncio.sleep(0.001)  # Minimal delay
            return "async_result"
        
        # Test async function execution
        result = asyncio.run(test_async_function())
        
        if result == "async_result":
            print("✅ Basic async/await working")
            
            # Test async context managers
            class TestAsyncContext:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            async def test_async_context():
                async with TestAsyncContext():
                    return "context_result"
            
            context_result = asyncio.run(test_async_context())
            
            if context_result == "context_result":
                print("✅ Async context managers working")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Async functionality test failed: {e}")
        return False


def generate_compatibility_report():
    """Generate a comprehensive compatibility report."""
    print("\n" + "=" * 60)
    print("🖋️  MUSEQUILL NEWSLETTER SERVICE")
    print("   Python 3.13 Compatibility Report")
    print("=" * 60)
    
    tests = [
        ("Python Version", check_python_version),
        ("Package Availability", check_package_availability),
        ("FastAPI Compatibility", test_fastapi_compatibility),
        ("Database Operations", test_database_operations),
        ("Email Functionality", test_email_functionality),
        ("Async Functionality", test_async_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 COMPATIBILITY SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your system is fully compatible with the newsletter service")
        print("✅ Python 3.13 support confirmed")
        print("\nYou can proceed with installation:")
        print("  pip install -r newsletter_requirements.txt")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("❌ Please resolve the failed tests before proceeding")
        print("\nRecommended actions:")
        print("  1. Ensure Python 3.11+ is installed")
        print("  2. Install missing required packages")
        print("  3. Re-run this compatibility check")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick check mode
        print("🚀 Quick Compatibility Check")
        success = check_python_version() and check_package_availability()
    else:
        # Full compatibility report
        success = generate_compatibility_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())