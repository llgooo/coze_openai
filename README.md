# Coze API OpenAI-Compatible Chat Completion API

This project provides an OpenAI-compatible API for Coze chat API.

## Setup

1. **Clone the repository**:
   ```sh
   git clone https://github.com/llgooo/coze_openai.git
   cd coze_openai
   ```

2. Install dependencies:
pip install -r requirements.txt

3. Create a .env file:Create a .env file in the root directory of the project and add the following environment variables:
BOT_ID=your_bot_id

4. Run the FastAPI application:
uvicorn main:app --host 0.0.0.0 --port 8000

5. Test the API with cURL:You can test the API using the following cURL command:
```sh
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer pat_3WDbo72AZeBhS7YEu3E3cCUGAUzTMdzuebrHVWgzt9SCMU6SibrZ84JFdXQAbvd7" \
-d '{
      "model": "your_bot_id",
      "messages": [
        {
          "role": "user",
          "content": "who are you?"
        }
      ],
      "stream": true
    }'
```
