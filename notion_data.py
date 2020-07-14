from notion.client import NotionClient
from notion.collection import NotionDate
import csv 
import os
import json
import datetime
from datetime import timedelta
import string
import time
import gspread
import pandas as pd
from config import notion_token_v2, sheets_client_email, sheets_client_id, sheets_client_x509_cert_url, sheets_private_key, sheets_private_key_id, sheets_project_id, s3_bucket, s3_key, s3_secret
from oauth2client.service_account import ServiceAccountCredentials
import boto3
 

#Reads through all cards in Notion in column 13, pulls data out of their Changes table
#Adds to a dataframe called allChanges
def get_changes_data():
    print("Scraping changes data off Notion stories")
    print()

    # client = NotionClient(token_v2=user_info.token_v2, monitor=True, start_monitoring=True)
    client = NotionClient(token_v2=notion_token_v2)
    cv = client.get_collection_view("https://www.notion.so/humanagency/53a3254e681e4eb6ab53e037d0b2f451?v=68afa83bf93f4c57aa38ffd807eb3bf1")
    addedStories = []
    allChanges = pd.DataFrame(columns=('ID', 'Story', 'Status', 'Change Date', 'Name', 'Title', 'Ship Date'))
    changeView = client.get_collection_view("https://www.notion.so/humanagency/a11ad18166f445e694c64037fbfd7d5b?v=67d6efa07c224fdc89603e1d9eb6ad5d")
    
    for row in cv.collection.get_rows():
        if row.status == '13. Complete! (On Live)':
            print(f"Scraping changes data from {row.story}") 
            if row.story == 'Duplicate an Experience':
                break
            # for child in block.children:
            #     if hasattr(child, 'title') and (child.title == 'Changes') and (row.story not in addedStories):
            #         changeTable = child
            #         ids = client.search_pages_with_parent(changeTable.collection.id)
            for change_row in changeView.collection.get_rows():
                block = client.get_block(change_row.id)
                for item in block.story:
                    if item.title == row.story:  
                        title = block.title
                        if block.time_correction:
                            time = block.time_correction.start
                        else:
                            time = block.time
                            time = time - timedelta(hours=5)
                        status = block.status
                        full_name = block.change_made_by
                        addedStories.append(row.story)
                        allChanges = allChanges.append({'ID': row.id, 'Story': row.story, 'Status': status, 
                                                        'Change Date': time, 'Name': full_name, 'Title': title, 
                                                        'Ship Date': row.ship_date.start}, ignore_index=True)

    return order_by_time(allChanges)
    
#Runs through dataframe of all the changes, groups by story, and orders by time within each story
#Converts the dataframe into changes_metrics.csv
def order_by_time(allChanges):
    print()
    print("Ordering by time")
    print()
    
    new_df = pd.DataFrame()
    firstRow = True
    newStory = True
    story = ''
    for _index, change in allChanges.iterrows():
        if firstRow: 
            firstRow = False
            story = change['Story']
        if change['Story']!=story: 
            newStory = True
            story = change['Story']
        if newStory:
            story_changes = allChanges.loc[allChanges['Story']==story]
            story_changes = story_changes.sort_values(by='Change Date', ascending=False)
            newStory = False
            new_df = pd.concat([story_changes, new_df])
    
    new_df.to_csv ('./changes_metrics.csv', sep="|", index = False, header=True)
    return new_df



#List of statuses - global var used for populating status_times & status_total_times csvs
statuses = ['0. On deck for Brendan', 
            '1. Verify Story Need',
            '2. Verify Story Structure',
            '3. Design Story',
            '4. Review Story Design',
            '5. Add Top Stories To Estimate Time of Story Week',
            '6. Estimate Time of Story',
            '7. Verify & Add Top Bugs',
            '8. Start This Week (Next up)',
            '9. Finish This Week (In Progress)',
            '10. Code Review',
            '11. QA Review',
            '12. PO Verify (Test UX & Push)',
            '13. Complete! (On Live)'
        ]


