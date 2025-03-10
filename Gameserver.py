#!/usr/bin/python3

from socket import *
import sys
import threading
import random
import signal #to close program gracefully 
import time
import multiprocessing


room_lock = threading.Lock()
game_semaphore = threading.Semaphore(2)
global server_stopped
server_stopped=False

shared_guesses = multiprocessing.RawArray('i', [-1, -1])

# Initialize the game_rooms dictionary with the shared memory array
# Define dictionary to store game rooms + their players + their guesses 

game_rooms = {room_num: {"player1": None, "player2": None, "shared_guesses": shared_guesses}
             for room_num in range(1, 11)}

DEBUG = 1

# Function to handle the /list command

def handle_list_command(client_socket):
    player_counts = [2 if room["player1"] is not None and room["player2"] is not None else 1 if room["player1"] is not None or room["player2"] is not None else 0 for room in game_rooms.values()]
    response = "3001 {} {}\n".format(len(game_rooms), " ".join(str(count) for count in player_counts))
    client_socket.send(response.encode())

def handle_enter_command(client_socket, target_room, game_lock):
    if target_room not in game_rooms:
        # Handle invalid room number
        client_socket.send(b"3010 Invalid room number\n")
        return -1

    with game_lock:
        room = game_rooms[target_room]
        if room["player1"] is None:
            room["player1"] = client_socket
            client_socket.send(b"3011 Wait\n")
        elif room["player2"] is None:
            room["player2"] = client_socket
            other_client_socket = room["player1"] 
            client_socket.send(b"3012 Game started. Please guess true or false\n")
            other_client_socket.send(b"3012 Game started. Please guess true or false\n")
        else:
            client_socket.send(b"3013 The Room is full\n")
            return -1
    handle_game(room,client_socket)
    return 0


def handle_exit_command(client_socket):
    client_socket.send(b"4001 Bye bye\n")
    # Close the client socket
    client_socket.close()

def individual_guess_game(client_socket, player_guess):
    random_choice = random.choice([0, 1])
    if (random_choice == player_guess):
        client_socket.send("3021 You are the winner\n".encode())
    else:
        client_socket.send("3022 You lost!\n".encode())

def process_guess(received_guess):
    if "true" in received_guess:
        return 1
    elif "false" in received_guess:
        return 0
    return -2


def handle_game(room,client_socket):
    game_semaphore.acquire()
    def receive_data():
        try:
            received_data = client_socket.recv(1024)
            if received_data:
                received_guess = received_data.decode().strip().lower()
                if received_guess.startswith("/guess "):
                    guess = process_guess(received_guess)
                    if room["player1"] == client_socket:
                        room["shared_guesses"][0] = guess
                    else:
                        room["shared_guesses"][1] = guess
                    print("Player guess received!")
                else:
                    client_socket.send(f"4002 Unrecognized message\n".encode())
        except Exception as e:
            pass
    # Create a thread to receive data from the client
    receive_thread = threading.Thread(target=receive_data)
    receive_thread.start()
    try:
        print("\u001b[35mPlayer entered the room!\u001b[37m")
        while (room["shared_guesses"][0] == -1) or (room["shared_guesses"][1] == -1) :
            time.sleep(1)
        while (room["shared_guesses"][0] > -1) and (room["shared_guesses"][1] > -1) :
            first_player_guess = room["shared_guesses"][0]
            second_player_guess = room["shared_guesses"][1]
            if first_player_guess ==  second_player_guess:
                client_socket.send("3023 The result is a tie\n".encode())
                return
            else:
                individual_guess_game(client_socket,first_player_guess)
                return
    except Exception as e:
            print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")

    finally:
        room["player1"]=None
        room["player2"]=None
        print("\u001b[33mCurrent Game ended! Rooms Cleared :)\u001b[37m")
        game_semaphore.release()



