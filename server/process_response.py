import re


def process_response(model, call_llm, llm_response, user_code):
    print(llm_response)
    # Gather the code inside the markdown (i.e. ```java {tests here} ```)
    pattern = r'```java(.*?)```'
    matches = re.findall(pattern, llm_response, re.DOTALL)
    generated_tests = ''.join(matches)
    # print(generated_tests)

    # If the llm has forgotten to include the package the user had, we can add it to the generated tests
    if user_code.startswith("package"):
        match = re.search(r'package\s+(.*?);', user_code, re.DOTALL)
        package_name = match.group(1).strip()
        if not generated_tests.__contains__(f"package {package_name}"):
            generated_tests = f"package {package_name};\n\n" + generated_tests

    # Collect names of test functions
    pattern = re.compile(r'@Test\s*\n\s*(?:\/\/[^\n]*\n\s*)*(?:public\s+)?void\s+(\w+)\(')
    test_function_names = pattern.findall(generated_tests)

    # Collect descriptions of test functions from comments (GPT 4 follows option 1 and GPT 3.5 favours option 2)
    # Option 1 (preferred) : Comments appear before `@Test`, i.e. "// Comment @Test"
    pattern = r'\/\/[^\n]*?(?=\n\s+@Test)'
    matches = re.findall(pattern, generated_tests, re.DOTALL)

    # Option 2 (backup) : Comments appear after @Test, i.e. "@Test // Comment"
    if len(matches) == 0:
        pattern = r'@Test\s*\n\s*(//[^\n]*)'
        matches = re.findall(pattern, generated_tests, re.DOTALL)

    # Dictionary of comments describing each test (with removed titles, colons, and comment symbols)
    descriptions = {
        str(i + 1): match.replace("Test case:", "").replace("Test case description:", "")
        .replace("Test description:", "").replace("//", "").replace("\"", "'").strip()
        for i, match in enumerate(matches)
    }

    # TODO: if any of these 3 are size 0, call the correction function to correct and then call this function again,
    #  get JSON data and check again indefinitely or just once.
    # if not descriptions:
    #     print("Recalling Llm because no descriptions (comments)")
    #     json_data = call_llm(model, "correction", user_code,
    #                          "There are no comments above each @Test in the tests acting as "
    #                          "descriptions for each test. Add comments above each @Test", generated_tests)
    # else:
    json_data = {
        "testFunctionNames": test_function_names,
        "descriptions": descriptions,
        "tests": generated_tests.strip()
    }
    print(json_data)

    return json_data
