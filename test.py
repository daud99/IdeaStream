import json
from openai import OpenAI
client = OpenAI()

import json

def perform_analysis(transcription):
    # Call OpenAI API for completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f'''
                You need to generate the titles and respective ideas based on the following transcription:
                \"\"\" 
                {transcription}
                \"\"\"
                The result should strictly be in the following JSON format without any extra explanation, text, or comments:
                {{
                  "titles": [
                    {{
                        "title": "Title 1",
                        "idea": "Idea 1",
                        "idea": "Idea 2"
                    }},
                    {{
                        "title": "Title 2",
                        "idea": "Idea 1",
                        "idea": "Idea 2"
                    }}
                  ],
                  "suggestions": [
                     "Suggestion 1"
                     "Suggestion 2"
                  ]
                }}
                Ensure the output is valid JSON and contains only the list structure provided.
                '''
            }
        ]
    )

    print('completion:')
    print(completion)
    # Access the content attribute correctly from the completion object
    response_text = completion.choices[0].message.content

    # Clean up the response text to extract valid JSON
    response_text = response_text.strip()  # Remove leading/trailing whitespace
    if response_text.startswith('```json') and response_text.endswith('```'):
        response_text = response_text[8:-3].strip()  # Remove the code block markers

    # Convert the response to a JSON object
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError:
        response_json = {"error": "Invalid JSON format in response"}

    return response_json



# print(perform_analysis("Today, we are discussing the future of artificial intelligence in healthcare. AI is expected to revolutionize the industry by improving diagnosis accuracy, optimizing treatment plans, and automating administrative tasks. There are still challenges to overcome, such as data privacy concerns, bias in algorithms, and integration with existing healthcare systems."))

print(perform_analysis('```json\n{\n  "titles": [\n    {\n        "title": "Revolutionizing Healthcare with AI",\n        "idea": "AI improves diagnosis accuracy",\n        "idea": "Optimizing treatment plans with AI"\n    },\n    {\n        "title": "Challenges and Opportunities for AI in Healthcare",\n        "idea": "Addressing data privacy concerns",\n        "idea": "Integrating AI with existing systems"\n    }\n  ],\n  "suggestions": [\n    {\n        "suggestion": "Implement rigorous data privacy standards"\n    },\n    {\n        "suggestion": "Develop unbiased AI algorithms"\n    }\n  ]\n}\n```'))