from commands import move, assign
from data import notion_data, display_data
import command_hub
from config import s3_key, s3_secret, s3_bucket, notion_token_v2, slack_verification_token, slack_token
from flask import Flask, request, Response, make_response, render_template, url_for, redirect, send_file
from flask_bootstrap import Bootstrap
from notion.client import NotionClient
from slack import WebClient
import json
import csv
import threading
import requests
import validators
import re
import datetime  
import boto3  
import mimetypes
import urllib 
import os
import io
from zipfile import ZipFile
from jinja2 import Template

    
#This is the home base of the flask app. It handles the different routes and 
#POST/GET requests

app = Flask(__name__)  
bootstrap = Bootstrap(app) 

#Authentication for Amazon s3, Notion, and Slack APIs
s3 = boto3.client(
        's3',
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret
)
notion_client = NotionClient(token_v2=notion_token_v2)
slack_client = WebClient(slack_token)

#Dict of statuses with people to automatically tag when a story moves into a status
#Use their real name on Slack! (Found by clicking on their profile and using the bolded name under the photo)
#Good ex: Volodymyr Solin instead of vladimirsolin
statuses = {'0. On deck for Brendan': ['Brendan Lind'], 
            '1. Verify Story Need': ['Brendan Lind'],
            '2. Verify Story Structure': ['Mike Menne'],
            '3. Design Story': ['Ben'],
            '4. Review Story Design': ['Pete', 'Hannah Allee', 'Brendan Lind', 'Mike Menne'],
            '5. Add Top Stories To Estimate Time of Story Week': ['Brendan Lind', 'Mike Menne', 'Ben'],
            '6. Estimate Time of Story': [],
            '7. Verify & Add Top Bugs': [],
            '8. Start This Week (Next up)': [],
            '9. Finish This Week (In Progress)': [],
            '10. Code Review': ['Mike Menne'],
            '11. QA Review': ['Volodymyr Solin', 'Slavik'],
            '12. PO Verify (Test UX & Push)': ['Ben', 'Volodymyr Solin'], 
            '13. Complete! (On Live)': []
}

#Routes to home page of the app (https://notion-slackbot.herokuapp.com/)
@app.route("/")
def home():
    #Get the time displayed for the last notion_data run
    obj = s3.get_object(Bucket=s3_bucket, Key='last_status_calc.csv')
    currentDate = obj['Body'].read().decode('utf-8')
    return render_template("index.html", today=currentDate, statuses=statuses.keys())

@app.route("/run-data", methods=['POST'])
def run_data():
    notion_data.main()
    return redirect('/')

#Page with scatter plots for each status 
@app.route("/display_data", methods=['POST', 'GET'])
def display():
    #Check if the request has furthest points selected in order to display the correct data
    furthest = "False"
    try:
        if request.form['furthest'] == 'True':
            furthest = 'True'
    except:
        pass
    try:
        if request.form['hidden_furthest'] == 'True':
            furthest = 'True'
    except:
        pass
    status = request.form['statuses']

    #Builds the bokeh plot, sends back the js and html to embed in the page
    script, div = display_data.scatter(status, furthest)
    
    return render_template("display_data.html", script=script, div=div, statuses=statuses, furthest=furthest, selected_status=status)

#Page with embedded Google Sheets data
@app.route("/sheets_data", methods=['POST', 'GET'])
def sheets():
    return render_template('sheets_data.html')

#Table with all files from s3 that can be downloaded
@app.route("/files", methods=['POST', 'GET'])
def files():
    files = s3.list_objects(Bucket=s3_bucket)['Contents']
    return render_template("files.html", files=files)

#Download s3 files
@app.route("/download", methods=['POST'])
def download():
    key = request.form['key']
    #Download all files into a zip
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
    #Download the individually selected file
    else:
        file_obj = s3.get_object(Bucket=s3_bucket, Key=key)
        #Make mime_type ipynb for the jupyter notebook files (the guess_type function isn't great)
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

