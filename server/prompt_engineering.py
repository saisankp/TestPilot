

FIZZBUZZ_NOVICE_CODE = """public class fizzbuzz {

    public static void main(String[] args) {
        fizzBuzz(15);
    }
    
    public static void fizzBuzz(int n) {
        for (int i = 1; i <= n; i++) {
            if (i % 3 == 0 && i % 5 == 0) {
                System.out.println("fizzbuzz");
            } else if (i % 3 == 0) {
                System.out.println("fizz");
            } else if (i % 5 == 0) {
                System.out.println("buzz");
            } else {
                System.out.println(i);
            }
        }
    }

}"""

FIZZBUZZ_SANITIZE_VAGUE_EXAMPLE = """I think it should return 500 if the input is divisible by 5"""

FIZZBUZZ_SANITIZE_CASE_EXAMPLE = """fizzBuzz(5), assertEquals(500), fizzBuzz should return 500 for input 5"""

FAILING_FIZZBUZZ_TEST_CODE_DIVISIBLE_BY_5 = """@Test
    public void testFizz() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(5);

        // Assert
        assertEquals("500", outContent.toString());
    }"""

FIZZBUZZ_TEST_CASE_DIVISIBLE_BY_3 = """Code should return fizz if the input is divisible by 3"""

FIZZBUZZ_TEST_CASES = """1. If the input is divisible by 3 and 5, return "fizzbuzz".
2. If the input is divisible by 3, return "fizz".
3. If the input is divisible by 5, return "buzz".
4. If the input is not divisible by 3, 5 or both, return the input number."""

FIZZBUZZ_TEST_CASES_WITH_X = """1. If the input is divisible by 3 and 5, return "fizzbuzz".
2. If the input is divisible by 3, return "fizz" (X).
3. If the input is divisible by 5, return "buzz".
4. If the input is not divisible by 3, 5 or both, return the input number."""

FIZZBUZZ_TEST_CODE_DIVISIBLE_BY_3 = """@Test
    public void testFizz() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(9);

        // Assert
        assertEquals("1\n2\nfizz\n4\n5\nfizz\n7\n8\nfizz\n", outContent.toString());
    }"""

FIZZBUZZ_INCORRECT_TEST_FILE = """import java.util.*;
import java.io.*;
import org.junit.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class fizzbuzzTest {

    // Test case: Provide an input number that is divisible by both 3 and 5. The code should return "fizzbuzz".
    @Test
    public void testFizzBuzz() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(15);

        // Assert
        assertEquals("1\n2\nfizz\n4\nbuzz\nfizz\n7\n8\nfizz\nbuzz\n11\nfizz\n13\n14\nfizzbuzz\n",
                outContent.toString());
    }

    // Test case: Provide an input number that is divisible only by 3. The code should return "fizz".
    @Test
    public void testDivisibleBy3() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(9);

        // Assert
        assertEquals("1\n2\nfizz\n4\n5\nfizz\n7\n8\nfizz\n", outContent.toString());
    }

    // Test case: Provide an input number that is divisible only by 5. The code should return "buzz".
    @Test
    public void testDivisibleByFive() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(10);

        // Assert
        assertEquals("1\n2\n3\n4\nbuzz\n6\n7\n8\n9\nbuzz\n", outContent.toString());
    }

    // Test case: Provide an input number that is not divisible by either 3 or 5. The code should return the input number.
    @Test
    public void testNotDivisibleByThreeOrFive() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(7);

        // Assert
        assertEquals("1\n2\n4\nfizz\nbuzz\n7\n", outContent.toString());
    }

}"""

FIZZBUZZ_INCORRECT_TEST_FILE_ERRORS = """1. Function testDivisibleBy3() expected:
1
2
fizz
4
5
fizz
7
8
fizz
But Was:
1
2
fizz
4
buzz
fizz
7
8
fizz

2. Function testDivisibleByFive() expected:
1
2
3
4
buzz
6
7
8
9
buzz
But Was:
1
2
fizz
4
buzz
fizz
7
8
fizz
buzz

3. Function testNotDivisibleByThreeOrFive() expected:
1
2
4
fizz
buzz
7
But Was:
1
2
fizz
4
buzz
fizz
7"""

FIZZBUZZ_CORRECT_TEST_FILE = """import java.util.*;
import java.io.*;
import org.junit.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class fizzbuzzTest {

    // Test case: Provide an input number that is divisible by both 3 and 5. The code should return "fizzbuzz".
    @Test
    public void testFizzBuzz() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(15);

        // Assert
        assertEquals("1\n2\nfizz\n4\nbuzz\nfizz\n7\n8\nfizz\nbuzz\n11\nfizz\n13\n14\nfizzbuzz\n",
                outContent.toString());
    }

    // Test case: Provide an input number that is divisible only by 3. The code should return "fizz".
    @Test
    public void testDivisibleBy3() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(9);

        // Assert
        assertEquals("1\n2\nfizz\n4\nbuzz\nfizz\n7\n8\nfizz\n", outContent.toString());
    }

    // Test case: Provide an input number that is divisible only by 5. The code should return "buzz".
    @Test
    public void testDivisibleByFive() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(10);

        // Assert
        assertEquals("1\n2\nfizz\n4\nbuzz\nfizz\n7\n8\nfizz\nbuzz\n", outContent.toString());
    }

    // Test case: Provide an input number that is not divisible by either 3 or 5. The code should return the input number.
    @Test
    public void testNotDivisibleByThreeOrFive() {
        // Arrange
        ByteArrayOutputStream outContent = new ByteArrayOutputStream();
        System.setOut(new PrintStream(outContent));

        // Act
        fizzbuzz.fizzBuzz(7);

        // Assert
        assertEquals("1\n2\nfizz\n4\nbuzz\nfizz\n7\n", outContent.toString());
    }

}"""


