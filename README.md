# PyPoker - Texas Hold'em Assistant 🎰

**Real-time poker odds calculator with AI-powered card recognition and Monte Carlo simulation**

PyPoker is a blazing-fast poker analysis tool that automatically detects opponents, recognizes cards using AI vision, and calculates your win probability in under 2 seconds. Perfect for practicing poker strategy and understanding equity in real-time.


<img width="1170" height="416" alt="setup" src="https://github.com/user-attachments/assets/91f0bae5-6675-46bb-8e0c-597d1d03a79e" />


## ✨ Features

- **🎯 Player Detection**: Automatically detects active opponents at the poker table
- **🤖 AI Card Recognition**: Uses Claude Haiku vision AI to recognize cards (2 parallel API calls)
- **📊 Monte Carlo Simulation**: 100,000 iteration equity calculation (~1.5s, ±0.15% accuracy)
- **⚡ Lightning Fast**: Complete analysis (detection + recognition + odds) in under 2 seconds
- **⌨️ Hotkey Support**: Trigger analysis with keyboard shortcuts (Keyboard Maestro compatible)
- **🖥️ GUI & Headless Modes**: Both interactive GUI and headless hotkey-triggered modes

## 🚀 Performance

| Operation | Time | Accuracy |
|-----------|------|----------|
| Player detection | ~50ms | Pixel-perfect |
| Card recognition (2 parallel calls) | ~600ms | 99%+ (Haiku vision) |
| Monte Carlo simulation (100k iterations) | ~1.5s | ±0.15% |
| **Total end-to-end** | **~2.1s** | **Excellent** |


<img width="1170" height="656" alt="winprob" src="https://github.com/user-attachments/assets/ef0978be-76ea-4714-a485-f78d23d53128" />


## 🧪 Test it with PokerTH

