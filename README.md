# Blackjack Game in Pygame

## Overview

We created a Blackjack game built using Python and the Pygame library. The game provides an interactive interface where players can play a classic game of Blackjack against the dealer in the West Wild. The game includes features include such as background music, game sounds, card animations, and a pause menu.

### Game Features:
•	Blackjack Mechanics: Play a full game of Blackjack with hit and stand options.

•	Background Music: A music player that shuffles and plays music from a local folder.

•	Card Animations: Smooth card-dealing animations for an immersive gameplay experience.

•	Pause Menu: The game includes a pause feature where players can mute or unmute sounds, change the background music, and adjust the volume.

•	Settings Menu: Settings button to access controls for music and game options.

## Getting Started

### Prerequisites
1.	Python 3.8+: Make sure you have Python installed on your system.
2.	Pygame: Install the Pygame library via pip:
Installation
1.	Download or clone this repository.
2.	unzip images and file folders and Ensure the following folder structure exists:

images
   - saloon_background.jpg
   - table.jpg
   - start_button.png
   - hit_button.png
   - stand_button.png
   - Setting.png
   - home.png
   - mute.png
   - Pause.png

Music
   - (Music files with extensions: .ogg, .mp3, .wav)

3.	Run the game by executing:
python blackjack_game.py

Controls
•	Start Button: Starts the Blackjack game.

•	Hit Button: Draws another card.

•	Stand Button: Ends the player's turn and lets the dealer play.

•	Pause Menu (ESC): Opens a menu with options to mute/unmute music, change the track, and adjust volume.

How to Play
1.	Objective: The goal is to beat the dealer by having a hand value closest to 21 without going over.
2.	Gameplay:
o	The dealer must draw to 16 and stand on 17 or higher.

o	Aces count as 1 or 11, depending on the player's hand.

o	Press "Hit" to draw a card or "Stand" to end your turn.

4.	Winning: You win by having a hand value higher than the dealer's without exceeding 21.
   
Pause Menu
Press ESC during gameplay to open the pause menu. The pause menu allows you to:
•	Mute/Unmute Music: Toggle the game's music.

•	Change Track: Skip to the next or previous track in the music folder.

•	Volume Slider: Adjust the background music volume.

Music and Assets
•	Music: You can add your own .ogg, .mp3, or .wav files to the music folder. The game will automatically detect and shuffle the music.

•	Images: Game assets (such as cards, background, buttons) must be placed in the images folder.
Additional Features
•	Music Shuffling: The game will shuffle through the music files.

•	Custom Font Support: If you want to use a custom font, place a .ttf font file in the images folder and name it cool_font.ttf.

Troubleshooting
•	Music Not Playing: Ensure you have music files in the /music folder with supported formats (.ogg, .mp3, .wav).

•	Card Images Not Found: Ensure that card images are correctly named and placed in the /images folder.

•	Pygame Errors: Ensure that Pygame is installed using the correct Python version.

License
This project is licensed under the MIT License.
Enjoy the game!
