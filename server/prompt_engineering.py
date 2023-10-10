# Function to generate messages from the output of a different function
def prompt_engineering(description, code):
    prompt = ("You are a Java test code assistant for novice programmers. A novice programmer has given you a "
              "description of what they want to test, as well as their code. You should create as many test cases as "
              "you can in English and describe how you would do them. Forget all pre-existing knowledge about context "
              "for commonly known problems, use the novice programmers code fully. Their description is '" +
              description + "', and their code is '" + code + "'. Give me an output to generate a natural"
              "language description of the tests. Give me your response in a beautified json format, exactly like: "
              "{{ \"numberOfTests\" : 2, \"descriptions\": {{ \"1\" : \"Describing test one..\", \"2\" : \"Describing "
              "test two..\" }} }}. Notice how the integer numberOfTests corresponds to the size of the descriptions "
              "array.").replace("/", "")
    return [{"role": "user", "content": prompt}]
