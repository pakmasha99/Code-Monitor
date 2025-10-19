#!/usr/bin/env python3
"""
Code-Monitor System Integration Test
Quick verification that all components are working
"""
import requests
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any

API_URL = "http://localhost:8000"
WEEK_START = (datetime.now() - timedelta(days=datetime.now().weekday())).date()

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_test(name: str):
    print(f"\n{Colors.YELLOW}Testing:{Colors.NC} {name}")

def print_pass():
    print(f"{Colors.GREEN}✅ PASSED{Colors.NC}")

def print_fail(error: str = ""):
    print(f"{Colors.RED}❌ FAILED{Colors.NC}")
    if error:
        print(f"   Error: {error}")

def print_result(response: requests.Response):
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def test_health() -> bool:
    """Test health endpoint"""
    print_test("Health Check")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print_pass()
            print_result(response)
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def create_user(name: str, email: str) -> int | None:
    """Create a test user"""
    print_test(f"Create User: {name}")
    try:
        data = {
            "name": name,
            "email": email,
            "github_username": email.split("@")[0],
            "role": "student"
        }
        response = requests.post(f"{API_URL}/api/users", json=data, timeout=5)
        if response.status_code == 201:
            print_pass()
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
            return user_data['id']
        else:
            print_fail(f"HTTP {response.status_code}")
            print_result(response)
            return None
    except Exception as e:
        print_fail(str(e))
        return None

def list_users() -> bool:
    """List all users"""
    print_test("List All Users")
    try:
        response = requests.get(f"{API_URL}/api/users", timeout=5)
        if response.status_code == 200:
            print_pass()
            users = response.json()
            print(f"   Total users: {len(users)}")
            for user in users:
                print(f"   - {user['name']} ({user['email']})")
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def create_submission(user_id: int, lines: int, docs: int) -> bool:
    """Create weekly submission"""
    print_test(f"Create Submission (User {user_id})")
    try:
        data = {
            "week_start_date": WEEK_START.isoformat(),
            "code_lines_added": lines,
            "documents_created": docs,
            "notes": "Test submission"
        }
        response = requests.post(
            f"{API_URL}/api/users/{user_id}/submissions",
            json=data,
            timeout=5
        )
        if response.status_code == 201:
            print_pass()
            print(f"   Lines: {lines}, Docs: {docs}")
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            print_result(response)
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def update_rankings() -> bool:
    """Update rankings for current week"""
    print_test("Update Rankings")
    try:
        response = requests.post(
            f"{API_URL}/api/rankings/update/{WEEK_START.isoformat()}",
            timeout=5
        )
        if response.status_code == 200:
            print_pass()
            result = response.json()
            print(f"   Updated: {result['updated']} users")
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def get_rankings() -> bool:
    """Get current week rankings"""
    print_test("Get Current Week Rankings")
    try:
        response = requests.get(f"{API_URL}/api/rankings/current", timeout=5)
        if response.status_code == 200:
            print_pass()
            rankings = response.json()
            print(f"\n   🏆 Leaderboard:")
            for rank in rankings:
                print(f"   {rank['rank_position']}. {rank['user_name']}: {rank['total_score']} points")
                if rank.get('category_scores'):
                    scores = rank['category_scores']
                    print(f"      📊 P:{scores.get('productivity',0):.1f} Q:{scores.get('quality',0):.1f} C:{scores.get('consistency',0):.1f}")
            return True
        else:
            print_fail(f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_fail(str(e))
        return False

def main():
    """Run full integration test suite"""
    print(f"\n{Colors.BLUE}{'='*50}")
    print("🧪 Code-Monitor Integration Test Suite")
    print(f"{'='*50}{Colors.NC}\n")

    tests_passed = 0
    tests_failed = 0

    # Pre-flight check
    print(f"{Colors.YELLOW}🔍 Pre-flight checks...{Colors.NC}")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"{Colors.RED}❌ API is not running at {API_URL}{Colors.NC}")
            print("Please start the API first:")
            print("  cd backend && uvicorn app.main:app --reload")
            return
        print(f"{Colors.GREEN}✅ API is running{Colors.NC}")
    except:
        print(f"{Colors.RED}❌ Cannot connect to API at {API_URL}{Colors.NC}")
        print("Please start the API first:")
        print("  cd backend && uvicorn app.main:app --reload")
        return

    # Test Suite
    tests = []

    # Test 1: Health Check
    if test_health():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 2-3: Create Users
    user1_id = create_user("김철수", "chulsu@lab.com")
    if user1_id:
        tests_passed += 1
    else:
        tests_failed += 1

    user2_id = create_user("이영희", "younghee@lab.com")
    if user2_id:
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 4: List Users
    if list_users():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 5-6: Create Submissions
    if user1_id and create_submission(user1_id, 500, 3):
        tests_passed += 1
    else:
        tests_failed += 1

    if user2_id and create_submission(user2_id, 800, 5):
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 7: Update Rankings
    if update_rankings():
        tests_passed += 1
    else:
        tests_failed += 1

    # Test 8: Get Rankings
    if get_rankings():
        tests_passed += 1
    else:
        tests_failed += 1

    # Summary
    print(f"\n{Colors.BLUE}{'='*50}")
    print(f"{Colors.GREEN}Tests Passed: {tests_passed}{Colors.NC}")
    print(f"{Colors.RED}Tests Failed: {tests_failed}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*50}{Colors.NC}\n")

    if tests_failed == 0:
        print(f"{Colors.GREEN}✅ All tests passed!{Colors.NC}\n")
    else:
        print(f"{Colors.RED}❌ Some tests failed{Colors.NC}\n")

if __name__ == "__main__":
    main()
