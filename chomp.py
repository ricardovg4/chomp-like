import socket
import pygame
import sys
import pickle
import constants

pygame.init()

game_data = {
    "player_id": 0,
    "turn": False,
    "gameover": False,
    "winner": 0,
}
running = True

# Initialize window
screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))
pygame.display.set_caption("Chomp")
font = pygame.font.Font(None, 72)
safe = pygame.image.load("./assets/safe2.png").convert()
safe = pygame.transform.scale(
    safe, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))
unsafe = pygame.image.load("./assets/unsafe1.png").convert()
unsafe = pygame.transform.scale(
    unsafe, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))

s = socket.socket()
try:
    s.connect((constants.HOST, constants.PORT))
    # should use threads for blocking instead
    s.setblocking(False)
except socket.error as msg:
    print("Server couldn't connect", msg)

# Create a 2D array
grid = [[True for _ in range(constants.GRID_SIZE)]
        for _ in range(constants.GRID_SIZE)]


def draw_grid():
    for row in range(constants.GRID_SIZE):
        for col in range(constants.GRID_SIZE):
            image = safe if grid[row][col] else unsafe
            screen.blit(image,
                        (col * constants.SQUARE_SIZE,  # posx
                         row * constants.SQUARE_SIZE),  # posy
                        )


def send_data(clicked_row, clicked_col, key):
    try:
        serialized_data = pickle.dumps({str(key): [clicked_row, clicked_col]})
        s.sendall(serialized_data)
        data = s.recv(1024)
        deserialized_data = pickle.loads(data)
        print(deserialized_data)
        # s.close()
    except socket.error as msg:
        # print("Server couldn't connect", msg)
        pass


# should fix with threads...
def receive():
    try:
        data = s.recv(1024)
        deserialized_data = pickle.loads(data)
        print(deserialized_data)
        if ("square_coord" in deserialized_data.keys()):
            update_grid(deserialized_data["square_coord"])
        if ("player_id" in deserialized_data.keys()):
            game_data["player_id"] = deserialized_data["player_id"]
        if ("lost" in deserialized_data.keys()):
            game_data["gameover"] = True
            if (deserialized_data["lost"] != game_data["player_id"]):
                game_data["winner"] = True
    except socket.error as msg:
        # print("Server couldn't connect", msg)
        pass


def update_grid(square_coord):
    clicked_row, clicked_col = square_coord

    for row in range(clicked_row, constants.GRID_SIZE):
        for col in range(clicked_col, constants.GRID_SIZE):
            grid[row][col] = False


def display_message(message):
    text = font.render(message, True, constants.BLACK)
    screen.blit(text, (
        constants.WIDTH // 2 - text.get_width() // 2,
        constants.HEIGHT // 2 - text.get_height() // 2
    ))


# Main game loop
while running:
    pygame.time.delay(10)
    receive()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            s.close()
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            clicked_col = mouse_x // constants.SQUARE_SIZE
            clicked_row = mouse_y // constants.SQUARE_SIZE

            # Check if the clicked square is valid
            if grid[clicked_row][clicked_col]:
                send_data(clicked_row, clicked_col, "square_coord")

    draw_grid()

    if (game_data["gameover"]):
        if (game_data["winner"]):
            display_message("You won!")
        else:
            display_message("You lost!")

    # Update the display
    pygame.display.flip()
