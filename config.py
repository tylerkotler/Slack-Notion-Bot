from decouple import config

slack_token = config('SLACK_TOKEN')
slack_verification_token = config('SLACK_VERIFICATION_TOKEN')
notion_token_v2 = config('NOTION_TOKEN_V2')
s3_bucket = config('S3_BUCKET')
s3_secret = config('S3_SECRET')
s3_key = config('S3_KEY')
# webhook='url' 