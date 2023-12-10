import re


def prompt_engineering(code, description):
    pattern = re.compile(r'\bclass\s+(\w+)')
    match = pattern.search(code)
    class_name = match.group(1)
    role = ("You are a Java unit test assistant for novice programmers. You are given a novice programmer's Java code "
            "and their description of a test case. Your goal is to generate 'JUnit 5' tests that cover test cases from "
            "their description for their code. The tests should be in a " + class_name + "Test class for the " +
            class_name + " class, and function calls to the class should be correct. Remember that each test case "
            "should keep logic from other test cases in mind as well as letter casing. In a newline above each JUnit "
            "test case, make sure to create a single line comment above it which is only a description of it with no "
            "titles or colons.  Make sure all imports are included. Do not truncate anything, provide the full code "
            "with no text before or after it. Tests should use assert statements to test the code's output and not "
            "only function calls. For testing print statements, use System.setOut to redirect standard output to "
            "capture the printed result. Do not use the novice programmer's function calls for your tests. Make each "
            "test call the function for testing different cases.")

    prompt = ("A novice programmer has described their code as '" + description + "'. Their Java code is '" + code +
              "'.")
    return [{"role": "user", "content": prompt},
            {"role": "system", "content": role}]


def corrective_prompt_engineering(original_code, previous_tests, errors):
    role = ("You are a Java unit test assistant for novice programmers. You were previously given a novice "
            "programmer's Java code and you previously made tests for their code. However, The tests you gave them "
            "are incorrect. Your goal is to fix it and return it to them with no errors by listening to what caused "
            "the issue. Do NOT change the format of the previous tests, only change what is needed to fix the issue. "
            "Do not truncate anything, provide the full original code with additional fixes by you.")
    prompt = ("The original code of the novice programmer was '" + original_code.replace("TestTest", "") +
              "'. The tests you gave was '" + previous_tests + "' and the issue was " + errors)
    return [{"role": "user", "content": prompt},
            {"role": "system", "content": role}]
