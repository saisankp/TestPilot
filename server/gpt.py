import os

from openai import OpenAI

from process_response import parse_test_cases, parse_test_snippet, parse_code_within_markdown
from prompt_engineering import (corrective_prompt_engineering, test_cases_prompt_engineering, \
                                test_snippets_prompt_engineering, explore_test_cases_prompt_engineering, \
                                sanitize_vague_description_prompt_engineering, test_snippet_prompt_engineering)
from vector_database import convert_text_to_embedding_vector, cosine_similarity_to_known_tests


def sanitize_vague_test_case(code, natural_language):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=sanitize_vague_description_prompt_engineering(code, natural_language)
    )
    return completion.choices[0].message.content.replace("\n", "")


def generate_test_cases(code, natural_language):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=test_cases_prompt_engineering(code, natural_language)
    )
    return parse_test_cases(completion.choices[0].message.content)


def generate_test_snippet(collection, code, test_case):
    list_of_test_snippets = []
    list_of_function_names = []
    similar_tests_from_vector_database = None
    similar_tests_code_coverage = None

    code_vector = convert_text_to_embedding_vector(code)
    score, similar_tests = cosine_similarity_to_known_tests(collection, code_vector)
    # Disregarded similar entry below from embeddings when doing internal evaluation (section 4.3.3 in thesis)
    if score > 0.8:
        similar_tests_from_vector_database = similar_tests
        similar_tests_code_coverage = similar_tests['code_coverage']

    client = OpenAI()
    completion = client.chat.completions.create(
        # Swapped model below to a non-finetuned "gpt-3.5-turbo-0125" for internal evaluation (section 4.3.2 in thesis)
        model=os.getenv("FINE_TUNED_GPT_3_POINT_5_TURBO"),
        messages=test_snippet_prompt_engineering(code, test_case, similar_tests_from_vector_database)
    )

    if completion.choices[0].message.content.startswith('{"Test": "'):
        llm_response = completion.choices[0].message.content.replace('{"Test": "', '')[: -2]
    else:
        llm_response = completion.choices[0].message.content

    test_snippet, function_name = parse_test_snippet(test_case.split(", ", 2)[-1],
                                                     llm_response)
    list_of_test_snippets.append(test_snippet)
    list_of_function_names.append(function_name)
    return list_of_test_snippets, list_of_function_names, similar_tests_code_coverage


def generate_test_snippets(collection, code, test_cases):
    list_of_test_snippets = []
    list_of_function_names = []
    similar_tests_from_vector_database = None
    similar_tests_code_coverage = None

    code_vector = convert_text_to_embedding_vector(code)
    score, similar_tests = cosine_similarity_to_known_tests(collection, code_vector)
    if score > 0.8:
        similar_tests_from_vector_database = similar_tests
        similar_tests_code_coverage = similar_tests['code_coverage']

    client = OpenAI()
    for test_case in test_cases:
        completion = client.chat.completions.create(
            model=os.getenv("FINE_TUNED_GPT_3_POINT_5_TURBO"),
            messages=test_snippets_prompt_engineering(code, test_case, similar_tests_from_vector_database)
        )

        if completion.choices[0].message.content.startswith('{"Test": "'):
            llm_response = completion.choices[0].message.content.replace('{"Test": "', '')[: -2]
        else:
            llm_response = completion.choices[0].message.content

        test_snippet, function_name = parse_test_snippet(test_case, llm_response)
        list_of_test_snippets.append(test_snippet)
        list_of_function_names.append(function_name)
    return list_of_test_snippets, list_of_function_names, similar_tests_code_coverage


def gpt_3_5_turbo(code, tests, list_of_function_names, errors):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=corrective_prompt_engineering(code, tests, list_of_function_names, errors)
    )
    return parse_code_within_markdown(completion.choices[0].message.content)


def explore_test_cases(original_code, test_cases, description):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=explore_test_cases_prompt_engineering(original_code, test_cases, description)
    )
    return parse_test_cases(completion.choices[0].message.content)

