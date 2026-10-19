"""AI Coding Practice Assistant - Phase 1

A minimal Streamlit app that lets beginners browse Python practice problems,
view their description, sample input/output, get progressive hints, check
their predicted output against predefined test cases, and write code in a text
area. No code execution, no database, no AI API.
"""

import streamlit as st
import pandas as pd
import altair as alt
import hashlib
import os
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: forgiving answer comparison (no code execution)
# ---------------------------------------------------------------------------
def _normalize_answer(value: str) -> str:
    """Strip whitespace, surrounding quotes/backticks, and spaces after commas."""
    value = value.strip()
    for quote in ("'", '"', '`'):
        if len(value) >= 2 and value[0] == quote and value[-1] == quote:
            value = value[1:-1].strip()
    # Normalize spacing after commas so "(2, 1)" and "(2,1)" both match
    value = value.replace(", ", ",")
    return value


def answers_match(user_answer: str, expected: str) -> bool:
    """Return True if the user's answer matches the expected output.

    Comparison is forgiving: whitespace, surrounding quotes, and spaces after
    commas are ignored; boolean answers (True/False) are case-insensitive; and
    numeric answers are compared by value (so "32" matches "32.0").
    """
    user = _normalize_answer(user_answer)
    exp = _normalize_answer(expected)
    if user == exp:
        return True
    # Allow True/False in any case (e.g. "false" matches "False")
    if exp.lower() in ("true", "false") and user.lower() == exp.lower():
        return True
    # Allow numeric equivalence (e.g. "32" matches "32.0")
    try:
        if float(user) == float(exp):
            return True
    except (ValueError, TypeError):
        pass
    return False


# ---------------------------------------------------------------------------
# Auth (DEMO ONLY — not secure authentication)
# ---------------------------------------------------------------------------
# A tiny first-version login. Accounts are stored in a local JSON file
# (users_demo.json) next to this script, with passwords hashed via SHA-256
# + a per-user salt. This demonstrates the flow only — see the note shown on
# the login page for what real production authentication requires.
USERS_FILE = Path(__file__).parent / "users_demo.json"


def _load_users():
    """Load the demo user store from disk (empty dict if missing/invalid)."""
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_users(users):
    """Persist the demo user store to disk (best-effort)."""
    try:
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    except OSError:
        pass


def _hash_password(password, salt):
    """Hash a password with the given salt using SHA-256 (demo only)."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _create_user(name, email, password):
    users = _load_users()
    salt = os.urandom(16).hex()
    users[email.lower()] = {
        "name": name,
        "salt": salt,
        "hash": _hash_password(password, salt),
    }
    _save_users(users)


def _verify_user(email, password):
    users = _load_users()
    record = users.get(email.lower())
    if not record:
        return None
    if _hash_password(password, record["salt"]) == record["hash"]:
        return record["name"]
    return None


def _user_exists(email):
    return email.lower() in _load_users()


def _init_auth_state():
    """Track login status in session_state (demo only)."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None


