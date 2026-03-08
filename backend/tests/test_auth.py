import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"
EMAIL = "arthurcristian.peter@gmail.com"
PASSWORD = "qwerty2003"

def print_cookies(session, label):
    print(f"\n🍪 Cookies {label}:")
    cookies = session.cookies.get_dict()
    if not cookies:
        print("   (No cookies found)")
    for name, value in cookies.items():
        # Find the cookie object to see the domain
        c_obj = next(c for c in session.cookies if c.name == name)
        print(f"   - {name}: {value}]... [Domain: {c_obj.domain}] [Path: {c_obj.path}]")

def run_test():
    session = requests.Session()

    print("--- STEP 1: LOGGING IN ---")
    login_data = {"email": EMAIL, "password": PASSWORD}
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login Failed!")
        return

    print("✅ Login Successful!")
    access_token = login_response.json().get("access_token")
    print_cookies(session, "AFTER LOGIN")

    print("⏳ Sleeping for 1 second...")
    time.sleep(1)

    print("\n--- STEP 2: REFRESHING TOKEN ---")
    csrf_refresh = session.cookies.get("csrf_refresh_token")
    if not csrf_refresh:
        print("❌ Error: No CSRF refresh token!")
        return
        
    refresh_headers = {"X-CSRF-TOKEN-Refresh": csrf_refresh}
    refresh_response = session.post(f"{BASE_URL}/auth/refresh", headers=refresh_headers)

    if refresh_response.status_code != 200:
        print(f"❌ Refresh Failed! {refresh_response.json()}")
        return

    print("✅ Refresh Successful!")
    access_token = refresh_response.json().get("access_token")
    print_cookies(session, "AFTER REFRESH")

    print("⏳ Sleeping for 1 second...")
    time.sleep(1)

    print("\n--- STEP 3: LOGGING OUT ---")
    
    # We pull the current values
    refresh_val = session.cookies.get("refresh_token_cookie")
    csrf_val = session.cookies.get("csrf_refresh_token")
    
    # DEBUG: See exactly what we are about to send
    print(f"📤 Sending Header: X-CSRF-TOKEN-Refresh: {csrf_val}")
    
    logout_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-CSRF-TOKEN-Refresh": csrf_val
    }

    # Use the session to ensure cookies are included automatically
    logout_response = session.post(f"{BASE_URL}/auth/logout", headers=logout_headers)

    if logout_response.status_code != 200:
        print(f"❌ Logout Failed! Status: {logout_response.status_code}")
        print(f"Detail: {logout_response.json()}")
        
        print(f"Sent Cookies: {logout_response.request.headers.get('Cookie')}")
    else:
        print("✅ Logout Successful!")

if __name__ == "__main__":
    run_test()