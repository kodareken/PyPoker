#!/usr/bin/env python3
"""
Poker AI Module - Card recognition using Claude Haiku and Monte Carlo equity calculation
"""

import anthropic
import base64
import os
import concurrent.futures
import sys
from datetime import datetime

# Import Monte Carlo simulator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monte_carlo_poker_equity import simulate_equity, parse_cards_str


def log_to_debug(message):
    """Append message to debug.txt with timestamp"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("debug.txt", "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Logging error: {e}")


class PokerAI:
    """Handles card recognition and win probability calculation"""

    def __init__(self, api_key=None):
        """Initialize with Anthropic API key"""
        if api_key is None:
            # Try to get API key from environment variable
            api_key = os.getenv('ANTHROPIC_API_KEY')

            if not api_key:
                raise ValueError(
                    "Anthropic API key not found!\n\n"
                    "Please set your API key in one of these ways:\n"
                    "1. Set environment variable: export ANTHROPIC_API_KEY='your-api-key-here'\n"
                    "2. Pass it directly: PokerAI(api_key='your-api-key-here')\n\n"
                    "Get your API key from: https://console.anthropic.com/"
                )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Hand cards recognition (ALWAYS 2 CARDS)
        self.hand_recognition_prompt = """Quickly identify the playing cards rank and suit (ALWAYS ONLY 2 CARDS) and return the correct answer?

reference  sheet:

Ranks:
Two = 2
Three = 3
Four = 4
Five = 5
Six = 6
Seven = 7
Eight = 8
Nine = 9
Ten = T (IMPORTANT: Use letter T, NOT the number 10)
Jack = J
Queen = Q
King = K
Ace = A

Suit:
Clubs=c
Spades=s
Hearts=h
Diamonds=d

Example correct output: "Th Kd" (Ten of hearts, King of diamonds)
CRITICAL: For tens, use "T" not "10" - write "Th Td Tc Ts" NOT "10h 10d 10c 10s"

**DO NOT OUTPUT ANYTHING ELSE THAN THIS FORMAT NOT A SINGLE WORD OR LETTER**"""

        # Board cards recognition (3-5 cards)
        self.board_recognition_prompt = """Quickly identify the playing cards rank and suit and return the correct answer?

reference  sheet:

Ranks:
Two = 2
Three = 3
Four = 4
Five = 5
Six = 6
Seven = 7
Eight = 8
Nine = 9
Ten = T (IMPORTANT: Use letter T, NOT the number 10)
Jack = J
Queen = Q
King = K
Ace = A

Suit:
Clubs=c
Spades=s
Hearts=h
Diamonds=d

Example correct output: "4s Th 5c" (Four of spades, Ten of hearts, Five of clubs)
CRITICAL: For tens, use "T" not "10" - write "Th Td Tc Ts" NOT "10h 10d 10c 10s"

