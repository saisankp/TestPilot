import re


def parse_ASCII_control_characters(text):
    return re.sub(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]', '', text.decode('utf-8'))


def parse_class_and_package_name(code):
    class_name = re.search(r'class\s+(\w+)\s*{', code)
    package_name = re.search(r'package\s+(.*?);', code, re.DOTALL)
    return class_name.group(1).strip(), package_name.group(1).strip()


def parse_test_cases(test_cases):
    unprocessed_test_cases = test_cases.split("\n")
    test_cases_list = []
    index_of_test_case_from_novice = 0
    for test_case in unprocessed_test_cases:
        # Check if the test case begins with a number (sometimes, the model returns extra text which should be ignored)
        match = re.match(r'^(\d+)\.', test_case.strip())
        if match:
            # Keep track of the test case which the novice programmer mentioned from their beginner description
            if '(X)' in test_case:
                # Tracking the index of the test case in the list of test cases
                index_of_test_case_from_novice = int(match.group(1)) - 1
                test_case = test_case.replace('(X)', '')
            # Add the test case to the list
            test_cases_list.append(test_case.split('. ', 1)[1])
    return test_cases_list, index_of_test_case_from_novice


def parse_test_snippet(test_case, test_snippet):
    # Get the function name from the test snippet
    pattern = re.compile(r'@Test\s*\n\s*(?:\/\/[^\n]*\n\s*)*(?:public\s+)?void\s+(\w+)\(')
    function_name = pattern.findall(test_snippet)
    # Replace '\n' inside quotation marks in the code itself with a "\\n" (to escape the newline)
    test_snippet = re.sub(r'"([^"]*)"', lambda match: match.group(0).replace('\n', '\\n'), test_snippet)

    # Append the test case in words as a comment above the test snippet
    return f'// Test case: {test_case}\n{test_snippet}', function_name


def combine_test_snippets(code, class_name, package_name, list_of_test_snippets):
    # When combining all the test snippets, we need to use data from the original code
    combined_test_file = []

    # Add the package statements if it exists
    if code.startswith('package'):
        combined_test_file.append(f'package {package_name};\n\n')

    # Add generalized import statements that should cover all novice cases
    combined_test_file.append('import java.util.*;\n')
    combined_test_file.append('import java.io.*;\n')
    combined_test_file.append('import org.junit.*;\n')
    combined_test_file.append('import static org.junit.jupiter.api.Assertions.*;\n')

    # Extract the class name from the original code and add 'class name' + Test for the test file class

    combined_test_file.append(f'public class {class_name}Test {{\n\n')

    # Add all the test snippets
    for test_snippet in list_of_test_snippets:
        combined_test_file.append(f'{test_snippet}\n\n')

    # Add the closing bracket for the class
    combined_test_file.append('}')

    return " ".join(combined_test_file)


def remove_package_references(code, package_name):
    test = code.replace(f'package {package_name};', '').replace(f'{package_name}.', '')
    return code.replace(f'package {package_name};', '').replace(f'{package_name}.', '')


def parse_error_output_from_junit(junit_output):
    # Extract output mentioning the exact failures
    index_where_failures_mentioned = junit_output.find("Failures")
    failures = junit_output[index_where_failures_mentioned:]

    # Extract what was expected versus what was actually returned for each test
    expected_versus_returned = re.findall(r'<(.*?)>', failures, re.DOTALL)

    # Find all function names using the pattern
    failed_functions = re.findall(r'JUnit Vintage:\w+:(\w+)', failures)

    return failed_functions, expected_versus_returned


def replace_expected_with_returned(list_of_test_snippets, failed_functions, expected_versus_returned):
    function_index = 0
    for failed_function in failed_functions:
        for test_snippet_index, test_snippet in enumerate(list_of_test_snippets):
            if failed_function in test_snippet:
                wrong_value = expected_versus_returned[function_index].replace('\n', '\\n')
                correct_value = expected_versus_returned[function_index + 1].replace('\n', '\\n')
                list_of_test_snippets[test_snippet_index] = test_snippet.replace(wrong_value, correct_value)
        function_index += 2

    return list_of_test_snippets


def parse_code_within_markdown(code):
    # Gather code from a markdown (i.e. ```java {tests here} ```)
    pattern = r'```java(.*?)```'
    matches = re.findall(pattern, code, re.DOTALL)
    return ''.join(matches)


def convert_code_into_list_of_functions(code):
    test_annotation_pattern = r'@Test\s*'
    function_pattern = r'(?:public\s+)?(?:void\s+)?\s*(\w+)\s*\(\s*\)\s*\{([^}]*)\}'

    # Find all occurrences of @Test annotations
    test_annotations = re.finditer(test_annotation_pattern, code)
    functions = []

    # Extract code for each test function
    for test_annotation in test_annotations:
        # Find the corresponding function definition
        function_match = re.search(function_pattern, code[test_annotation.end():], re.DOTALL)
        if function_match:
            function_name = function_match.group(1)
            function_body = function_match.group(2)
            # Add @Test annotation and function body to the list
            functions.append(f'@Test\n  public void {function_name}() {{{function_body}}}')

    return functions


def remove_unknown_tests_from_code(code, list_of_functions, list_of_known_test_case_indices):
    for index, function in enumerate(list_of_functions):
        if index not in list_of_known_test_case_indices:
            function.replace("\n", "\\n")
            code.replace("\n", "\\n")
            code = code.replace('@Test\n    ', '@Test\n  ').replace('@Test\npublic', '@Test\n  public').replace(
                function, "")

    # Incase a 'catch' statement is remaining which regex didn't catch
    if "catch" in code:
        pattern = r'catch \(.*?\)\s*{.*?}.*?}'
        matches = re.finditer(pattern, code, flags=re.DOTALL)
        for _ in matches:
            code = re.sub(pattern, '', code, flags=re.DOTALL)
    return code