#Handles the move command
@app.route("/slack/move", methods=['POST'])
def move_handler():
    token = request.form.get('token')
    if token == slack_verification_token:
        #Get text of command
        text = request.form.get('text')
        arr = text.split("\xa0")
        if len(arr) > 1:
            text = " ".join(arr)

        #get help
        if text.strip(" ") == 'help' or text.strip(" ") == 'subcommands':
            channel = request.form.get('channel_id')
            send_data = {
                'command': 'move',
                'help': text.strip(" "),
                'channel': channel
            }
            t = threading.Thread(target=command_hub.help, args=[send_data])
            t.setDaemon(False)
            t.start()
            
            data = {
                "text": 'Getting information...',
                "response_type": 'in_channel'
            }
            return Response(response=json.dumps(data), status=200, mimetype="application/json")
            
        #split subcommands from command
        text = text.replace(" --", "--")
        commands = text.split("--")
        main_command = commands[0]
        subcommands = commands[1:]

        #Get story
        res = [i for i in range(len(main_command)) if main_command.startswith("to ", i)] 
        last_to = res[-1]
        story = str(main_command[0:(last_to-1)])
        if validators.url(story):
            block = notion_client.get_block(story)
            story = block.title

        #Get status
        status = ''
        status_num = main_command.split(" ")[-1]
        for key in statuses.keys():
            if key.startswith(status_num):
                status = key
                break
        
        #Get user who made move command
        user = request.form.get('user_id')

        command = "move"
        command_info = {
            'story': story,
            'status': status,
            'user': user
        }

        #Use threading to allow move and all functions after to execute, but code can return
        #response to slack within 3 seconds to avoid the Slack timeout error
        t = threading.Thread(target=command_hub.main, args=[command, command_info, subcommands])
        t.setDaemon(False)
        t.start()

        #Reply in channel
        data = {
            "text": f"Moving {story}",
            "response_type": 'in_channel'
        }
        return Response(response=json.dumps(data), status=200, mimetype="application/json")

#Handles the assign command
@app.route("/slack/assign", methods=['POST'])
def assign_handler():
    token = request.form.get('token')
    if token == slack_verification_token:
        #Get text of command
        text = str(request.form.get('text'))
        arr = text.split("\xa0")
        if len(arr) > 1:
            text = " ".join(arr)

        #get help
        if text.strip(" ") == 'help' or text.strip(" ") == 'subcommands':
            channel = request.form.get('channel_id')
            send_data = {
                'command': 'assign',
                'help': text.strip(" "),
                'channel': channel
            }
            t = threading.Thread(target=command_hub.help, args=[send_data])
            t.setDaemon(False)
            t.start()
            
            data = {
                "text": 'Getting information...',
                "response_type": 'in_channel'
            }
            return Response(response=json.dumps(data), status=200, mimetype="application/json")

        #split subcommands from command
        text = text.replace(" --", "--")
        commands = text.split("--")
        main_command = commands[0]
        subcommands = commands[1:]

        #Get story
        res = [i for i in range(len(main_command)) if main_command.startswith("to ", i)] 
        last_to = res[-1]
        story = str(main_command[0:(last_to-1)])
        if validators.url(story):
            block = notion_client.get_block(story)
            story = block.title

        #Get users who are being assigned to story 
        users = main_command[main_command.index("@"):].split(" ")
        users = [s.strip("@") for s in users]
        slack_users = slack_client.users_list()
        slack_names = []
        for slack_user in slack_users["members"]:
            name = slack_user.get('name')
            if name in users:
                slack_names.append(slack_user.get('real_name'))
        

        #Get user who made assign command
        user = request.form.get('user_id')

        command = "assign"
        command_info = {
            'story': story,
            'slack_names': slack_names,
            'user': user
        
        }
        t = threading.Thread(target=command_hub.main, args=[command, command_info, subcommands])
        t.setDaemon(False)
        t.start()
        
        #return response in channel
        slack_names_string = ", ".join(slack_names)
        data = {
                "text": f"Assigning {slack_names_string} to {story}",
                "response_type": 'in_channel'
        }
        return Response(response=json.dumps(data), status=200, mimetype="application/json")


#Authorize (not needed for this app, only if it were to be deployed to another Slack team)
@app.route("/slack/authorize", methods=['GET'])
def authenticate():
    return render_template("authorize.html")


# Start the server
if __name__ == "__main__":
  app.run(port=3000)
