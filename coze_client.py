import json
import requests
from aiohttp import ClientSession


class CozeClient:
    def __init__(self, token):
        self.base_url = "https://api.coze.com"
        self.token = token

    def request_header(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Host": "api.coze.com"
        }

    def make_request(self, endpoint, method, payload):
        url = f"{self.base_url}{endpoint}"
        headers = self.request_header()
        response = requests.request(method, url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        return response.json()

    async def handle_stream_response(self, response):
        async for line in response.content:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("data:"):
                line_str = line_str[len("data:"):].strip()
            if line_str:
                yield json.loads(line_str)

    async def chat_stream(self, request):
        request['stream'] = True
        url = f"{self.base_url}/open_api/v2/chat"
        headers = self.request_header()

        async with ClientSession() as session:
            async with session.post(url, headers=headers, json=request, ssl=False) as response:
                response.raise_for_status()
                async for stream_resp in self.handle_stream_response(response):
                    yield stream_resp

    def chat_non_stream(self, request):
        request['stream'] = False
        return self.make_request("/open_api/v2/chat", "POST", request)
