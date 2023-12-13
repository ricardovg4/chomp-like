import socket
import pickle
import constants
import threading

game_started = False
players = {
    "1": 0,
    "2": 0
}
turn = 1


def handle_client(s, clients, addr):
    global turn
    player_number = int(list(players.keys())[
                        list(players.values()).index(addr)])
    initial_data = {
        "player_id": player_number,
        "turn": turn,
    }

    s.sendall(pickle.dumps(initial_data))

    while True:
        data = s.recv(1024)
        if not data:
            break
        deserialized_data = pickle.loads(data)
        print(deserialized_data)

        if (game_started):
            if ("square_coord" in deserialized_data.keys() and
                    deserialized_data["square_coord"] == [0, 0]):
                deserialized_data.update({"lost": player_number})

            turn = 1 if turn == 2 else 2
            deserialized_data.update({"turn": turn})

            serialized_data = pickle.dumps(deserialized_data)
            broadcast_data(serialized_data, clients)

    # Remove the disconnected client from the list
    clients.remove(s)
    s.close()
    # global player_number
    # player_number -= 1


def broadcast_data(message, clients):
    # print(clients)
    for client in clients:
        try:
            client.sendall(message)
        except Exception as e:
            print(f"Error broadcasting data: {e}")


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((constants.HOST, constants.PORT))
s.listen(2)

clients = []
player_number = 1

while player_number <= 2:
    conn, addr = s.accept()
    print(
        f"Accepted connection from Player {player_number} - {addr}")

    clients.append(conn)

    players[str(player_number)] = addr

    client_handler = threading.Thread(
        target=handle_client, args=(conn, clients, addr))
    client_handler.start()

    player_number += 1

    if (player_number > 2):
        game_started = True