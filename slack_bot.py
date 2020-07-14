import move_story
from config import s3_key, s3_secret, s3_bucket, notion_token_v2, slack_verification_token
from flask import Flask, request, Response, make_response, render_template, url_for, redirect, send_file
from flask_bootstrap import Bootstrap
from notion.client import NotionClient
import json
import csv
import threading
import requests
import notion_data
import validators
import re
import datetime  
import boto3  
import mimetypes
import urllib 
import os
import io
from zipfile import ZipFile

#This is the home base of the flask app. It handles the different routes and 
#POST/GET requests

app = Flask(__name__)  
bootstrap = Bootstrap(app) 


s3 = boto3.client(
        's3',
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret
)
notion_client = NotionClient(token_v2=notion_token_v2)


@app.route("/")
def home():
    if os.path.isfile('./last_status_calc.csv'):
        with open('last_status_calc.csv', 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                currentDate = row[0]
    else:
        currentDate = "Hasn't been run since last Heroku build"
    return render_template("index.html", today=currentDate)

@app.route("/run-data", methods=['POST'])
def run_data():
    return_home()
    notion_data.main()
    
def return_home():
    return redirect('/')

@app.route("/files", methods=['POST', 'GET'])
def files():
    files = s3.list_objects(Bucket=s3_bucket)['Contents']
    return render_template("files.html", files=files)


@app.route("/download", methods=['POST'])
def download():
    key = request.form['key']
    if key=="all_keys":
        s3_resource = boto3.resource(
            's3',
            aws_access_key_id=s3_key,
            aws_secret_access_key=s3_secret
        )
        my_bucket = s3_resource.Bucket(s3_bucket)
        data = io.BytesIO()
        with ZipFile(data, mode='w') as zipObj:
            for s3_object in my_bucket.objects.all(): 
                 #pylint: disable=unused-argument
                _path, filename = os.path.split(s3_object.key)
                print(s3_object.key)
                my_bucket.download_file(s3_object.key, filename)
                zipObj.write(s3_object.key)
        data.seek(0)
        return send_file( 
            data,
            mimetype='application/zip',
            as_attachment=True,
            attachment_filename='changes_data.zip'
        )
    else:
        file_obj = s3.get_object(Bucket=s3_bucket, Key=key)
        if(key.split('.')[1]=="ipynb"):
            mime_type = 'application/x-ipynb+json'
        else:    
            mime = mimetypes.MimeTypes()
            url = urllib.request.pathname2url(key)
            mime_type_tuple = mime.guess_type(url)
            mime_type = mime_type_tuple[0]
        return Response(
            file_obj['Body'].read(),
            mimetype=mime_type,
            headers={"Content-Disposition": f"attachment;filename={key}"}
        )

statuses = {'0. On deck for Brendan': ['Brendan Lind'], 
            '1. Verify Story Need': [],
            '2. Verify Story Structure': [],
            '3. Design Story': [],
            '4. Review Story Design': [],
            '5. Add Top Stories To Estimate Time of Story Week': [],
            '6. Estimate Time of Story': [],
            '7. Verify & Add Top Bugs': [],
            '8. Start This Week (Next up)': [],
            '9. Finish This Week (In Progress)': [],
            '10. Code Review': ['Mike Menne'],
            '11. QA Review': ['Tyler Kotler', 'Slavik'],
            '12. PO Verify (Test UX & Push)': ['Ben', 'Volodymyr Solin'],
            '13. Complete! (On Live)': []
}

@app.route("/slack/move", methods=['POST'])
def move_handler():
    token = request.form.get('token')
    if token == slack_verification_token:
        text = request.form.get('text')
        res = [i for i in range(len(text)) if text.startswith("to ", i)] 
        last_to = res[-1]
        story = str(text[0:(last_to-1)])
        status = ''
        status_num = text.split(" ")[-1]
        for key in statuses.keys():
            if key.startswith(status_num):
                status = key
                break
        if validators.url(story):
            block = notion_client.get_block(story)
            story = block.title
        user = request.form.get('user_id')
        #Use threading to allow move_story and all functions after to execute, but code can return
        #response to slack within 3 seconds to avoid the timeout error
        t = threading.Thread(target=move_story.move_story, args=[story, status, user])
        t.setDaemon(False)
        t.start()
        data = {
            "text": f"Moving {story}",
            "response_type": 'in_channel'
        }
        return Response(response=json.dumps(data), status=200, mimetype="application/json")


@app.route("/slack/authorize", methods=['GET'])
def authenticate():
    return render_template("authorize.html")


# Start the server on port 3000
if __name__ == "__main__":
  app.run()