def render_login_page():
    """Render the demo login / sign-up page, then stop the script."""
    st.markdown("#### Sign in to continue to your practice dashboard")
    st.warning(
        "⚠️ Demo login only — this is not secure authentication. "
        "See the note below the form before relying on it."
    )

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if not email.strip() or not password:
                    st.error("Please fill in both fields.")
                else:
                    name = _verify_user(email.strip(), password)
                    if name:
                        st.session_state.logged_in = True
                        st.session_state.current_user = name
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Sign Up"):
                if not name.strip() or not email.strip() or not password or not confirm:
                    st.error("Please fill in all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif _user_exists(email.strip()):
                    st.error("An account with this email already exists. Please log in instead.")
                else:
                    _create_user(name.strip(), email.strip(), password)
                    st.session_state.logged_in = True
                    st.session_state.current_user = name.strip()
                    st.rerun()

    st.markdown("---")
    st.markdown(
        "**🔒 About this demo login**  \n"
        "Passwords are hashed with SHA-256 + a per-user salt and stored in a "
        "local `users_demo.json` file. This is **not** secure authentication: "
        "SHA-256 is too fast for password hashing, and there is no HTTPS, rate "
        "limiting, or server-side session validation — Streamlit "
        "`session_state` is not a real secure session.  \n"
        "**For production**, use a proper auth provider (e.g. Auth0, Cognito) "
        "or `passlib` with `bcrypt`/`argon2`, a real database, secure session "
        "tokens (JWT or server-side sessions), HTTPS, CSRF protection, and "
        "rate limiting."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Problem bank (hardcoded for Phase 1)
# ---------------------------------------------------------------------------
PROBLEMS = [
    {
        "id": 1,
        "category": "Basics",
        "title": "Check Even or Odd",
        "description": (
            "Write a function `is_even(n)` that returns `True` if the given "
            "integer `n` is even, and `False` if it is odd."
        ),
        "sample_input": "n = 7",
        "expected_output": "False",
        "hints": [
            "Think about what makes a number even. What remains when you divide an even number by 2?",
            "Use the modulo operator `%`. It gives the remainder of a division. Check what `7 % 2` equals.",
            "Return `n % 2 == 0`. This expression is `True` when n is even and `False` when it is odd.",
        ],
        "test_cases": [
            {"input": "n = 7", "expected": "False", "explanation": "7 % 2 = 1, so 7 is odd and is_even(7) returns False."},
            {"input": "n = 4", "expected": "True", "explanation": "4 % 2 = 0, so 4 is even and is_even(4) returns True."},
            {"input": "n = 0", "expected": "True", "explanation": "0 % 2 = 0, so 0 is even and is_even(0) returns True."},
        ],
    },
    {
        "id": 2,
        "category": "Loops",
        "title": "Find Factorial",
        "description": (
            "Write a function `factorial(n)` that returns the factorial of a "
            "non-negative integer `n`. Factorial of 0 is 1."
        ),
        "sample_input": "n = 5",
        "expected_output": "120",
        "hints": [
            "Factorial of n means: n × (n-1) × (n-2) × … × 1. Factorial of 0 is defined as 1.",
            "Use a `for` loop over `range(1, n+1)` and multiply each number into a running result that starts at 1.",
            "Start with `result = 1`, then loop: `for i in range(1, n+1): result *= i`. Return `result`.",
        ],
        "test_cases": [
            {"input": "n = 5", "expected": "120", "explanation": "5! = 5 x 4 x 3 x 2 x 1 = 120."},
            {"input": "n = 0", "expected": "1", "explanation": "By definition, 0! = 1."},
            {"input": "n = 3", "expected": "6", "explanation": "3! = 3 x 2 x 1 = 6."},
        ],
    },
    {
        "id": 3,
        "category": "Strings and Lists",
        "title": "Reverse a String",
        "description": (
            "Write a function `reverse_string(s)` that returns the reversed "
            "version of the input string `s`."
        ),
        "sample_input": "s = 'hello'",
        "expected_output": "'olleh'",
        "hints": [
            "Python strings support slicing with `[start:stop:step]`. A negative step walks the string backwards.",
            "Try `s[::-1]`. The `::` means 'all characters', and `-1` means 'go backwards one step at a time'.",
            "Your entire function body can be a single line: `return s[::-1]`.",
        ],
        "test_cases": [
            {"input": "s = 'hello'", "expected": "'olleh'", "explanation": "'hello' read backwards is 'olleh'."},
            {"input": "s = 'abc'", "expected": "'cba'", "explanation": "'abc' read backwards is 'cba'."},
            {"input": "s = 'a'", "expected": "'a'", "explanation": "A single character reversed is still 'a'."},
        ],
    },
    {
        "id": 4,
        "category": "Basics",
        "title": "Find the Largest of Three Numbers",
        "description": (
            "Write a function `largest(a, b, c)` that returns the largest of "
            "the three given integers."
        ),
        "sample_input": "a = 4, b = 9, c = 2",
        "expected_output": "9",
        "hints": [
            "Compare the three values. Which one is bigger than both others? Think about using `if` statements.",
            "Chain comparisons: `if a >= b and a >= c` means a is the largest. Write similar conditions for b and c.",
            "Python has a built-in shortcut: `return max(a, b, c)` does exactly this in one line.",
        ],
        "test_cases": [
            {"input": "a = 4, b = 9, c = 2", "expected": "9", "explanation": "Among 4, 9, and 2, the largest is 9."},
            {"input": "a = 10, b = 3, c = 7", "expected": "10", "explanation": "Among 10, 3, and 7, the largest is 10."},
            {"input": "a = -1, b = -5, c = -3", "expected": "-1", "explanation": "Among -1, -5, and -3, the largest is -1."},
        ],
    },
    {
        "id": 5,
        "category": "Strings and Lists",
        "title": "Check a Palindrome",
        "description": (
            "Write a function `is_palindrome(s)` that returns `True` if the "
            "string `s` reads the same forwards and backwards."
        ),
        "sample_input": "s = 'racecar'",
        "expected_output": "True",
        "hints": [
            "A palindrome reads the same in both directions. Try writing 'racecar' backwards — what do you notice?",
            "Reverse the string using slicing (`s[::-1]`) and compare it to the original string.",
            "Return `s == s[::-1]`. This gives `True` when both are identical, meaning it is a palindrome.",
        ],
        "test_cases": [
            {"input": "s = 'racecar'", "expected": "True", "explanation": "'racecar' reversed is 'racecar', so it is a palindrome -> True."},
            {"input": "s = 'hello'", "expected": "False", "explanation": "'hello' reversed is 'olleh', which differs, so it is not a palindrome -> False."},
            {"input": "s = 'madam'", "expected": "True", "explanation": "'madam' reversed is 'madam', so it is a palindrome -> True."},
        ],
    },
    {
        "id": 6,
        "category": "Basics",
        "title": "Add Two Numbers",
        "description": "Write a function `add(a, b)` that returns the sum of `a` and `b`.",
        "sample_input": "a = 3, b = 5",
        "expected_output": "8",
        "hints": [
            "Adding means combining two values. Python uses the `+` operator.",
            "Return the result of `a + b`.",
            "The function body can be `return a + b`.",
        ],
        "test_cases": [
            {"input": "a = 3, b = 5", "expected": "8", "explanation": "3 + 5 = 8."},
            {"input": "a = 0, b = 0", "expected": "0", "explanation": "0 + 0 = 0."},
            {"input": "a = -2, b = 6", "expected": "4", "explanation": "-2 + 6 = 4."},
        ],
    },
    {
        "id": 7,
        "category": "Basics",
        "title": "Convert Celsius to Fahrenheit",
        "description": "Write a function `celsius_to_fahrenheit(c)` that converts Celsius to Fahrenheit using F = (c * 9/5) + 32.",
        "sample_input": "c = 0",
        "expected_output": "32.0",
        "hints": [
            "The conversion formula is F = (C * 9/5) + 32.",
            "In Python, 9/5 is 1.8, so multiply c by 1.8 and add 32.",
            "Return `(c * 9/5) + 32`.",
        ],
        "test_cases": [
            {"input": "c = 0", "expected": "32.0", "explanation": "(0 * 9/5) + 32 = 32.0."},
            {"input": "c = 100", "expected": "212.0", "explanation": "(100 * 9/5) + 32 = 212.0."},
            {"input": "c = -40", "expected": "-40.0", "explanation": "(-40 * 9/5) + 32 = -40.0."},
        ],
    },
    {
        "id": 8,
        "category": "Basics",
        "title": "Check Positive, Negative or Zero",
        "description": "Write a function `check_sign(n)` that returns 'Positive', 'Negative', or 'Zero' for the given integer.",
        "sample_input": "n = -5",
        "expected_output": "Negative",
        "hints": [
            "A number greater than 0 is positive, less than 0 is negative, and equal to 0 is zero.",
            "Use `if n > 0`, `elif n < 0`, and `else` for zero.",
            "Return the matching word as a string.",
        ],
        "test_cases": [
            {"input": "n = -5", "expected": "Negative", "explanation": "-5 is less than 0 -> 'Negative'."},
            {"input": "n = 7", "expected": "Positive", "explanation": "7 is greater than 0 -> 'Positive'."},
            {"input": "n = 0", "expected": "Zero", "explanation": "0 equals 0 -> 'Zero'."},
        ],
    },
    {
        "id": 9,
        "category": "Basics",
        "title": "Swap Two Numbers",
        "description": "Write a function `swap(a, b)` that returns a tuple with a and b swapped, i.e. (b, a).",
        "sample_input": "a = 1, b = 2",
        "expected_output": "(2, 1)",
        "hints": [
            "Swapping means exchanging the values of two variables.",
            "Python lets you build a tuple with parentheses: `(b, a)`.",
            "Return `(b, a)` directly.",
        ],
        "test_cases": [
            {"input": "a = 1, b = 2", "expected": "(2, 1)", "explanation": "Swapping 1 and 2 gives (2, 1)."},
            {"input": "a = 5, b = 9", "expected": "(9, 5)", "explanation": "Swapping 5 and 9 gives (9, 5)."},
            {"input": "a = 0, b = -3", "expected": "(-3, 0)", "explanation": "Swapping 0 and -3 gives (-3, 0)."},
        ],
    },
    {
        "id": 10,
        "category": "Basics",
        "title": "Check Leap Year",
        "description": "Write a function `is_leap_year(year)` that returns True if `year` is a leap year, else False. A year is a leap year if divisible by 4, but not by 100, unless also divisible by 400.",
        "sample_input": "year = 2020",
        "expected_output": "True",
        "hints": [
            "A leap year is divisible by 4. But years divisible by 100 are not, unless also divisible by 400.",
            "Check divisibility using `%`: `year % 4 == 0`.",
            "Return `year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)`.",
        ],
        "test_cases": [
            {"input": "year = 2020", "expected": "True", "explanation": "2020 % 4 == 0 and not divisible by 100 -> leap year -> True."},
            {"input": "year = 1900", "expected": "False", "explanation": "1900 is divisible by 100 but not 400 -> not a leap year -> False."},
            {"input": "year = 2000", "expected": "True", "explanation": "2000 is divisible by 400 -> leap year -> True."},
        ],
    },
    {
        "id": 11,
        "category": "Basics",
        "title": "Calculate Square",
        "description": "Write a function `square(n)` that returns the square of `n`.",
        "sample_input": "n = 6",
        "expected_output": "36",
        "hints": [
            "Squaring a number means multiplying it by itself.",
            "Use `n * n` or `n ** 2`.",
            "Return `n ** 2`.",
        ],
        "test_cases": [
            {"input": "n = 6", "expected": "36", "explanation": "6 * 6 = 36."},
            {"input": "n = 0", "expected": "0", "explanation": "0 * 0 = 0."},
            {"input": "n = -4", "expected": "16", "explanation": "(-4) * (-4) = 16."},
        ],
    },
    {
        "id": 12,
        "category": "Basics",
        "title": "Find the Average of Two Numbers",
        "description": "Write a function `average(a, b)` that returns the average of a and b as a float.",
        "sample_input": "a = 4, b = 8",
        "expected_output": "6.0",
        "hints": [
            "The average is the sum divided by the count (here, 2).",
            "Use `/` for float division: `(a + b) / 2`.",
            "Return `(a + b) / 2`.",
        ],
        "test_cases": [
            {"input": "a = 4, b = 8", "expected": "6.0", "explanation": "(4 + 8) / 2 = 6.0."},
            {"input": "a = 0, b = 0", "expected": "0.0", "explanation": "(0 + 0) / 2 = 0.0."},
            {"input": "a = 3, b = 6", "expected": "4.5", "explanation": "(3 + 6) / 2 = 4.5."},
        ],
    },
    {
        "id": 13,
        "category": "Basics",
        "title": "Convert Kilometers to Miles",
        "description": "Write a function `km_to_miles(km)` that converts kilometers to miles using 1 km = 0.6214 miles.",
        "sample_input": "km = 10",
        "expected_output": "6.214",
        "hints": [
            "Multiply kilometers by 0.6214 to get miles.",
            "Use `km * 0.6214`.",
            "Return `km * 0.6214`.",
        ],
        "test_cases": [
            {"input": "km = 10", "expected": "6.214", "explanation": "10 * 0.6214 = 6.214."},
            {"input": "km = 0", "expected": "0.0", "explanation": "0 * 0.6214 = 0.0."},
            {"input": "km = 5", "expected": "3.107", "explanation": "5 * 0.6214 = 3.107."},
        ],
    },
    {
        "id": 14,
        "category": "Loops",
        "title": "Sum of First N Natural Numbers",
        "description": "Write a function `sum_n(n)` that returns the sum of numbers from 1 to n.",
        "sample_input": "n = 5",
        "expected_output": "15",
        "hints": [
            "You need to add 1 + 2 + ... + n.",
            "Loop `for i in range(1, n+1)` and add to a running total.",
            "Or use the formula `n * (n + 1) // 2`.",
        ],
        "test_cases": [
            {"input": "n = 5", "expected": "15", "explanation": "1+2+3+4+5 = 15."},
            {"input": "n = 1", "expected": "1", "explanation": "Just 1 = 1."},
            {"input": "n = 10", "expected": "55", "explanation": "1+2+...+10 = 55."},
        ],
    },
    {
        "id": 15,
        "category": "Loops",
        "title": "Numbers 1 to N",
        "description": "Write a function `numbers_up_to(n)` that returns a list of numbers from 1 to n.",
        "sample_input": "n = 3",
        "expected_output": "[1, 2, 3]",
        "hints": [
            "You need a list containing 1, 2, ..., n.",
            "Use `list(range(1, n+1))`.",
            "Return `list(range(1, n + 1))`.",
        ],
        "test_cases": [
            {"input": "n = 3", "expected": "[1, 2, 3]", "explanation": "Numbers 1 to 3 -> [1, 2, 3]."},
            {"input": "n = 1", "expected": "[1]", "explanation": "Numbers 1 to 1 -> [1]."},
            {"input": "n = 5", "expected": "[1, 2, 3, 4, 5]", "explanation": "Numbers 1 to 5 -> [1, 2, 3, 4, 5]."},
        ],
    },
    {
        "id": 16,
        "category": "Loops",
        "title": "Count Digits in a Number",
        "description": "Write a function `count_digits(n)` that returns the number of digits in the integer `n` (ignore the sign).",
        "sample_input": "n = 12345",
        "expected_output": "5",
        "hints": [
            "Each digit is one character. How can you turn the number into text?",
            "Convert to a string and take its length: `len(str(abs(n)))`.",
            "Return `len(str(abs(n)))`.",
        ],
        "test_cases": [
            {"input": "n = 12345", "expected": "5", "explanation": "12345 has 5 digits."},
            {"input": "n = 7", "expected": "1", "explanation": "7 has 1 digit."},
            {"input": "n = -408", "expected": "3", "explanation": "abs(-408) = 408 has 3 digits."},
        ],
    },
    {
        "id": 17,
        "category": "Loops",
        "title": "Multiplication Table",
        "description": "Write a function `table(n)` that returns a list of `n` multiplied by 1 through 10, i.e. [n*1, n*2, ..., n*10].",
        "sample_input": "n = 3",
        "expected_output": "[3, 6, 9, 12, 15, 18, 21, 24, 27, 30]",
        "hints": [
            "You need n*1, n*2, ..., n*10 in a list.",
            "Use a loop `for i in range(1, 11)` and multiply `n * i`.",
            "Or use a list comprehension: `[n * i for i in range(1, 11)]`.",
        ],
        "test_cases": [
            {"input": "n = 3", "expected": "[3, 6, 9, 12, 15, 18, 21, 24, 27, 30]", "explanation": "3 times 1..10 -> [3, 6, ..., 30]."},
            {"input": "n = 2", "expected": "[2, 4, 6, 8, 10, 12, 14, 16, 18, 20]", "explanation": "2 times 1..10 -> [2, 4, ..., 20]."},
            {"input": "n = 1", "expected": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", "explanation": "1 times 1..10 -> [1, 2, ..., 10]."},
        ],
    },
    {
        "id": 18,
        "category": "Loops",
        "title": "Sum of Digits",
        "description": "Write a function `sum_digits(n)` that returns the sum of the digits of the integer `n` (ignore the sign).",
        "sample_input": "n = 123",
        "expected_output": "6",
        "hints": [
            "Add each digit of the number together: for 123 that's 1+2+3.",
            "Convert to a string and loop over each character, converting each to int.",
            "Return `sum(int(d) for d in str(abs(n)))`.",
        ],
        "test_cases": [
            {"input": "n = 123", "expected": "6", "explanation": "1+2+3 = 6."},
            {"input": "n = 9", "expected": "9", "explanation": "Single digit 9 = 9."},
            {"input": "n = -45", "expected": "9", "explanation": "abs(-45) -> 4+5 = 9."},
        ],
    },
    {
        "id": 19,
        "category": "Loops",
        "title": "Reverse a Number",
        "description": "Write a function `reverse_number(n)` that returns the integer formed by reversing the digits of `n` (ignore the sign).",
        "sample_input": "n = 1234",
        "expected_output": "4321",
        "hints": [
            "Reversing 1234 gives 4321.",
            "Convert to a string, reverse with slicing `[::-1]`, then convert back to int.",
            "Return `int(str(abs(n))[::-1])`.",
        ],
        "test_cases": [
            {"input": "n = 1234", "expected": "4321", "explanation": "Reversing 1234 -> 4321."},
            {"input": "n = 50", "expected": "5", "explanation": "Reversing '50' -> '05' -> int 5."},
            {"input": "n = 9", "expected": "9", "explanation": "Single digit reversed is itself -> 9."},
        ],
    },
    {
        "id": 20,
        "category": "Loops",
        "title": "Even Numbers up to N",
        "description": "Write a function `evens_up_to(n)` that returns a list of even numbers from 0 up to n (inclusive).",
        "sample_input": "n = 8",
        "expected_output": "[0, 2, 4, 6, 8]",
        "hints": [
            "Even numbers are divisible by 2.",
            "Loop `for i in range(0, n+1)` and keep `i` if `i % 2 == 0`.",
            "Or use `[i for i in range(0, n+1, 2)]`.",
        ],
        "test_cases": [
            {"input": "n = 8", "expected": "[0, 2, 4, 6, 8]", "explanation": "Even numbers 0..8 -> [0, 2, 4, 6, 8]."},
            {"input": "n = 1", "expected": "[0]", "explanation": "Even numbers 0..1 -> [0]."},
            {"input": "n = 5", "expected": "[0, 2, 4]", "explanation": "Even numbers 0..5 -> [0, 2, 4]."},
        ],
    },
    {
        "id": 21,
        "category": "Loops",
        "title": "Fibonacci Number",
        "description": "Write a function `fibonacci(n)` that returns the nth Fibonacci number, where fib(0)=0, fib(1)=1, and fib(n)=fib(n-1)+fib(n-2).",
        "sample_input": "n = 6",
        "expected_output": "8",
        "hints": [
            "The sequence starts 0, 1, 1, 2, 3, 5, 8, ... Each term is the sum of the previous two.",
            "Use two variables `a, b = 0, 1` and loop n times, updating them.",
            "After the loop, return `a`.",
        ],
        "test_cases": [
            {"input": "n = 6", "expected": "8", "explanation": "fib(6) = 8 (sequence: 0, 1, 1, 2, 3, 5, 8)."},
            {"input": "n = 0", "expected": "0", "explanation": "fib(0) = 0."},
            {"input": "n = 1", "expected": "1", "explanation": "fib(1) = 1."},
        ],
    },
    {
        "id": 22,
        "category": "Loops",
        "title": "Power of a Number",
        "description": "Write a function `power(base, exp)` that returns `base` raised to `exp` using a loop (do not use `**`).",
        "sample_input": "base = 2, exp = 5",
        "expected_output": "32",
        "hints": [
            "Multiply base by itself exp times.",
            "Start with `result = 1` and loop exp times, multiplying by base each time.",
            "Loop `for _ in range(exp): result *= base`, then return result.",
        ],
        "test_cases": [
            {"input": "base = 2, exp = 5", "expected": "32", "explanation": "2^5 = 32."},
            {"input": "base = 3, exp = 0", "expected": "1", "explanation": "Any number to power 0 is 1."},
            {"input": "base = 5, exp = 2", "expected": "25", "explanation": "5^2 = 25."},
        ],
    },
    {
        "id": 23,
        "category": "Strings and Lists",
        "title": "Count Vowels",
        "description": "Write a function `count_vowels(s)` that returns the number of vowels (a, e, i, o, u) in `s` (case-insensitive).",
        "sample_input": "s = 'Hello'",
        "expected_output": "2",
        "hints": [
            "Vowels are a, e, i, o, u. Count them, ignoring case.",
            "Loop over each character and check `if ch.lower() in 'aeiou'`.",
            "Return `sum(1 for ch in s if ch.lower() in 'aeiou')`.",
        ],
        "test_cases": [
            {"input": "s = 'Hello'", "expected": "2", "explanation": "'Hello' has e and o -> 2 vowels."},
            {"input": "s = 'sky'", "expected": "0", "explanation": "'sky' has no vowels -> 0."},
            {"input": "s = 'AEIOU'", "expected": "5", "explanation": "'AEIOU' has 5 vowels -> 5."},
        ],
    },
    {
        "id": 24,
        "category": "Strings and Lists",
        "title": "Count Characters",
        "description": "Write a function `count_chars(s)` that returns the number of characters in `s`.",
        "sample_input": "s = 'hello'",
        "expected_output": "5",
        "hints": [
            "This is the length of the string.",
            "Use the built-in `len(s)`.",
            "Return `len(s)`.",
        ],
        "test_cases": [
            {"input": "s = 'hello'", "expected": "5", "explanation": "'hello' has 5 characters."},
            {"input": "s = ''", "expected": "0", "explanation": "An empty string has 0 characters."},
            {"input": "s = 'abc'", "expected": "3", "explanation": "'abc' has 3 characters."},
        ],
    },
    {
        "id": 25,
        "category": "Strings and Lists",
        "title": "Convert to Uppercase",
        "description": "Write a function `to_upper(s)` that returns `s` converted to uppercase.",
        "sample_input": "s = 'hello'",
        "expected_output": "'HELLO'",
        "hints": [
            "Uppercase means all capital letters.",
            "Use the string method `.upper()`.",
            "Return `s.upper()`.",
        ],
        "test_cases": [
            {"input": "s = 'hello'", "expected": "'HELLO'", "explanation": "'hello'.upper() -> 'HELLO'."},
            {"input": "s = 'PyThon'", "expected": "'PYTHON'", "explanation": "'PyThon'.upper() -> 'PYTHON'."},
            {"input": "s = 'abc'", "expected": "'ABC'", "explanation": "'abc'.upper() -> 'ABC'."},
        ],
    },
    {
        "id": 26,
        "category": "Strings and Lists",
        "title": "Count Words",
        "description": "Write a function `count_words(s)` that returns the number of words in `s` (words are separated by spaces).",
        "sample_input": "s = 'I love Python'",
        "expected_output": "3",
        "hints": [
            "Words are separated by spaces. Splitting on spaces gives a list of words.",
            "Use `s.split()` to break the string into words.",
            "Return `len(s.split())`.",
        ],
        "test_cases": [
            {"input": "s = 'I love Python'", "expected": "3", "explanation": "Three words: I, love, Python."},
            {"input": "s = 'hello'", "expected": "1", "explanation": "One word: hello."},
            {"input": "s = 'one two three four'", "expected": "4", "explanation": "Four words."},
        ],
    },
    {
        "id": 27,
        "category": "Strings and Lists",
        "title": "Length of a List",
        "description": "Write a function `list_length(lst)` that returns the number of elements in the list.",
        "sample_input": "lst = [10, 20, 30]",
        "expected_output": "3",
        "hints": [
            "The length of a list is how many items it has.",
            "Use the built-in `len(lst)`.",
            "Return `len(lst)`.",
        ],
        "test_cases": [
            {"input": "lst = [10, 20, 30]", "expected": "3", "explanation": "The list has 3 elements."},
            {"input": "lst = []", "expected": "0", "explanation": "An empty list has 0 elements."},
            {"input": "lst = [1]", "expected": "1", "explanation": "The list has 1 element."},
        ],
    },
    {
        "id": 28,
        "category": "Strings and Lists",
        "title": "Maximum in a List",
        "description": "Write a function `list_max(lst)` that returns the largest value in the list (assume the list is non-empty).",
        "sample_input": "lst = [3, 7, 2, 9, 5]",
        "expected_output": "9",
        "hints": [
            "You need the biggest value in the list.",
            "Use the built-in `max(lst)`.",
            "Return `max(lst)`.",
        ],
        "test_cases": [
            {"input": "lst = [3, 7, 2, 9, 5]", "expected": "9", "explanation": "The largest is 9."},
            {"input": "lst = [-5, -1, -9]", "expected": "-1", "explanation": "The largest is -1."},
            {"input": "lst = [42]", "expected": "42", "explanation": "Single element -> 42."},
        ],
    },
    {
        "id": 29,
        "category": "Strings and Lists",
        "title": "Sum of a List",
        "description": "Write a function `list_sum(lst)` that returns the sum of all numbers in the list.",
        "sample_input": "lst = [1, 2, 3, 4]",
        "expected_output": "10",
        "hints": [
            "Add every number in the list together.",
            "Use the built-in `sum(lst)`.",
            "Return `sum(lst)`.",
        ],
        "test_cases": [
            {"input": "lst = [1, 2, 3, 4]", "expected": "10", "explanation": "1+2+3+4 = 10."},
            {"input": "lst = []", "expected": "0", "explanation": "Sum of an empty list is 0."},
            {"input": "lst = [5, 5, 5]", "expected": "15", "explanation": "5+5+5 = 15."},
        ],
    },
    {
        "id": 30,
        "category": "Strings and Lists",
        "title": "Reverse a List",
        "description": "Write a function `reverse_list(lst)` that returns a new list with the elements in reverse order.",
        "sample_input": "lst = [1, 2, 3]",
        "expected_output": "[3, 2, 1]",
        "hints": [
            "Reversing [1, 2, 3] gives [3, 2, 1].",
            "Lists support slicing with a negative step, just like strings.",
            "Return `lst[::-1]`.",
        ],
        "test_cases": [
            {"input": "lst = [1, 2, 3]", "expected": "[3, 2, 1]", "explanation": "Reversed -> [3, 2, 1]."},
            {"input": "lst = [7]", "expected": "[7]", "explanation": "Single element reversed -> [7]."},
            {"input": "lst = [1, 2, 3, 4]", "expected": "[4, 3, 2, 1]", "explanation": "Reversed -> [4, 3, 2, 1]."},
        ],
    },
    {
        "id": 31,
        "category": "Patterns and Logic",
        "title": "Check Prime Number",
        "description": "Write a function `is_prime(n)` that returns True if `n` is a prime number (greater than 1 and divisible only by 1 and itself), else False.",
        "sample_input": "n = 7",
        "expected_output": "True",
        "hints": [
            "A prime is greater than 1 and has no divisors other than 1 and itself.",
            "Loop from 2 to n-1 and check if `n % i == 0`; if any divides, it's not prime.",
            "Return `n > 1 and all(n % i != 0 for i in range(2, n))`.",
        ],
        "test_cases": [
            {"input": "n = 7", "expected": "True", "explanation": "7 is divisible only by 1 and 7 -> prime -> True."},
            {"input": "n = 9", "expected": "False", "explanation": "9 = 3*3 -> not prime -> False."},
            {"input": "n = 1", "expected": "False", "explanation": "1 is not prime -> False."},
        ],
    },
    {
        "id": 32,
        "category": "Patterns and Logic",
        "title": "GCD of Two Numbers",
        "description": "Write a function `gcd(a, b)` that returns the greatest common divisor of `a` and `b`.",
        "sample_input": "a = 12, b = 8",
        "expected_output": "4",
        "hints": [
            "The GCD is the largest number that divides both a and b.",
            "Use the Euclidean algorithm: while b is not 0, set `a, b = b, a % b`.",
            "Return a once b becomes 0.",
        ],
        "test_cases": [
            {"input": "a = 12, b = 8", "expected": "4", "explanation": "GCD(12, 8) = 4."},
            {"input": "a = 7, b = 5", "expected": "1", "explanation": "7 and 5 share no common divisor > 1 -> 1."},
            {"input": "a = 100, b = 10", "expected": "10", "explanation": "GCD(100, 10) = 10."},
        ],
    },
    {
        "id": 33,
        "category": "Patterns and Logic",
        "title": "Check Armstrong Number",
        "description": "Write a function `is_armstrong(n)` that returns True if `n` is a 3-digit Armstrong number (the sum of its digits each cubed equals the number), else False.",
        "sample_input": "n = 153",
        "expected_output": "True",
        "hints": [
            "A 3-digit Armstrong number equals the sum of its digits cubed.",
            "For 153: 1^3 + 5^3 + 3^3 = 1 + 125 + 27 = 153.",
            "Return `sum(int(d)**3 for d in str(n)) == n`.",
        ],
        "test_cases": [
            {"input": "n = 153", "expected": "True", "explanation": "1^3 + 5^3 + 3^3 = 153 -> True."},
            {"input": "n = 123", "expected": "False", "explanation": "1^3 + 2^3 + 3^3 = 36, which is not 123 -> False."},
            {"input": "n = 370", "expected": "True", "explanation": "3^3 + 7^3 + 0^3 = 370 -> True."},
        ],
    },
    {
        "id": 34,
        "category": "Patterns and Logic",
        "title": "Count Even Numbers in a List",
        "description": "Write a function `count_even(lst)` that returns how many even numbers are in the list.",
        "sample_input": "lst = [1, 2, 3, 4, 6]",
        "expected_output": "3",
        "hints": [
            "Count items where `x % 2 == 0`.",
            "Loop and add 1 to a counter for each even number.",
            "Return `sum(1 for x in lst if x % 2 == 0)`.",
        ],
        "test_cases": [
            {"input": "lst = [1, 2, 3, 4, 6]", "expected": "3", "explanation": "Even numbers: 2, 4, 6 -> 3."},
            {"input": "lst = [1, 3, 5]", "expected": "0", "explanation": "No even numbers -> 0."},
            {"input": "lst = [2, 4]", "expected": "2", "explanation": "Both even -> 2."},
        ],
    },
    {
        "id": 35,
        "category": "Patterns and Logic",
        "title": "Find Second Largest in a List",
        "description": "Write a function `second_largest(lst)` that returns the second largest unique value in the list (assume at least 2 unique values).",
        "sample_input": "lst = [5, 1, 9, 3]",
        "expected_output": "5",
        "hints": [
            "You need the largest value that is smaller than the maximum.",
            "Remove duplicates by converting to a set, then sort.",
            "Return `sorted(set(lst))[-2]`.",
        ],
        "test_cases": [
            {"input": "lst = [5, 1, 9, 3]", "expected": "5", "explanation": "Unique sorted: [1, 3, 5, 9], second largest = 5."},
            {"input": "lst = [10, 10, 8]", "expected": "8", "explanation": "Unique sorted: [8, 10], second largest = 8."},
            {"input": "lst = [7, 2]", "expected": "2", "explanation": "Sorted: [2, 7], second largest = 2."},
        ],
    },
    {
        "id": 36,
        "category": "Patterns and Logic",
        "title": "Check Perfect Number",
        "description": "Write a function `is_perfect(n)` that returns True if `n` is a perfect number (equal to the sum of its proper divisors, excluding itself), else False.",
        "sample_input": "n = 6",
        "expected_output": "True",
        "hints": [
            "A perfect number equals the sum of its divisors below itself.",
            "For 6: 1 + 2 + 3 = 6, so it's perfect.",
            "Return `sum(i for i in range(1, n) if n % i == 0) == n`.",
        ],
        "test_cases": [
            {"input": "n = 6", "expected": "True", "explanation": "1+2+3 = 6 -> perfect -> True."},
            {"input": "n = 10", "expected": "False", "explanation": "1+2+5 = 8, which is not 10 -> False."},
            {"input": "n = 28", "expected": "True", "explanation": "1+2+4+7+14 = 28 -> perfect -> True."},
        ],
    },
    {
        "id": 37,
        "category": "Patterns and Logic",
        "title": "FizzBuzz for a Number",
        "description": "Write a function `fizzbuzz(n)` that returns 'FizzBuzz' if `n` is divisible by 3 and 5, 'Fizz' if divisible by 3, 'Buzz' if divisible by 5, otherwise the number as a string.",
        "sample_input": "n = 15",
        "expected_output": "'FizzBuzz'",
        "hints": [
            "Check divisibility by 3 and 5 using `%`.",
            "Check the combined case (3 and 5) first, then 3, then 5, else the number.",
            "Use `if n % 15 == 0: return 'FizzBuzz'` and so on.",
        ],
        "test_cases": [
            {"input": "n = 15", "expected": "'FizzBuzz'", "explanation": "15 is divisible by 3 and 5 -> 'FizzBuzz'."},
            {"input": "n = 9", "expected": "'Fizz'", "explanation": "9 is divisible by 3 -> 'Fizz'."},
            {"input": "n = 7", "expected": "'7'", "explanation": "7 is not divisible by 3 or 5 -> '7'."},
        ],
    },
    {
        "id": 38,
        "category": "Patterns and Logic",
        "title": "Sum of Even Numbers up to N",
        "description": "Write a function `sum_even_upto(n)` that returns the sum of all even numbers from 0 up to n (inclusive).",
        "sample_input": "n = 10",
        "expected_output": "30",
        "hints": [
            "Add the even numbers 0, 2, 4, ..., up to n.",
            "Loop `for i in range(0, n+1, 2)` and add to a total.",
            "Return `sum(range(0, n+1, 2))`.",
        ],
        "test_cases": [
            {"input": "n = 10", "expected": "30", "explanation": "0+2+4+6+8+10 = 30."},
            {"input": "n = 1", "expected": "0", "explanation": "Only 0 is even up to 1 -> 0."},
            {"input": "n = 5", "expected": "6", "explanation": "0+2+4 = 6."},
        ],
    },
    {
        "id": 39,
        "category": "Patterns and Logic",
        "title": "Check if a Number is a Perfect Square",
        "description": "Write a function `is_perfect_square(n)` that returns True if `n` is a perfect square (like 0, 1, 4, 9, 16), else False.",
        "sample_input": "n = 16",
        "expected_output": "True",
        "hints": [
            "A perfect square is the square of some integer.",
            "Take the integer square root with `int(n ** 0.5)` and square it back.",
            "Return `int(n ** 0.5) ** 2 == n`.",
        ],
        "test_cases": [
            {"input": "n = 16", "expected": "True", "explanation": "4*4 = 16 -> perfect square -> True."},
            {"input": "n = 14", "expected": "False", "explanation": "No integer squared gives 14 -> False."},
            {"input": "n = 0", "expected": "True", "explanation": "0*0 = 0 -> perfect square -> True."},
        ],
    },
    {
        "id": 40,
        "category": "Patterns and Logic",
        "title": "LCM of Two Numbers",
        "description": "Write a function `lcm(a, b)` that returns the least common multiple of `a` and `b`.",
        "sample_input": "a = 4, b = 6",
        "expected_output": "12",
        "hints": [
            "The LCM is the smallest number divisible by both a and b.",
            "Use the relation LCM(a, b) = a * b // GCD(a, b).",
            "First compute the GCD, then return `a * b // gcd(a, b)`.",
        ],
        "test_cases": [
            {"input": "a = 4, b = 6", "expected": "12", "explanation": "LCM(4, 6) = 12."},
            {"input": "a = 5, b = 7", "expected": "35", "explanation": "LCM(5, 7) = 35."},
            {"input": "a = 3, b = 9", "expected": "9", "explanation": "LCM(3, 9) = 9."},
        ],
    },
]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Coding Practice Assistant", page_icon="🐍")
st.title("🐍 AI Coding Practice Assistant")
st.caption("Phase 1 — Browse problems and write your solution")

# ---------------------------------------------------------------------------
# Dashboard theme (dark navy + teal/green accents) via injected CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --primary-color: #2dd4bf;
        --background-color: #0a1929;
        --secondary-background-color: #102a43;
        --text-color: #e6f1ff;
    }
    html, body, .stApp { background-color: #0a1929; color: #e6f1ff; }
    h1, h2, h3, h4 { color: #e6f1ff !important; }
    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #112844;
        border: 1px solid #1f3b5c;
        border-left: 5px solid #2dd4bf;
        border-radius: 12px;
        padding: 14px 16px !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetricLabel"] { color: #9fb3c8 !important; }
    div[data-testid="stMetricValue"] { color: #2dd4bf !important; font-weight: 700; }
    /* Progress bar fill */
    div[data-testid="stProgress"] > div > div { background-color: #2dd4bf !important; }
    /* Expander */
    details { background-color: #0f2438 !important; border: 1px solid #1f3b5c !important; border-radius: 12px !important; }
    summary { color: #e6f1ff !important; }
    /* Charts: transparent so the navy shows through */
    .vega-embed, .stAltairChart { background: transparent !important; }
    /* Save My Solution button: blue-purple styling */
    #save-button-container button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    #save-button-container button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    #save-button-container button:active {
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3) !important;
        transform: translateY(0px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Auth (DEMO) — login / sign-up gate
# ---------------------------------------------------------------------------
_init_auth_state()

# Extra styling for the login / sign-up form (scoped to <form> so the
# dashboard's other buttons and inputs are not affected).
st.markdown(
    """
    <style>
    form input {
        background-color: #112844 !important;
        color: #e6f1ff !important;
        border: 1px solid #1f3b5c !important;
        border-radius: 8px !important;
    }
    form input::placeholder { color: #9fb3c8 !important; }
    form button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    form button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.logged_in:
    render_login_page()  # shows the login/signup page, then calls st.stop()

# Logged in: small welcome + logout bar above the dashboard
_wcol1, _wcol2 = st.columns([5, 1])
_wcol1.markdown(f"👋 Welcome, **{st.session_state.current_user}**")
if _wcol2.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()
st.divider()

# ---------------------------------------------------------------------------
# Progress tracker (session-only, stored in st.session_state)
# ---------------------------------------------------------------------------
# attempts:      total "Check Answer" clicks
# correct_count: total correct attempts (solving the same problem twice counts twice)
# solved:        set of problem IDs answered correctly at least once (unique)
# history:       per-click cumulative (attempts, correct) for the trend chart
for _key, _default in (
    ("attempts", 0),
    ("correct_count", 0),
    ("solved", set()),
    ("history", []),
):
    if _key not in st.session_state:
        st.session_state[_key] = _default

total_problems = len(PROBLEMS)
solved_count = len(st.session_state.solved)
attempt_count = st.session_state.attempts
correct_count = st.session_state.correct_count
completion = solved_count / total_problems if total_problems else 0.0
success_rate = (correct_count / attempt_count * 100) if attempt_count > 0 else 0.0

with st.expander("📊 Practice Dashboard", expanded=True):
    st.markdown("#### Your progress at a glance")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total problems", total_problems)
    m2.metric("Solved (unique)", solved_count)
    m3.metric("Total attempts", attempt_count)
    m4.metric("Success rate", f"{success_rate:.0f}%")

    st.markdown(
        f"**Overall completion: {completion * 100:.0f}%** "
        f"({solved_count}/{total_problems} problems solved)"
    )
    st.progress(completion)

    st.markdown("#### Progress by category")
    cat_rows = []
    for _cat in ["Basics", "Loops", "Strings and Lists", "Patterns and Logic"]:
        _total = sum(1 for p in PROBLEMS if p["category"] == _cat)
        _solved = sum(
            1 for p in PROBLEMS
            if p["category"] == _cat and p["id"] in st.session_state.solved
        )
        cat_rows.append({"Category": _cat, "Type": "Solved", "Count": _solved})
        cat_rows.append({"Category": _cat, "Type": "Remaining", "Count": _total - _solved})
    cat_df = pd.DataFrame(cat_rows)
    cat_chart = (
        alt.Chart(cat_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "Category:N",
                sort=["Basics", "Loops", "Strings and Lists", "Patterns and Logic"],
                title="Category",
            ),
            y=alt.Y("Count:Q", title="Problems", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color(
                "Type:N",
                scale=alt.Scale(
                    domain=["Solved", "Remaining"],
                    range=["#2dd4bf", "#1f3b5c"],
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=["Category", "Type", "Count"],
        )
        .properties(height=280)
    )
    cat_chart = (
        cat_chart
        .configure_view(fill="transparent", strokeWidth=0)
        .configure_axis(labelColor="#e6f1ff", titleColor="#e6f1ff", gridColor="#1f3b5c")
        .configure_title(color="#e6f1ff")
        .configure_legend(labelColor="#e6f1ff", titleColor="#e6f1ff")
    )
    st.altair_chart(cat_chart, use_container_width=True)

    st.markdown("#### Attempts vs correct answers")
    if len(st.session_state.history) >= 2:
        hist_df = pd.DataFrame(st.session_state.history)
        hist_df = hist_df.rename(
            columns={"attempts": "Attempt number", "correct": "Correct answers"}
        )
        line_chart = (
            alt.Chart(hist_df)
            .mark_line(point=True, color="#2dd4bf")
            .encode(
                x=alt.X("Attempt number:Q", title="Attempt number"),
                y=alt.Y("Correct answers:Q", title="Cumulative correct answers"),
                tooltip=["Attempt number", "Correct answers"],
            )
            .properties(height=280)
        )
        line_chart = (
            line_chart
            .configure_view(fill="transparent", strokeWidth=0)
            .configure_axis(labelColor="#e6f1ff", titleColor="#e6f1ff", gridColor="#1f3b5c")
            .configure_title(color="#e6f1ff")
        )
        st.altair_chart(line_chart, use_container_width=True)
        st.caption("Built from your real Check Answer clicks in this session.")
    else:
        st.info(
            "Solve a few problems (2+ Check Answer clicks) to see an "
            "attempts-vs-correct-answers trend chart here."
        )

st.divider()

# Category filter
categories = ["All", "Basics", "Loops", "Strings and Lists", "Patterns and Logic"]
category_choice = st.selectbox("Filter by category", categories)
if category_choice == "All":
    visible_problems = PROBLEMS
else:
    visible_problems = [p for p in PROBLEMS if p["category"] == category_choice]

# Problem selector (from the filtered list)
problem_titles = [f"{p['id']}. {p['title']}" for p in visible_problems]
choice = st.selectbox("Choose a problem", problem_titles)
selected = visible_problems[problem_titles.index(choice)]

st.divider()

# Problem details
st.subheader(f"Problem {selected['id']}: {selected['title']}")
st.markdown(f"**Category:** {selected['category']}")
st.markdown(f"**Description:** {selected['description']}")
st.markdown(f"**Sample input:** `{selected['sample_input']}`")
st.markdown(f"**Expected output:** `{selected['expected_output']}`")

# Progressive hints (each shown only when its button is clicked)
st.markdown("**Hints** (try them in order, only if you're stuck)")
col1, col2, col3 = st.columns(3)
if col1.button("Hint 1: Small clue"):
    st.info(f"💡 {selected['hints'][0]}")
if col2.button("Hint 2: Logic"):
    st.info(f"💡 {selected['hints'][1]}")
if col3.button("Hint 3: Approach"):
    st.info(f"💡 {selected['hints'][2]}")

st.divider()

# Check answer (compares the user's predicted output to predefined expected
# outputs; no user-submitted code is executed)
st.subheader("Check your answer")
st.markdown(
    "Pick a test case, work out what the output should be, then enter it below. "
    "Your code is not run — this only checks your predicted output."
)

test_case_labels = [
    f"Test {i + 1}: {tc['input']}" for i, tc in enumerate(selected["test_cases"])
]
tc_choice = st.selectbox("Choose a test case", test_case_labels)
tc = selected["test_cases"][test_case_labels.index(tc_choice)]

answer = st.text_input(
    "Your answer",
    placeholder="e.g. False, 120, or 'olleh'",
)

if st.button("Check Answer"):
    st.session_state.attempts += 1
    if not answer.strip():
        st.warning("Please enter an answer first.")
    elif answers_match(answer, tc["expected"]):
        st.session_state.solved.add(selected["id"])
        st.session_state.correct_count += 1
        st.success(f"Correct! ✅ {tc['explanation']}")
    else:
        st.error(
            f"Try again ❌ The expected answer is `{tc['expected']}`. "
            f"{tc['explanation']}"
        )
    # Record this real attempt for the trend chart. This block only runs when
    # the button is actually clicked, so reruns never double-count it.
    st.session_state.history.append({
        "attempts": st.session_state.attempts,
        "correct": st.session_state.correct_count,
    })

st.divider()

# Code editor (plain text area for Phase 1)
st.subheader("Your code")
code = st.text_area(
    "Write your Python solution below",
    height=300,
    placeholder=(
        f"# Define your function here, e.g.:\n"
        f"def {selected['title'].lower().replace(' ', '_')}():\n"
        f"    pass\n"
    ),
)

# A simple "Save" acknowledgement that just confirms the code is present.
st.markdown('<div id="save-button-container">', unsafe_allow_html=True)
if st.button("Save my solution"):
    if code.strip():
        st.success("Your solution has been recorded for this session. "
                   "Code execution is not enabled in Phase 1.")
    else:
        st.warning("Please write some code before saving.")
st.markdown('</div>', unsafe_allow_html=True)
