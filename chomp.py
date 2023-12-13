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

safe = pygame.image.load("./assets/safe.png").convert()
safe = pygame.transform.scale(
    safe, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))
unsafe = pygame.image.load("./assets/unsafe.png").convert()
unsafe = pygame.transform.scale(
    unsafe, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))

safeBright = pygame.image.load("./assets/safe_bright.png").convert()
safeBright = pygame.transform.scale(
    safeBright, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))
unsafeBright = pygame.image.load("./assets/unsafe_bright.png").convert()
unsafeBright = pygame.transform.scale(
    unsafeBright, (constants.SQUARE_SIZE, constants.SQUARE_SIZE))

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

            # get hovered position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            hovered_row = mouse_y // constants.SQUARE_SIZE
            hovered_col = mouse_x // constants.SQUARE_SIZE

            if ([row, col] == [hovered_row, hovered_col]
                    and grid[row][col]
                    and [mouse_x, mouse_y] != [0, 0]
                    and pygame.mouse.get_focused()):
                image = safeBright

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
        if ("turn" in deserialized_data.keys()):
            game_data["turn"] = deserialized_data["turn"]
        if ("square_coord" in deserialized_data.keys()):
            update_grid(deserialized_data["square_coord"])
        if ("player_id" in deserialized_data.keys()):
            game_data["player_id"] = deserialized_data["player_id"]
        if ("lost" in deserialized_data.keys()):
            game_data["gameover"] = True
            if (deserialized_data["lost"] != game_data["player_id"]):
                game_data["winner"] = True
        if ("restart" in deserialized_data.keys()):
            restart()
    except socket.error as msg:
        # print("Server couldn't connect", msg)
        pass


def update_grid(square_coord):
    clicked_row, clicked_col = square_coord

    for row in range(clicked_row, constants.GRID_SIZE):
        for col in range(clicked_col, constants.GRID_SIZE):
            grid[row][col] = False


def display_message(message):
    text = font.render(message, True, constants.WHITE)
    screen.blit(text, (
        constants.WIDTH // 2 - text.get_width() // 2,
        constants.HEIGHT // 2 - text.get_height() * 4
    ))


def send_restart():
    try:
        serialized_data = pickle.dumps({"restart": True})
        s.sendall(serialized_data)
    except socket.error as msg:
        pass


def restart():
    global grid
    grid = [[True for _ in range(constants.GRID_SIZE)]
            for _ in range(constants.GRID_SIZE)]
    game_data["gameover"] = False
    game_data["winner"] = False


def button(message):
    font = pygame.font.Font(None, 36)
    width = 200
    height = 50
    button = pygame.Rect(constants.WIDTH / 2 - width/2,
                         constants.HEIGHT / 2 - height/2,
                         200, 50)

    pygame.draw.rect(screen, constants.WHITE, button)

    start_text = font.render(message, True, constants.BLACK)

    screen.blit(start_text, (button.x + 50, button.y + 15))

    return button


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
            if (game_data["turn"] == game_data["player_id"]
                    and grid[clicked_row][clicked_col]):
                send_data(clicked_row, clicked_col, "square_coord")

            if (game_data["gameover"]):
                restart_button = button("Restart")
                if (restart_button.collidepoint(mouse_x, mouse_y)):
                    send_restart()

    draw_grid()

    if (game_data["gameover"]):
        button("Restart")
        if (game_data["winner"]):
            display_message("You won!")
        else:
            display_message("You lost!")

    # Update the display
    pygame.display.flip()
