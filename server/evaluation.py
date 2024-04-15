import csv
import json
import os
import re

import pandas as pd

from process_response import combine_test_snippets, parse_class_and_package_name
from prompt_engineering import sanitize_vague_description_prompt_engineering, test_snippet_prompt_engineering
from utility import compile_code, run_code, delete_generated_files


# Used to manually convert the code where the evaluation dataset is from, into one line for evaluation.json
def convert_code_into_one_line_for_evaluation_dataset(code):
    return (repr(code)[1:-1].replace('\\n', '\\n')).replace('"', '\\"').replace("\\'", "'")


# Used to measure 3 metrics from an inference (for internal and external evaluations)
def append_result_of_inference_to_result_file(code, returned_test, expected_test_status, result_csv_file_path):
    compiled = True
    accurate_test = True

    # Compilation rate  - do the generated tests compile?
    class_name, package_name = parse_class_and_package_name(code)
    returned_test_in_file = combine_test_snippets(code, class_name, package_name, [returned_test])
    compilation_process = compile_code(code, f'java/{class_name}.java', package_name)
    _, compile_error = compilation_process.communicate()
    compilation_process = compile_code(returned_test_in_file, f'java/{class_name}Test.java', package_name,
                                       dependency_file_path=f'java/{class_name}.java')
    compilation_process.communicate()
    if compilation_process.returncode != 0:
        compiled = False

    # Test accuracy rate - do the test pass or fail when it should?
    run_process = run_code(f'{class_name}Test')
    test_output, _ = run_process.communicate()
    if run_process.returncode != 0:
        # Test failed when it was expected to pass
        if expected_test_status == 1:
            accurate_test = False
    else:
        # Test passed when it was expected to fail
        if expected_test_status == 0:
            accurate_test = False

    delete_generated_files(class_name)

    # Documentation rate - are there comments in the generated tests?
    comment_pattern = r'//.*?$'
    documentation = bool(re.search(comment_pattern, returned_test, re.MULTILINE))

    # Append the entry of the results to the correct csv
    file_exists = os.path.exists(result_csv_file_path)
    os.makedirs(os.path.dirname(result_csv_file_path), exist_ok=True)
    if not file_exists:
        with open(result_csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Compiled', 'Accurate', 'Documentation'])
    with open(result_csv_file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([compiled, accurate_test, documentation])


# Get metrics as percentages from result CSV files
def get_metrics(path_to_result_file):
    df = pd.read_csv(path_to_result_file)
    for column in df.columns:
        if df[column].dtype == bool:
            continue
        # If the cell is a string representation of a boolean, convert it to a boolean for getting a percentage later
        df[column] = df[column].apply(lambda x: eval(x))
    return round(df['Compiled'].mean() * 100), round(df['Accurate'].mean() * 100), round(
        df['Documentation'].mean() * 100)


def get_average_gpt_4_code_input_tokens(evaluation_dataset_path):
    f = open(evaluation_dataset_path)
    data = json.load(f)
    total_tokens = 0
    for i in data['evaluation_dataset']:
        total_tokens = total_tokens + len(i['description'])
    f.close()
    return total_tokens / len(data['evaluation_dataset'])

def get_gpt_4_prompt_input_tokens():
    response = sanitize_vague_description_prompt_engineering("", "")
    total_tokens = 0
    for item in response:
        total_tokens = total_tokens + len(item['content'])
    return total_tokens

def get_gpt_3_point_5_code_input_tokens():
    response = test_snippet_prompt_engineering("", "", None)
    total_tokens = 0
    for item in response:
        total_tokens = total_tokens + len(item['content'])
    return total_tokens


def get_average_gpt_3_point_5_code_input_tokens(evaluation_dataset_path):
    f = open(evaluation_dataset_path)
    data = json.load(f)
    total_tokens = 0
    for i in data['evaluation_dataset']:
        total_tokens = total_tokens + len(i['code'])
    f.close()
    return total_tokens / len(data['evaluation_dataset'])



if __name__ == "__main__":
    # Comment below is used for appending metrics to the correct result CSV file from an inference done manually
    # append_result_of_inference_to_result_file("Test code", "Returned test snippet", 0, "evaluation/results/prompt_engineering/without_prompt_engineering.csv")

    # print("INTERNAL EVALUATION: PROMPT ENGINEERING")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/prompt_engineering/default_testpilot.csv")
    # print("Default TestPilot:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/prompt_engineering/without_prompt_engineering.csv")
    # print("TestPilot without prompt engineering:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    #
    # print("INTERNAL EVALUATION: FINE-TUNING")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/fine_tuning/default_testpilot.csv")
    # print("Default TestPilot:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/fine_tuning/without_fine_tuning.csv")
    # print("TestPilot without fine-tuning:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    #
    # print("INTERNAL EVALUATION: EMBEDDINGS")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/embeddings/default_testpilot.csv")
    # print("Default TestPilot:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/embeddings/without_embeddings.csv")
    # print("TestPilot without embeddings:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    #
    # print("EXTERNAL EVALUATION: TESTPILOT VS CHATGPT")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/chatgpt/testpilot.csv")
    # print("Default TestPilot:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    # compilation_rate, test_accuracy_rate, documentation_rate = get_metrics(
    #     "evaluation/results/chatgpt/chatgpt.csv")
    # print("ChatGPT:")
    # print(f"Compilation rate: {compilation_rate}%")
    # print(f"Test accuracy rate: {test_accuracy_rate}%")
    # print(f"Documentation rate: {documentation_rate}%")
    print(get_average_gpt_4_code_input_tokens("evaluation/dataset/evaluation.json"))
    print(get_average_gpt_3_point_5_code_input_tokens("evaluation/dataset/evaluation.json"))
    print(get_gpt_4_prompt_input_tokens())
    print(get_gpt_3_point_5_code_input_tokens())

    #print(len(sanitize_vague_description_prompt_engineering("", "")))
