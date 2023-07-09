import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message. Prints debug info, then sends it to the given socket.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    :param code: the name of the chosen method
    :type code: str
    :param data: full data
    :type data: str
    Returns: Nothing
    """
    full_msg = chatlib.build_message(code, data)
    conn.send(full_msg.encode())  # Change the text to binary code
    print("[CLIENT] ", full_msg)  # Debug print
    # print("The massage was sent successfully to server.")


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket, then parses the message using chatlib.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    return: cmd (str) and data (str) of the received message. If error occurred, will return None, None
    """
    # Receive the data from the server - until 1024 bytes.
    msg_code = conn.recv(1024)  # Receive coded massage from the server.
    msg = msg_code.decode()  # Change the massage code to text by decode().
    cmd, data = chatlib.parse_message(msg)  # Parses protocol message and returns command name and data field.
    if cmd == "ALL_SCORE":
        print("[SERVER] " + msg.replace(data, ""))  # Debug print
    else:
        print("[SERVER] ", msg)  # Debug print
    return cmd, data


def connect():
    """  Uses the constant ip, port and creates a connected socket. """
    # Create a socket object
    # Insert to it IP protocol (AF_INET), and then TCP protocol (SOCK_STREAM)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))  # Connect to server using local host
    return client_socket


def error_and_exit(error_msg):
    """
    Exits from the server in case of trouble issues
    Returns: str, or None if error occurred
    :param error_msg: A message to print
    :type error_msg: str
    """
    print(error_msg)
    exit()  # Python’s in-built function which works only if the site module is imported.


def login(conn):
    """
    Ask from the client to user and pass, then build a massage to protocol with method name and data.
    If the user exists in server then stop loop, else try again.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    """
    while True:
        username = input("Please enter username: \n")
        password = input("Please enter password: \n")
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], username + "#" + password)
        recv_message = recv_message_and_parse(conn)
        if recv_message == (None, None):
            print("An error occurred. Try again.\n")
        elif recv_message[0] == "ERROR":
            print("Try again.\n")
        else:
            print("Logged in!\n")
            break


def logout(conn):
    """
    Sends a logout massage to server
    :param conn: an opened socket from the connect method.
    :type conn: socket
    """
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


def build_send_recv_parse(conn, code, data):
    """
    Builds a new message using chatlib, chosen code and message, then sends it to server by the given socket.
    After then receives a new message from the server using the given socket, then parses the message using chatlib.
    :param conn: an opened socket from the connect method.
    :type conn: socket
    :param code: the name of the chosen method
    :type code: str
    :param data: full data
    :type data: str
    return: cmd (str) and data (str) of the received message. If error occurred, will return None, None
    """
    build_and_send_message(conn, code, data)
    msg_code, data = recv_message_and_parse(conn)
    return msg_code, data


def get_score(conn):
    """
    Prints the client points by his user details
    :param conn:
    :type conn: socket
    """
    recv_message = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["my_score_msg"], "")
    if recv_message == (None, None) or recv_message[0] == "ERROR":
        print("An error occurred.\n")
    else:
        print("Your score is " + str(recv_message[1]) + ".\n")


def get_highscore(conn):
    """
    Prints the highest scores in game.
    :param conn:
    :type conn: socket
    """
    recv_message = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["highscore_msg"], "")
    if recv_message == (None, None) or recv_message[0] == "ERROR":
        print("An error occurred.\n")
    else:
        print("\nHigh-Score table:" + str(recv_message[1]) + "\n")


def user_options():
    """
    Prints the available options to the user
    """
    print("""    p    Play a trivia question
    s    Get my score
    h    Get high score
    l    Get logged users
    q    Quit""")


def play_question(conn):
    """
    Ask for a question from server
    :param conn:
    :type conn: socket
    """
    # Gets the questions and checks there isn't error or out of questions:
    recv_message = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    if recv_message == (None, None) or recv_message[0] == "ERROR":
        print("An error occurred.\n")
        return
    elif recv_message[0] == "NO_QUESTIONS":
        print("No more questions.\n")
        return
    # If there is a question, the massage will be sum as "YOUR_QUESTION   |0026|2#How much is 1+1?#5#6#7#2":
    else:
        question_list_recv_message = chatlib.split_data(recv_message[1], 5)  # Separate the massage to list at #
        question_id = question_list_recv_message[0]  # Get the question id from the first cell of list
        print("\nQ: " + question_list_recv_message[1])  # Print id and question to the user
        counter_number_question = 0  # A counter for saving the answer number for the loop
        for answer in question_list_recv_message[2:6]:
            counter_number_question += 1
            print("    " + str(counter_number_question) + ".  " + answer)  # Print the answer number + answer for user
        chosen_answer_of_user = input("\nPlease enter your choice:")  # Asking from user his chosen answer
        while int(chosen_answer_of_user) not in range(1, 5):  # Validation of the input of the user chosen answer
            print("\nIllegal choice. Please enter number in range of 1 - 4.")
            chosen_answer_of_user = input("\nPlease enter your choice:")
        data = str(question_id) + "#" + str(chosen_answer_of_user)  # Making data of id question#user chosen answer
        # Check if the answer is correct or not by sending it to server:
        recv_message = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], data)
        if recv_message[0] == "WRONG_ANSWER":
            print("Nope, correct answer is " + recv_message[1] + ".\n")
        elif recv_message == (None, None) or recv_message[0] == "ERROR":
            print("An error occurred.\n")
        else:
            print("YES!!!!\n")


def get_logged_users(conn):
    """
    Ask for a question from server
    :param conn:
    :type conn: socket
    """
    recv_message = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_msg"], "")
    print("Logged users: \n" + recv_message[1] + "\n")


def main():
    client_socket = connect()
    login(client_socket)
    chosen_action_of_user = ""
    while chosen_action_of_user != "Quit":
        user_options()
        chosen_action_of_user = input("\nPlease enter your choice:")
        chosen_action_of_user = chosen_action_of_user.upper()
        if chosen_action_of_user == "S":
            get_score(client_socket)
        elif chosen_action_of_user == "H":
            get_highscore(client_socket)
        elif chosen_action_of_user == "L":
            get_logged_users(client_socket)
        elif chosen_action_of_user == "P":
            play_question(client_socket)
        elif chosen_action_of_user == "Q":
            break
        else:
            print("Illegal choice. Try again.")
    logout(client_socket)
    print("Goodbye!")
    client_socket.close()  # Close the socket.


if __name__ == '__main__':
    main()
