from flask import Flask, Response, request, jsonify, render_template, make_response, flash
from flask_pymongo import pymongo
from pymongo import MongoClient
from database import DatabaseConnection
from Services.UserServices import UserServices
from bson.objectid import ObjectId

import json
import datetime
import uuid
import ast

app = Flask(__name__)
app.secret_key = '123'
db = DatabaseConnection()
UserServices = UserServices()

#Sends people to the frontpage to create account/login, unless they are already logged in from before, sending them to their userpage
@app.route("/", methods=["GET"])
def hello():
    if (request.cookies.get('sid') != None):
        user = UserServices.authorize(request.cookies.get('sid'))
        firstName = UserServices.getFirstName(user)
        greeting = ""
        hourOfDay = datetime.datetime.now().time().hour

        if hourOfDay < 12:
            greeting = "Good morning,"
        elif hourOfDay < 18:
            greeting = "Good afternoon,"
        else:
            greeting = "Good evening,"
    
        response = greeting + " " + firstName + "!"
        return render_template("userpage.html", result = response)

    return render_template("index.html")


#This sends people to the createAccount page
@app.route("/createAccount", methods=["GET"])
def createAccount():
    return render_template("createAccount.html")

#This takes the create account form entries and adds the user to the mongoDB users collection
#If not all boxes are filled out, it sends user back to fill in all boxes (didn't figure out how to maintain box entries)
@app.route("/addNewUser", methods=["POST"])
def addNewUser():

    username = request.form["username"]
    password = request.form["password"]
    firstName = request.form["firstName"]
    lastName = request.form["lastName"]
    email = request.form["email"]

    userDoc = db.findMany("users", {"username": username} )

    if (username.strip() == "" or password.strip() == "" or firstName.strip() == "" or lastName.strip() == "" or email.strip() == ""):
        flash('Please fill in all boxes')
        return render_template("createAccount.html")

    if len(userDoc) != 0:
        flash('Username already taken')
        return render_template("createAccount.html")
    else:
        flash('You have successfully made an account')
       
        document = {
            "username": (request.form["username"]),
            "password": (request.form["password"]),
            "firstName": (request.form["firstName"]),
            "lastName": (request.form["lastName"]),
            "email": (request.form["email"])
        }
            
        db.insert("users", document)

        return render_template("index.html")

#This takes people to the login page
@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

#This checks the validity of people's login information. If not valid, sends them back to login page
#If valid, it creates a cookie for the user and sends them to the userpage
@app.route("/loginValidity", methods=["POST"])
def checkLoginValidity():
    username = request.form["username"]
    password = request.form["password"]

    print(username)
    print(password)

    if UserServices.authenticate(username, password):
        response = make_response(render_template("welcome.html"))
        print(response)
        
        if (db.findOne("sessions", {"username": username}) == None):
            sid = str(uuid.uuid4())
            session = {
            "sid": sid,
            "username": username
            }
            
            db.insert("sessions", session)
            response.set_cookie("sid", sid)
            return response

        else:
            user = UserServices.authorize(request.cookies.get('sid'))
            firstName = UserServices.getFirstName(user)
            
            greeting = ""
            hourOfDay = datetime.datetime.now().time().hour

            if hourOfDay < 12:
                greeting = "Good morning,"
            elif hourOfDay < 18:
                greeting = "Good afternoon,"
            else:
                greeting = "Good evening,"
    
            response = greeting + " " + firstName + "!"
            return render_template("userpage.html", {{response}})
            
    else:
        flash("Incorrect login credentials")
        return render_template("login.html")    
    return render_template("login.html")


#The user page greets the user with a time-sensitive greeting and then leads them to 4 main functions
#1. Add a new property for listing
#2. View the properties they've listed out
#3. View the properties available to rent
#4. View the properties they are currently renting
@app.route("/userpage", methods=["POST"])
def greeting():
    user = UserServices.authorize(request.cookies.get('sid'))
    if user:
        firstName = UserServices.getFirstName(user)
    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")

    print(firstName)
    greeting = ""
    hourOfDay = datetime.datetime.now().time().hour

    if hourOfDay < 12:
       greeting = "Good morning,"
    elif hourOfDay < 18:
       greeting = "Good afternoon,"
    else:
       greeting = "Good evening,"
    
    response = greeting + " " + firstName + "!"
    print(response)

    return render_template("userpage.html", result = response)

#Next 2 functions are to create an add new property page
#First sends them to the html page
#Second checks to see if all boxes are filled (and not just blanks) and then fills database with a new property
#If house names are same, it asks user to create a unique name 
@app.route("/propertyAddPage", methods=["POST"])
def propertyAddPage():
    return render_template("propertyAddPage.html")

