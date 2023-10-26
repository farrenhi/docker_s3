from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import os
load_dotenv()  # take environment variables from .env.

import boto3
from datetime import datetime
from werkzeug.utils import secure_filename


# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id = os.getenv('s3_access'),
    aws_secret_access_key = os.getenv('s3_secret'),
)

### Connection Pool
import mysql.connector.pooling

app = Flask(
    __name__,
    static_folder="",
    static_url_path="/",
)

app.secret_key = os.getenv('app_secret_key') # session would need this!

# local parameters
# rds_db_config = os.getenv('rds_db_config')
# rds_db_config = eval(rds_db_config)

# Create a connection pool
# connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **db_config_haha)

rds_db_config = {'host': os.getenv('rds_host'), 
                 'port': 3306, 
                 'user': os.getenv('rds_user'), 
                 'password': os.getenv('rds_password'), 
                 'database': os.getenv('rds_database')}

rds_connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool_rds", pool_size=5, **rds_db_config)


# Function to execute a query using a connection from the pool
def execute_query_create(query, data=None):
    connection = rds_connection_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, data)
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print("Error:", e)
        return False
    finally:
        cursor.close()
        connection.close()

def execute_query_read(query, data=None):
    # To request a connection from the pool, use its get_connection() method: 
    connection = rds_connection_pool.get_connection() 
    cursor = connection.cursor(dictionary=True)
    myresult = None
    try:
        cursor.execute(query, data)
        myresult = cursor.fetchall()
        if len(myresult) == 0:
            myresult = None
    except Exception as e:
        print("Error:", e)
    finally:
        cursor.close()
        connection.close()
        return myresult

def execute_query_update(query, data=None):
    connection = rds_connection_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, data)
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print("Error:", e)
        return False
    finally:
        cursor.close()
        connection.close()

def execute_query_delete(query, data=None):
    connection = rds_connection_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, data)
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print("Error:", e)
        return False
    finally:
        cursor.close()
        connection.close()

@app.route("/") # , methods=["GET"]
def index():
    return render_template("index.html")

## Version 3: Connection Pool!
def get_info_from_sql(username):
    '''input username and return corresponding info from SQL'''
    query = "SELECT * FROM member WHERE username = (%s)"
    data = (username,)
    # print(execute_query_read(query, data))
    return execute_query_read(query, data)

def commit_info_into_sql(name, username, password):
    '''this function would write data into SQL database'''
    query = "INSERT INTO member (name, username, password) VALUES (%s, %s, %s)"
    data = (name, username, password)
    execute_query_create(query, data)
    # return redirect(url_for("index"))
    # Question: if it is commit, we will go to index directly. but how to design it?
    # in case if database writing does not work, we should show error message about database

# message board: how to do it?
# Previously, the data could be saved as dictionary from SQL database
# https://chat.openai.com/c/4e9b8b76-7d77-4403-9a51-7054aac4203f
# Question: so, what if we save the data as dictionary for message board?
def get_all_messages_from_sql():
    query = "SELECT message.content, member.name, message.member_id, message.id, message.cloudfront_link FROM message INNER JOIN member ON message.member_id = member.id;"
    return execute_query_read(query)    

# Create function version 2
def commit_to_sql_message(member_id, content, cloudfront_link):
    '''this function would write data into SQL database Table message'''
    query = "INSERT INTO message (member_id, content, cloudfront_link) VALUES (%s, %s, %s)"
    data = (member_id, content, cloudfront_link)
    execute_query_create(query, data)

# Delete function version 2
def delete_sql_message(message_id):
    '''Delete a row data from SQL database'''
    query = "DELETE FROM message WHERE id = %s"
    data = (message_id, )
    return execute_query_delete(query, data)

def update_name_sql(username, new_name):
    '''Based on the input username, we will update the name as new_name'''
    query = "UPDATE member SET name = %s WHERE username = %s"
    data = (new_name, username)
    return execute_query_update(query, data)


# Look Up API
# @app.route("/api/member/<string:username>", methods=["GET"])
# def look_up_api(username):
#     return username

@app.route("/api/member", methods=["GET", "PATCH"])
def get_patch_member():
    if request.method == 'GET':
        username = request.args.get("username")
        user_data = get_info_from_sql(username)
        if user_data is not None:
            for item in user_data:
                user_data_selected = {'id': item['id'], 'username': item['username'], 'name': item['name']}
            response_data = {"data": user_data_selected}
        else:
            response_data = {"data": None}
        return jsonify(response_data)
    
    elif request.method == 'PATCH':
        data = request.json
        new_name = data.get('name')
        # print(new_name)
        
        if not new_name:
            return jsonify({"error": True})
        
        username = session["username"]
        update_result = update_name_sql(username, new_name)
        
        if update_result:
            return jsonify({"ok": True})
        else:
            return jsonify({"error": True})
        
