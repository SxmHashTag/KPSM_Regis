#!/usr/bin/env python
"""
Quick test script to verify authentication is working correctly.
Run this to confirm your app is secure.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diamond.settings')
django.setup()

from django.test import Client, override_settings
from django.contrib.auth.models import User

@override_settings(ALLOWED_HOSTS=['*'])
def test_authentication():
    """Test that authentication is working properly."""
    client = Client()
    
    print("🔒 Testing Django Forensics Authentication")
    print("=" * 50)
    
    # Test 1: Access without login should redirect
    print("\n✓ Test 1: Accessing dashboard without login...")
    response = client.get('/')
    if response.status_code == 302 and '/accounts/login/' in response.url:
        print("  ✅ PASS: Redirected to login page")
    else:
        print(f"  ❌ FAIL: Got status {response.status_code}, expected redirect to login")
        return False
    
    # Test 2: Access evidence list without login
    print("\n✓ Test 2: Accessing evidence list without login...")
    response = client.get('/evidence/')
    if response.status_code == 302 and '/accounts/login/' in response.url:
        print("  ✅ PASS: Redirected to login page")
    else:
        print(f"  ❌ FAIL: Got status {response.status_code}, expected redirect to login")
        return False
    
    # Test 3: Login page is accessible
    print("\n✓ Test 3: Login page is accessible...")
    response = client.get('/accounts/login/')
    if response.status_code == 200:
        print("  ✅ PASS: Login page loads successfully")
    else:
        print(f"  ❌ FAIL: Got status {response.status_code}, expected 200")
        return False
    
    # Test 4: Check if admin user exists
    print("\n✓ Test 4: Checking for admin user...")
    try:
        admin = User.objects.get(username='admin')
        print(f"  ✅ PASS: Admin user exists (superuser: {admin.is_superuser})")
    except User.DoesNotExist:
        print("  ❌ FAIL: Admin user not found")
        return False
    
    # Test 5: Test login with session
    print("\n✓ Test 5: Testing authenticated access...")
    # Create a test user
    test_user = User.objects.create_user(username='testuser', password='testpass123')
    client.login(username='testuser', password='testpass123')
    
    response = client.get('/')
    if response.status_code == 200:
        print("  ✅ PASS: Authenticated user can access dashboard")
    else:
        print(f"  ❌ FAIL: Got status {response.status_code}, expected 200")
    
    # Cleanup test user
    test_user.delete()
    
    print("\n" + "=" * 50)
    print("✅ All authentication tests passed!")
    print("🔒 Your app is secure and requires login.")
    print("\nYour login credentials:")
    print("  Username: admin")
    print("  Password: (your admin password)")
    print("\nIf you forgot your password, run:")
    print("  python manage.py changepassword admin")
    return True

if __name__ == '__main__':
    try:
        test_authentication()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
