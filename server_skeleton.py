##############################################################################
# server.py
##############################################################################
import select
import socket
import chatlib
import random
import requests
import json
import xml.etree.ElementTree
import html

# GLOBALS
users = {}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
questions = {}
old_questions = {}
messages_to_send = []  # List of tuples with the socket of the addressee and the msg.

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER DICT METHODS

def get_key_by_value(dictionary, target_value):
    """
    Gets dict and a value and return it's key.
    """
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None  # Return None if the value is not found in the dictionary


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message. Prints debug info, then sends it to the given socket.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    :param code: the name of the chosen method
    :type code: str
    :param msg: full data
    :type msg: str
    Returns: Nothing
    """
    global messages_to_send
    full_msg = chatlib.build_message(code, msg)
    # conn.send(full_msg.encode())  # Change the text to binary code
    messages_to_send.append((conn, full_msg))  # Add msg and conn to list of massages
    # print("The massage was sent successfully to client.")
    print("[SERVER] ", full_msg)  # Debug print


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket, then parses the message using chatlib.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    return: cmd (str) and data (str) of the received message. If error occurred, will return None, None
    """
    # Receive the data from the client - until 1024 bytes.
    msg_code = conn.recv(1024)  # Receive coded massage from the client.
    msg = msg_code.decode()  # Change the massage code to text by decode().
    cmd, data = chatlib.parse_message(msg)  # Parses protocol message and returns command name and data field.
    print("[CLIENT] ", msg)  # Debug print
    return cmd, data


# Data Loaders #

