import pygame
import sys
import os
import random
import gamedata as g

# --------------------------- Initialize Pygame Mixer and Pygame --------------------------- #
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()

# --------------------------- Constants and Configuration --------------------------- #
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
FPS = 60

# Define colors
TEXT_COLOR = pygame.Color('brown')
BACKGROUND_COLOR = pygame.Color('black')
SIGN_BACKGROUND_COLOR = pygame.Color('dimgray')  # Background color for the welcome sign
PAUSE_OUTLINE_COLOR = (255, 255, 255)  # Light brown color for outline
PAUSE_TEXT_COLOR = (255, 255, 255)     # Light brown color for texts

# --------------------------- Paths --------------------------- #
script_dir = os.path.dirname(os.path.abspath(__file__))
images_folder_path = os.path.join(script_dir, 'images')
music_folder = os.path.join(script_dir, 'music')

# Supported music formats
SUPPORTED_MUSIC_FORMATS = ['.ogg', '.mp3', '.wav']

# --------------------------- Fonts --------------------------- #
font = pygame.font.SysFont("sans-serif", 40)
pause_font = pygame.font.SysFont("sans-serif", 30)

# Load a custom cool font for song titles
try:
    song_font_path = os.path.join(images_folder_path, 'cool_font.ttf')  # Ensure 'cool_font.ttf' exists in the images folder
    song_font = pygame.font.Font(song_font_path, 24)  # 24 is the font size
except FileNotFoundError:
    print("Custom font 'cool_font.ttf' not found. Using default system font.")
    song_font = pygame.font.SysFont("arial", 24)

# --------------------------- Initialize Mute and Pause States --------------------------- #
is_muted = False  # Initialize is_muted early to avoid NameError
previous_volume = 0.5  # Default previous volume

is_paused = False  # Initialize is_paused to track music pause state

# --------------------------- New Variables for Song Title Display --------------------------- #
current_song_title = ""  # Stores the current song title

# --------------------------- Button Classes --------------------------- #
class Button:
    def __init__(self, x, y, image, scale=1):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.clicked = False

    def draw(self, surface):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        surface.blit(self.image, self.rect)

        return action

class SettingsButton(Button):
    def __init__(self, x, y, image, scale=0.18, rotation_speed=1):
        super().__init__(x, y, image, scale)
        self.rotation_speed = rotation_speed
        self.angle = 0
        self.original_scaled_image = self.image

    def update(self):
        self.angle = (self.angle - self.rotation_speed) % 360
        rotated_image = pygame.transform.rotate(self.original_scaled_image, self.angle)
        self.image = rotated_image
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def draw(self, surface):
        self.update()
        return super().draw(surface)

# --------------------------- Slider Class --------------------------- #
class Slider:
    def __init__(self, x, y, width, height, min_val=0.0, max_val=1.0, initial_val=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.handle_radius = height // 2
        self.handle_color = pygame.Color('white')
        self.track_color = pygame.Color('lightgray')
        self.fill_color = pygame.Color('skyblue')  # Color for the filled portion
        self.dragging = False

    def draw(self, surface):
        # Draw the track
        pygame.draw.rect(surface, self.track_color, self.rect)

        # Calculate handle position
        handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        handle_y = self.rect.centery

        # Draw the filled portion of the slider
        filled_rect = pygame.Rect(self.rect.x, self.rect.y, handle_x - self.rect.x, self.rect.height)
        pygame.draw.rect(surface, self.fill_color, filled_rect)

        # Draw the handle
        pygame.draw.circle(surface, self.handle_color, (handle_x, handle_y), self.handle_radius)

    def handle_event(self, event):
        global is_muted, previous_volume
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                handle_x = self.rect.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
                handle_y = self.rect.centery
                distance = ((mouse_pos[0] - handle_x) ** 2 + (mouse_pos[1] - handle_y) ** 2) ** 0.5
                if distance <= self.handle_radius:
                    self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_x = event.pos[0]
                mouse_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
                relative_x = mouse_x - self.rect.x
                self.value = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)
                pygame.mixer.music.set_volume(self.value)
                if self.value == 0:
                    if not is_muted:
                        previous_volume = self.value  # Save the volume before muting
                    is_muted = True
                else:
                    if is_muted:
                        is_muted = False
                        pygame.mixer.music.set_volume(self.value)
                        previous_volume = self.value  # Update the previous_volume when unmuted

# --------------------------- Initialize Volume Slider --------------------------- #
slider_width = 300
slider_height = 20
popup_width = 600
popup_height = 400
popup_x = (SCREEN_WIDTH - popup_width) // 2
popup_y = (SCREEN_HEIGHT - popup_height) // 2
slider_x = popup_x + (popup_width - slider_width) // 2
slider_y = popup_y + 200  # Adjust as needed for layout

