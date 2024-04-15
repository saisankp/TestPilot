import os

from astrapy.db import AstraDB
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from gpt import (generate_test_cases, generate_test_snippets, gpt_3_5_turbo, explore_test_cases,
                 sanitize_vague_test_case, generate_test_snippet)
from process_response import (combine_test_snippets, parse_error_output_from_junit,
                              replace_expected_with_returned, parse_class_and_package_name,
                              parse_ASCII_control_characters, convert_code_into_list_of_functions,
                              remove_unknown_tests_from_code)
from utility import compile_code, run_code, indent_code, delete_generated_files, generate_jacoco_report, \
    get_code_coverage
from vector_database import access_collection, convert_text_to_embedding_vector, insert_to_collection

testpilot = Flask(__name__)
CORS(testpilot, support_credentials=True)


@testpilot.route("/testpilot/testing")
@cross_origin(supports_credentials=True)
def testing_mode():
    code = request.args.get('code')
    description = request.args.get('description')
    if code and description:
        # Extract class name and package name (if any) from novice code
        class_name, package_name = parse_class_and_package_name(code)

        # Compile the novice programmer's code, returning 400 if it doesn't compile
        compilation_process = compile_code(code, f'java/{class_name}.java', package_name)
        _, compile_error = compilation_process.communicate()
        if compilation_process.returncode != 0:
            return jsonify({'error': 'Compilation failed', 'message': compile_error}), 400

        # Generate a concise natural language test case with GPT-4
        test_case = sanitize_vague_test_case(code, description)

        # Allocate each test case to GPT-3.5 Turbo (fine-tuned) to generate @Test code snippets
        list_of_test_snippets, list_of_function_names, vector_database_code_coverage = generate_test_snippet(
            collection, code, test_case)

        # Remove the parameter call and assertEquals call, leaving the description only
        test_case = test_case.split(", ", 2)[-1]

        # Combine all code test snippets into one file using string manipulation
        combined_test_file = combine_test_snippets(code, class_name, package_name, list_of_test_snippets)

        # Compile the generated combined test file
        compilation_process = compile_code(combined_test_file, f'java/{class_name}Test.java', package_name,
                                           dependency_file_path=f'java/{class_name}.java')
        _, compile_error = compilation_process.communicate()

        # Run the generated tests and correct them using local string manipulation if there are any errors
        run_process = run_code(f'{class_name}Test')
        test_output, _ = run_process.communicate()
        if run_process.returncode != 0:
            test_status = False
        else:
            test_status = True

        # Generate case coverage metrics using JaCoCo
        generate_report = generate_jacoco_report(f'{class_name}Test')
        generate_report.communicate()
        generate_code_coverage = get_code_coverage(f'{class_name}Test')
        code_coverage, _ = generate_code_coverage.communicate()
        code_coverage = int(float(code_coverage.decode('utf-8')))
        os.unlink(f'report/{class_name}Test.exec')
        os.unlink(f'report/{class_name}Test.csv')

        # Indent code using google-java-format
        indent_process = indent_code(combined_test_file, f'java/{class_name}Test.java')
        formatted_test_file, _ = indent_process.communicate()
        formatted_test_file = formatted_test_file.decode('utf-8')

        # Add the generated code into the vector database as a known good working solution
        code_as_embedding = convert_text_to_embedding_vector(code)
        insert_to_collection(collection, code, formatted_test_file, code_coverage, code_as_embedding)

        # Delete the generated files
        delete_generated_files(class_name)

        return jsonify({
            "descriptions": [test_case],
            "tests": formatted_test_file,
            "codeCoverage": code_coverage,
            "vectorDatabaseCoverage": vector_database_code_coverage,
            "testFunctionNames": list_of_function_names,
            "testStatus": test_status
        })
    else:
        return jsonify({'error': 'Missing parameter to API'}), 400