def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Receives: -
    Returns: questions dictionary
    """
    global questions
    questions_input_file = open(r"C:\trivia\fina_with_extensions\questions.txt", "r")
    line_counter = 0
    for line in questions_input_file:
        if line_counter % 2 == 0:
            line = line.replace("\n", "")
            list_questions_details = line.split(",")
            question_id = list_questions_details[0]
        else:
            line = line.replace(" \n", "")
            list_questions_details = line.split(",")
            for i in range(1, 6):
                list_questions_details[i] = list_questions_details[i].replace(" ", "")
            question = list_questions_details[0]
            answers = [list_questions_details[1], list_questions_details[2], list_questions_details[3], list_questions_details[4]]
            correct = list_questions_details[5]
            questions[question_id] = {"question": question, "answers": answers, "correct": correct}
        line_counter += 1
    questions_input_file.close()
    return questions


def load_questions_from_web():
    """
    Loads questions bank from web service called Open Trivia Database
    Receives: -
    Returns: questions dictionary
    """
    global questions
    # Because the XML format is causing difficulties, and the API supports alternative data formats, we would use JSON
    api_url = "https://opentdb.com/api.php?amount=50&type=multiple"

    # Send a GET request to the API
    # Get method is used as part of the "requests" library to send a GET request to the specified URL.
    response = requests.get(api_url)  # The response object contains info about the HTTP response, including the response content.

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        # response.content retrieves the raw content of the response as bytes
        # json.loads() is a func provided by the json module in Python.It takes a str or bytes representing a JSON object and converts it into a Python object.
        data = json.loads(response.content)

        question_id = 0
        answers = []
        for question in data["results"]:
            question_id += 1
            # html.unescape used to decode any HTML entities to ensure that special characters, such as &amp;, &lt;, &gt;, etc., are converted back to their original characters.
            question_text = html.unescape(question["question"])
            correct_answer = html.unescape(question["correct_answer"])
            incorrect_answers = [html.unescape(ans) for ans in question["incorrect_answers"]]

            answers.append(correct_answer)
            answers += incorrect_answers  # Add the right and incorrect ans to the answers field
            random.shuffle(answers)  # Make the order random so the user won't remember the numer of correct ans from one game to another.
            correct_answer_index = answers.index(correct_answer) + 1

            questions[question_id] = {
                "question": question_text,
                "answers": answers,
                "correct": str(correct_answer_index)
            }

            answers = []  #  Initializes the answer field for each new question
            correct_answer_index = 0  #  Initializes the correct answer index field for each new question

        return questions

    else:
        print("Request failed with status code:", response.status_code)
        return load_questions()  # If the web service doesn't work then use the based method of the game


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Receives: -
    Returns: user dictionary
    """
    global users
    users_input_file = open(r"C:\trivia\fina_with_extensions\users.txt", "r")
    for line in users_input_file:
        line = line.replace(" ", "")
        line = line.replace("\n", "")
        list_user_details = line.split(",")
        username = list_user_details[0]
        password = list_user_details[1]
        score = list_user_details[2]
        users[username] = {"password": password, "score": score, "questions_asked": []}
    users_input_file.close()
    return users


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    return: the socket object
    """
    print("Setting up server...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object of the server and insert to it IP protocol (AF_INET), and then TCP protocol (SOCK_STREAM).
    sock.bind((SERVER_IP, SERVER_PORT))  # Bind the server socket to local IP and port number for listening to clients and also to who comes from outside to IP address
    sock.listen()  # Listening to connections from clients
    print("Listening for clients...")
    return sock


# HELPER QUESTIONS METHODS
def create_random_question(username):
    """
    :param username: the user's name
    :type username: str
    Returns str with a question
    """
    global questions
    global users
    answers = ""
    if len(questions) != len(users[username]["questions_asked"]):
        while True:
            questions_id, info = random.choice(list(questions.items()))  # Change info to list
            if questions_id not in users[username]["questions_asked"]:
                break
        for answer in info["answers"]:
            answers = answers + answer + "#"
        answers = answers[0:-1]  # Remove last #
        return str(questions_id) + "#" + str(info["question"]) + "#" + answers  # Returns question id and answers as str separated by #
    else:
        return ""


def send_error(conn, error_msg):
    """
    Send error message with given message
    :param conn: an opened socket from the connect method
    :type conn: socket
    :param error_msg: a message error string from called function
    :type error_msg: str
    Returns: None
    """
    build_and_send_message(conn, "ERROR", error_msg)


# MESSAGE HANDLING

def handle_question_message(conn, username):
    """
    :param conn: an opened socket
    :type conn: socket
    :param username: the user's name
    :type username: str
    Gets sockets and sends random question to client
    """
    question = create_random_question(username)
    if question != "":
        build_and_send_message(conn, "YOUR_QUESTION", str(question))
    else:
        build_and_send_message(conn, "NO_QUESTIONS", str(question))


def handle_getscore_message(conn, username):
    """
    Sends user's score
    :param conn: an opened socket
    :type conn: socket
    :param username: the user name
    :type username: str
    """
    global users
    msg = users[username]["score"]
    build_and_send_message(conn, "YOUR_SCORE", str(msg))


def handle_answer_message(conn, username, data):
    """
    Checks if the answer is correct (if it's ok than update score) and send fits msg
    :param conn: an opened socket
    :type conn: socket
    :param username: the user's name
    :type username: str
    :param data: the user's answer
    :type data: str
    """
    global users
    global questions
    idquestion_choice = chatlib.split_data(data, 1)
    idquestion = int(idquestion_choice[0])
    choice = idquestion_choice[1]
    # answers = questions[idquestion]["answers"]
    correct_ans = questions[idquestion]["correct"]
    if str(correct_ans) == str(choice):
        build_and_send_message(conn, "CORRECT_ANSWER", "")
        users[username]["score"] = int(users[username]["score"]) + 5
    else:
        build_and_send_message(conn, "WRONG_ANSWER", str(correct_ans))
    users[username]["questions_asked"].append(idquestion)


def handle_highscore_message(conn):
    """
    Sends the five most high scores of users
    :param conn: an opened socket
    :type conn: socket
    """
    global users
    msg = ""
    sorted_users_by_scores = dict(sorted(users.items(), key=lambda x: int(x[1]["score"]), reverse=True))
    counter = 0
    for username in sorted_users_by_scores:
        msg = msg + "\n" + username + ": " + str(users[username]["score"])
        counter += 1
        if counter == 5:
            break
    build_and_send_message(conn, "ALL_SCORE", msg)


def handle_logged_message(conn):
    """
    Sends names of the logged users
    :param conn: an opened socket
    :type conn: socket
    """
    global logged_users
    msg = ""
    for username in logged_users:
        msg = msg + username + ", "
    msg = msg[0:-2]  # Remove last comma
    build_and_send_message(conn, "LOGGED_ANSWER", msg)


def handle_logout_message(conn):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictionary)
    :param conn: an opened socket from the connect method
    :type conn: socket
    Returns: None
    """
    global logged_users
    username = get_key_by_value(logged_users, conn)
    del logged_users[username]
    conn.close()  # Close the connection
    print("Connection closed. Client " + username + " has logged out.")


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    :param conn: an opened socket from the connect method
    :type conn: socket
    :param data: a message data of login message
    :type data: str
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users' dictionary from all functions
    global logged_users  # To be used later

    user_and_pass = chatlib.split_data(data, 1)  # Split the msg of user#password to list
    user = user_and_pass[0]
    password = user_and_pass[1]
    if user in users:  # If user is registered in game and the password is correct
        if user in logged_users:
            send_error(conn, "Error! The user is already logged in!")
        elif users[user]["password"] == password:  # If the user and the password are correct
            build_and_send_message(conn, "LOGIN_OK", "")
            logged_users[user] = conn  # Adding the user socket to logged_users dict
        else:
            send_error(conn, "Error! Password does not match!")
    else:
        send_error(conn, "Error! Username does not exist")


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    :param conn: an opened socket
    :type conn: socket
    :param cmd: message code
    :type cmd: str
    param data: data
    :type data: str
    Returns: None
    """
    global logged_users
    username = ""
    if conn not in logged_users.values() and cmd == "LOGIN":
        handle_login_message(conn, data)
    elif conn in logged_users.values():
        username = get_key_by_value(logged_users, conn)
        if cmd == "LOGOUT":
            handle_logout_message(conn)
        if cmd == "MY_SCORE":
            handle_getscore_message(conn, username)
        if cmd == "HIGHSCORE":
            handle_highscore_message(conn)
        if cmd == "LOGGED":
            handle_logged_message(conn)
        if cmd == "GET_QUESTION":
            handle_question_message(conn, username)
        if cmd == "SEND_ANSWER":
            handle_answer_message(conn, username, data)
    else:
        send_error(conn, "Unknown command.")


def print_client_sockets(client_sockets):
    global logged_users
    for user in logged_users.values():
        print("\t", user.getpeername())  # The method bringS the ip + port of the current client, /t is for tab space


def main():
    # Initializes global users and questions dictionaries using load functions, will be used later
    global users
    global questions
    global messages_to_send
    users = load_user_database()
    questions = load_questions_from_web()

    print("Welcome to Trivia Server!")

    server_socket = setup_socket()
    client_sockets = []  # Contains all the objects of the clients who connect to the server

    # Getting information from the clients: #
    while True:  # While true the server looks for new clients
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets,
                                                                [])  # Sending to the func list of clients on server and the socket of the server
        for current_socket in ready_to_read:  # Scanning the clients list
            if current_socket is server_socket:  # if the current belong to server then new client wants join
                # The running of the code stops ("blocking") until client will be connected.
                # Client_socket - contain the info that the server must have for the connections to client.
                # Client_address - a tuple with the IP, port (also in client_socket)
                (client_socket, client_address) = current_socket.accept()
                print("New client joined!", client_address)
                client_sockets.append(client_socket)
            else:
                # noinspection PyBroadException
                try:
                    print("New data from client")
                    cmd, data = recv_message_and_parse(current_socket)
                    if cmd is None and data is None:
                        handle_logout_message(current_socket)
                        client_sockets.remove(current_socket)
                        break
                    handle_client_message(current_socket, cmd, data)
                    if cmd == "LOGOUT":
                        client_sockets.remove(current_socket)
                        break
                except:  # Handle in clients which closed cmd without error: #
                    handle_logout_message(current_socket)
                    client_sockets.remove(current_socket)
                    break

            for message in messages_to_send:
                current_socket, data = message
                if current_socket in ready_to_write:  # If the client's socket is available, means it's in rtw, send it's msg
                    current_socket.send(data.encode())
                    messages_to_send.remove(message)
        # If client's socket isn't available, it will be sent next time


if __name__ == '__main__':
    main()
