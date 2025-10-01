# Keyboard Maestro Setup Guide

This guide shows you how to trigger poker analysis with a simple hotkey while playing.

## Overview

**Workflow:**
1. Run `poker_seat_monitor.py` once to configure seat positions and card areas
2. Set up Keyboard Maestro with a hotkey (e.g., ⌘⇧P)
3. While playing poker, press the hotkey
4. Analysis runs automatically and shows win probability on screen
5. Continue playing!

---

## Step 1: Initial Configuration (One-Time Setup)

Before using the hotkey, you need to configure where to detect players and capture cards:

```bash
conda activate poker
python poker_seat_monitor.py
```

In the GUI:
1. **Add Seats** - Create seats for each player position at the table
2. **Record Locations** - For each seat, click "Record Location" and position mouse over a red card back
3. **Record Hole Cards Area** - Click "🂠 Record Hole Cards" and drag to select your card area
4. **Record Community Cards Area** - Click "🂡 Record Community Cards" and drag to select the board area

This saves configuration to `poker_monitor_config.json` which the hotkey script will use.

**You only need to do this once per poker table layout!**

---

## Step 2: Keyboard Maestro Setup

### Option A: Using the Shell Script (Recommended)

1. **Open Keyboard Maestro Editor**

2. **Create a New Macro**
   - Click the "+" button to create a new macro
   - Name it: "Poker AI Analysis"

3. **Set the Hotkey Trigger**
   - Click "New Trigger"
   - Select "Hot Key Trigger"
   - Choose your hotkey (e.g., ⌘⇧P - Command+Shift+P)
   - Make sure "Available in all applications" is checked

4. **Add Shell Script Action**
   - Click "New Action"
   - Search for "Execute Shell Script"
   - In the script field, enter:
   ```bash
   /Users/admin/Code/0.dev/0.python/poker/AIpokerplayer/poker_hotkey.sh
   ```
   - Set "Execute" to: "in a shell window"
   - Check "Display results in a window"

5. **Save the Macro**

### Option B: Direct Python Execution

If you prefer to run Python directly:

1. **Create New Macro** (same as above)

2. **Set Hotkey** (same as above)

3. **Add Shell Script Action** with this content:
```bash
cd /Users/admin/Code/0.dev/0.python/poker/AIpokerplayer
source ~/miniconda3/bin/activate
conda activate poker
python run_analysis.py
```

---

## Step 3: Test the Setup

1. **Open your poker table** (or a screenshot of one)

2. **Press your hotkey** (e.g., ⌘⇧P)

3. **Watch the magic happen:**
   - Terminal window appears showing progress
   - Analysis completes in ~3 seconds
   - Large popup shows win probability
   - Popup auto-closes after 5 seconds

---

## Using During Poker Games

### Typical Workflow:

1. **Game starts** - You're dealt cards
2. **Press hotkey** - Triggers analysis
3. **See result** - Win probability displays on screen (e.g., "5.9%")
4. **Make decision** - Use the information to fold, call, or raise
5. **Popup closes** - Continue playing

### Best Practices:

- **Configure once per table layout** - Different poker sites may need different configurations
- **Press hotkey after flop/turn/river** - Get updated probabilities as more cards appear
- **Use while thinking** - Analysis takes ~3 seconds, fits naturally in poker thinking time
- **Don't spam** - Each analysis uses 2 API calls (costs money)

---

## Troubleshooting

### "Configuration file not found"
**Problem:** You haven't configured seat positions yet

**Solution:** Run `poker_seat_monitor.py` and set up seats and card areas

### "Failed to recognize cards"
**Problem:** Screenshot area is wrong or cards aren't visible

**Solution:**
- Check that card areas are configured correctly
- Make sure cards are fully visible on screen
- Re-run `poker_seat_monitor.py` to adjust card areas

### "No active players detected"
**Problem:** Card back color detection not working

**Solution:**
- Make sure seat positions are over the red card backs
- Adjust seat positions in `poker_seat_monitor.py`
- Try different spots on the card backs

### Hotkey doesn't work
**Problem:** Keyboard Maestro macro not set up correctly

**Solution:**
- Make sure Keyboard Maestro is running
- Check that your hotkey doesn't conflict with other apps
- Verify the script path is correct
- Test by running `poker_hotkey.sh` directly in Terminal

### "conda: command not found"
**Problem:** Conda environment path is wrong

**Solution:**
- Check your conda installation path
- Update `poker_hotkey.sh` with correct conda path
- Or use Option B (Direct Python) with your python path

---

## Advanced: Customization

### Change Popup Duration

Edit `run_analysis.py`, line ~240:
```python
popup = WinProbabilityPopup(root, win_probability, duration=5)
```

Change `duration=5` to your preferred seconds.

### Change Monte Carlo Iterations

For faster results (less accurate):
```python
iterations=50000  # ~0.8s instead of ~1.5s
```

For more accurate results (slower):
```python
iterations=200000  # ~3s instead of ~1.5s
```

### Silent Mode (No Terminal Window)

In Keyboard Maestro, change:
- "Execute" from "in a shell window" to "in the background"
- Uncheck "Display results in a window"

You'll only see the probability popup, no terminal.

---

## Example Keyboard Maestro Macro

**Macro Name:** Poker AI Analysis

**Trigger:** ⌘⇧P (Command+Shift+P)

**Action:** Execute Shell Script
```bash
/Users/admin/Code/0.dev/0.python/poker/AIpokerplayer/poker_hotkey.sh
```

**Execute:** In a shell window (or "in the background" for silent mode)

---

## Performance

**Total Time:** ~3 seconds
- Player detection: < 0.1s
- Screenshot capture: < 0.1s
- Card recognition: ~1.5s (2 parallel API calls)
- Monte Carlo calculation: ~1.5s (100k iterations)
- Display popup: < 0.1s

**Cost:** 2 Haiku API calls per analysis (~$0.0002 per analysis at current pricing)

---

## Tips for Live Play

1. **Pre-configure multiple poker sites** - Save different config files for different sites
2. **Use descriptive hotkeys** - e.g., ⌘⇧1 for Site 1, ⌘⇧2 for Site 2
3. **Practice offline first** - Test with poker screenshots before using live
4. **Respect game rules** - Make sure AI assistance is allowed in your game
5. **Don't rely 100%** - Use as a learning tool and decision aid, not autopilot

---

## Files Involved

- `poker_seat_monitor.py` - Configuration GUI (run once to set up)
- `run_analysis.py` - Headless analysis script (triggered by hotkey)
- `poker_hotkey.sh` - Shell wrapper for Keyboard Maestro
- `poker_monitor_config.json` - Saved configuration (auto-generated)

**That's it! Press your hotkey and enjoy instant poker odds!** 🎰