def sanitize_vague_description_prompt_engineering(code, description):
    # Assign a role for the model
    role = ('You are an expert software tester who is given code and a vague test case in English. You MUST turn this'
            ' vague test case into an expected function call parameter, expected assertEquals parameter and description purely based on the vague test case. Ensure '
            'that your answer is unbiased and avoids relying on stereotypes. Use the function call parameter and '
            'assertEquals parameter that is given to you.')

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". A possible test case was '
                        f'{FIZZBUZZ_SANITIZE_VAGUE_EXAMPLE}. Convert this to a function call parameter, '
                        f'an assertEquals parameter,and a description in English.')
    example_answer = f'{FIZZBUZZ_SANITIZE_CASE_EXAMPLE}'

    # Create test cases for novice programmer's code
    current_question = (f'The code is "{code}". A possible test case was {description}. Convert this to a function '
                        f'call parameter, an assertEquals parameter,and a description in English.')

    return [{"role": "system", "content": role},
            {"role": "user", "content": example_question},
            {"role": "system", "content": example_answer},
            {"role": "user", "content": current_question}
            ]


def test_snippet_prompt_engineering(code, test_case, similar_tests_from_vector_database):
    chat = []

    # Assign a role for the model
    role = ('You are a Java unit test assistant for novice programmers. Using Java code, generate a single JUnit @Test '
            'function using the given input function call (Act stage) and expected assertEquals parameter (Assert '
            'stage), The test function should use assert statements in the format "Arrange Act Assert" in comments. '
            'Do not use your own knowledge to make the test.'
            'Only pass use the input and expected output that is given to you.')
    chat.append({"role": "system", "content": role})

    # # Help model with similar test from vector database (if it exists)
    if similar_tests_from_vector_database is not None:
        tests_for_inspiration = (f'To help you create the 1 @Test you need, here is an entire testing file to help you '
                                 f'create 1 test function to improve your knowledge base: '
                                 f'"{similar_tests_from_vector_database["tests"]}"')
        chat.append({"role": "user", "content": tests_for_inspiration})

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". The function call and assertEquals parameter is '
                        f'{FIZZBUZZ_SANITIZE_CASE_EXAMPLE}. Create an @Test function using these. ')
    chat.append({"role": "user", "content": example_question})
    example_answer = f'{FAILING_FIZZBUZZ_TEST_CODE_DIVISIBLE_BY_5}'
    chat.append({"role": "system", "content": example_answer})

    current_question = (f'The code is "{code}". The function call and assertEquals parameter is {test_case}. '
                        f'Create an @Test function using these. ')
    chat.append({"role": "user", "content": current_question})
    return chat


def test_cases_prompt_engineering(code, description):
    # Assign a role for the model
    role = ('You are an expert software tester who is given code and a possible test case in English, you must come up '
            'with English test cases for Java code in plain words in a list for 100% code coverage, with an "(X)" at '
            'the end of a list element if the given possible test case matches it')

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". A possible test case was '
                        f'{FIZZBUZZ_TEST_CASE_DIVISIBLE_BY_3}. Create a list of test cases in English for 100% code '
                        f'coverage, placing an "(X)" on an element if it matches the possible test case.')
    example_answer = f'{FIZZBUZZ_TEST_CASES_WITH_X}'

    # Create test cases for novice programmer's code
    current_question = (f'The code is "{code}". A possible test case was {description}. Create a list of test cases '
                        f'in English for 100% code coverage, placing an "(X)" on an element if it matches the '
                        f'possible test case.')

    return [{"role": "system", "content": role},
            {"role": "user", "content": example_question},
            {"role": "system", "content": example_answer},
            {"role": "user", "content": current_question}
            ]


