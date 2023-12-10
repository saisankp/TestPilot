import openai
from flask import jsonify

from process_response import process_response
from prompt_engineering import prompt_engineering, corrective_prompt_engineering


def gpt(model, action, code, natural_language, previous_tests=None):
    if action == "prompt":
        messages = prompt_engineering(code, natural_language)
    elif action == "correction":
        messages = corrective_prompt_engineering(code, previous_tests, natural_language)
    else:
        raise ValueError("Action for GPT was not either prompting or correction.")
    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )
    return jsonify(process_response(model, gpt, completion['choices'][0]['message']['content'], code))

# `natural_language` is either the description from the novice or the description of errors from generated tests before
