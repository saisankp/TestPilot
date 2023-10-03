from flask import Flask, request, jsonify

testpilot = Flask(__name__)

@testpilot.route("/")
def home():
    return "Home"

if __name__ == "__main__":
    testpilot.run(debug=True)