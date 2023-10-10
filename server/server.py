from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from prompt_engineering import prompt_engineering
import openai

testpilot = Flask(__name__)
CORS(testpilot, support_credentials=True)


@testpilot.route("/gpt")
@cross_origin(supports_credentials=True)
def gpt():
    description = request.args.get('description')
    code = request.args.get('code')
    if code and description:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt_engineering(description, code)
        )
        return jsonify(completion)
    else:
        return jsonify({'error': 'Missing code parameter'}), 400


if __name__ == "__main__":
    load_dotenv()
    testpilot.run(debug=True)