def read_user_info_file(file_path):
    user_info = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    user, password = line.strip().split(':')
                    user_info[user] = password
                except ValueError:
                    print(f"Error while parsing line: {line}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return -1
    return user_info

def tcp_authenticate(client_socket,user_info):
    client_ip = client_socket.getpeername()
    print(f"\u001b[32mAccepted connection from {client_ip}\u001b[37m")

# Authenticate the client
    auth_status = False
    try:
        client_socket.send("Please input your username:".encode())
    except Exception as e:
        print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")
        return -1

    for i in range (10):
        try:
            # Receive and handle the username
            username = client_socket.recv(1024).decode().strip()
            if not username:
                client_socket.send("Please input your username:".encode())
                continue
            print("Username received:", username)

            # Check if the username exists
            if username not in user_info:
                try:
                    client_socket.send(b"1002 Authentication failed.\nPlease input your username:")
                    print("Username not in user_info")
                    continue
                except Exception as e:
                    print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")

            # Receive and handle password
            client_socket.send(b"Please input your password: ")
            password = client_socket.recv(1024).decode()
            print("Password received:", password)

            # Check if the password matches the username
            if user_info[username] == password:
                client_socket.send(b"1001 Authentication successful!\n")
                print("\u001b[32mAuthentication successful!\u001b[37m")
                return 0
            else:
                client_socket.send(b"1002 Authentication failed.\nPlease input your username:")
                print("Authentication failed. Please try again.")
                continue
        except ConnectionResetError:
            print(f"Connection from {client_ip} was reset by the peer.")
            return -1
        except Exception as e:
            print(f"\u001b[31mUnexepcted error occurred: {e}\u001b[37m")
            return -1


# Function to handle client connections
def handle_client(client_socket, user_info):
    authentification=tcp_authenticate(client_socket,user_info)
    if authentification==-1:
        return -1
    
    while not server_stopped:
        try:
            # Receive client commands
            command = client_socket.recv(1024).decode().strip()
            client_ip = client_socket.getpeername()  # Get the client's IP address
            if command.startswith("/list"):
                # Handle the /list command
                handle_list_command(client_socket)
            elif command.startswith("/enter"):
                # split into 2 enter command
                parts = command.split()
                if len(parts) == 2:
                    try:
                        target_room = int(parts[1])
                        handle_enter_command(client_socket, target_room,room_lock)
                    except ValueError:
                        client_socket.send(b"Invalid room number format.\n")
                else:
                    client_socket.send(b"Invalid /enter command format.\n")
            elif command.startswith("/exit"):
        # Handle the /exit command
                handle_exit_command(client_socket)
                print("4001 bye bye!")
            elif command.startswith("/guess"):
                client_socket.send(b"3024 You are not in a game. Use /enter to join a game.\n")

            else:
                client_socket.send(b"4002 Unrecognized message\n")
        except ConnectionResetError:
            print(f"Connection from {client_ip} was reset by the peer.")
            break
        except Exception as e:
                print(f"\u001b[34mConnection disconnected\u001b[37m")
                break


def sigint_handler(signum, frame):
    server_stopped = True
    print("\n\u001b[35mServer is shutting down. Closing connections...\u001b[37m")
    # Close the server socket and all client sockets
    sys.exit(0)

# Register the signal handler for KeyboardInterrupt (Control+C)
signal.signal(signal.SIGINT, sigint_handler)

def main_server(serverPort, user_info_path):
    server = socket(AF_INET, SOCK_STREAM)
    try:
        server.bind(("", serverPort))
    except OSError as e:
        print(f"\u001b[31mOSError: {e} Exiting\u001b[37m")
        return
    server.listen(5)
    print(f"\u001b[33mServer listening on port {serverPort}\u001b[37m")

    user_info = read_user_info_file(user_info_path)
    if user_info == -1:
        return

    while True:
        client_socket, client_addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, user_info))
        client_thread.start()
    
def main():
    argc = len(sys.argv[1:])
    print("\u001b[35mWelcome to Server\u001b[37m")
    if argc < 2:
        print("Insufficient arguments!")
        return
    try:
        listen_port = int(sys.argv[1])
    except ValueError:
        print("Invalid port number. Please provide a valid integer for the port.")
        return
    user_info_path = sys.argv[2]
    main_server(listen_port, user_info_path)

if __name__ == "__main__":
    main()