Want to try PyPoker without real money? Use **[PokerTH](https://www.pokerth.net/)** - a free, open-source Texas Hold'em simulator!

**PokerTH** is a Texas Hold'em simulator written in C++ with the Qt framework that runs on Windows, Mac OS X, Linux, and Android. It allows up to 10 human players with computer-controlled players filling in the remaining seats.

Perfect for:
- Learning PyPoker setup and configuration
- Testing your poker strategy
- Practicing hand reading and equity calculations

## 📋 Requirements

- **Python 3.8+**
- **macOS / Linux / Windows** (tested on macOS)
- **Anthropic API Key** (for Claude Haiku card recognition)

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/kodareken/PyPoker.git
cd PyPoker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install anthropic>=0.18.0 Pillow>=9.0.0
```

### 3. Set up your Anthropic API Key

Get your API key from [https://console.anthropic.com/](https://console.anthropic.com/)

**Option 1: Environment Variable (Recommended)**

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Add to `~/.bashrc` or `~/.zshrc` to make it permanent:

```bash
echo "export ANTHROPIC_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

**Option 2: Pass directly in code**

```python
from poker_ai import PokerAI
ai = PokerAI(api_key='your-api-key-here')
```

## 📖 Usage Guide

### Quick Start (GUI Mode)

1. **Launch the poker seat monitor**

```bash
python poker_seat_monitor.py
```

2. **Configure seat positions**
   - Click "**+ Add Seat**" for each player position (typically 9 seats)
   - For each seat, click "**Record Location**" and position your mouse over the player's seat indicator
   - The app will capture a 5x5 pixel area to detect player presence

3. **Configure seat color**
   - Click "**Pick Color from Screen**" and hover over an active player indicator
   - This sets the RGB color used to detect active players

4. **Configure card areas**
   - Click "**🂠 Record Hole Cards**" and drag to select your hole cards area
   - Click "**🂡 Record Community Cards**" and drag to select the board area

5. **Test your setup**
   - Click "**Check Seats**" to verify player detection
   - Click "**📸 Capture Cards**" to test card area screenshots

6. **Run AI analysis**
   - Click "**🤖 AI WIN PROBABILITY**"
   - The app will:
     - Detect active opponents
     - Capture card screenshots
     - Recognize cards with AI
     - Calculate win probability
     - Display result in a popup window

### Headless Mode (Hotkey Triggered)

For keyboard shortcut automation (e.g., with Keyboard Maestro):

1. **Configure using GUI first** (run `poker_seat_monitor.py` once to save config)

2. **Run analysis via script**

```bash
bash poker_hotkey.sh
```

Or directly:

```bash
python run_analysis.py
```

This will:
- Load saved configuration
- Detect active opponents
- Capture cards
- Run AI analysis
- Show result popup (auto-closes in 5 seconds)

### Keyboard Maestro Setup

1. Create a new macro
2. Set trigger (e.g., `Ctrl+Shift+P`)
3. Add "Execute Shell Script" action:

```bash
cd /path/to/PyPoker
bash poker_hotkey.sh
```

## 🗂️ Project Structure

```
PyPoker/
├── poker_seat_monitor.py    # Main GUI application
├── run_analysis.py           # Headless analysis script
├── poker_ai.py               # AI card recognition & Monte Carlo
├── monte_carlo_poker_equity.py  # Fast equity simulator
├── poker_hotkey.sh           # Hotkey launcher script
├── poker_monitor_config.json # Saved configuration
├── imgs/                     # Screenshot storage
│   ├── hand.png             # Hole cards screenshot
│   └── board.png            # Community cards screenshot
├── debug.txt                 # Analysis debug log
└── requirements.txt          # Python dependencies
```

## 🎮 Configuration File

Settings are saved to `poker_monitor_config.json`:

```json
{
  "seats": [
    {
      "name": "1",
      "position": [337, 479],
      "area": {
        "x": 337,
        "y": 479,
        "x_start": 335,
        "y_start": 477,
        "x_end": 340,
        "y_end": 482
      }
    }
  ],
  "card_areas": {
    "hole_cards": {
      "x": 498,
      "y": 435,
      "width": 80,
      "height": 83
    },
    "community_cards": {
      "x": 390,
      "y": 271,
      "width": 274,
      "height": 83
    }
  },
  "seat_color": [99, 146, 145]
}
```

## 🐛 Troubleshooting

### "API key not found" error

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### "Already running" error (stale lock file)

The app now automatically detects and removes stale lock files. If you still see this error:

```bash
rm ~/.poker_monitor.lock
```

### Card recognition errors

- Check `debug.txt` for detailed logs
- Verify card area screenshots in `imgs/` folder
- Ensure cards are clearly visible and not overlapped
- Try reconfiguring card areas with better boundaries

### Opponent count is 0

- Verify seat color matches active player indicators
- Click "Check Seats" to test detection
- Reconfigure seat color using "Pick Color from Screen"
- Check `debug.txt` for detailed seat detection logs

## 🧠 How It Works

### 1. Player Detection (Pixel Scanning)
- Monitors 5x5 pixel areas at each seat position
- Matches RGB color with configured tolerance (10%)
- Detects active/inactive players in ~50ms

### 2. Card Recognition (AI Vision)
- Captures screenshots of card areas
- Sends to Claude Haiku vision API (2 parallel calls)
- Optimized prompt for fast, accurate card notation
- Handles "10" → "T" conversion automatically
- Recognition time: ~600ms for both hand and board

### 3. Equity Calculation (Monte Carlo)
- Fast Python-based Monte Carlo simulator
- 100,000 iterations in ~1.5 seconds
- Accuracy: ±0.15% from true equity
- Simulates random opponent hands and runouts
- Returns win probability percentage

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📜 License

MIT License - See LICENSE file for details

## ⚠️ Disclaimer

This tool is for **educational and practice purposes only**. Do not use for real-money online poker, as it may violate terms of service. Always follow the rules and regulations of poker platforms you use.

## 🙏 Credits

- **Card Recognition**: Claude Haiku by Anthropic
- **Monte Carlo Simulation**: Custom Python implementation
- **Test Environment**: [PokerTH](https://www.pokerth.net/) - Open-source Texas Hold'em simulator

---

**Happy analyzing! 🎰🤖**

Questions? Open an issue on GitHub!
