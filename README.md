# Cryptographic-Guessing-Game
Most notable:

0. Status = Complete
1. Multiple Authentification supported 
2. Semaphores to block room access + room clearing after game end
4. Graceful closing with signals
5. Messages may differ slightly from assignment prompt
6. Added ASCII Colors
7.See attached screenshot for use example :)

Full Description
This is a server-client based guessing game implemented in Python. The game allows multiple clients to connect to the server and participate in a guessing game. The server manages game rooms where players can join and compete against each other by guessing true or false.

Prerequisites
Python 3.x
socket module
sys module
threading module
random module
signal module
time module
multiprocessing module

Usage

Start the server by running the gameserver.py script: python gameserver.py <port> <user_info_file>
<port>: The port number on which the server should listen for incoming connections.
<user_info_file>: The path to a file containing user information in the format username:password.
Clients can connect to the server using any TCP client software (e.g., Telnet).
Once connected, clients can interact with the server by sending commands.
/list: Lists the available game rooms and the number of players in each room.
/enter <room_number>: Enters a game room specified by <room_number>.
/exit: Exits the current game room or disconnects from the server.
/guess <true|false>: Submits a guess of either "true" or "false" in the current game room.
The server handles the game logic, including managing players, starting games, and determining the winner.
The game ends when there is a winner or a tie, and the players can enter a new game room or exit the server.

Implementation Details
The server uses multithreading to handle multiple client connections concurrently. Each client connection is handled by a separate thread. The server maintains a dictionary of game rooms, where each room consists of two players and a shared array to store their guesses.
