import boto3
import re
import email

origin_address = 'host@domain.com'
forward_address = 'host@domain.com'
ses_region = 'region_name'
s3_bucket = 'bucket_name'

def convert_message(message):
    # replace 'From:' and 'Return-Path:' header
    from_header = message['From'].replace('"', '')
    del message['From']
    del message['Return-Path']
    message['From'] = '"{}" <{}>'.format(from_header, origin_address)
    message['Return-Path'] = '"{}" <{}>'.format(from_header, origin_address)
    
    # remove 'DKIM-Signature:' header
    del message['DKIM-Signature']
    
    # remove 'Sender:' header
    del message['Sender']
 
    return message

def send_mail(message):
    ses = boto3.client('ses', region_name=ses_region)
    
    ses.send_raw_email(
        Source = forward_address,
        Destinations = [forward_address],
        RawMessage = {'Data': message.as_bytes()}
    )

def lambda_handler(event, context):
    try:
        s3_key = event['Records'][0]['s3']['object']['key']
        
        s3 = boto3.client('s3')
        response = s3.get_object(
            Bucket = s3_bucket,
            Key = s3_key
        )
        message = response['Body'].read()
        message = email.message_from_bytes(message)
        message = convert_message(message)
        send_mail(message)

    except Exception as e:
        return e
