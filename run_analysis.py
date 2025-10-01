#!/usr/bin/env python3
"""
Headless poker analysis script - Run analysis without GUI
Designed to be triggered by keyboard shortcuts (e.g., Keyboard Maestro)

Usage:
    python run_analysis.py

This script:
1. Loads saved configuration from poker_monitor_config.json
2. Detects active players
3. Captures card screenshots
4. Recognizes cards with AI (2 parallel Haiku calls)
5. Calculates win probability (Monte Carlo)
6. Displays result in popup window

Perfect for keyboard shortcut automation!
"""

import tkinter as tk
from PIL import ImageGrab
import json
import os
import sys
from datetime import datetime
from poker_ai import PokerAI


class WinProbabilityPopup:
    """Large, temporary popup showing win probability"""
    def __init__(self, parent, probability_text, duration=5):
        self.window = tk.Toplevel(parent)
        self.window.title("Win Probability")
        self.window.geometry("500x350")
        self.window.attributes('-topmost', True)

        # Center the window
        self.center_window()

        # Background color
        self.window.configure(bg='#1a1a1a')

        # Title label
        title_label = tk.Label(self.window, text="Win Probability",
                              font=("Arial", 20, "bold"),
                              fg="#00ff00", bg='#1a1a1a')
        title_label.pack(pady=20)

        # Probability display - HUGE text
        self.prob_label = tk.Label(self.window, text=probability_text,
                                   font=("Arial", 72, "bold"),
                                   fg="#00ff00", bg='#1a1a1a')
        self.prob_label.pack(pady=30)

        # Info label
        info_label = tk.Label(self.window, text="Window will close automatically",
                             font=("Arial", 12),
                             fg="#888888", bg='#1a1a1a')
        info_label.pack(pady=10)

        # Close button
        close_btn = tk.Button(self.window, text="Close Now",
                            command=self.close_and_quit,
                            bg="#ff0000", fg="white",
                            font=("Arial", 14, "bold"),
                            padx=20, pady=10)
        close_btn.pack(pady=10)

        # Auto-close after duration
        self.window.after(duration * 1000, self.close_and_quit)

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def close_and_quit(self):
        """Close window and quit application"""
        self.window.destroy()


def load_config():
    """Load configuration from JSON file"""
    config_file = "poker_monitor_config.json"
    if not os.path.exists(config_file):
        print(f"ERROR: Configuration file '{config_file}' not found!")
        print("Please run poker_seat_monitor.py first to configure seat positions and card areas.")
        sys.exit(1)

    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        return config_data
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)


def check_seat_area(area, target_colors, tolerance):
    """Check 5x5 pixel area for target red color"""
    try:
        screenshot = ImageGrab.grab(bbox=(area["x_start"], area["y_start"],
                                        area["x_end"], area["y_end"]))

        # Check each pixel in the 5x5 area
        for x in range(5):
            for y in range(5):
                try:
                    pixel_color = screenshot.getpixel((x, y))
                    if len(pixel_color) >= 3:  # Ensure RGB format
                        r, g, b = pixel_color[:3]
                        if color_matches_target((r, g, b), target_colors, tolerance):
                            return True
                except:
                    continue

        return False
    except Exception as e:
        return False


def color_matches_target(rgb_color, target_colors, tolerance):
    """Check if RGB color matches target red colors with tolerance"""
    r, g, b = rgb_color

    for target_r, target_g, target_b in target_colors:
        red_tolerance = target_r * tolerance
        if (abs(r - target_r) <= red_tolerance and
            abs(g - target_g) <= target_g * tolerance and
            abs(b - target_b) <= target_b * tolerance):
            return True
    return False


def save_card_screenshot(area, filename):
    """Save screenshot of card area"""
    try:
        screenshot = ImageGrab.grab(bbox=(area["x"], area["y"],
                                        area["x"] + area["width"],
                                        area["y"] + area["height"]))

        filepath = os.path.join("imgs", filename)
        screenshot.save(filepath)
        return True
    except Exception as e:
        print(f"ERROR: Failed to save screenshot: {e}")
        return False


