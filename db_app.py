#CMPT354 Assignment 7 - due Monday, December 4 2023
#Submitted By: Asmita Srivastava (Student No. 301436340)
import pypyodbc as odbc
import datetime
import uuid

#creates the application menu for user display
def application_menu():
    print("Welcome to Yelp database application! Choose your option from the following choices (choose a number from 0 to 5): ")
    print("[1] Login")
    print("[2] Search Business")
    print("[3] Search Users")
    print("[4] Make Friend (requires login first)")
    print("[5] Review Business (requires login first)")
    print("[0] Exit the application program. ")

#sign in a user and remember them 
def login(connection):
    #give multiple tries to login incase the user_id is wrong
    while True:
        user_id = input("Enter your user ID: ")

        cursor = connection.cursor()
        #look if the user_id is valid and exists in the database
        cursor.execute("SELECT * FROM user_yelp WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            print("Login Successful!")
            return user_id
        else:
            print("Invalid userID. Please try again.")

#used to search business by name, stars, city
def search_business(connection):
    #filter criteria
    print("Please provide your search criteria: ")
    min_stars = int(input("Enter minimum number of stars: "))
    city = input("Enter city: ").upper() #to avoid case-sensitivity
    name = input("Enter name (or part of the name) of the business: ").upper() #to avoid case-sensitivity
    print("Please provide your choice for ordering: ")
    order_by = input("Enter your choice - by name/by city/by stars: ").upper() #to avoid case-sensitivity

    filter_query = "SELECT business_id, name, address, city, stars FROM business WHERE stars >= ?"
    filters = [min_stars] 

    if city:
        filter_query = filter_query + " AND UPPER(city) = ?"
        filters.append(city)
    
    if name:
        filter_query = filter_query + " AND UPPER(name) LIKE ?"
        filters.append(f"%{name}%")

    filter_query = filter_query + f" ORDER BY {order_by}"
    cursor = connection.cursor()
    #execute the above defined query with the provided parameters. 
    cursor.execute(filter_query, filters)
    results = cursor.fetchall() #return all matching results

    if results:
        print("Search Results: ")
        for result in results:
            print(f"Business_id: {result[0]}, Business_name: {result[1]}, Address: {result[2]}, City: {result[3]}, Number_stars: {result[4]}")
    else:
        print("No businesses found matching the search criteria. ")

#used to search users based on name, review count and stars
def search_users(connection):
    #filter criteria
    print("Please provide your search criteria: ")
    name = input("Enter name (or part of the name) of the user: ").upper() #to avoid case sensitivity
    min_rcount = int(input("Enter minimum review count: "))
    min_avgstars = float(input("Enter minimum average stars: "))

    #LIKE to match any part of the name to the database entries. 
    filter_query = "SELECT user_id, name, review_count, useful, funny, cool, average_stars, yelping_since FROM user_yelp WHERE UPPER(name) LIKE ?"
    filters = [f"%{name}%"]

    filter_query = filter_query + " AND review_count >= ?"
    filters.append(min_rcount)
 
    filter_query = filter_query + " AND average_stars >= ?"
    filters.append(min_avgstars)

    filter_query = filter_query + f" ORDER BY name"
    cursor = connection.cursor()
    cursor.execute(filter_query, filters)
    results = cursor.fetchall()

    if results:
        print("Search Results: ")
        for result in results:
            print(f"user_id: {result[0]}, name: {result[1]}, review_count: {result[2]}, useful: {result[3]}, funny: {result[4]}, cool: {result[5]}, average_stars: {result[6]}, yelping_since: {result[7]}")
    else:
        print("No users found matching the search criteria. ")


#used to make friends with other users based on search
def make_friend(connection, logged_in_userid):
    #first display user with search option to view choices for friendship 
    search_users(connection)

    friend_id = input("Please enter the ID of user you wish to befriend: ")
    cursor = connection.cursor()
    #check if user_id is valid and exists in user database
    cursor.execute("SELECT COUNT(*) FROM user_yelp WHERE user_id = ?", (friend_id,))
    #select the count column from fetchone
    count = cursor.fetchone()[0]
    if count <= 0:
        print("Invalid User id. Please select a user again. ")
    cursor = connection.cursor()
    #check if friendship already exists, else create a new friendship 
    cursor.execute("SELECT COUNT(*) FROM friendship WHERE (user_id = ? AND friend = ?) OR (user_id = ? AND friend = ?)", (logged_in_userid, friend_id, friend_id, logged_in_userid))
    count = cursor.fetchone()[0]
    if count > 0:
        print("Friendship already exists. ")
    else: 
        cursor.execute("INSERT INTO friendship (user_id, friend) VALUES (?, ?), (?, ?)", (logged_in_userid, friend_id, friend_id, logged_in_userid))
        connection.commit()
        print("Frienship now exists in Friendship table with user_id : ", friend_id)

#code to generate a unique review id is adapted from: https://www.uuidgenerator.net/dev-corner/python
def custom_review_id(cursor):
    # keep generating until a unqiue one is found 
    while True:
        review_id = str(uuid.uuid4())[:22]  # Generate a new 22 char UUID
        cursor.execute("SELECT COUNT(*) FROM review WHERE review_id = ?", (review_id,))
        count = cursor.fetchone()[0]
        #no similar entry exists, the review id generated is unique, return it!
        if count == 0:
            return review_id  # Return the unique review ID

#used to review businesses based on search results
def review_business(connection, logged_in_userid):

    search_business(connection)

    b_id = input("Enter the business ID of the business you'd like to review: ")

    cursor = connection.cursor()
    #check if b_id is valid and exists in business table. 
    cursor.execute("SELECT COUNT(*) FROM business WHERE business_id = ?", (b_id,))
    count = cursor.fetchone()[0]
    if count <= 0:
            print("Invalid Business id. Please select a user again. ")
    
    rating = int(input("Enter the number of stars between 1 and 5: "))
    #make sure stars rating is between the range [1,5]
    if rating < 1 or rating > 5:
        print("Invalid rating given. Please enter a number between 1 and 5. ")
        return
    #extract the reviews from the user
    funny = int(input("Please rate the business a number in terms of being funny: "))
    useful = int(input("Please rate the business a number in terms of being useful: "))
    cool = int(input("Please rate the business a number in terms of being cool: "))
    cursor = connection.cursor()
    #generate a unique review_id for this review submission. 
    review_id = custom_review_id(cursor)
    #insert the review abiding by the trigger constraints. 
    cursor.execute("INSERT INTO review(review_id, user_id, business_id, stars, funny, useful, cool, date) VALUES (?,?,?,?,?,?,?,?)", (review_id,logged_in_userid,b_id,rating,funny, useful, cool, datetime.datetime.now()))
    connection.commit()
    print("Review successfully submitted. ")
    cursor = connection.cursor()
    #update the business table with updated stars = average of old and new value; and review count += 1. 
    cursor.execute("UPDATE business SET stars = (stars + ?) / 2, review_count = review_count + 1 WHERE business_id = ?", (rating, b_id))
    connection.commit()


#setting up a connection 
DRIVER_NAME = 'SQL SERVER'
SERVER_NAME = 'CS-DB-MS1'
DATABASE_NAME = 'asa313354'
connection_string = f"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trust_connection=yes;
    uid=s_asa313;
    pwd=Meb2Tebd4RnJTRgd;
"""
conn = odbc.connect(connection_string)
print("Connection successfully established.")
#display application menu to user, dont quit until user chooses 0 to exit the application. 
application_menu()
option = int(input("Enter your choice: "))

while option != 0:
    if option == 1:
        print("Welcome to LOGIN! ")
        logged_in_user = login(conn)
        print(f"Logged in as UserID: {logged_in_user}")
    elif option == 2:
        print("Welcome to SEARCH BUSINESS! ")
        search_business(conn)
    elif option == 3:
        print("Welcome to SEARCH USERS! ")
        search_users(conn)
    elif option == 4:
        print("Welcome to MAKE FRIEND! ")
        make_friend(conn, logged_in_user)
    elif option == 5:
        print("Welcome to REVIEW BUSINESS! ")
        review_business(conn, logged_in_user)
    else:
        print("Invalid choice. Please enter choice between 0-5")

    print()
    application_menu()
    option = int(input("Enter your choice: "))
#if the user chose 0 = exit the application. 
print("Closing the application! Thank You! ")
#closing connection
conn.close()