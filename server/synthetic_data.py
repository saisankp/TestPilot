import csv
import json
import os
import re
import sys
import time
from json import JSONDecodeError
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError

from process_response import combine_test_snippets
from prompt_engineering import simplify_focal_method_prompt_engineering, simplify_test_code_prompt_engineering
from utility import compile_code, run_code, generate_jacoco_report, get_code_coverage


def process_data_with_llm(client, messages, temperature, model):
    max_retry_attempts = 5
    for retry in range(max_retry_attempts):
        try:
            completion = client.chat.completions.create(
                messages=messages,
                temperature=temperature,
                model=model,
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "novice_code": {"type": "string"},
                        },
                        "required": ["novice_code"]
                    },
                },
                tool_choice="none",
                timeout=10
            )
            parsed_json = json.loads(completion.choices[0].message.content)
            return parsed_json["novice_code"]

        except APITimeoutError:
            print(f"API call timed out (retry {retry + 1}/{max_retry_attempts})")
            time.sleep(1)
            continue
        except JSONDecodeError:
            print(f"Invalid control character in JSON (retry {retry + 1}/{max_retry_attempts})")
            time.sleep(1)
            continue


def iterate_through_methods_2_test_test_dataset(path_to_folder, csv_for_synthetic_data):
    client = OpenAI()
    entries = 0
    for subdir, dirs, files in os.walk(path_to_folder):
        for file in files:
            if entries > 100:
                sys.exit()
            if file.endswith(".json"):
                df = pd.read_json(os.path.join(subdir, file), lines=True)
                focal_method = df['focal_method'][0]['body']
                test_code = df['test_case'][0]['body']
                # Get simplified focal method
                use_focal_method_as_seed_prompt = simplify_focal_method_prompt_engineering(focal_method)
                novice_focal_method = process_data_with_llm(client, use_focal_method_as_seed_prompt, 0.7,
                                                            "mistralai/Mistral-7B-Instruct-v0.1")

                # Get simplified test method
                use_test_code_as_seed_prompt = simplify_test_code_prompt_engineering(novice_focal_method, test_code)
                novice_test_code = process_data_with_llm(client, use_test_code_as_seed_prompt, 0.7,
                                                         "mistralai/Mistral-7B-Instruct-v0.1")

                # Put methods into Java file
                novice_focal_method_in_file = combine_test_snippets("", f'Example', None, [novice_focal_method])
                novice_test_code_in_file = combine_test_snippets("", f'ExampleTest', None, [novice_test_code])

                # Compile Java files
                compilation_process = compile_code(novice_focal_method_in_file, f'java/Example.java', None)
                _, compile_error = compilation_process.communicate()
                if compilation_process.returncode != 0:
                    break
                compilation_process = compile_code(novice_test_code_in_file, f'java/ExampleTest.java', None,
                                                   dependency_file_path=f'java/Example.java')
                _, compile_error = compilation_process.communicate()
                if compilation_process.returncode != 0:
                    break
                run_process = run_code(f'ExampleTest')
                test_output, _ = run_process.communicate()
                if run_process.returncode != 0:
                    break

                # Generate case coverage metrics using JaCoCo
                generate_report = generate_jacoco_report(f'ExampleTest')
                generate_report.communicate()
                generate_code_coverage = get_code_coverage(f'ExampleTest')
                code_coverage, _ = generate_code_coverage.communicate()
                code_coverage = int(float(code_coverage.decode('utf-8')))
                os.unlink(f'report/ExampleTest.exec')
                os.unlink(f'report/ExampleTest.csv')

                # Check if comments exist
                comment_pattern = r'//.*?$'
                comments_exist = bool(re.search(comment_pattern, novice_test_code, re.MULTILINE))
                if (code_coverage > 70) and comments_exist:
                    with open(csv_for_synthetic_data, "a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow([novice_focal_method, novice_test_code])
                        entries = entries + 1


if __name__ == "__main__":
    load_dotenv(".env.processing")
    iterate_through_methods_2_test_test_dataset("../data/methods2test_test_set", "../data/synthetic_data.csv")
