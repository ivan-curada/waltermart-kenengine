# Copyright 2019 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START run_pubsub_server_setup]
import base64
from flask import Flask, request
import os
import sys
from core import watermark
from gmailapi import gmail
import glob
import urllib.request
import logging

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

app = Flask(__name__)
# [END run_pubsub_server_setup]

def handleMessage(payload):
    logger.info('Handling payload...')
    try:
        fileUrl = payload['filePath']
        sender = payload['sender']
        receiver = payload['receiver']
        access_token = payload['access_token']

        urllib.request.urlretrieve(fileUrl, 'input.pdf')             # download the file from storage
        logger.info('File downloaded')
        watermark.mainRuntime(receiver, 'input.pdf')                    # run Kenengine watermarke
        logger.info('Watermarking completed. Attempting to send email...')

        message = gmail.create_message(sender, receiver, '')           # compose email
        gmail.sendMessage(sender, message, access_token)
        logger.info('Sent to Gmail API. Cleaning resources...')
        cleanResources()
        return ('', 204)
    except Exception as e:
        logger.critical(f'error: {e}')
        print(e)
        return f'Internal server error: {e}', 500

def cleanResources():
    fileList = glob.glob('*.pdf')
    for file in fileList:
        try:
            os.remove(file)
        except Exception as e:
            print(e)
    logger.info('Resources cleaned')

# [START run_pubsub_handler]
@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        logger.critical(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        logger.critical(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']

    payload = ''
    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        logger.info('Payload Received')
        payload = base64.b64decode(pubsub_message['data']).decode('utf-8').strip()
    sys.stdout.flush()

    return handleMessage(payload)
# [END run_pubsub_handler]


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)
