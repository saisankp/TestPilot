from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from gpt import gpt

testpilot = Flask(__name__)
CORS(testpilot, support_credentials=True)

#TODO: Support multiple LLM's (Google's Gemini/Bard, Meta's LLaMA, Locally running LLMs such as Mistral etc)
#TODO: Make a class of each LLM with their model along with action class instead of strings.
@testpilot.route("/testpilot")
@cross_origin(supports_credentials=True)
def test_pilot():
    code = request.args.get('code')
    description = request.args.get('description')
    if code and description:
        # model="gpt-4-1106-preview",
        return gpt("gpt-3.5-turbo-1106", "prompt", code, description)
    else:
        print('ERROR')
        return jsonify({'error': 'Missing parameter to API'}), 400


@testpilot.route("/testpilot-correction")
@cross_origin(supports_credentials=True)
def test_pilot_correction():
    print("Error correction in progress...")
    original_code = request.args.get('code')
    previous_tests = request.args.get('tests')
    errors = request.args.get('errors')
    model = request.args.get('model')
    print("original code is " + original_code)
    print("previous tests is " + previous_tests)
    print("errors is " + errors)
    print("model is " + model)
    if original_code and previous_tests and errors:
        return gpt(model, "correction", original_code, errors, previous_tests)
    else:
        print('ERROR')
        return jsonify({'error': 'Missing parameter to API'}), 400


if __name__ == "__main__":
    load_dotenv()
    testpilot.run(port=8000, debug=True)
