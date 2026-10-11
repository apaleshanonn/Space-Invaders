import pygame

from settings_manager import load_settings


class AudioManager:
    MUSIC = "assets/sounds/shamusic.mp3"
    HIT = "assets/sounds/shallet.mp3"
    CLICK = "assets/sounds/shabutton.mp3"

    def __init__(self):
        self.ready = False
        self.music_failed = False
        self.hit = None
        self.click = None
        self.settings = load_settings()

    def init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.ready = True
        except pygame.error as error:
            print(f"Audio disabled: {error}")
            return

        self.hit = self._load(self.HIT)
        self.click = self._load(self.CLICK)
        self.apply()

    def _load(self, path):
        try:
            return pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError):
            print(f"Sound file missing: {path}")
            return None

    def volume(self):
        value = self.settings.get("sound_volume", 50)
        return max(0, min(100, value)) / 100.0

    def apply(self, settings=None):
        if settings is not None:
            self.settings = settings

        if not self.ready:
            return

        volume = self.volume()

        pygame.mixer.music.set_volume(volume * 0.7)

        for sound in (self.hit, self.click):
            if sound:
                sound.set_volume(volume)

        self.start_music()

    def start_music(self):
        if not self.ready:
            return

        if self.settings.get("music_enabled", True):
            if self.music_failed or pygame.mixer.music.get_busy():
                return

            try:
                pygame.mixer.music.load(self.MUSIC)
                pygame.mixer.music.play(-1)
            except (pygame.error, FileNotFoundError):
                self.music_failed = True
                print(f"Music file missing: {self.MUSIC}")
        else:
            pygame.mixer.music.stop()

    def _play(self, sound):
        if (
            self.ready
            and sound
            and self.settings.get("sound_enabled", True)
        ):
            sound.play()

    def play_click(self):
        self._play(self.click)

    def play_hit(self):
        self._play(self.hit)


audio = AudioManager()