# Registration Endpoint
@app.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]
    
    # check if any username info in SQL
    if get_info_from_sql(username) is not None:
        return redirect(url_for("error", message="Username is registered!"))
    else:
        commit_info_into_sql(name, username, password)
        return redirect(url_for("index"))
        # return redirect(url_for("error", message="Database is not accessible!"))
        # return """<h1> This is the new username! </h1>"""

# Delete Message Endpoint
@app.route("/deleteMessage", methods=["POST"])
def deleteMessage():
    message_id = request.form.get("message_id")
    delete_sql_message(message_id)
    return redirect(url_for("messageboard"))

# Create Message Endpoint
@app.route("/createMessage", methods=["POST"])
def createMessage():
    content = request.form["message"]
    member_id = session.get("id")
   
    current_datetime = datetime.now()
    time_stamp = current_datetime.strftime("%Y%m%d%H%M%S%f")

    # Get the uploaded file
    uploaded_file = request.files['imageFile']
    
    if uploaded_file:
        # Generate a unique name for the uploaded file
        file_name = f"{member_id}_{time_stamp}_{secure_filename(uploaded_file.filename)}"

        # Upload the file to S3
        s3.upload_fileobj(uploaded_file, 'login-aws-docker', file_name)
    
        cloudfront_distribution_domain = os.getenv('cloudfront_distribution_domain')
        cloudfront_link = generate_cloudfront_link(cloudfront_distribution_domain, file_name)
    else:
        cloudfront_link = None

    # Save the message and S3 URL to your database
    print(cloudfront_link)
    commit_to_sql_message(member_id, content, cloudfront_link) #, s3_url
    return redirect(url_for("messageboard"))


def generate_cloudfront_link(distribution_domain, object_key):
    return f"https://{distribution_domain}/{object_key}"


# # previous createMessage code
# def createMessage():
#     content = request.form["message"]
#     member_id = session.get("id")
#     commit_to_sql_message(member_id, content)
#     return redirect(url_for("messageboard"))


# Verification Endpoint
@app.route("/signin", methods=["POST"])
def signin():
    username = request.form["username"]
    password = request.form["password"]
    if username == '' or password == '':
        message_info = "Please enter username and password"
        return redirect(url_for("error", message=message_info))
    
    ## We need to go to SQL to get the password info
    # user_info_from_sql = get_info_from_sql(username)
    user_info_from_sql = get_info_from_sql(username)[0]
    
    password_from_sql = user_info_from_sql["password"]
        
    if password == password_from_sql:
        session["SIGNED-IN"] = True  # Set the "SIGNED-IN" state to True in the session.
        session["id"] = user_info_from_sql["id"]
        session["name"] = user_info_from_sql["name"]
        session["username"] = username
        session["password"] = password
        session["follower_count"] = user_info_from_sql["follower_count"]
        session["time"] = user_info_from_sql["time"]
       
        # , message_data=messages_for_board
        return redirect(url_for("member"))
    else:
        message_info = "Username or password is not correct"
        return redirect(url_for("error", message=message_info))

@app.route("/member")
def member():
    if session.get("SIGNED-IN"):
        # User is signed in, render the success page.
        messages_for_board = get_all_messages_from_sql()
        name = session.get("name")
        this_member_id = session.get("id")
        return render_template(
            "member.html", data_name=name, message_data=messages_for_board, data_this_member_id=this_member_id)
    else:
        # User is not signed in, redirect to the login page or show an error message.
        return redirect(url_for("index"))  # Redirect to the login page if not signed in.


# message board (copied from member route)
@app.route("/messageboard")
def messageboard():
    if session.get("SIGNED-IN"):
        # User is signed in, render the success page.
        messages_for_board = get_all_messages_from_sql()
        # print(messages_for_board)
        name = session.get("name")
        this_member_id = session.get("id")
        return render_template(
            "messages.html", data_name=name, message_data=messages_for_board, data_this_member_id=this_member_id)
    else:
        # User is not signed in, redirect to the login page or show an error message.
        return redirect(url_for("index"))  # Redirect to the login page if not signed in.



@app.route("/error")
def error():
    data_received = request.args.get("message")
    return render_template("error.html", data=data_received)

@app.route("/square/<int:num>", methods=["GET"])
def square(num):
    # Get method: this does not show up in the URL
    #maxNumber = request.args.get("max", "")
    
    # Post method: you need to use request! This method is good for privacy
    # maxNumber = request.form["max"]
    # maxNumber = int(maxNumber)
    result = num * num

    # "Result:" + str(result)
    return render_template("result.html", data=result)

@app.route('/signout', methods=["GET"])
def signout():
    session["SIGNED-IN"] = False 
    session.pop('username', None)  # Remove the username from the session
    session.clear()  # Clear all session data
    return redirect(url_for('index'))

# run server
app.run(host="0.0.0.0", port=3002, debug=True)
