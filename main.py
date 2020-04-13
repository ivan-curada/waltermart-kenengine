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
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': 'blasteroidpoc'
})

db = firestore.client()

app = Flask(__name__)
# [END run_pubsub_server_setup]

def handleMessage(payload):
    print('Handling payload...')
    try:
        fileUrl = payload['filePath']
        sender = payload['sender']
        receiver = payload['receiver']
        access_token = payload['access_token']
        userId = payload['userId']
        blastId = payload['blastId']

        urllib.request.urlretrieve(fileUrl, 'input.pdf')                    # download the file from storage
        print('File downloaded')
        watermark.mainRuntime(receiver, 'input.pdf')                        # run Kenengine watermarke
        print('Watermarking completed. Attempting to send email...')

        message = gmail.create_message(sender, receiver, '')                # compose email
        gmail.sendMessage(sender, message, access_token)
        updateBlastEntry(userId, blastId)                                   # Update database blast

        print('Sent to Gmail API. Cleaning resources...')
        cleanResources()
        return ('', 204)
    except Exception as e:
        print(f'error: {e}')
        return f'Internal server error: {e}', 500

def updateBlastEntry(userId, blastId):
    doc_ref = db.collection(f'users/{userId}/blasts').document(blastId)
    doc_ref.update({
        u"status":"SENT"
    })
    return None

def cleanResources():
    fileList = glob.glob('*.pdf')
    for file in fileList:
        try:
            os.remove(file)
        except Exception as e:
            print(e)
    print('Resources cleaned')

# [START run_pubsub_handler]
@app.route('/', methods=['POST'])
def index():
    envelope = request.get_json()
    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    pubsub_message = envelope['message']

    payload = ''
    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        print('Payload Received')
        payload = base64.b64decode(pubsub_message['data']).decode('utf-8').strip()
        tmp = json.loads(payload)
    sys.stdout.flush()

    return handleMessage(tmp)
# [END run_pubsub_handler]


if __name__ == '__main__':
    print('=============Worker Spawned============')
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080
    app.run(host='127.0.0.1', port=PORT, debug=True)