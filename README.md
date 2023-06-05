# Instagram Replica

This is a cloud based web development project based on Instagram's functionality.

**Languages Used:**
* FrontEnd: HTML, CSS, JavaScript
* BackEnd: Python's Flask, JavaScript

**Integrations:**
* Firebase Authentication
* Google Cloud Platform
* Google Storgae Bucket
* Firebase Datastore

This project is developed as a data management application. All the data is stored on cloud for each user including images and activity.

## How to run?

* Clone this repo
* Open terminal and navigate to this repo
* Type & Run: pip install -r requirements.txt
* Type and Run: set GOOGLE_APPLICATION_CREDENTIALS="your datastore credential file - read below how to get this"
* Type and Run: python main.py
* Open Browser and go to localhost:8080 or the port your terminal shows.

Before running this, you need to integrate datastore and Google Cloud Project with this app. Read below for guidelines on how to do that.

### Create Google Cloud Project
Go to https://console.cloud.google.com/

Add a new project and give it a name.

Go to the hamburger menu on the top left, under “Serverless” click on “App Engine”.
Click on “Create Application”. Select region, Select language as “python” and the 'standard environment'.
Your app engine project is now setup.

### Adding Datastore
Go to https://console.cloud.google.com

Go to the hamburger menu on the top left. Under “Databases” click on 
“Datastore”. One of three things will happen here:
* You'll see a message “your database is ready to go. Just add data” and in the top 
right it should say “Cloud Firestore in Datastore mode” this is what we want.
* If it states “your database is ready to go. Just add data” and in the top right it states “Cloud 
Firestore in Native mode” click the button to “Switch to Datastore mode”
* If instead you get a page asking you to create a datastore in either “Native mode” or 
“Datastore mode” click “Datastore mode” and you should get to the page described in the 
first bullet point.

On the hamburger menu in the submenu for “IAM & Admin” click “Service accounts”. 

Click on that account that say “App Engine default service account” and then click on “keys” along the top.

Under “add key” click “Create new key”. It with then give you a dialog and you want the “JSON” key type. Select that and press “create”.

Download the JSON file and save it in this directory.
