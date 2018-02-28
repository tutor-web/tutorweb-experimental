import socket

def current():
    """
    Return the current host, making sure it exists in the database first
    """
    # TODO: Check DB
    return socket.getfqdn()