#Takes data pulled from Changes tables and calculates times spent in each status for each story
#Writes to new csv file called status_times.csv
def get_status_times(new_df):
    

    print("Calculating status times")

    status_file = open('status_times.csv', 'w')
    csv_writer = csv.writer(status_file, delimiter="|")

    reverse_array = []
    times = [0]*14

    currentStory = ''
    currentShipDate = None
    previousDate = None
    currentDate = None
    currentStatusNum = 0
    rowNum = 0
    firstRow = True 

    for _index, change in new_df.iterrows():
        
        reverse_array.insert(0, change)

        if firstRow:
            currentStory = change['Story']
            currentShipDate = change['Ship Date']
            firstRow = False

        if change['Story']!=currentStory and change['Story']:
            indexCount = 0
            for time in times:
                csv_writer.writerow([currentStory,statuses[indexCount],time,currentShipDate])
                indexCount=indexCount+1
            times = [0]*14
            currentStory = change['Story']
            currentShipDate = change['Ship Date']
            rowNum = 0
        
        change_date = str(change['Change Date'])
        if "." in change_date:
            change_date = change_date.split(".")[0]
        currentDate = datetime.datetime.strptime(change_date, '%Y-%m-%d %H:%M:%S')
        currentStatusNum = int(change['Status'].split(".")[0])
        
        if rowNum!=0:
            timeElapsed = (previousDate - currentDate).total_seconds()/3600
            times[currentStatusNum]+=timeElapsed
        
        previousDate = currentDate
        rowNum = rowNum+1

    indexCount = 0
    for time in times:
        csv_writer.writerow([change['Story'],statuses[indexCount],time,change['Ship Date']])
        indexCount=indexCount+1

    status_file.close()

    return reverse_array


#Takes data pulled from Changes tables and calculates times spent in each status for each story
#Abides by condition that a story in its furthest column is still in that column even if it moves
#back to an earlier column
#Writes to new csv file called status_times_furthest.csv
def get_status_times_furthest(reverse_array):
    print()
    print("Calculating status times w/ furthest point")
    print()

    status_file = open('status_times_furthest.csv', 'w')
    csv_writer = csv.writer(status_file, delimiter="|")

    times = [0]*14

    currentStory = ''
    currentShipDate = None
    previousDate = None
    currentDate = None
    previousStatusNum = 0
    rowNum = 0
    firstRow = True

    for row in reverse_array:
        if firstRow:
            currentStory = row[1]
            currentShipDate = row[6]
            previousStatusNum = int(row[2].split(".")[0])
            
            firstRow = False

        if row[1]!=currentStory and row[1]:
            indexCount = 0
            for time in times:
                csv_writer.writerow([currentStory,statuses[indexCount],time,currentShipDate])
                indexCount=indexCount+1
            times = [0]*14
            currentStory = row[1]
            currentShipDate = row[6]
            previousStatusNum = int(row[2].split(".")[0])
            
            rowNum = 0
        
        change_date = str(row[3])
        if "." in change_date:
            change_date = change_date.split(".")[0]
        currentDate = datetime.datetime.strptime(change_date, '%Y-%m-%d %H:%M:%S')
        currentStatusNum = int(row[2].split(".")[0])
        
        if rowNum!=0:
            timeElapsed = (currentDate - previousDate).total_seconds()/3600
            times[previousStatusNum]+=timeElapsed
            if currentStatusNum > previousStatusNum:
                previousStatusNum = currentStatusNum
        
        previousDate = currentDate
        rowNum = rowNum+1

    indexCount = 0
    for time in times:
        csv_writer.writerow([row[1],statuses[indexCount],time,row[6]])
        indexCount=indexCount+1

    status_file.close()


#Takes data from status times csv and aggregates by status to get total time across all
#stories spent in each status
#Writes to new csv file called status_total_times.csv
def get_status_totals():
    print("Calculating status totals")
    print()

    statusTotal_file = open('status_total_times.csv', 'w')
    csv_writer = csv.writer(statusTotal_file, delimiter="|")

    times = [0]*14

    with open('status_times.csv', 'r', newline='') as file:
        statusReader = csv.reader(file, delimiter='|')

        for row in statusReader:
            statusNum = int(row[1].split(".")[0])
            times[statusNum] = times[statusNum]+float(row[2])
        timeCount = 0

        for time in times:
            csv_writer.writerow([statuses[timeCount], time])
            timeCount+=1

    statusTotal_file.close()


