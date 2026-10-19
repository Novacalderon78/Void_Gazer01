import random
import math
from array import array
import pygame
import config


class DangerSounds:
    def __init__(self):
        self.alarm_channel = None
        self.engine_channel = None
        self.sounds = {}
        self.paused = False
        self.alarm_timer = 0
        self.warning = False
        self.firing = False
        self.engine_playing = False
        mixer = pygame.mixer.get_init()
        if not mixer or mixer[1] != -16:
            return
        try:
            pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(6)
            self.alarm_channel = pygame.mixer.Channel(4)
            self.engine_channel = pygame.mixer.Channel(5)
            # Short, cached tones need no extra sound files or libraries.
            for name, duration in (("alarm", 0.13), ("fire", 0.3), ("engine", 0.2)):
                samples = array("h")
                for index in range(round(mixer[0] * duration)):
                    t = index / mixer[0]
                    if name == "engine":
                        wave = math.sin(math.tau * 80 * t) + 0.3 * math.sin(math.tau * 240 * t)
                        envelope = 0.055
                    else:
                        frequency = 880 if name == "alarm" else 220 + t * 950
                        wave = math.sin(math.tau * frequency * t) + 0.4 * math.sin(math.tau * frequency * 1.5 * t)
                        envelope = 0.16 * min(1, t / 0.008, (duration - t) / 0.018)
                    value = round(max(-1, min(1, wave * envelope)) * 32767)
                    for channel in range(mixer[2]):
                        samples.append(value)
                self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())
        except (pygame.error, OSError, ValueError):
            self.sounds.clear()

    def play_alarm(self, name):
        if self.alarm_channel is not None and name in self.sounds:
            try:
                self.alarm_channel.play(self.sounds[name])
            except pygame.error:
                self.alarm_channel = None

    def update(self, boss, player, dt):
        if dt <= 0 or self.paused:
            return
        warning = boss is not None and boss.beam_warning
        firing = boss is not None and boss.beam_active
        if warning:
            self.alarm_timer -= dt
            if not self.warning or self.alarm_timer <= 0:
                self.play_alarm("alarm")
                self.alarm_timer = 0.14 if boss.timer < 0.6 else 0.34
        if firing and not self.firing:
            self.play_alarm("fire")
        self.warning, self.firing = warning, firing
        if player.nitro_active != self.engine_playing:
            self.engine_playing = player.nitro_active
            if self.engine_channel is not None and "engine" in self.sounds:
                try:
                    if self.engine_playing:
                        self.engine_channel.play(self.sounds["engine"], loops=-1, fade_ms=80)
                    else:
                        self.engine_channel.fadeout(100)
                except pygame.error:
                    self.engine_channel = None

    def set_paused(self, paused):
        if paused == self.paused:
            return
        self.paused = paused
        try:
            for channel in (self.alarm_channel, self.engine_channel):
                if channel is not None:
                    channel.pause() if paused else channel.unpause()
        except pygame.error:
            pass

    def stop(self):
        try:
            for channel in (self.alarm_channel, self.engine_channel):
                if channel is not None:
                    channel.stop()
                    channel.unpause()
        except pygame.error:
            pass
        self.paused = False
        self.warning = False
        self.firing = False
        self.engine_playing = False
        self.alarm_timer = 0


class EnemyDeathSounds:
    def __init__(self):
        self.sounds = []
        self.channels = []
        self.next_channel = 0
        self.paused = False
        if not pygame.mixer.get_init():
            return

        # Load death sounds once, rather than reading a file for every kill.
        for path in config.ENEMY_DEATH_SOUNDS:
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(0.45)
                self.sounds.append(sound)
            except (OSError, pygame.error):
                pass

        if self.sounds:
            try:
                # Dedicated voices: boss 0, enemies 1-2, player 3, alarm 4, nitro 5.
                pygame.mixer.set_reserved(3)
                self.channels = [pygame.mixer.Channel(1), pygame.mixer.Channel(2)]
            except pygame.error:
                self.channels = []

    def play(self):
        if self.paused or not self.sounds or not self.channels:
            return False
        try:
            index = self.next_channel
            for number, channel in enumerate(self.channels):
                if not channel.get_busy():
                    index = number
                    break
            self.channels[index].play(random.choice(self.sounds))
            # At most two death clips overlap. New kills replace the older voice.
            self.next_channel = (index + 1) % len(self.channels)
            return True
        except pygame.error:
            self.channels = []
            return False

    def set_paused(self, paused):
        if self.paused == paused:
            return
        self.paused = paused
        try:
            for channel in self.channels:
                if paused:
                    channel.pause()
                else:
                    channel.unpause()
        except pygame.error:
            self.channels = []

    def stop(self):
        try:
            for channel in self.channels:
                channel.stop()
                channel.unpause()
        except pygame.error:
            self.channels = []
        self.paused = False
        self.next_channel = 0


