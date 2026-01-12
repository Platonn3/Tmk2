import os
import requests
from celery import shared_task
from dotenv import load_dotenv

from source.services.promt import get_prompt

load_dotenv()
API_KEY = os.getenv("API_KEY")


@shared_task(name="source.services.llm.get_llm_response")
def get_llm_response(text: str) -> str:
    prompt = get_prompt(text)
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "model": "qwen/qwen3-coder:free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            return content
        else:
            return "Ошибка: Пустой ответ от модели"

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except Exception as err:
        return f"Other error occurred: {err}"


if __name__ == "__main__":
    test_question = "Напиши короткую гипотезу о том, почему коты любят коробки."
    print("Запрос отправлен...")
    answer = get_llm_response(test_question)
    print("\nОТВЕТ ОТ НЕЙРОСЕТИ:\n")
    print(answer)