def initialize_debug_log():
    """Initialize debug.txt with run header"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("debug.txt", "w") as f:
            f.write("=" * 80 + "\n")
            f.write(f"POKER AI DEBUG LOG - RUN STARTED: {timestamp}\n")
            f.write("=" * 80 + "\n\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize debug log: {e}")


def main():
    # Initialize debug log for this run
    initialize_debug_log()

    print("=" * 60)
    print("POKER AI ANALYSIS - HEADLESS MODE")
    print("=" * 60)

    # Load configuration
    print("\n[1/5] Loading configuration...")
    config = load_config()

    seats = config.get("seats", [])
    card_areas = config.get("card_areas", {})

    # Validate configuration
    configured_seats = [seat for seat in seats if seat.get("area")]
    if not configured_seats:
        print("ERROR: No seats configured!")
        print("Please run poker_seat_monitor.py to set up seat positions.")
        sys.exit(1)

    if not card_areas.get("hole_cards"):
        print("ERROR: Hole cards area not configured!")
        print("Please run poker_seat_monitor.py to set up card areas.")
        sys.exit(1)

    print(f"✓ Loaded {len(configured_seats)} seats")
    print(f"✓ Hole cards area: configured")
    print(f"✓ Community cards area: {'configured' if card_areas.get('community_cards') else 'not set (pre-flop)'}")

    # Detect active players
    print("\n[2/5] Detecting active players...")

    # Load seat color from config (don't hardcode!)
    seat_color_list = config.get("seat_color", [149, 73, 70])
    seat_color = tuple(seat_color_list)
    target_colors = [seat_color]  # Use configured color
    tolerance = 0.10

    print(f"Using seat color: {seat_color}")

    # Import logging from poker_ai
    from poker_ai import log_to_debug

    log_to_debug("=== HEADLESS AI ANALYSIS: Counting active opponents ===")
    log_to_debug(f"Seat color from config: {seat_color}")
    log_to_debug(f"Total configured seats: {len(configured_seats)}")

    active_count = 0
    for seat in configured_seats:
        is_active = check_seat_area(seat["area"], target_colors, tolerance)
        status = "ACTIVE" if is_active else "INACTIVE"
        log_to_debug(f"Seat {seat['name']} at ({seat['position'][0]}, {seat['position'][1]}): {status}")
        if is_active:
            active_count += 1

    # All detected seats are opponents (player is NOT in these seats)
    active_opponents = active_count  # Don't subtract 1!

    log_to_debug(f"Total active opponents: {active_opponents}")
    log_to_debug("=== Opponent counting completed ===\n")

    print(f"✓ Active opponents detected: {active_opponents}")

    # Capture screenshots
    print("\n[3/5] Capturing card screenshots...")
    if not os.path.exists("imgs"):
        os.makedirs("imgs")

    if not save_card_screenshot(card_areas["hole_cards"], "hand.png"):
        print("ERROR: Failed to capture hole cards!")
        sys.exit(1)
    print("✓ Hole cards captured")

    if card_areas.get("community_cards"):
        save_card_screenshot(card_areas["community_cards"], "board.png")
        print("✓ Community cards captured")

    # Recognize cards with AI
    print("\n[4/5] Recognizing cards (AI - 2 parallel calls)...")
    ai = PokerAI()

    hand_path = "imgs/hand.png"
    board_path = "imgs/board.png"

    player_hand, board_cards = ai.recognize_cards_parallel(hand_path, board_path)

    if not player_hand:
        print("ERROR: Failed to recognize hole cards!")
        sys.exit(1)

    print(f"✓ Player hand: {player_hand}")

    community_cards = ""
    if board_cards and board_cards.strip():
        community_cards = board_cards
        print(f"✓ Community cards: {community_cards}")
    else:
        print("✓ Community cards: None (pre-flop)")

    # Calculate win probability
    print("\n[5/5] Calculating win probability (Monte Carlo 100k iterations)...")
    win_probability = ai.calculate_win_probability(
        player_hand=player_hand,
        community_cards=community_cards,
        active_opponents=active_opponents
    )

    if not win_probability:
        print("ERROR: Failed to calculate win probability!")
        sys.exit(1)

    print(f"✓ Win probability: {win_probability}")

    # Display result
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Player Hand:        {player_hand}")
    print(f"Community Cards:    {community_cards if community_cards else 'None (pre-flop)'}")
    print(f"Active Opponents:   {active_opponents}")
    print(f"Win Probability:    {win_probability}")
    print("=" * 60)

    print("\nDisplaying result popup...")

    # Show popup window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    popup = WinProbabilityPopup(root, win_probability, duration=5)

    root.mainloop()

    print("Analysis complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