#Adds all data from status_times to HA Google Spreadsheets - Notion_Changes_Data worksheet
def update_spreadsheet():
    print("Adding all data to Google Sheets")
    
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    sheets_auth_data = {
        "type": "service_account",
        "project_id": sheets_project_id,
        "private_key_id": sheets_private_key_id,
        "private_key": sheets_private_key.replace("\\n", "\n"),
        "client_email": sheets_client_email,
        "client_id": sheets_client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": sheets_client_x509_cert_url
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sheets_auth_data, scope)
    client = gspread.authorize(creds)
    sheet = client.open('Human Agency Experience Dashboard').worksheet("Notion_Changes_Data")
    sheet_furthest = client.open('Human Agency Experience Dashboard').worksheet("Notion_Changes_Data_Furthest")
    
    update_spreadsheet_helper(sheet, 'status_times.csv')
    
    print("Waiting for Google Sheets API's limit on requests per 100 seconds :(")
    time.sleep(100)
    print("Done sleeping")
    update_spreadsheet_helper(sheet_furthest, 'status_times_furthest.csv')

def update_spreadsheet_helper(sheet, csv_file):

    max_rows = len(sheet.get_all_values())
    sheet.delete_rows(6,max_rows)
    
    with open(csv_file, 'r', newline='') as file:
        statusReader = csv.reader(file, delimiter='|')

        firstRow = True
        currentStory = ''
        currentShipDate = ''
        newSheetRow = []

        for row in statusReader:
            
            if firstRow:
                currentStory = row[0]
                currentShipDate = row[3]
                newSheetRow.append(currentStory)
                newSheetRow.append(currentShipDate)
                firstRow = False

            if(row[0]!=currentStory):
                sheet.append_row(newSheetRow)

                currentStory = row[0]
                currentShipDate = row[3]
                newSheetRow = []
                newSheetRow.append(currentStory)
                newSheetRow.append(currentShipDate)
            
            newSheetRow.append(float(row[2]))

        sheet.append_row(newSheetRow)

    #Calculating/Adding totals and averages to spreadsheet
    last_row = len(sheet.get_all_values()) 
    alphabet = list(string.ascii_uppercase)

    for i in range(2, 16):
        letter = alphabet[i]
        formula = f'=SUM({letter}6:{letter}{last_row})'
        sheet.update_acell(f'{letter}2', formula)
        avg_formula = f'=AVERAGE({letter}6:{letter}{last_row})'
        sheet.update_acell(f'{letter}3', avg_formula)
    
    sheet.format(f'{alphabet[2]}2:{alphabet[15]}3', {'numberFormat': {'type': 'NUMBER', 'pattern': '#0.0#'}})
    
    status_condensed = open(f'{csv_file.split(".")[0]}_condensed.csv', 'w')
    csv_writer = csv.writer(status_condensed, delimiter="|")
    csv_writer.writerows(sheet.get(f"A5:P{last_row}"))
    status_condensed.close()


file_names = [
    "changes_metrics.csv", 
    "status_times_condensed.csv",
    "status_times_furthest_condensed.csv",
    "status_times_furthest.csv",
    "status_times.csv",
    "status_total_times.csv",
]

def upload_files_to_s3():
    print()
    print("Uploading files to s3")
    s3 = boto3.client(
        's3',
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret
    )
    for file_name in file_names:
        s3.delete_object(Bucket=s3_bucket, Key=file_name)
        with open(file_name, "rb") as f:
            s3.upload_fileobj(f, s3_bucket, file_name)
    

def main():
    new_df = get_changes_data()
    reverse_array = get_status_times(new_df)
    get_status_times_furthest(reverse_array)
    get_status_totals()
    update_spreadsheet()
    upload_files_to_s3()


if __name__ == "__main__":
    main()
    
    