current_volume = 0.5  # Default volume
volume_slider = Slider(slider_x, slider_y, slider_width, slider_height, 0.0, 1.0, current_volume)

# --------------------------- Initialize Music --------------------------- #
def load_music():
    music_files = []
    if not os.path.isdir(music_folder):
        print(f"Music folder '{music_folder}' does not exist.")
        return music_files

    for file in os.listdir(music_folder):
        if any(file.lower().endswith(ext) for ext in SUPPORTED_MUSIC_FORMATS):
            full_path = os.path.join(music_folder, file)
            music_files.append(full_path)

    if not music_files:
        print(f"No supported music files found in {music_folder}.")
    else:
        random.shuffle(music_files)
    return music_files

music_files = load_music()
current_music_index = 0

def play_music(index):
    global current_song_title  # Declare as global to modify
    if music_files:
        try:
            pygame.mixer.music.load(music_files[index])
            pygame.mixer.music.set_volume(volume_slider.value if not is_muted else 0.0)
            pygame.mixer.music.play()

            # Extract song title from file name
            song_path = music_files[index]
            song_name = os.path.splitext(os.path.basename(song_path))[0]
            current_song_title = song_name

            print(f"Now playing: {song_name}")
        except pygame.error as e:
            print(f"Failed to load the music file '{music_files[index]}': {e}")

if music_files:
    play_music(current_music_index)

# --------------------------- Initialize Pygame Display --------------------------- #
screen = pygame.display.set_mode(SCREEN_SIZE)
pygame.display.set_caption("Blackjack Game")

# -------------------------- Utility Functions -------------------------- #
def fade(width, height):
    fade_surface = pygame.Surface((width, height))
    fade_surface.fill((0, 0, 0))
    for alpha in range(0, 300, 5):
        fade_surface.set_alpha(alpha)
        
        # Draw the game screen without the song title
        screen.blit(saloon_background, (background_x, 0))
        draw_welcome_sign()
        start_button.draw(screen)
        settings_button.draw(screen)
        
        # Blit the fade surface
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        pygame.time.delay(5)

def redrawWindow():
    screen.fill((255,255,255))
    screen.blit(saloon_background, (background_x, 0))
    settings_button.draw(screen)

def draw_centered_text(text, font, text_col, surface, center_x, center_y):
    img = font.render(text, True, text_col)
    text_rect = img.get_rect(center=(center_x, center_y))
    surface.blit(img, text_rect)

def place_welcome(x, y):
    screen.blit(welcome, (x, y))