@testpilot.route("/testpilot/discovery")
@cross_origin(supports_credentials=True)
def discovery_mode():
    code = request.args.get('code')
    description = request.args.get('description')
    test_code = request.args.get('testCode')
    test_cases = request.args.get('testCases')
    known_test_case_indices = request.args.get('knownTestCaseIndices')
    if code and description and test_code and test_cases and known_test_case_indices:
        # Extract class name and package name (if any) from novice code
        class_name, package_name = parse_class_and_package_name(code)

        # Identify which test case the novice programmer has found with GPT-4 (if any)
        _, index_of_test_case_from_novice = explore_test_cases(code, test_cases, description)

        # Add this index of the discovered test case to the list of indices of known test cases
        list_of_known_test_case_indices = list(set(known_test_case_indices.replace("'", "").split(',')))
        list_of_known_test_case_indices = [int(x) for x in list_of_known_test_case_indices]
        list_of_known_test_case_indices.append(index_of_test_case_from_novice)

        # Make a test file with the known (unblurred) test cases in the list of test cases shown in cards
        test_functions = convert_code_into_list_of_functions(test_code)
        code_with_only_known_tests = remove_unknown_tests_from_code(test_code, test_functions,
                                                                    list_of_known_test_case_indices)

        # Compile the novice programmer's code, returning 400 if it doesn't compile
        compilation_process = compile_code(code, f'java/{class_name}.java', package_name)
        _, compile_error = compilation_process.communicate()
        if compilation_process.returncode != 0:
            return jsonify({'error': 'Compilation failed', 'message': compile_error}), 400

        # Compile the generated combined test file
        compilation_process = compile_code(code_with_only_known_tests, f'java/{class_name}Test.java', package_name,
                                           dependency_file_path=f'java/{class_name}.java')
        compilation_process.communicate()

        # Run the generated tests, correcting them using local string manipulation if there are any errors
        run_process = run_code(f'{class_name}Test')
        test_output, _ = run_process.communicate()

        # Generate case coverage metrics using JaCoCo
        generate_report = generate_jacoco_report(f'{class_name}Test')
        generate_report.communicate()
        generate_code_coverage = get_code_coverage(f'{class_name}Test')
        case_coverage, _ = generate_code_coverage.communicate()
        case_coverage = int(float(case_coverage.decode('utf-8')))

        # Delete the generated files
        delete_generated_files(class_name)
        return jsonify({
            "descriptions": None,
            "tests": None,
            "codeCoverage": None,
            "vectorDatabaseCoverage": None,
            "caseCoverage": case_coverage,
            "testFunctionNames": None,
            "indexOfDescriptionFromNovice": index_of_test_case_from_novice,
        })

    elif code and description:
        # Extract class name and package name (if any) from novice code
        class_name, package_name = parse_class_and_package_name(code)

        # Compile the novice programmer's code, returning 400 if it doesn't compile
        compilation_process = compile_code(code, f'java/{class_name}.java', package_name)
        _, compile_error = compilation_process.communicate()
        if compilation_process.returncode != 0:
            return jsonify({'error': 'Compilation failed', 'message': compile_error}), 400

        # Generate natural language test cases with GPT-4, identifying which test case (if any) is from the novice
        test_cases, index_of_test_case_from_novice = generate_test_cases(code, description)

        # Allocate each test case to GPT-3.5 Turbo (fine-tuned) to generate @Test code snippets
        list_of_test_snippets, list_of_function_names, vector_database_code_coverage = generate_test_snippets(
            collection, code, test_cases)

        # Combine all code test snippets into one file using string manipulation
        combined_test_file = combine_test_snippets(code, class_name, package_name, list_of_test_snippets)

        # Compile the generated combined test file
        compilation_process = compile_code(combined_test_file, f'java/{class_name}Test.java', package_name,
                                           dependency_file_path=f'java/{class_name}.java')
        _, compile_error = compilation_process.communicate()
        if compilation_process.returncode != 0:
            combined_test_file = gpt_3_5_turbo(code, combined_test_file, list_of_function_names, compile_error)
            compilation_process = compile_code(combined_test_file, f'java/{class_name}Test.java', package_name,
                                               dependency_file_path=f'java/{class_name}.java')
            _, compile_error = compilation_process.communicate()

        # Run the generated tests and correct them using local string manipulation if there are any errors
        run_process = run_code(f'{class_name}Test')
        test_output, _ = run_process.communicate()
        if run_process.returncode != 0:
            sanitized_output = parse_ASCII_control_characters(test_output)
            failed_functions, expected_versus_returned = parse_error_output_from_junit(sanitized_output)
            list_of_updated_test_snippets = replace_expected_with_returned(list_of_test_snippets, failed_functions,
                                                                           expected_versus_returned)
            combined_test_file = combine_test_snippets(code, class_name, package_name, list_of_updated_test_snippets)

        # Generate case coverage metrics using JaCoCo
        generate_report = generate_jacoco_report(f'{class_name}Test')
        generate_report.communicate()
        generate_code_coverage = get_code_coverage(f'{class_name}Test')
        code_coverage, _ = generate_code_coverage.communicate()
        code_coverage = int(float(code_coverage.decode('utf-8')))
        os.unlink(f'report/{class_name}Test.exec')
        os.unlink(f'report/{class_name}Test.csv')

        # Make a test file with the known (unblurred) test cases in the list of test cases shown in cards
        list_of_known_test_case_indices = [index_of_test_case_from_novice]
        test_functions = convert_code_into_list_of_functions(combined_test_file)
        code_with_only_known_tests = remove_unknown_tests_from_code(combined_test_file, test_functions,
                                                                    list_of_known_test_case_indices)

        # Compile the generated test file
        compilation_process = compile_code(code_with_only_known_tests, f'java/{class_name}Test.java', package_name,
                                           dependency_file_path=f'java/{class_name}.java')
        compilation_process.communicate()

        # Run the generated tests and correct them using local string manipulation if there are any errors
        run_process = run_code(f'{class_name}Test')
        test_output, _ = run_process.communicate()

        # Generate case coverage metrics using JaCoCo
        generate_report = generate_jacoco_report(f'{class_name}Test')
        generate_report.communicate()
        generate_code_coverage = get_code_coverage(f'{class_name}Test')
        case_coverage, _ = generate_code_coverage.communicate()
        case_coverage = int(float(case_coverage.decode('utf-8')))

        # Indent code using google-java-format
        indent_process = indent_code(combined_test_file, f'java/{class_name}Test.java')
        formatted_test_file, _ = indent_process.communicate()
        formatted_test_file = formatted_test_file.decode('utf-8')

        # Add the generated code into the vector database as a known good working solution
        code_as_embedding = convert_text_to_embedding_vector(code)
        insert_to_collection(collection, code, formatted_test_file, code_coverage, code_as_embedding)

        # Delete the generated files
        delete_generated_files(class_name)

        return jsonify({
            "descriptions": test_cases,
            "tests": formatted_test_file,
            "codeCoverage": code_coverage,
            "vectorDatabaseCoverage": vector_database_code_coverage,
            "caseCoverage": case_coverage,
            "testFunctionNames": list_of_function_names,
            "indexOfDescriptionFromNovice": index_of_test_case_from_novice,
        })
    else:
        return jsonify({'error': 'Missing parameter to API'}), 400


if __name__ == "__main__":
    load_dotenv(".env.server")
    vector_database = AstraDB(token=os.environ.get('ASTRA_DB_KEY'), api_endpoint=os.environ.get('ASTRA_DB_API'))
    collection = access_collection(vector_database, 'TestPilot')
    testpilot.run(port=8000, debug=True)
