import json
import os

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.model_selection import train_test_split


def format_synthetic_data(data):
    data_for_finetuning = []
    for _, row in data.iterrows():
        json_response = '{"Test": "' + row['test'] + '"}'
        data_for_finetuning.append({
            "messages": [
                {"role": "user", "content": row['code']},
                {"role": "assistant", "content": json_response}
            ]
        })
    return data_for_finetuning


def split_data_into_training_and_validation(data_for_finetuning):
    training_data, validation_data = train_test_split(data_for_finetuning, test_size=0.2)
    return training_data, validation_data


def create_jsonl_file(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as file:
        for row in data:
            json.dump(row, file)
            file.write('\n')


def upload_jsonl_to_openai(OpenAI_client, training_jsonl, validation_jsonl):
    training_file = OpenAI_client.files.create(
        file=open(training_jsonl, "rb"), purpose="fine-tune"
    )
    validation_file = OpenAI_client.files.create(
        file=open(validation_jsonl, "rb"), purpose="fine-tune"
    )

    name_for_finetuning = "testpilot"
    finetuning_job = OpenAI_client.fine_tuning.jobs.create(training_file=training_file.id,
                                                           validation_file=validation_file.id,
                                                           model="gpt-3.5-turbo-0125",
                                                           suffix=name_for_finetuning)
    return finetuning_job


if __name__ == "__main__":
    load_dotenv(".env.server")
    csv = pd.read_csv("../data/synthetic_data.csv")
    synthetic_data = format_synthetic_data(csv)
    training_data, validation_data = split_data_into_training_and_validation(synthetic_data)
    create_jsonl_file(training_data, "../data/fine-tuning.jsonl")
    create_jsonl_file(validation_data, "../data/validation.jsonl")
    client = OpenAI()
    fine_tuning_job = upload_jsonl_to_openai(client, "../data/fine-tuning.jsonl", "../data/validation.jsonl")
    print(fine_tuning_job)