# -------------------------- Game State Functions -------------------------- #
def draw_pause_menu():
    popup_width, popup_height = 400, 200
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2

    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    popup_surface = pygame.Surface((popup_width, popup_height))
    popup_surface.set_alpha(220)
    popup_surface.fill((50, 50, 50))
    screen.blit(popup_surface, (popup_x, popup_y))

    pygame.draw.rect(screen, TEXT_COLOR, popup_rect, 5)

    draw_centered_text("Paused", small_font, TEXT_COLOR, screen, SCREEN_WIDTH // 2, popup_y + 50)
    draw_centered_text("Press ESC to Resume", small_font, TEXT_COLOR, screen, SCREEN_WIDTH // 2, popup_y + 130)

    if current_song_title:
        draw_centered_text(current_song_title, small_font, TEXT_COLOR, screen, SCREEN_WIDTH // 2, popup_y + 160)

def run_game():
    screen.blit(poker_table_background, (SCREEN_WIDTH // 2 - poker_table_background.get_width() // 2, SCREEN_HEIGHT //  1 - poker_table_background.get_height()))
    draw_centered_text("Dealer must stand on 17 and must draw to 16", medium_font, TEXT_COLOR, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# -------------------------- Card Placement Function -------------------------- #
def place_card(x, y):
    screen.blit(card, (x, y))

# -------------------------- Music Functions -------------------------- #
def load_music():
    music_files = []
    if not os.path.isdir(music_folder):
        print(f"Music folder '{music_folder}' does not exist.")
        return music_files

    for file in os.listdir(music_folder):
        if any(file.lower().endswith(ext) for ext in SUPPORTED_MUSIC_FORMATS):
            full_path = os.path.join(music_folder, file)
            music_files.append(full_path)

    if not music_files:
        print(f"No supported music files found in {music_folder}.")
    else:
        random.shuffle(music_files)
    return music_files

def play_music(index):
    global current_song_title
    if music_files:
        try:
            pygame.mixer.music.load(music_files[index])
            pygame.mixer.music.play()
            current_song_title = os.path.splitext(os.path.basename(music_files[index]))[0]
            print(f"Now playing: {current_song_title}")
        except pygame.error as e:
            print(f"Failed to load the music file '{music_files[index]}': {e}")

def play_next_song():
    global current_music_index
    if music_files:
        current_music_index += 1
        if current_music_index >= len(music_files):
            random.shuffle(music_files)
            current_music_index = 0
        play_music(current_music_index)

def play_previous_song():
    global current_music_index
    if music_files:
        current_music_index -= 1
        if current_music_index < 0:
            current_music_index = len(music_files) - 1
        play_music(current_music_index)
# -------------------------- Load Images -------------------------- #
def load_image(filename):
    path = os.path.join(images_folder_path, filename)
    try:
        image = pygame.image.load(path).convert_alpha()
        return image
    except FileNotFoundError:
        print(f"Image '{filename}' not found in {images_folder_path}.")
        pygame.quit()
        sys.exit()

# Load backgrounds
saloon_background = load_image('saloon_background.jpg')
poker_table_background = load_image('table.jpg')

# Load Game Logo
game_logo = load_image('welcome.png')
# Scale Game Logo if necessary
game_logo = pygame.transform.scale(game_logo, (400, 200))  # Adjust size as needed

# Scale backgrounds
def scale_background(image):
    scale_factor = SCREEN_HEIGHT / image.get_height()
    width = int(image.get_width() * scale_factor)
    return pygame.transform.scale(image, (width, SCREEN_HEIGHT))

saloon_background = scale_background(saloon_background)
poker_table_background = scale_background(poker_table_background)

# Load button images
start_img = load_image('start_button.png')
settings_img = load_image('Setting.png')
mute_img = load_image('mute.png')
pause_img = load_image('Pause.png')  # Load Pause.png
hit_img = load_image('hit_button.png')
stand_img = load_image('stand_button.png')

# Load Next and Previous button images
next_img = load_image('next.png')
previous_img = load_image('previous.png')

# Create button instances
start_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, start_img, scale=1.5)  # Adjusted y-position
hit_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, hit_img, scale=1)
stand_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50, stand_img, scale=1)

# Settings button setup
SETTINGS_BUTTON_SCALE = 0.18
PADDING = 20

scaled_width = int(settings_img.get_width() * SETTINGS_BUTTON_SCALE)
scaled_height = int(settings_img.get_height() * SETTINGS_BUTTON_SCALE)

temp_scaled_image = pygame.transform.scale(settings_img, (scaled_width, scaled_height))
rotated_temp_image = pygame.transform.rotate(temp_scaled_image, 0)
rotated_width, rotated_height = rotated_temp_image.get_size()

settings_button_x = SCREEN_WIDTH - rotated_width - PADDING
settings_button_y = PADDING + rotated_height // 2

settings_button = SettingsButton(
    settings_button_x,
    settings_button_y,
    settings_img,
    scale=SETTINGS_BUTTON_SCALE,
    rotation_speed=0.3
)

#Create Back to Home button
home_img = load_image('home.png')  # Adjust the filename as needed
home_img_scaled = pygame.transform.scale(home_img, (int(home_img.get_width() * 0.5), int(home_img.get_height() * 0.5)))
home_button = Button(0, 0, home_img_scaled, scale=.25)

# Create mute button
mute_img_scaled = pygame.transform.scale(mute_img, (int(mute_img.get_width() * 0.5), int(mute_img.get_height() * 0.5)))
mute_button = Button(0, 0, mute_img_scaled, scale=.19)

# Create pause music button
pause_img_scaled = pygame.transform.scale(pause_img, (int(pause_img.get_width() * 0.5), int(pause_img.get_height() * 0.5)))
pause_button = Button(0, 0, pause_img_scaled, scale=.25)

# Create Next and Previous buttons
next_img_scaled = pygame.transform.scale(next_img, (int(next_img.get_width() * 0.5), int(next_img.get_height() * 0.5)))
previous_img_scaled = pygame.transform.scale(previous_img, (int(previous_img.get_width() * 0.5), int(previous_img.get_height() * 0.5)))

next_button = Button(0, 0, next_img_scaled, scale=0.50)
previous_button = Button(0, 0, previous_img_scaled, scale=0.54)

# --------------------------- Initialize Cards --------------------------- #
card_path = os.path.join(images_folder_path, '2C.png')  # Example card

try:
    card = pygame.image.load(card_path).convert_alpha()
    card_height = int(SCREEN_HEIGHT * 0.2)  # 20% of screen height
    card_width = int(card.get_width() * (card_height / card.get_height()))
    card = pygame.transform.scale(card, (card_width, card_height))
except FileNotFoundError:
    print(f"Card image not found in {card_path}.")
    pygame.quit()
    sys.exit()
# -------------------------- Initialize Pygame and Music -------------------------- #
pygame.init()
pygame.mixer.pre_init(44100, 16, 2, 4096)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Blackjack Game")

script_dir = os.path.dirname(os.path.abspath(__file__))
images_folder_path = os.path.join(script_dir, 'images')
music_folder = os.path.join(script_dir, 'music')

SUPPORTED_MUSIC_FORMATS = ['.ogg', '.mp3', '.wav']
music_files = load_music()
current_music_index = 0
if music_files:
    play_music(current_music_index)

# --------------------------- Fade Function --------------------------- #
def fade(width, height):
    fade_surface = pygame.Surface((width, height))
    fade_surface.fill((0, 0, 0))
    for alpha in range(0, 300, 5):
        fade_surface.set_alpha(alpha)
        redraw_window()
        screen.blit(fade_surface, (0, 0))
        pygame.display.update()
        pygame.time.delay(5)

# --------------------------- Rendering Functions --------------------------- #
def render_text_with_shadow(text, font, text_color, shadow_color, surface, pos, shadow_offset=(2, 2)):
    """
    Renders text with a drop shadow.

    :param text: The text to render.
    :param font: The pygame font object.
    :param text_color: The color of the main text.
    :param shadow_color: The color of the shadow.
    :param surface: The surface to render the text on.
    :param pos: Tuple (x, y) for the position of the main text.
    :param shadow_offset: Tuple (x_offset, y_offset) for the shadow position.
    
    # Render the shadow text
    shadow_text = font.render(text, True, shadow_color)
    shadow_rect = shadow_text.get_rect(center=(pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]))
    surface.blit(shadow_text, shadow_rect)"""

    # Render the main text
    main_text = font.render(text, True, text_color)
    main_rect = main_text.get_rect(center=pos)
    surface.blit(main_text, main_rect)

def draw_centered_text(text, font, text_col, surface, center_x, center_y):
    img = font.render(text, True, text_col)
    text_rect = img.get_rect(center=(center_x, center_y))
    surface.blit(img, text_rect)


def draw_pause_menu():
    # Define the size and position of the pop-up window
    popup_width = 600
    popup_height = 400
    popup_x = (SCREEN_WIDTH - popup_width) // 2
    popup_y = (SCREEN_HEIGHT - popup_height) // 2

    # Create a rectangle for the pop-up window
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    # Draw the pop-up window with a semi-transparent dark background
    popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    popup_surface.fill((50, 50, 50, 220))  # Semi-transparent dark background
    screen.blit(popup_surface, (popup_x, popup_y))

    # Draw a border around the pop-up window with light brown color
    pygame.draw.rect(screen, (210, 180, 140), popup_rect, 5)
    # Draw the pause menu text with light brown color
    pause_text = "PAUSE MENU"
    resume_text = "PRESS ESC TO RESUME"

    draw_centered_text(pause_text, font, PAUSE_TEXT_COLOR, screen, SCREEN_WIDTH // 2, popup_y + 55)
    draw_centered_text(resume_text, pause_font, PAUSE_TEXT_COLOR, screen, SCREEN_WIDTH // 2, popup_y + 110)

    # -------------------- Add Song Title Display in Pause Menu -------------------- #
    if current_song_title:
        # Define position for the song title within the popup
        song_title_y = popup_y + 160  # Adjust as needed
        song_title_x = popup_x + popup_width // 2  # Centered horizontally within the popup

        # Render the song title with drop shadow
        render_text_with_shadow(
            text=current_song_title,
            font=song_font,
            text_color=PAUSE_TEXT_COLOR,         # Use appropriate color
            shadow_color=(0, 0, 0),              # Black shadow
            surface=screen,
            pos=(song_title_x, song_title_y),
            shadow_offset=(2, 2)              # Offset for the shadow
        )
    # ---------------------------------------------------------------------------------- #

    home_button_x = popup_x + 50  # Positioned near the top-right of the popup
    home_button_y = popup_y + 50    # Adjust Y position as needed
    home_button.rect.center = (home_button_x, home_button_y)

    # Position the mute button within the pop-up
    mute_button_x = popup_x + 550  # Positioned near the top-right of the popup
    mute_button_y = popup_y + 50    # Adjust Y position as needed
    mute_button.rect.center = (mute_button_x, mute_button_y)

    # Position the pause music button within the pop-up
    pause_button_x = popup_x + 300  # Positioned to the left of the mute button
    pause_button_y = popup_y + 300  # Align with mute button
    pause_button.rect.center = (pause_button_x, pause_button_y)

    # Position the Next and Previous buttons within the pop-up
    previous_button_x = popup_x + 150  # Adjust as needed
    previous_button_y = popup_y + 300
    previous_button.rect.center = (previous_button_x, previous_button_y)

    next_button_x = popup_x + 450  # Adjust as needed
    next_button_y = popup_y + 300
    next_button.rect.center = (next_button_x, next_button_y)

    # Draw the mute button and handle its action
    if mute_button.draw(screen):
        toggle_mute()

    # Draw the pause music button and handle its action
    if pause_button.draw(screen):
        toggle_pause_music()

    # Draw the Next and Previous buttons and handle their actions
    if previous_button.draw(screen):
        play_previous_song()

    if home_button.draw(screen):
        return_to_home()  # Use return_to_home instead of toggle_home

    if next_button.draw(screen):
        play_next_song()

    # Draw the volume slider
    volume_slider.draw(screen)

    # Add volume label next to the slider
    # Position the label to the left of the slider
    volume_label_x = slider_x - 50  # Adjust as needed
    volume_label_y = slider_y + slider_height // 2
    draw_centered_text("VOLUME:", pause_font, PAUSE_TEXT_COLOR, screen, volume_label_x, volume_label_y)

def draw_welcome_sign():
    padding = 0
    logo_width, logo_height = welcome.get_size()
    bg_rect_width = logo_width 
    bg_rect_height = logo_height

    # Keep the position consistent

    # Draw the rounded rectangle background

    # Blit the welcome sign on top of the rounded rectangle
    screen.blit(welcome, (logo_width + padding, logo_height + padding))

'''def draw_game_screen_logo():
    padding = 0  # Padding around the logo
    logo_width, logo_height = game_logo.get_size()
    bg_rect_width = logo_width + 2 * padding
    bg_rect_height = logo_height + 2 * padding

    # Define the position for the background rectangle (shifted up by 50 pixels)
    bg_rect_x = (SCREEN_WIDTH - bg_rect_width) // 2
    bg_rect_y = 100 - 50  # Shift up by 50 pixels

    # Draw the rounded rectangle background
    pygame.draw.rect(screen, SIGN_BACKGROUND_COLOR, (bg_rect_x, bg_rect_y, bg_rect_width, bg_rect_height), border_radius=30)

    # Blit the logo on top of the rounded rectangle
    screen.blit(game_logo, (bg_rect_x + padding, bg_rect_y + padding))
    '''
def redraw_window():
    if game_state == "menu":
        screen.blit(saloon_background, (background_x, 0))
        place_welcome(SCREEN_WIDTH // 2 - welcome.get_width() // 2, SCREEN_HEIGHT // 1.6 - welcome.get_height())
        start_button.draw(screen)
        settings_button.draw(screen)
    elif game_state == "game":
        run_game()
        settings_button.draw(screen)
        hit_button.draw(screen)
        stand_button.draw(screen)
    elif game_state == "pause":
        if previous_state == "menu":
            screen.blit(saloon_background, (background_x, 0))
            draw_welcome_sign()
            start_button.draw(screen)
            settings_button.draw(screen)
        elif previous_state == "game":
            run_game()
            settings_button.draw(screen)
            hit_button.draw(screen)
            stand_button.draw(screen)
        draw_pause_menu()

# --------------------------- Game Screen Logic --------------------------- #
def run_game(startup, characters=None, deck=None):
    global game_over, winner
    
    if not startup:
        screen.blit(poker_table_background, (0, 0))
        player1 = g.Player(name='Player', card_pos_x=350, card_pos_y=350)
        dealer = g.Player(name='Dealer', card_pos_x=350, card_pos_y=50)

        characters = [player1, dealer]
        deck = g.Deck()
        deck.generate_deck()
        deck.shuffle()
        deal_start_cards(characters, deck)
        startup = True
        game_over = False
        winner = None

    if not game_over:
        if stand_button.draw(screen):
            stand(characters, deck)
        
        if hit_button.draw(screen):
            hit(characters, deck)

    display_scores(characters)
    display_cards(characters)
    deck_pos = display_deck()

    if game_over:
        display_winner(winner)
        if play_again_button.draw(screen):
            startup = False
            return startup, None, None, None

    return startup, characters, deck, deck_pos

def stand(characters, deck):
    global game_over, winner
    player, dealer = characters

    # Reveal dealer's face-down card
    display_cards(characters)
    pygame.display.update()
    pygame.time.wait(500)  # Pause for dramatic effect

    deck_pos = display_deck()
    # Dealer's turn
    while dealer.bjcount < 17:
        try:
            card = deck.deal_card()
        except IndexError:
            print("Error: Deck is empty")
            return

        dealer.hand.append(card)
        dealer.bjcount += get_card_value(card)
        
        if card[0] == 'A' and dealer.bjcount <= 21:
            dealer.softhand = True
        
        animate_card_movement(card, dealer, deck_pos, characters, len(dealer.hand) - 1)
        
        if dealer.bjcount > 21:
            if dealer.softhand:
                dealer.bjcount -= 10
                dealer.softhand = False
            else:
                game_over = True
                winner = player
                return

    # Determine winner
    game_over = True
    if len(player.hand) == 2 and player.bjcount == 21:  # Player has Blackjack
        winner = player
    elif dealer.bjcount > player.bjcount:
        winner = dealer
    elif dealer.bjcount < player.bjcount:
        winner = player
    else:
        winner = None  # It's a tie

def hit(characters, deck):
    global game_over, winner
    player = characters[0]

    card = deck.deal_card()
    player.hand.append(card)
    if card[0] == 'A':
        player.softhand = True
    player.bjcount += get_card_value(card)

    deck_pos = display_deck()
    animate_card_movement(card, player, deck_pos, characters, len(player.hand) - 1)

    if player.bjcount > 21:
        if player.softhand:
            player.bjcount -= 10
            player.softhand = False
        else:
            game_over = True
            winner = characters[1]  # Dealer wins

    # Refresh the display after dealing
    screen.blit(poker_table_background, (0, 0))
    display_scores(characters)
    display_cards(characters)
    display_deck()
    pygame.display.update()

def get_card_value(card):
    if card[0] in ['T', 'J', 'Q', 'K']:
        return 10
    elif card[0] == 'A':
        return 11
    else:
        return int(card[0])

def deal_start_cards(characters, deck):
    deck_pos = display_deck()
    player, dealer = characters
    
    # Deal first card to player
    card = deck.deal_card()
    player.hand.append(card)
    if card[0] == 'A':
        player.softhand = True
    player.bjcount += get_card_value(card)
    animate_card_movement(card, player, deck_pos, characters, len(player.hand) - 1)

    # Deal first card to dealer (face down)
    card = deck.deal_card()
    dealer.hand.append(card)
    if card[0] == 'A':
        dealer.softhand = True
    dealer.bjcount += get_card_value(card)
    animate_card_movement('Blank', dealer, deck_pos, characters, len(dealer.hand) - 1)

    # Deal second card to player
    card = deck.deal_card()
    player.hand.append(card)
    if card[0] == 'A':
        player.softhand = True
    player.bjcount += get_card_value(card)
    animate_card_movement(card, player, deck_pos, characters, len(player.hand) - 1)

    # Deal second card to dealer (face up)
    card = deck.deal_card()
    dealer.hand.append(card)
    if card[0] == 'A':
        dealer.softhand = True
    dealer.bjcount += get_card_value(card)
    animate_card_movement(card, dealer, deck_pos, characters, len(dealer.hand) - 1)

    for player in characters:
        if player.bjcount == 21:
            global game_over, winner
            game_over = True
            winner = player
            return

    # Refresh the display after dealing
    screen.blit(poker_table_background, (0, 0))
    display_scores(characters)
    display_cards(characters)
    display_deck()
    pygame.display.update()

def display_cards(characters, animate=False, animated_card=None):
    player, dealer = characters
    for i, card in enumerate(player.hand):
        card_image = load_card_image(card)
        x = player.card_pos_x + i * 30
        y = player.card_pos_y
        screen.blit(card_image, (x, y))

    for i, card in enumerate(dealer.hand):
        if i == 0 and not game_over:
            card_image = load_card_image('Blank')
        else:
            card_image = load_card_image(card)
        x = dealer.card_pos_x + i * 30
        y = dealer.card_pos_y
        screen.blit(card_image, (x, y))

    if animate and animated_card:
        screen.blit(animated_card[0], animated_card[1])

def load_card_image(card):
    card_path = os.path.join(images_folder_path, card + '.png')
    try:
        cardimg = pygame.image.load(card_path)
        card_height = int(SCREEN_HEIGHT * 0.2)
        card_width = int(cardimg.get_width() * (card_height / cardimg.get_height()))
        return pygame.transform.scale(cardimg, (card_width, card_height))
    except FileNotFoundError as e:
        print(f"Image not found: {e}")
        pygame.quit()
        sys.exit()

def display_deck():
    deck_image = load_card_image('Blank')
    deck_x = 20
    deck_y = 50
    screen.blit(deck_image, (deck_x, deck_y))
    return (deck_x, deck_y)
    
def display_scores(characters):
    player, dealer = characters
    player_score = large_font.render(f"Player: {player.bjcount}", True, GAME_TEXT_COLOR)
    if game_over:
        dealer_score = large_font.render(f"Dealer: {dealer.bjcount}", True, GAME_TEXT_COLOR)
        
    else:
        visible_dealer_score = sum(get_card_value(card) for card in dealer.hand[1:])
        dealer_score = large_font.render(f"Dealer: {visible_dealer_score}", True, GAME_TEXT_COLOR)
        
    screen.blit(player_score, (10, SCREEN_HEIGHT - 40))
    screen.blit(dealer_score, (10, 10))
    
def display_winner(winner):
    if winner is None:
        message = "It's a tie!"
    elif winner.name == "Player":
        message = "You win!"
    else:
        message = "Dealer wins!"
    
    winner_text = medium_font.render(message, True, GAME_TEXT_COLOR)
    text_rect = winner_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(winner_text, text_rect)


    
# -------------------------- Card Animation Functions -------------------------- #
def animate_card(start_pos, end_pos, card_image, characters, deck_pos, duration=500):
    start_time = pygame.time.get_ticks()
    while True:
        current_time = pygame.time.get_ticks()
        if current_time - start_time > duration:
            return

        progress = (current_time - start_time) / duration
        current_pos = (
            start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
            start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        )

        screen.blit(poker_table_background, (0, 0))
        display_scores(characters)
        display_cards(characters, animate=True, animated_card=(card_image, current_pos))
        display_deck()
        pygame.display.update()
        clock.tick(60)

def animate_card_movement(card, player, start_pos, characters, card_index, duration=500):
    card_image = load_card_image(card)
    end_pos = (player.card_pos_x + card_index * 30, player.card_pos_y)
    start_time = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        if current_time - start_time > duration:
            break

        progress = (current_time - start_time) / duration
        current_pos = (
            start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
            start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        )

        screen.blit(poker_table_background, (0, 0))
        display_scores(characters)
        display_cards(characters)
        screen.blit(card_image, current_pos)
        display_deck()
        pygame.display.update()
        clock.tick(60)

# ----------------------------- Music Functions ----------------------------- #
def play_next_song():
    global current_music_index, music_files
    if not music_files:
        return
    current_music_index += 1
    if current_music_index >= len(music_files):
        random.shuffle(music_files)
        current_music_index = 0
    play_music(current_music_index)

def play_previous_song():
    global current_music_index, music_files
    if not music_files:
        return
    current_music_index -= 1
    if current_music_index < 0:
        current_music_index = len(music_files) - 1
    play_music(current_music_index)

def toggle_mute():
    global is_muted, previous_volume
    if not is_muted:
        previous_volume = volume_slider.value  # Save the current volume before muting
        pygame.mixer.music.set_volume(0)
        is_muted = True
        print("Music muted.")
        volume_slider.value = 0.0
    else:
        # Restore to previous volume or default if slider is at 0
        restored_volume = previous_volume if previous_volume > 0 else 0.5
        pygame.mixer.music.set_volume(restored_volume)
        is_muted = False
        print("Music unmuted.")
        volume_slider.value = restored_volume

def return_to_home():
    global game_state, startup, characters, deck, game_over, winner
    # Reset all necessary game variables
    startup = False
    characters = None
    deck = None
    game_over = False
    winner = None
    game_state = "menu"
    print("Returning to home screen...")

def toggle_pause_music():
    global is_paused
    if not is_paused:
        pygame.mixer.music.pause()
        is_paused = True
        print("Music paused.")
    else:
        pygame.mixer.music.unpause()
        is_paused = False
        print("Music resumed.")

# --------------------------- Initialize Music End Event --------------------------- #
MUSIC_END_EVENT = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END_EVENT)

# ------------------------- Initialize Variables ------------------------- #
# Variables for scrolling background
background_x = 0
scroll_speed = 0.35
direction = 1

# Clock for frame rate
clock = pygame.time.Clock()

# Game state variables
game_state = "menu"
previous_state = None
# -------------------------- Load Assets -------------------------- #
saloon_background_path = os.path.join(images_folder_path, 'saloon_background.jpg')
poker_table_background_path = os.path.join(images_folder_path, 'table.jpg')
card_path = os.path.join(images_folder_path, '2C.png')
welcome_path = os.path.join(images_folder_path, 'welcome.png')

try:
    saloon_background = pygame.image.load(saloon_background_path)
    poker_table_background = pygame.image.load(poker_table_background_path)
    card = pygame.image.load(card_path)
    welcome = pygame.image.load(welcome_path)

    # Scale backgrounds
    scale_factor = SCREEN_HEIGHT / saloon_background.get_height()
    saloon_background_width = int(saloon_background.get_width() * scale_factor)
    saloon_background = pygame.transform.scale(saloon_background, (saloon_background_width, SCREEN_HEIGHT))

    scale_factor = SCREEN_HEIGHT / poker_table_background.get_height()
    poker_table_background_width = int(poker_table_background.get_width() * scale_factor)
    poker_table_background = pygame.transform.scale(poker_table_background, (poker_table_background_width * 1, SCREEN_HEIGHT * 1))

    card_height = int(SCREEN_HEIGHT * 0.2)
    card_width = int(card.get_width() * (card_height / card.get_height()))
    card = pygame.transform.scale(card, (card_width, card_height))

    welcome_height = int(SCREEN_HEIGHT * 0.5)
    welcome_width = int(welcome.get_width() * (welcome_height / welcome.get_height()))
    welcome = pygame.transform.scale(welcome, (welcome_width, welcome_height))

except FileNotFoundError as e:
    print(f"Image not found: {e}")
    pygame.quit()
    sys.exit()

button_images = {
    'start': 'start_button.png',
    'hit': 'hit_button.png',
    'stand': 'stand_button.png',
    'settings': 'Setting.png'
}

for key, filename in button_images.items():
    path = os.path.join(images_folder_path, filename)
    try:
        button_images[key] = pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        print(f"{key.capitalize()} button image not found in {path}.")
        pygame.quit()
        sys.exit()

# -------------------------- Create Game Objects -------------------------- #
start_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.3, button_images['start'], scale=1.5)
hit_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.05, button_images['hit'], scale=1)
stand_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.18, button_images['stand'], scale=1)
play_again_button = Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 1.3, button_images['start'], scale=1)

SETTINGS_BUTTON_SCALE = 0.18
PADDING = 25

scaled_width = int(button_images['settings'].get_width() * SETTINGS_BUTTON_SCALE)
scaled_height = int(button_images['settings'].get_height() * SETTINGS_BUTTON_SCALE)

temp_scaled_image = pygame.transform.scale(button_images['settings'], (scaled_width, scaled_height))
rotated_temp_image = pygame.transform.rotate(temp_scaled_image, 0)
rotated_width, rotated_height = rotated_temp_image.get_size()

settings_button_x = SCREEN_WIDTH - rotated_width - PADDING
settings_button_y = PADDING + rotated_height // 2

settings_button = SettingsButton(
    settings_button_x,
    settings_button_y,
    button_images['settings'],
    scale=SETTINGS_BUTTON_SCALE,
    rotation_speed=0.3
)

# -------------------------- Game Variables -------------------------- #
background_x = 0
scroll_speed = 0.35
direction = 1

GAME_TEXT_COLOR = pygame.Color('white')
TEXT_COLOR = pygame.Color('black')
large_font = pygame.font.SysFont("sans-serif", 60)
medium_font = pygame.font.SysFont("sans-serif", 45)
small_font = pygame.font.SysFont("sans-serif", 30)

clock = pygame.time.Clock()

game_state = "menu"
previous_state = None

game_over = False
winner = None
startup = False
characters = None
deck = None

# -------------------------- Main Game Loop -------------------------- #
run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "pause":
                    game_state = previous_state
                    print("Resuming game...")
                elif game_state in ["menu", "game"]:
                    previous_state = game_state
                    game_state = "pause"
                    print("Game paused.")

        if game_state == "pause":
            volume_slider.handle_event(event)

    # Update background position for scrolling
    background_x -= scroll_speed
    if background_x <= -saloon_background.get_width():
        background_x = 0  # Reset background_x when it scrolls off the screen

    # Redraw window with updated background position
    if game_state == "menu":
        screen.blit(saloon_background, (background_x, 0))
        screen.blit(saloon_background, (background_x + saloon_background.get_width(), 0))  # For seamless scrolling

        place_welcome(SCREEN_WIDTH // 2 - welcome.get_width() // 2, SCREEN_HEIGHT // 1.6 - welcome.get_height())

        # Check if the start button is clicked
        if start_button.draw(screen):
            fade(SCREEN_WIDTH, SCREEN_HEIGHT)
            game_state = "game"

        # Check if the settings button is clicked
        if settings_button.draw(screen):
            print("Settings button clicked from menu!")
            previous_state = game_state
            game_state = "pause"  # Change to pause menu or settings screen

    elif game_state == "game":
        startup, characters, deck, deck_pos = run_game(startup, characters, deck)

        if settings_button.draw(screen):
            previous_state = game_state
            game_state = "pause"

    elif game_state == "pause":
        if previous_state == "menu":
            screen.blit(saloon_background, (background_x, 0))
            screen.blit(saloon_background, (background_x + saloon_background.get_width(), 0))
            place_welcome(SCREEN_WIDTH // 2 - welcome.get_width() // 2, SCREEN_HEIGHT // 1.6 - welcome.get_height())
            start_button.draw(screen)
        elif previous_state == "game":
            run_game(startup, characters, deck)
        draw_pause_menu()

    pygame.display.update()
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()
