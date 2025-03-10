#!/usr/bin/python3


import socket
import sys
import time
import signal
import threading

DEBUG = 1

def establish_client_socket(server_host, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_host, server_port))
        print("Connected to the server.")
    #Exception handling
    except Exception as e:
        print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")
        return -1
    return client


def tcp_authentication(client):
    try:
                print(client.recv(1024).decode())
    except Exception as e:
        print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")
        return -1    
    for _ in range(10):
        username = input()
        if not username:
            print("Input is empty. Please provide valid input.")
        client.send(username.encode())
        response = client.recv(1024).decode().strip()
        print(response)
        if ("failed" in response):
            continue
        password = input()
        if not password:
                print("Input is empty. Please provide valid input.")
                password = input()
        client.send(password.encode())
        response = client.recv(1024).decode()
        print(response)
        if "Authentication successful" in response:
            return 0
    return -1

def receive_data(client_socket):
    try:
        while True:
            received_data = client_socket.recv(1024)
            if not received_data:
                break
            if "bye" in received_data.decode():
                print(received_data.decode())
                sys.exit(0)
            print(received_data.decode().strip())
    except ConnectionResetError:
        print("Connection reset by client.")
    except socket.timeout:
        pass
    except socket.error:
            pass
def play_guessing_game(client):
    #Background reception
    receive_thread = threading.Thread(target=receive_data, args=(client,))
    receive_thread.daemon = True  # Set as a daemon thread to exit when the main program exits
    receive_thread.start()

    while True:
        command = input()
        client.send(command.encode())       
        if  command.startswith("/exit"):
            receive_thread.join()
            # Close the client socket and exit
            break
    client.close()

def main_client(server_host, server_port):
    client=establish_client_socket(server_host, server_port)
    if client==-1:
        return -1
    client_tcp_authentification = tcp_authentication(client)

    if client_tcp_authentification==-1:
        return -1
    
    print("\u001b[34mTCP Handshake Established! You are now authenticated to the server.\u001b[37m")
    play_guessing_game(client)
    print("\u001b[32mClient ends\u001b[37m")



def handle_interrupt(signum, frame):
    print("\n\u001b[35mExiting gracefully.\u001b[37m")
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, handle_interrupt)


def main():
    argc = len(sys.argv[1:])
    if argc < 2:
        print("\u001b[32mInsufficient arguments!\u001b[37m")
        return
    try:
       server_host = str(sys.argv[1])
    except Exception:
        server_host = int(sys.argv[1])
    server_port = int(sys.argv[2])  
    print("\u001b[35mWelcome to the Client Program!\n\u001b[34mServer Port:\u001b[37m",server_port)
    main_client(server_host, server_port)

if __name__ == "__main__":
    main()