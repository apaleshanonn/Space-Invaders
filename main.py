import pygame

from db import setup_database
from managers.game_manager import GameManager
from managers.home import Home
from managers.leader import Leader
from managers.login import LoginManager
from managers.profile import Profile
from managers.settings import SettingsScreen
from sound import audio

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Space Invaders by Apale, Shanonn Pearl.")

if setup_database():
    print("DATABASE READY")
else:
    print("DATABASE SETUP FAILED")

audio.init()

login = LoginManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
game = GameManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

home = None
profile = None
leader = None
settings_screen = None
current_screen = "login"

clock = pygame.time.Clock()
running = True


def new_home():
    return Home(
        screen,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        login.logged_in_player,
    )


while running:

    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            if current_screen == "game":
                game.finish_session()

            running = False

    if current_screen == "login":

        login.handle_events(events)
        login.draw()

        if login.logged_in_player is not None:
            home = new_home()
            current_screen = "home"

    elif current_screen == "home":

        home.handle_events(events)
        home.draw()

        action = home.action
        home.action = None

        if action == "profile":
            profile = Profile(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player,
            )
            current_screen = "profile"

        elif action == "leaderboard":
            leader = Leader(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                login.logged_in_player,
            )
            current_screen = "leader"

        elif action == "settings":
            settings_screen = SettingsScreen(
                screen,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
            )
            current_screen = "settings"

        elif action == "play":
            game.current_player_id = login.logged_in_player["player_id"]
            game.player_name = login.logged_in_player["username"]
            game.start_again()
            current_screen = "game"

        elif action == "logout":
            login.reset()
            home = None
            profile = None
            leader = None
            settings_screen = None
            current_screen = "login"

    elif current_screen == "profile":

        profile.handle_events(events)
        profile.draw()

        if profile.player is not None:
            login.logged_in_player = profile.player

        if profile.action == "back":
            profile.action = None
            home = new_home()
            current_screen = "home"

        elif profile.action == "deleted":
            login.reset()
            profile = None
            home = None
            leader = None
            current_screen = "login"

    elif current_screen == "leader":

        leader.handle_events(events)
        leader.draw()

        if leader.action == "back":
            leader.action = None
            home = new_home()
            current_screen = "home"

    elif current_screen == "settings":

        settings_screen.handle_events(events)
        settings_screen.draw()

        if settings_screen.action == "back":
            settings_screen.action = None
            home = new_home()
            current_screen = "home"

    elif current_screen == "game":

        game.update(events)
        game.draw()

        if game.game_state == "back_home":
            game.game_state = "playing"
            home = new_home()
            current_screen = "home"

    pygame.display.update()
    clock.tick(60)

pygame.quit()