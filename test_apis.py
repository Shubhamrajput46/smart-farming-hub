
import getpass
import requests

BASE_URL = "http://127.0.0.1:8000"


def run_api_tests():
    session = requests.Session()
    results = []

    def check(name, method, path, **kwargs):
        try:
            response = session.request(
                method,
                BASE_URL + path,
                timeout=30,
                **kwargs
            )

            ok = 200 <= response.status_code < 300
            results.append((name, response.status_code, ok))

            status = "PASS" if ok else "FAIL"
            print(f"{status} | {response.status_code} | {name}")

            if not ok:
                print("    Response:", response.text[:500])

            return response

        except requests.RequestException as exc:
            results.append((name, "ERROR", False))
            print(f"ERROR | {name} | {exc}")
            return None

    # 1. Public APIs
    print("\n=== PUBLIC API TESTS ===")

    check("API Schema", "GET", "/api/schema/")
    check("Mandi Prices", "GET", "/api/services/mandi-prices/")
    check("Government Schemes", "GET", "/api/services/schemes/")

    # 2. JWT Login
    print("\n=== JWT LOGIN ===")

    username = input("Registered username: ").strip()
    password = getpass.getpass("Password: ")

    response = check(
        "JWT Login",
        "POST",
        "/api/auth/token/",
        json={
            "username": username,
            "password": password,
        },
    )

    if response is not None and response.status_code == 200:
        token_data = response.json()
        access = token_data.get("access")
        refresh = token_data.get("refresh")

        if access:
            session.headers.update({
                "Authorization": f"Bearer {access}"
            })

            # 3. Protected APIs
            print("\n=== PROTECTED API TESTS ===")

            protected_apis = [
                ("Farmer Profile", "/api/auth/profile/"),
                ("Lands", "/api/lands/"),
                ("Crops", "/api/crops/"),
                ("Operations", "/api/operations/"),
                ("Expenses", "/api/expenses/"),
                ("Sales", "/api/sales/"),
            ]

            for name, path in protected_apis:
                check(name, "GET", path)

            # 4. JWT Refresh
            if refresh:
                check(
                    "JWT Refresh",
                    "POST",
                    "/api/auth/token/refresh/",
                    json={"refresh": refresh},
                )

            # 5. OpenAI Assistant
            print("\n=== OPENAI ASSISTANT TEST ===")
            answer = input(
                "Send one real AI request? (y/n): "
            ).strip().lower()

            if answer == "y":
                check(
                    "OpenAI Assistant",
                    "POST",
                    "/api/ai/assistant/",
                    json={
                        "prompt": (
                            "Give one short general farming tip."
                        )
                    },
                )
        else:
            print("Login succeeded but access token is missing.")
    else:
        print("Login failed. Protected API tests skipped.")

    # 6. Final report
    print("\n=== FINAL REPORT ===")

    passed = sum(1 for _, _, ok in results if ok)
    failed = len(results) - passed

    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed:
        print("\nFailed endpoints:")

        for name, status, ok in results:
            if not ok:
                print(f"- {name}: {status}")

    print("\nAPI testing completed.")


if __name__ == "__main__":
    run_api_tests()
