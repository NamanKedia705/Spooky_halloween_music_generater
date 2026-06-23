import pygame
import pygame_gui
import random
import threading
import time
import os
import tempfile
from audiocraft.models import MusicGen
import torch
# --- Constants ---
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WHITE = pygame.Color(255, 255, 255)
BLACK = pygame.Color(0, 0, 0)
BEAT_COLOR = pygame.Color(50, 50, 50)
BEAT_SELECTED_COLOR = pygame.Color(255, 0, 0)
BEAT_HIGHLIGHT_COLOR = pygame.Color(150, 100, 100, 200)

# --- Sound loading function ---
def load_sound(filename):
    """Load a sound file, or return a 'fake' sound object if it fails."""
    try:
        sound = pygame.mixer.Sound(filename)
    except pygame.error:
        print(f"Warning: Could not load sound file {filename}")
        class DummySound:
            def play(self): pass
        sound = DummySound()
    return sound
 
# --- Main application class ---
class SequencerApp:
    def __init__(self, manager):
        self.manager = manager
        
        # Sequencer data: 3 instruments, 8 steps
        self.beat_matrix = [[False for _ in range(8)] for _ in range(3)]
        self.instrument_names = ["Bass Drum", "Snare", "Hi-Hat"]
        self.current_step = -1
        self.is_playing = False
        self.tempo_bpm = 120
        self.halloween_playing = False
        self.stop_halloween_event = threading.Event()
        self.ai_playing = False
        self.stop_ai_event = threading.Event()
        self.current_ai_sound = None
        # Load MusicGen model once
        self.musicgen_model = MusicGen.get_pretrained('facebook/musicgen-medium')
        self.musicgen_model.set_generation_params(duration=16)
        self.musicgen_model.to(torch.device("cpu"))  # force CPU if no GPU
        # Create GUI elements
        self.create_gui_elements()
        self.load_sounds()

        # Audio thread control
        self.audio_thread = None
        self.stop_thread = threading.Event()

    def create_gui_elements(self):
        """Build the user interface."""
        # Step sequencer grid
        self.beat_buttons = []
        for i in range(3): # Rows for each instrument
            row_buttons = []
            for j in range(8): # Columns for each step
                x = 100 + j * 70
                y = 100 + i * 50
                button_rect = pygame.Rect(x, y, 50, 40)
                button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text="",
                    manager=self.manager
                )
                button.instrument_index = i
                button.step_index = j
                row_buttons.append(button)
            self.beat_buttons.append(row_buttons)

        # Instrument labels
        for i, name in enumerate(self.instrument_names):
            label_rect = pygame.Rect(10, 100 + i * 50, 80, 40)
            pygame_gui.elements.UILabel(
                relative_rect=label_rect,
                text=name,
                manager=self.manager
            )
            
        # Tempo slider
        # Tempo label
        label_rect = pygame.Rect(10, 300, 80, 20)
        pygame_gui.elements.UILabel(relative_rect=label_rect, text="Tempo:", manager=self.manager)

        # Tempo slider
        slider_rect = pygame.Rect(100, 300, 200, 20)
        self.tempo_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=slider_rect,
            start_value=120,
            value_range=(60, 240),
            manager=self.manager
        )

        # Tempo text input (right next to slider)
        tempo_input_rect = pygame.Rect(320, 300, 60, 25)
        self.tempo_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=tempo_input_rect,
            manager=self.manager
        )
        self.tempo_input.set_text(str(self.tempo_bpm))

        # Play/Stop buttons
        play_button_rect = pygame.Rect(10, 350, 100, 40)
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=play_button_rect,
            text="Play",
            manager=self.manager
        )
        
        stop_button_rect = pygame.Rect(120, 350, 100, 40)
        self.stop_button = pygame_gui.elements.UIButton(
            relative_rect=stop_button_rect,
            text="Stop",
            manager=self.manager
        )

        stop_halloween_rect = pygame.Rect(10, 470, 190, 40)
        self.stop_halloween_button = pygame_gui.elements.UIButton(
            relative_rect=stop_halloween_rect,
            text="Stop Halloween Track",
            manager=self.manager
        )
        # Convert to song button
        convert_button_rect = pygame.Rect(10, 425, 230, 40)
        self.convert_button = pygame_gui.elements.UIButton(
            relative_rect=convert_button_rect,
            text="Convert to Halloween Song",
            manager=self.manager
        )
                
        # Randomize Beat button
        randomize_button_rect = pygame.Rect(230, 350, 160, 40)
        self.randomize_button = pygame_gui.elements.UIButton(
            relative_rect=randomize_button_rect,
            text="Randomize Beat",
            manager=self.manager
        )
        
        # Generate AI Track button
        generate_button_rect = pygame.Rect(420, 450, 220, 40)
        self.generate_ai_button = pygame_gui.elements.UIButton(
            relative_rect=generate_button_rect,
            text="Generate AI Spooky Track",
            manager=self.manager
        )

    def load_sounds(self):
        """Loads sound effects into memory."""
        self.sounds = {
            "bass": load_sound("sounds/bass.wav"),
            "snare": load_sound("sounds/snare.wav"),
            "hihat": load_sound("sounds/hihat.wav"),
            "spooky_melodies": [
                load_sound("sounds/spooky1.wav"),
                load_sound("sounds/spooky2.wav"),
                load_sound("sounds/spooky3.wav")
             ]
        }
        self.instrument_sounds = [
            self.sounds["bass"],
            self.sounds["snare"],
            self.sounds["hihat"]
        ]

    def load_background(self):
        """Load the background image and scale it to fit the window."""
        try:
            bg = pygame.image.load("images/halloween_bg.jpg").convert()
            self.background = pygame.transform.scale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except Exception as e:
            print("Warning: could not load background image:", e)
            self.background = None
    
    def handle_event(self, event):
        """Processes user input events."""
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                # Handle sequencer button clicks
                if hasattr(event.ui_element, 'instrument_index'):
                    instr = event.ui_element.instrument_index
                    step = event.ui_element.step_index
                    self.beat_matrix[instr][step] = not self.beat_matrix[instr][step]
                # Handle control button clicks
                elif event.ui_element == self.play_button:
                    self.start_playback()
                elif event.ui_element == self.stop_button:
                    self.stop_playback()
                elif event.ui_element == self.convert_button:
                    self.stop_playback()
                    self.convert_to_halloween_song()
                elif event.ui_element == self.stop_halloween_button:
                    print("Stopping any AI or Halloween track...")
                    self.stop_halloween_event.set()
                    self.stop_ai_event.set()
                    if self.current_ai_sound:
                        self.current_ai_sound.stop()
                        self.current_ai_sound = None
                    self.stop_spooky_background()
                    self.halloween_playing = False
                    self.ai_playing = False
                    self.current_step = -1
                elif event.ui_element == self.randomize_button:
                    self.randomize_beat()
                elif event.ui_element == self.generate_ai_button:
                    # Stop any other tracks first
                    if self.halloween_playing:
                        self.stop_halloween_event.set()
                        self.halloween_playing = False
                    self.stop_playback()
                    # Launch AI track generation in a separate thread
                    threading.Thread(target=self.play_ai_track_from_pattern, daemon=True).start()

    def start_playback(self):
        """Starts the audio playback loop in a separate thread."""
        if not self.is_playing:
            self.is_playing = True
            self.stop_thread.clear()
            self.audio_thread = threading.Thread(target=self.playback_loop)
            self.audio_thread.start()
            
    def randomize_beat(self):
        """Randomly fills the beat grid with drum hits."""
        for i in range(3):  # 3 instruments
            for j in range(8):  # 8 steps
                # Randomly decide if a beat should be on (True) or off (False)
                self.beat_matrix[i][j] = random.choice([True, False])

        print("Random drum pattern generated!")

    def stop_playback(self):
        """Stops the audio playback loop."""
        if self.is_playing:
            self.is_playing = False
            self.stop_thread.set()
            if self.audio_thread:
                self.audio_thread.join()
            self.current_step = -1

    def playback_loop(self):
        while not self.stop_thread.is_set():
            self.current_step = (self.current_step + 1) % 8
            
            for i in range(3):
                if self.beat_matrix[i][self.current_step]:
                    self.instrument_sounds[i].play()

            # Sleep but can be interrupted
            if self.stop_thread.wait(timeout=60.0 / self.tempo_bpm / 2):
                break

    def convert_to_halloween_song(self):
        """Start the Halloween song in a new thread."""
        if self.halloween_playing:
            return  # Already playing

        self.halloween_playing = True
        self.stop_halloween_event.clear()
        threading.Thread(target=self._halloween_song_loop, daemon=True).start()

    def _halloween_song_loop(self):
        """Actual Halloween song loop."""
        print("Mixing your beat with spooky sounds...")
        self.play_spooky_background()

        total_steps = 8
        for _ in range(16):  # Repeat 16 steps
            if self.stop_halloween_event.is_set():
                break
            for step in range(total_steps):
                if self.stop_halloween_event.is_set():
                    break
                for instr in range(3):
                    if self.beat_matrix[instr][step]:
                        self.instrument_sounds[instr].play()
                # Sleep based on tempo, but can wake early if stop pressed
                if self.stop_halloween_event.wait(timeout=60.0 / self.tempo_bpm / 2):
                    break  # Stop was pressed

        self.stop_spooky_background()
        time.sleep(0.1)  # short delay to prevent abrupt cutoff
        self.halloween_playing = False
        self.current_step = -1
        print("Halloween song completed or stopped.")

    def play_spooky_background(self):
        """Play a random spooky melody in the background."""
        self.current_spooky = random.choice(self.sounds["spooky_melodies"])
        print("Playing spooky melody:")
        self.current_spooky.play(loops=-1)  # loop infinitely

    def stop_spooky_background(self):
        """Stop the currently playing spooky melody."""
        if hasattr(self, "current_spooky"):
            self.current_spooky.stop()
            print("Stopped spooky melody")

    def update_gui(self):
        """Updates tempo and visuals."""
        # --- TEMPO LOGIC ---

        # Detect if user is typing (box is focused)
        if self.tempo_input.is_focused:
            try:
                # Try to parse the typed number
                typed_value = int(self.tempo_input.get_text())
                if 60 <= typed_value <= 240:
                    self.tempo_bpm = typed_value
                    self.tempo_slider.set_current_value(self.tempo_bpm)
            except ValueError:
                # Ignore invalid text while typing
                pass
        else:
            # If not typing, follow the slider value
            slider_value = int(self.tempo_slider.get_current_value())
            if slider_value != self.tempo_bpm:
                self.tempo_bpm = slider_value
                self.tempo_input.set_text(str(self.tempo_bpm))

        # --- BUTTON COLORS ---
        for i in range(3):
            for j in range(8):
                button = self.beat_buttons[i][j]

                if self.is_playing and j == self.current_step:
                    color = BEAT_HIGHLIGHT_COLOR
                elif self.beat_matrix[i][j]:
                    color = BEAT_SELECTED_COLOR
                else:
                    color = BEAT_COLOR

                if button.colours['normal_bg'] != color:
                    button.colours['normal_bg'] = color
                    button.colours['hovered_bg'] = color
                    button.colours['active_bg'] = color
                    button.rebuild()
    def describe_pattern(self):
        """Generate a text description of the beat pattern to guide AI generation."""
        total_steps = len(self.beat_matrix[0]) * len(self.beat_matrix)
        hits = sum(sum(row) for row in self.beat_matrix)
        density = hits / total_steps

        # Decide mood from how dense the beat is
        if density < 0.25:
            mood = "slow and eerie"
        elif density < 0.6:
            mood = "steady and suspenseful"
        else:
            mood = "intense and chaotic"
        # Describe which instruments are active
        active_instruments = [name for i, name in enumerate(self.instrument_names) if any(self.beat_matrix[i])]
        instruments_desc = ", ".join(active_instruments) if active_instruments else "no percussion"
        description = f"A {mood} spooky melody at {self.tempo_bpm} BPM, matching {instruments_desc} rhythm."
        return description
    def play_ai_track_from_pattern(self):
        """Generate a spooky track using MusicGen and play it in real-time."""
        description = self.describe_pattern()
        self.ai_playing = True
        self.stop_ai_event.clear()

        try:
            print("Generating AI spooky track with MusicGen...")
            
            # Generate audio tensor
            wav = self.musicgen_model.generate([description])
            wav = wav.cpu().numpy()[0]  # convert tensor to numpy array

            # Save to a temporary WAV file
            import soundfile as sf
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(tmp_file.name, wav, samplerate=32000)  # MusicGen default is 32 kHz
            tmp_file.close()

            # Play using pygame
            self.current_ai_sound = pygame.mixer.Sound(tmp_file.name)
            self.current_ai_sound.play(loops=-1)
            print("AI track playing...")

            # Overlay drum pattern for same number of bars
            total_steps = 8
            bars = 16
            for _ in range(bars):
                if self.stop_ai_event.is_set():
                    break
                for step in range(total_steps):
                    if self.stop_ai_event.is_set():
                        break
                    for i in range(3):
                        if self.beat_matrix[i][step]:
                            self.instrument_sounds[i].play()
                    if self.stop_ai_event.wait(timeout=60.0 / self.tempo_bpm / 2):
                        break

            # Stop AI track
            self.current_ai_sound.stop()
            self.ai_playing = False
            self.current_ai_sound = None
            print("AI spooky track stopped.")

        except Exception as e:
            print("Error generating AI track:", e)
            self.ai_playing = False

def main():
    """Main function to run the application."""
    pygame.init()
    pygame.mixer.init()  # Ensure the mixer is initialized properly
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Halloween Step Sequencer")
    clock = pygame.time.Clock()

    ui_manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT))
    app = SequencerApp(ui_manager)
    app.load_background()
    
    is_running = True
    while is_running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            # process events *first* so text boxes & sliders work
            ui_manager.process_events(event)
    
            # then handle custom app logic
            app.handle_event(event)
        
        ui_manager.update(time_delta)
        app.update_gui()

        if app.background:
            screen.blit(app.background, (0, 0))
        else:
            screen.fill(WHITE)

        ui_manager.draw_ui(screen)
        pygame.display.update()

    app.stop_playback()
    pygame.quit()

if __name__ == "__main__":
    main()
