import os

from openai import OpenAI


client = OpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)

response = client.responses.create(
    model=os.environ["BEDROCK_OPENAI_MODEL_ID"],
    input=[
        {
            "role": "developer",
            "content": "You are a software engineer with excellent AWS cloud knowledge. Be concise and practical.",
        },
        {
            "role": "user",
            "content": "Design a distributed architecture on AWS in Python that should support 100k requests per second across multiple geographic regions.",
        },
    ],
    reasoning={"effort": "medium"},
    text={"verbosity": "low"},
)

print(response.output_text)