@app.route("/addNewProperty", methods=["POST"])
def addNewProperty():
    
    user = UserServices.authorize(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")

    print(firstName)
    ownerData = db.findOne("users", {"username": firstName})
    
    ownerUsername = user
    owner = firstName
    name = request.form["name"]
    propertyType = request.form["type"]
    price = request.form["price"]
  
    if (name.strip() == "" or propertyType.strip() == "" or price.strip() == ""):
        flash("Please fill in all boxes")
        return render_template("propertyAddPage.html")
    
    ownerNameComparison = db.findMany("properties", {"name": name})
    
    for houses in ownerNameComparison:
        if (houses["ownerUsername"] == ownerUsername):
            flash("Please use a unique name for your new property. Property name can't be same as one you've currently listed")
            return render_template("propertyAddPage.html")

    document = {
        "ownerUsername": user,
        "owner": firstName,
        "name": request.form["name"],
        "propertyType": request.form["type"],
        "price": request.form["price"],
        "sold": "False",
        "buyer": ""
    }
        
    db.insert("properties", document)
    
    flash("Property successfully added")
    return render_template("propertyAddPage.html")

#This function is to view the properties user is putting out on the market

@app.route("/propertyYouRenting", methods=["GET"])
def viewRentingProperties():
    user = UserServices.authorize(request.cookies.get('sid'))

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")

    properties = db.findAll("properties")

    rentingProperties = db.findMany("properties", {"ownerUsername": user})
    
    print(user)
    print(rentingProperties)

    return render_template("rentingProperties.html", allProperties = properties, username = user)

#This function allows people to delete entries from the market, but only if it's not currently being rented
@app.route("/cancelEntry", methods=["POST"])
def removeListing():

    user = UserServices.authorize(request.cookies.get('sid'))
    print(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")
    

    gettingProperty = request.form["property"]
    gettingProperty = ast.literal_eval(gettingProperty)

    print(gettingProperty)
    print(type(gettingProperty))
    
    id = gettingProperty.get("_id")

    client = MongoClient('localhost', 27017)
    client["airbnblite"]["properties"].delete_one({"_id" : ObjectId(id)})    

    flash("Successfully removed listing")

    properties = db.findAll("properties")
    return render_template("rentingProperties.html", allProperties = properties, username = user)


#This function allows users to see the properties that are available for buying
@app.route("/propertiesForSale", methods=["GET"])
def getProperties():
    user = UserServices.authorize(request.cookies.get('sid'))
    print(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")
    
    properties = db.findAll("properties")
    return render_template("propertiesForSale.html", allProperties = properties, username = user)

#This function allows users to actually rent out the properties that they want to get
#so they aren't stuck window-shopping for the ideal upper-middle class household they always
#dreamed of
@app.route("/makeSold", methods=["POST"])
def makeSold():
    user = UserServices.authorize(request.cookies.get('sid'))
    print(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")
    

    gettingProperty = request.form["property"]
    gettingProperty = ast.literal_eval(gettingProperty)

    print(gettingProperty)
    print(type(gettingProperty))
    
    sold = gettingProperty.get("sold")
    
    db.update("properties", {"sold": sold}, {"$set": {"sold": "True"}})
    db.update("properties", {"buyer": ""}, {"$set": {"buyer": user}})
    
    flash("Rented successfully")

    properties = db.findAll("properties")
    return render_template("propertiesForSale.html", allProperties = properties, username = user)


#This function shows the properties you are currently renting from others

@app.route("/propertiesYouRent", methods=["GET"])
def getRentedProperties():
    user = UserServices.authorize(request.cookies.get('sid'))
    print(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")
    
    properties = db.findAll("properties")

    return render_template("propertiesYouRent.html", allProperties = properties, username = user)

#This function allows you to cancel a rental so you aren't stuck renting a place forever
@app.route("/cancelRental", methods=["POST"])
def cancelRental():
    user = UserServices.authorize(request.cookies.get('sid'))
    print(request.cookies.get('sid'))    

    if user:
        firstName = UserServices.getFirstName(user)

    else:
        flash("You are not logged in; this may have been an automatic timeout")
        return render_template("login.html")
    

    gettingProperty = request.form["property"]
    gettingProperty = ast.literal_eval(gettingProperty)

    print(gettingProperty)
    print(type(gettingProperty))
    
    sold = gettingProperty.get("sold")
    
    db.update("properties", {"sold": sold}, {"$set": {"sold": "False"}})
    db.update("properties", {"buyer": user}, {"$set": {"buyer": ""}})
    
    flash("Rental cancelled successfully")

    properties = db.findAll("properties")
    return render_template("propertiesYouRent.html", allProperties = properties, username = user)

#This function logs the user out, deleting their sessionID from mongoDB as well as from the cookies
@app.route("/logout", methods=["GET"])
def logout():
    response = make_response(render_template("index.html"))
    print(response)

    sid = request.cookies.get('sid')

    client = MongoClient('localhost', 27017)
    client["airbnblite"]["sessions"].delete_one({"sid" : sid})
    response.set_cookie('sid', '', expires=0)

    response.delete_cookie("sid", sid)

    return response

#yes
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)