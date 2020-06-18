from notion.client import NotionClient
from notion.collection import NotionDate
import csv 
import os
import datetime
from datetime import timedelta
import gspread
import pandas as pd
import user_info
from oauth2client.service_account import ServiceAccountCredentials

#Reads through all cards in Notion in column 13, pulls data out of their Changes table
#Adds to a dataframe called allChanges

def get_changes_data():
    print("Scraping changes data off Notion stories")
    print()

    client = NotionClient(token_v2=user_info.token_v2, monitor=True, start_monitoring=True)
    cv = client.get_collection_view("https://www.notion.so/humanagency/53a3254e681e4eb6ab53e037d0b2f451?v=68afa83bf93f4c57aa38ffd807eb3bf1")

    addedStories = []
    allChanges = pd.DataFrame(columns=('ID', 'Story', 'Status', 'Change Date', 'Name', 'Title', 'Ship Date'))

    # with open('changes_metrics_unsorted.csv', 'w', newline='') as file:
    #     writer = csv.writer(file, delimiter='|')
    #     writer.writerow(['ID', 'Story', 'Status', 'Change Date', 'Name', 'Title', 'Ship Date'])
    for row in cv.collection.get_rows():
        if row.status == '13. Complete! (On Live)':
            if row.story == 'Duplicate an Experience':
                break
            block = client.get_block(row.id)
            for child in block.children:
                if hasattr(child, 'title') and (child.title == 'Changes') and (row.story not in addedStories):
                    changeTable = child
                    ids = client.search_pages_with_parent(changeTable.collection.id)
                    print(f"Scraping changes data from {row.story}")
                    for id in ids:
                        for item in client.get_block(id).story:
                            if item.title == row.story:
                                title = client.get_block(id).title
                                if client.get_block(id).time_correction:
                                    time = client.get_block(id).time_correction.start
                                else:
                                    time = client.get_block(id).time
                                    time = time - timedelta(hours=5)
                                status = client.get_block(id).status
                                full_name = ""
                                for creator in client.get_block(id).change_made_by:
                                    full_name = creator.full_name
                                # writer.writerow([row.id, row.story, status, time, full_name, title, row.ship_date.start])
                                addedStories.append(row.story)
                                allChanges = allChanges.append({'ID': row.id, 'Story': row.story, 'Status': status, 
                                                                'Change Date': time, 'Name': full_name, 'Title': title, 
                                                                'Ship Date': row.ship_date.start}, ignore_index=True)
    
    return order_by_time(allChanges)
    

def order_by_time(allChanges):
    print()
    print("Ordering by time")
    print()
    # all_changes = pd.read_csv("./changes_metrics_unsorted.csv", sep="|")
    # df = pd.DataFrame(allChanges)
    
    new_df = pd.DataFrame()
    firstRow = True
    newStory = True
    story = ''
    for index, change in allChanges.iterrows():
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
    print()

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

    for index, change in new_df.iterrows():
        
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
        
        currentDate = datetime.datetime.strptime(str(change['Change Date']), '%Y-%m-%d %H:%M:%S')
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
        
        currentDate = datetime.datetime.strptime(str(row[3]), '%Y-%m-%d %H:%M:%S')
        currentStatusNum = int(row[2].split(".")[0])
        
        #I want to run through the changes in a story and hold each change's current status number
        #Then for each change I will check if the status number is lower or higher than the previous 
        #If it's lower, add to the furthest (current) time slot in times[] and don't change the
        #current status number
        #If it's higher, add to the new time slot and change the current status number
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
    creds = ServiceAccountCredentials.from_json_keyfile_name('Notion Changes Data.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('Human Agency Experience Dashboard').worksheet("Notion_Changes_Data")
    
    max_rows = len(sheet.get_all_values())
    sheet.delete_rows(2,max_rows)

   
    with open('status_times.csv', 'r', newline='') as file:
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
            
            newSheetRow.append(row[2])

        sheet.append_row(newSheetRow)
            

if __name__ == '__main__':
    new_df = get_changes_data()
    reverse_array = get_status_times(new_df)
    get_status_times_furthest(reverse_array)
    get_status_totals()
    update_spreadsheet()
    
    