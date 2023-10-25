from flask import Flask, request, render_template, redirect, url_for, session, jsonify

### Python-SQL
import mysql.connector.pooling
import mysql.connector
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="12345678",
  database='website'
)
###

app = Flask(
    __name__,
    static_folder="",
    static_url_path="/",
)

app.secret_key = "secret" # session would need this!

@app.route("/") # , methods=["GET"]
def index():
    return render_template("index.html")

### Python SQL function
# version 1: data saved as tuple. not good. version 2 is dictionary
# def get_info_from_sql(username):
#     '''input username and return corresponding info from SQL'''
#     mycursor = mydb.cursor()

#     sql = "SELECT * FROM member WHERE username = (%s)"
#     val = (username,)
#     mycursor.execute(sql, val)

#     myresult = mycursor.fetchall()
#     if myresult:
#         return myresult[0]
#     else:
#         return None

# # version2: Dictionary Cursor implementation
def get_info_from_sql(username):
    '''input username and return corresponding info from SQL'''
    mycursor = mydb.cursor(dictionary=True)

    sql = "SELECT * FROM member WHERE username = (%s)"
    val = (username,)
    mycursor.execute(sql, val)
    myresult = mycursor.fetchall()
    # Close cursor and connection
    mycursor.close()
    # mydb.close()
    if myresult:
        return myresult
    else:
        return None

def commit_info_into_sql(name, username, password):
    '''this function would write data into SQL database'''
    mycursor = mydb.cursor()

    sql = "INSERT INTO member (name, username, password) VALUES (%s, %s, %s)"
    val = (name, username, password)
    mycursor.execute(sql, val)
    mydb.commit()
    # return redirect(url_for("index"))
    # Question: if it is commit, we will go to index directly. but how to design it?
    # in case if database writing does not work, we should show error message about database

# message board: how to do it?
# Previously, the data could be saved as dictionary from SQL database
# https://chat.openai.com/c/4e9b8b76-7d77-4403-9a51-7054aac4203f
# Question: so, what if we save the data as dictionary for message board?
def get_all_messages_from_sql():
    mycursor = mydb.cursor()
    mycursor.execute(
      # "SELECT message.*, member.name FROM message INNER JOIN member ON message.member_id = member.id;"
      "SELECT message.content, member.name, message.member_id, message.id FROM message INNER JOIN member ON message.member_id = member.id;"
    )
    myresult = mycursor.fetchall()
    return myresult    

def commit_to_sql_message(member_id, content):
    '''this function would write data into SQL database Table message'''
    mycursor = mydb.cursor()

    sql = "INSERT INTO message (member_id, content) VALUES (%s, %s)"
    val = (member_id, content)
    mycursor.execute(sql, val)

    mydb.commit()  

def delete_sql_message(message_id):
    '''Delete a row data from SQL database'''
    mycursor = mydb.cursor()
    sql = "DELETE FROM message WHERE id = %s"
    id_input = (message_id, )
    mycursor.execute(sql, id_input)
    mydb.commit()

def update_name_sql(username, new_name):
    '''Based on the input username, we will update the name as new_name'''
    try:
        mycursor = mydb.cursor()
        sql = "UPDATE member SET name = %s WHERE username = %s"
        id_input = (new_name, username)
        mycursor.execute(sql, id_input)
        mydb.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        mycursor.close()
###

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
    return redirect(url_for("member"))

# Create Message Endpoint
@app.route("/createMessage", methods=["POST"])
def createMessage():
    content = request.form["message"]
    member_id = session.get("id")
    commit_to_sql_message(member_id, content)
    return redirect(url_for("member"))

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
app.run(port=3000, debug=True)
