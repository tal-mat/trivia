# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",
    "logout_msg": "LOGOUT",
    "my_score_msg": "MY_SCORE",
    "highscore_msg": "HIGHSCORE",
    "get_question_msg": "GET_QUESTION",
    "send_answer_msg": "SEND_ANSWER",
    "logged_msg": "LOGGED"
}  # Add more commands if needed

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",
    "login_failed_msg": "ERROR",

}  # ..  Add more commands if needed

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
    """
    Gets command name (str) and data field (str) and creates a valid protocol message
    Returns: str, or None if error occurred
    :param cmd: A command name
    :type cmd: str
    :param data: A data field
    :type data: str
    return: list of fields if all ok. If some error occurred, returns None
    :rtype: str, or None if error occurred
    """
    full_msg = ""
    if len(cmd) <= CMD_FIELD_LENGTH and len(data) <= MAX_DATA_LENGTH:  # If cmd and data lengths are allowed:
        cmd = cmd + (" " * int(CMD_FIELD_LENGTH - len(cmd)))  # Change cmd to cmd and space's chars until len is 16
        data_length = ""  # Also create a variable for data length in format of "0004" for example
        if len(data) < 10:  # Adding zeros to data's 'length depend what size is it
            data_length = "000" + str(len(data))
        elif len(data) < 100:
            data_length = "00" + str(len(data))
        elif len(data) < 1000:
            data_length = "0" + str(len(data))
        elif len(data) < 10000:
            data_length = str(len(data))
        full_msg = cmd + DELIMITER + data_length + DELIMITER + data  # Returns all msg separated by "|"
        return full_msg
    else:
        return None


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occurred, returns None, None
    :param data: A parses' protocol message
    :type data: str
    return: A tuples contains command name and data field - the function should return 2 values
    :rtype: tuple
    """
    data = str(data)  # Make sure variable "data" is string
    if data == "":  # Make sure variable "data" isn't empty
        return None, None
    if not data[16] == DELIMITER and data[21] == DELIMITER:  # if data not includes | in the right index, then None
        return None, None
    parse_message_list = data.split(DELIMITER)  # A list made from data separated by |
    cmd = parse_message_list[0].replace(" ", "")  # Cmd = cmd without spaces
    data_length = parse_message_list[1].replace(" ", "")  # Data's length = itself without spaces
    if not data_length.isnumeric():  # Make sure Data's length is number only
        return None, None
    msg = parse_message_list[2]  # msg = msg
    # If cmd, data length, msg - all lengths are allowed then returns separated massage, else None:
    if len(cmd) <= CMD_FIELD_LENGTH and len(msg) <= MAX_DATA_LENGTH and len(data_length) <= LENGTH_FIELD_LENGTH:
        return cmd, msg
    else:
        return None, None


def split_data(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's data field delimiter (|#) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occurred, returns None
    :param msg: A string of expected fields in it
    :type msg: str
    :param expected_fields: A number of expected fields in it
    :type expected_fields: int
    return: list of fields if all ok. If some error occurred, returns None
    :rtype: list
    """
    if msg.count(DATA_DELIMITER) == expected_fields:  # If the number of # is same like we got in expected_fields:
        return msg.split(DATA_DELIMITER)  # Then returns list of the fields separated in #
    else:
        return [None]


def join_data(msg_fields):
    """
    Helper method. Gets a list, joins all of its fields to one string divided by the data delimiter.
    Returns: string that looks like cell1#cell2#cell3
    :param msg_fields: A string of expected fields in it
    :type msg_fields: list
    return: string that looks like cell1#cell2#cell3
    :rtype: str
    """
    msg = ""  # The string that will be returned
    for item in msg_fields:  # Add every item in list to str separated by "#"
        msg += str(item) + DATA_DELIMITER
    return msg[0:len(msg) - 1]  # Return the whole str separated by "#" without the last one

