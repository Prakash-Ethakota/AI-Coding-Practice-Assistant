"""AI Coding Practice Assistant - Phase 1

A minimal Streamlit app that lets beginners browse Python practice problems,
view their description, sample input/output, and a predefined hint, and write
code in a text area. No code execution, no database, no AI API.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Problem bank (hardcoded for Phase 1)
# ---------------------------------------------------------------------------
PROBLEMS = [
    {
        "id": 1,
        "title": "Check Even or Odd",
        "description": (
            "Write a function `is_even(n)` that returns `True` if the given "
            "integer `n` is even, and `False` if it is odd."
        ),
        "sample_input": "n = 7",
        "expected_output": "False",
        "hint": (
            "Use the modulo operator `%`. A number is even when "
            "`n % 2 == 0`."
        ),
    },
    {
        "id": 2,
        "title": "Find Factorial",
        "description": (
            "Write a function `factorial(n)` that returns the factorial of a "
            "non-negative integer `n`. Factorial of 0 is 1."
        ),
        "sample_input": "n = 5",
        "expected_output": "120",
        "hint": (
            "Factorial means multiplying all numbers from 1 to n. Try a loop "
            "from 1 to n, or use recursion with the base case factorial(0) = 1."
        ),
    },
    {
        "id": 3,
        "title": "Reverse a String",
        "description": (
            "Write a function `reverse_string(s)` that returns the reversed "
            "version of the input string `s`."
        ),
        "sample_input": "s = 'hello'",
        "expected_output": "'olleh'",
        "hint": (
            "Python has a slicing trick for reversing: `s[::-1]`. "
            "You can also use the `reversed()` function."
        ),
    },
    {
        "id": 4,
        "title": "Find the Largest of Three Numbers",
        "description": (
            "Write a function `largest(a, b, c)` that returns the largest of "
            "the three given integers."
        ),
        "sample_input": "a = 4, b = 9, c = 2",
        "expected_output": "9",
        "hint": (
            "Python has a built-in `max(a, b, c)` function, or you can compare "
            "the numbers with `if` statements."
        ),
    },
    {
        "id": 5,
        "title": "Check a Palindrome",
        "description": (
            "Write a function `is_palindrome(s)` that returns `True` if the "
            "string `s` reads the same forwards and backwards."
        ),
        "sample_input": "s = 'racecar'",
        "expected_output": "True",
        "hint": (
            "Compare the string with its reverse using slicing `s[::-1]`. "
            "If `s == s[::-1]`, it is a palindrome."
        ),
    },
]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Coding Practice Assistant", page_icon="🐍")
st.title("🐍 AI Coding Practice Assistant")
st.caption("Phase 1 — Browse problems and write your solution")

# Problem selector
problem_titles = [f"{p['id']}. {p['title']}" for p in PROBLEMS]
choice = st.selectbox("Choose a problem", problem_titles)
selected = PROBLEMS[problem_titles.index(choice)]

st.divider()

# Problem details
st.subheader(f"Problem {selected['id']}: {selected['title']}")
st.markdown(f"**Description:** {selected['description']}")
st.markdown(f"**Sample input:** `{selected['sample_input']}`")
st.markdown(f"**Expected output:** `{selected['expected_output']}`")

# Hint (kept behind a button so it stays optional)
if st.button("Show hint", help="Click to reveal a hint for this problem"):
    st.info(f"💡 {selected['hint']}")

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
if st.button("Save my solution"):
    if code.strip():
        st.success("Your solution has been recorded for this session. "
                   "Code execution is not enabled in Phase 1.")
    else:
        st.warning("Please write some code before saving.")
