from flask import Flask, request, Response
import json

dummy_webhook = Flask(__name__)

@dummy_webhook.route('/test', methods=['POST'])

def webhook():
    print('Received webhook. Request details:')
    print('Headers:', json.dumps(dict(request.headers), indent=2))
    
    data = request.get_data()
    try:
        json_data = json.loads(data)
        print('Parsed JSON data:')
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError as e:
        print('Error parsing JSON:', str(e))
        print('Raw body:', data.decode())
    
    return Response('Webhook received', status=200)

if __name__ == '__main__':
    dummy_webhook.run(port=8000)