def test_snippets_prompt_engineering(code, test_case, similar_tests_from_vector_database):
    chat = []
    # Assign a role for the model
    role = ('You are a Java unit test assistant for novice programmers. Using their Java code and a test case in '
            'English, you must return a JUnit 5 function implementing this test case in an "@Test" function which '
            'calls the original class correctly. Do not truncate anything inside the function. The test function '
            'should use assert statements in the format "Arrange Act Assert" in comments. Return only the function. '
            'Ensure that your answer is unbiased and avoids relying on stereotypes.')
    chat.append({"role": "system", "content": role})

    # Help model with similar test from vector database (if it exists)
    if similar_tests_from_vector_database is not None:
        tests_for_inspiration = (f'To help you create the 1 @Test you need, here is an entire testing file to help you '
                                 f'create 1 test function to improve your knowledge base: '
                                 f'"{similar_tests_from_vector_database["tests"]}"')
        chat.append({"role": "user", "content": tests_for_inspiration})

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". The test case to implement is '
                        f'{FIZZBUZZ_TEST_CASE_DIVISIBLE_BY_3}. Create an @Test function for this test case. ')
    chat.append({"role": "user", "content": example_question})
    example_answer = f'{FIZZBUZZ_TEST_CODE_DIVISIBLE_BY_3}'
    chat.append({"role": "system", "content": example_answer})

    current_question = (f'The code is "{code}". The test case to implement is {test_case}. Create an @Test function '
                        f'for this test case.')
    chat.append({"role": "user", "content": current_question})
    return chat


def explore_test_cases_prompt_engineering(code, test_cases, description):
    # Assign a role for the model
    role = ('You are an expert software tester who is given code, a list of test cases in English and a description of '
            'a test case, you must mark the end of a test case list element with an "(X)" if it matches the '
            'description. If the description does not match any list element, return the list of test cases unchanged.')

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". A list of test cases is "{FIZZBUZZ_TEST_CASES}". The '
                        f'description of a possible test case is {FIZZBUZZ_TEST_CASE_DIVISIBLE_BY_3}. Place an "(X)" '
                        f'at the end of a list element if it matches the possible test case.')
    example_answer = f'{FIZZBUZZ_TEST_CASES_WITH_X}'

    # Create test cases for novice programmer's code
    current_question = (f'The code is "{code}". A list of test cases is "{test_cases}". The description of a possible '
                        f'test case is {description}. Place an "(X)" at the end of a list '
                        f'element if it matches the possible test case.')

    return [{"role": "system", "content": role},
            {"role": "user", "content": example_question},
            {"role": "system", "content": example_answer},
            {"role": "user", "content": current_question}
            ]


def corrective_prompt_engineering(code, tests, list_of_function_names, errors):
    # Assign a role for the model
    role = (f'You are an expert software tester who is given some Java code, a JUnit test file, and errors from the '
            f'tests. You must fix the errors for each function and return the entire file with the same functions '
            f'{list_of_function_names}. Keep the exact comments above each function, do not change the comments. I\'ll tip $100 for a better solution!')

    # Few-shot prompting
    example_question = (f'The code is "{FIZZBUZZ_NOVICE_CODE}". The test file is "{FIZZBUZZ_INCORRECT_TEST_FILE}". '
                        f'The errors are "{FIZZBUZZ_INCORRECT_TEST_FILE_ERRORS}". Fix all errors and return the entire '
                        f'test file.')
    example_answer = f'{FIZZBUZZ_CORRECT_TEST_FILE}'

    current_question = (f'The code is "{code}". The test file is "{tests}". The errors are "{errors}". Fix all errors '
                        f'and return the entire test file.')

    return [{"role": "system", "content": role},
            {"role": "user", "content": example_question},
            {"role": "system", "content": example_answer},
            {"role": "user", "content": current_question}
            ]


def simplify_focal_method_prompt_engineering(focal_method):
    role = ("Your goal is to take a complex Java method that requires external libraries or undefined functions, and "
            "convert it to a simple method that can be run with only standard Java and no external functions. You "
            "will be penalized if you return code that depends on undefined functions or classes such as 'this.'. "
            "Your goal should be to convert the code to a simple example that a novice programmer would understand. "
            "You cannot assume anything is defined elsewhere, all necessary code should be within the function.")
    prompt = (
            "A complex Java method is '" + focal_method + "'. I'm going to tip $100 for a better solution! Return a "
                                                          "simple method in a JSON.")
    return [{"role": "system", "content": role},
            {"role": "user", "content": prompt}]


def simplify_test_code_prompt_engineering(novice_java_method, test_case):
    role = ("Your goal is to take a Java method and generate a simple JUnit test function with comments. "
            "You will also be given a complex JUnit test to help get inspiration. "
            "You will be penalized if you use undefined functions or classes such as 'this.'. "
            "You will be punished if you return an entire class with imports. "
            "Your task is to only return a JUnit @Test method that covers one case only."
            "Your response should start with //Test case: description of input/output \n @Test"
            "Do structure the test in the format 'Arrange, Act, Assert'. "
            "Add a comment above the annotation '@Test' that describes what the method does.")
    prompt = (f"Generate a JUnit test for the Java method '{novice_java_method}'. Use this JUnit test as inspiration "
              f"'{test_case}'. I'm going to tip $100 for a better solution! Return the test in a JSON.")
    return [{"role": "system", "content": role},
            {"role": "user", "content": prompt}]


# The code above was swapped for the code below for internal evaluation of prompt engineering (section 4.3.1 in thesis)
# This prompt uses around 93 characters.
def evaluation_prompt_engineering(source_code, description):
    prompt = (f"My source code is '{source_code}'. I think {description}. Create a JUnit test case that can pass or "
              f"fail to test this belief.")
    return [{"role": "user", "content": prompt}]
