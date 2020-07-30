from decouple import config

#All environment variables are stored in Heroku in config vars
slack_token = config('SLACK_TOKEN')
slack_verification_token = config('SLACK_VERIFICATION_TOKEN')
notion_token_v2 = config('NOTION_TOKEN_V2')
s3_bucket = config('S3_BUCKET')
s3_secret = config('S3_SECRET')
s3_key = config('S3_KEY')
# webhook='url' 
sheets_private_key_id = config('SHEETS_PRIVATE_KEY_ID')
sheets_private_key = config('SHEETS_PRIVATE_KEY')
sheets_client_id = config('SHEETS_CLIENT_ID')
sheets_project_id = config('SHEETS_PROJECT_ID')
sheets_client_email = config('SHEETS_CLIENT_EMAIL')
sheets_client_x509_cert_url = config('SHEETS_CLIENT_X509_CERT_URL')
heroku_api_key = config('HEROKU_API_KEY')