class PlayerDeathSound:
    def __init__(self):
        self.sound = None
        self.channel = None
        self.paused = False
        self.played = False
        if not pygame.mixer.get_init():
            return

        try:
            self.sound = pygame.mixer.Sound(str(config.PLAYER_DEATH_SOUND))
            self.sound.set_volume(0.7)
            # Keep this voice separate from boss and enemy sounds.
            pygame.mixer.set_num_channels(max(4, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(4)
            self.channel = pygame.mixer.Channel(3)
        except (OSError, pygame.error):
            self.sound = None
            self.channel = None

    def play(self):
        if self.played or self.paused or self.sound is None or self.channel is None:
            return False
        try:
            self.channel.play(self.sound)
            self.played = True
            return True
        except pygame.error:
            self.channel = None
            return False

    def set_paused(self, paused):
        if self.paused == paused:
            return
        self.paused = paused
        if self.channel is not None:
            try:
                if paused:
                    self.channel.pause()
                else:
                    self.channel.unpause()
            except pygame.error:
                self.channel = None

    def stop(self):
        if self.channel is not None:
            try:
                self.channel.stop()
                self.channel.unpause()
            except pygame.error:
                self.channel = None
        self.paused = False
        self.played = False


class BossSounds:
    def __init__(self):
        self.sounds = {}
        self.channel = None
        self.stage = "stopped"
        self.paused = False
        self.arrival_played = False
        self.roar_faded = False
        self.combat_timer = random.uniform(6, 10)

        if not pygame.mixer.get_init():
            return

        volumes = {"roar": 0.75, "arrival": 0.65, "combat": 0.65, "death": 1.0}
        for name, path in config.BOSS_SOUNDS.items():
            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(volumes[name])
                self.sounds[name] = sound
            except (OSError, pygame.error):
                # One missing sound should not silence the other boss sounds.
                pass

        try:
            pygame.mixer.set_reserved(1)
            self.channel = pygame.mixer.Channel(0)
        except pygame.error:
            self.channel = None

    def play(self, name):
        if self.channel is not None and name in self.sounds:
            try:
                self.channel.play(self.sounds[name])
                if self.paused:
                    self.channel.pause()
            except pygame.error:
                self.channel = None

    def start(self):
        self.stop()
        self.stage = "intro"
        self.play("roar")

    def update(self, boss, dt):
        if dt <= 0 or self.paused or boss is None:
            return
        if self.stage in ("stopped", "death") or boss.health <= 0:
            return

        elapsed = boss.intro_duration - boss.intro_timer
        fade_time = boss.approach_time + boss.arrival_time - 0.25
        if not self.roar_faded and elapsed >= fade_time:
            self.roar_faded = True
            if self.channel is not None:
                try:
                    self.channel.fadeout(200)
                except pygame.error:
                    self.channel = None

        if boss.arrival_landed and not self.arrival_played:
            self.arrival_played = True
            self.play("arrival")

        if boss.intro_timer > 0:
            return

        self.stage = "combat"
        self.combat_timer -= dt
        if self.combat_timer <= 0:
            try:
                busy = self.channel is not None and self.channel.get_busy()
            except pygame.error:
                self.channel = None
                busy = False
            if not busy:
                self.play("combat")
                self.combat_timer = random.uniform(6, 10)

    def defeated(self):
        if self.stage == "death":
            return
        self.stage = "death"
        if self.channel is not None:
            try:
                self.channel.stop()
            except pygame.error:
                self.channel = None
        self.play("death")

    def set_paused(self, paused):
        if paused == self.paused:
            return
        self.paused = paused
        if self.channel is not None:
            try:
                if paused:
                    self.channel.pause()
                else:
                    self.channel.unpause()
            except pygame.error:
                self.channel = None

    def stop(self):
        if self.channel is not None:
            try:
                self.channel.stop()
                self.channel.unpause()
            except pygame.error:
                self.channel = None
        self.stage = "stopped"
        self.paused = False
        self.arrival_played = False
        self.roar_faded = False
        self.combat_timer = random.uniform(6, 10)
