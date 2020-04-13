import json
import argparse
from googleapiclient.discovery import build
import google.oauth2.credentials
from google.oauth2 import id_token
from google.auth.transport import requests
import os

from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.encoders import encode_base64
import base64

client_id = "363232934631-pjbd198u1kic7hlmpooh690kirmqg7iq.apps.googleusercontent.com"
client_secret =  "-pR-QnJtA7ViS9gV9Exbb9dK"

def sendMessage(sender, message, token):
    credentials = google.oauth2.credentials.Credentials(token, client_id=client_id, client_secret=client_secret)
    service = build('gmail','v1', credentials=credentials)
    if service:
        print('Successfully connected to Gmail')
        print(service)
    
    response = (service.users().messages().send(userId=sender, body=message)).execute()
    print(f"Message sent with ID: {response['id']}")

    
def create_message(sender, receiver, subject):
    with open('watermarked_output.pdf', 'rb') as pdf_file:
        pdf = MIMEBase('application','pdf')
        pdf.set_payload(pdf_file.read())
        encode_base64(pdf)
        pdf.add_header('Content-Disposition','attachment',filename='confid.pdf')

    message = MIMEMultipart()
    message['to'] = receiver
    message['from'] = sender
    message['subject'] = 'CONFIDENTIAL EMAIL'
    message.attach(pdf)
    encoded_message = base64.urlsafe_b64encode(message.as_bytes())
    return { 'raw': encoded_message.decode()}

def verifyToken(idToken):
    try:
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(idToken, request)
        print(id_info)
    except Exception as e:
        print(e)
        print(type(e))
    # if id_info['iss'] != 'https://accounts.google.com':
    #     raise ValueError('Wrong issuer')