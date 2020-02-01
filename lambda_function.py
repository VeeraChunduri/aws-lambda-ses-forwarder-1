import boto3
import re

origin_address = b'host@domain.com'
forward_address = b'host@domain.com'
ses_region = 'region_Name'
s3_bucket = 'bucket_name'

def parse_mail(message):
    from_name = 'No Name'
    
    pattern = re.compile(b'^From:\s*(.+?)[\r\n]', re.MULTILINE)
    search = re.search(pattern, message)
    if search:
        from_name = search.group(1).replace(b'"', b'')
    message = message.replace(origin_address, forward_address)
    
    pattern = re.compile(b'^DKIM-Signature: (.*[\r\n]+)(\t.*[\r\n]+)*', re.MULTILINE)
    iter = re.finditer(pattern, message)
    for find in iter:
        if b'amazonses.com' not in find.group():
            message = message.replace(find.group(), b'')

    message = re.sub(b'^From:\s*.+?[\r\n]', b'From: "%s" <%s>' % (from_name, origin_address), message, flags=re.MULTILINE)
    message = re.sub(b'^Return-Path:\s*.+?[\r\n]', b'Return-Path: "%s" <%s>' % (from_name, origin_address), message, flags=re.MULTILINE)
    return message

def send_mail(message):
    ses = boto3.client('ses', region_name=ses_region)
    
    ses.send_raw_email(
        Source = forward_address.decode(),
        Destinations = [forward_address.decode()],
        RawMessage = {'Data': message}
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
        message = parse_mail(message)
        send_mail(message)

    except Exception as e:
        return e
