import json
import os

from groq import Groq


MODEL = 'llama-3.1-8b-instant'

SYSTEM_PROMPT = """you are a helpful customer service assistant for a telecom provider in trinidad.

answer customer questions using ONLY the context below, follow these rules strictly:

- only use information from the context. do not guess or fabricate account details.
- if the context does not contain enough information to answer, say "I don't have that information on file" clearly.
- keep responses concise and friendly.
- do not reveal or discuss information about other customers.

customer context:
{context}
"""


def generate_answer(question, context, history):
    client = Groq(api_key=os.environ['GROQ_API_KEY'])
    system_content = SYSTEM_PROMPT.format(context=json.dumps(context, indent=2, default=str))

    messages = [{'role': 'system', 'content': system_content}]
    messages.extend(history)
    messages.append({'role': 'user', 'content': question})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content