**DO NOT OUTPUT ANYTHING ELSE THAN THIS FORMAT NOT A SINGLE WORD OR LETTER**"""

    def encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def recognize_cards(self, image_path, is_hand=False):
        """
        Recognize cards from an image using Claude Haiku (simple method from notebook)

        Args:
            image_path: Path to card image
            is_hand: True for hand cards (2 cards), False for board cards (3-5 cards)

        Returns: String of cards (e.g., "Ad 2s") or None if error
        """
        try:
            card_type = "HAND" if is_hand else "BOARD"
            log_to_debug(f"=== Starting {card_type} recognition for {image_path} ===")

            if not os.path.exists(image_path):
                log_to_debug(f"ERROR: Image file not found: {image_path}")
                return None

            base64_image = self.encode_image(image_path)
            log_to_debug(f"Image encoded successfully, size: {len(base64_image)} bytes")

            # Choose appropriate prompt based on card type
            system_prompt = self.hand_recognition_prompt if is_hand else self.board_recognition_prompt

            log_to_debug(f"Calling Haiku API for {card_type} recognition...")
            message = self.client.messages.create(
                model='claude-3-5-haiku-20241022',
                max_tokens=200,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": " "
                            }
                        ]
                    }
                ]
            )

            result = message.content[0].text.strip()
            log_to_debug(f"Haiku response for {card_type}: '{result}'")
            log_to_debug(f"=== Completed {card_type} recognition ===\n")

            return result
        except Exception as e:
            log_to_debug(f"ERROR in card recognition: {e}")
            print(f"Card recognition error: {e}")
            return None

    def normalize_card_notation(self, cards_str):
        """
        Normalize card notation: Convert '10x' to 'Tx' format
        Examples: '10h' -> 'Th', '10d' -> 'Td', '10c' -> 'Tc', '10s' -> 'Ts'

        Args:
            cards_str: Card string like "Ks 10h" or "10d 10c"

        Returns: Normalized string like "Ks Th" or "Td Tc"
        """
        if not cards_str:
            return cards_str

        # Replace all instances of "10" with "T"
        normalized = cards_str.replace('10', 'T')
        log_to_debug(f"Card notation normalized: '{cards_str}' -> '{normalized}'")
        return normalized

    def recognize_cards_parallel(self, hand_path, board_path):
        """
        Recognize both hand and board cards in parallel using concurrent API calls

        Args:
            hand_path: Path to hand.png (player's 2 hole cards)
            board_path: Path to board.png (3-5 community cards)

        Returns: (hand_cards, board_cards) tuple or (None, None) if error
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both API calls simultaneously with appropriate prompts
            hand_future = executor.submit(self.recognize_cards, hand_path, is_hand=True)
            board_future = executor.submit(self.recognize_cards, board_path, is_hand=False)

            # Get results
            hand_cards = hand_future.result()
            board_cards = board_future.result()

            # Normalize card notation (10x -> Tx)
            if hand_cards:
                hand_cards = self.normalize_card_notation(hand_cards)
            if board_cards:
                board_cards = self.normalize_card_notation(board_cards)

            return hand_cards, board_cards

    def calculate_win_probability(self, player_hand, community_cards, active_opponents, iterations=100000):
        """
        Calculate win probability using Monte Carlo simulation

        Args:
            player_hand: String like "Ad 2s" or "Jd 4h"
            community_cards: String like "5d 4c 6c" or empty for pre-flop
            active_opponents: Integer count of opponents (not including player)
            iterations: Number of Monte Carlo iterations (default 100000 - 1.5s, ±0.15% accuracy)

        Returns: String like "5.9%" or None if error
        """
        try:
            log_to_debug("=== Starting Monte Carlo Simulation ===")
            log_to_debug(f"INPUT - Player hand: '{player_hand}'")
            log_to_debug(f"INPUT - Community cards: '{community_cards}'")
            log_to_debug(f"INPUT - Active opponents: {active_opponents}")
            log_to_debug(f"INPUT - Iterations: {iterations}")

            # Parse cards to internal format
            hero_cards = parse_cards_str(player_hand)
            board_cards = parse_cards_str(community_cards) if community_cards.strip() else []

            log_to_debug(f"PARSED - Hero cards: {hero_cards}")
            log_to_debug(f"PARSED - Board cards: {board_cards}")

            # Run Monte Carlo simulation
            log_to_debug("Running Monte Carlo simulation...")
            win_rate, equity, wins, ties, losses = simulate_equity(
                hero=hero_cards,
                board=board_cards,
                n_opponents=active_opponents,
                iterations=iterations,
                seed=None  # Random seed for variation
            )

            # Convert equity to percentage
            equity_pct = equity * 100
            win_pct = win_rate * 100

            log_to_debug(f"RESULTS - Wins: {wins}")
            log_to_debug(f"RESULTS - Ties: {ties}")
            log_to_debug(f"RESULTS - Losses: {losses}")
            log_to_debug(f"RESULTS - Win rate: {win_pct:.2f}%")
            log_to_debug(f"RESULTS - Equity (with ties): {equity_pct:.2f}%")
            log_to_debug(f"=== Completed Monte Carlo Simulation ===\n")

            # Return formatted percentage
            return f"{equity_pct:.1f}%"

        except Exception as e:
            log_to_debug(f"ERROR in Monte Carlo calculation: {e}")
            print(f"Monte Carlo calculation error: {e}")
            return None


# For standalone testing
if __name__ == "__main__":
    ai = PokerAI()

    # Test card recognition if image exists
    if os.path.exists("imgs/hand.png"):
        print("Testing card recognition...")
        cards = ai.recognize_cards("imgs/hand.png", is_hand=True)
        print(f"Recognized hand: {cards}")

    # Test odds calculation with Monte Carlo
    print("\nTesting Monte Carlo odds calculation (100k iterations, ~1.5s)...")
    probability = ai.calculate_win_probability(
        player_hand="Jd 4h",
        community_cards="5c 3c 3s",
        active_opponents=5
    )
    print(f"Win probability: {probability}")
