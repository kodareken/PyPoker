#!/usr/bin/env python3
"""
Poker Seat Monitor - Simple GUI application to monitor active players
by detecting red card colors at specified screen locations.

Usage: python poker_seat_monitor.py
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from PIL import ImageGrab, Image, ImageTk
import json
import time
import os
import threading
from poker_ai import PokerAI


class CountdownWindow:
    """Visual countdown window for better user experience"""
    def __init__(self, parent, message, seconds=3):
        self.parent = parent
        self.seconds = seconds
        self.window = tk.Toplevel(parent)
        self.window.title("Get Ready!")
        self.window.geometry("300x150")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.center_window()
        
        # Create GUI elements
        self.message_label = tk.Label(self.window, text=message, 
                                     font=("Arial", 12), wraplength=280)
        self.message_label.pack(pady=20)
        
        self.countdown_label = tk.Label(self.window, text=str(seconds), 
                                       font=("Arial", 24, "bold"), fg="red")
        self.countdown_label.pack(pady=10)
        
        self.start_countdown()
        
    def center_window(self):
        """Center the countdown window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def start_countdown(self):
        """Start the countdown timer"""
        if self.seconds > 0:
            self.countdown_label.config(text=str(self.seconds))
            self.window.after(1000, self.start_countdown)
            self.seconds -= 1
        else:
            self.countdown_label.config(text="GO!", fg="green")
            self.window.after(500, self.window.destroy)


class VisualAreaSelector:
    """Visual overlay for selecting screen areas with click and drag"""
    def __init__(self, parent, area_name):
        self.parent = parent
        self.area_name = area_name
        self.area = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        
    def get_area(self):
        """Show area selection overlay"""
        # Hide parent window
        self.parent.withdraw()
        
        # Create fullscreen overlay
        self.overlay = tk.Toplevel()
        self.overlay.overrideredirect(True) # Make window borderless
        width = self.overlay.winfo_screenwidth()
        height = self.overlay.winfo_screenheight()
        self.overlay.geometry(f"{width}x{height}+0+0")
        self.overlay.attributes('-alpha', 0.3)  # Semi-transparent
        self.overlay.configure(bg='black')
        self.overlay.attributes('-topmost', True)
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.overlay, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.configure(bg='black')
        
        # Instructions
        instruction_text = f"Click and drag to select {self.area_name} area\nPress ESC to cancel"
        self.canvas.create_text(
            self.overlay.winfo_screenwidth() // 2, 50,
            text=instruction_text,
            fill="white",
            font=("Arial", 16, "bold"),
            justify=tk.CENTER
        )
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.overlay.bind('<Escape>', self.cancel_selection)
        self.overlay.focus_set()
        
        # Wait for selection
        self.overlay.wait_window()
        
        # Restore parent window
        self.parent.deiconify()
        
        return self.area
        
    def on_click(self, event):
        """Handle mouse click"""
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.canvas.delete("selection")
        
    def on_drag(self, event):
        """Handle mouse drag"""
        if self.start_x is not None:
            self.canvas.delete("selection")
            # Draw selection rectangle
            self.canvas.create_rectangle(
                self.start_x - self.overlay.winfo_rootx(),
                self.start_y - self.overlay.winfo_rooty(),
                event.x,
                event.y,
                outline="red",
                width=3,
                tags="selection"
            )
            
    def on_release(self, event):
        """Handle mouse release - complete selection"""
        if self.start_x is not None:
            self.end_x = event.x_root
            self.end_y = event.y_root
            
            # Calculate area
            x1 = min(self.start_x, self.end_x)
            y1 = min(self.start_y, self.end_y)
            x2 = max(self.start_x, self.end_x)
            y2 = max(self.start_y, self.end_y)
            
            width = x2 - x1
            height = y2 - y1
            
            # Minimum area check
            if width > 10 and height > 10:
                self.area = {
                    "x": x1,
                    "y": y1,
                    "width": width,
                    "height": height
                }
            
            self.overlay.destroy()
            
    def cancel_selection(self, event=None):
        """Cancel area selection"""
        self.area = None
        self.overlay.destroy()


class ResultsWindow:
    """Enhanced results display window"""
    def __init__(self, parent, title, results):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x300")
        self.window.transient(parent)

        # Create scrollable text area
        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text widget
        self.text_widget = tk.Text(frame, yscrollcommand=scrollbar.set,
                                  font=("Arial", 10), wrap=tk.WORD)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)

        # Add results
        for result in results:
            self.text_widget.insert(tk.END, result + "\n")

        self.text_widget.config(state=tk.DISABLED)

        # Close button
        close_btn = tk.Button(self.window, text="Close", command=self.window.destroy,
                             bg="#f0f0f0", fg="black")
        close_btn.pack(pady=5)


class WinProbabilityPopup:
    """Large, temporary popup showing win probability"""
    def __init__(self, parent, probability_text, duration=5):
        self.window = tk.Toplevel(parent)
        self.window.title("Win Probability")
        self.window.geometry("500x350")
        self.window.transient(parent)
        self.window.attributes('-topmost', True)

        # Center the window
        self.center_window()

        # Remove window decorations for cleaner look (optional)
        # self.window.overrideredirect(True)

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
                            command=self.window.destroy,
                            bg="#ff0000", fg="white",
                            font=("Arial", 14, "bold"),
                            padx=20, pady=10)
        close_btn.pack(pady=10)

        # Auto-close after duration
        self.window.after(duration * 1000, self.window.destroy)

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')


class PokerSeatMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker Monitor - Seats & Cards")
        self.root.geometry("500x750")

        # Configuration
        self.seats = []
        self.card_areas = {
            "hole_cards": None,
            "community_cards": None
        }
        self.config_file = "poker_monitor_config.json"
        self.imgs_folder = "imgs"

        # Create imgs folder if it doesn't exist
        if not os.path.exists(self.imgs_folder):
            os.makedirs(self.imgs_folder)

        # Target color with tolerance
        self.seat_color = (149, 73, 70)  # Default red color
        self.tolerance = 0.10  # 10% tolerance

        # Initialize AI
        self.poker_ai = PokerAI()

        self.create_widgets()
        self.load_config()
        self.update_seat_list()
        self.update_card_areas_display()
        
    def create_widgets(self):
        """Create the main GUI interface"""
        # Title
        title_label = tk.Label(self.root, text="Poker Monitor - Seats & Cards", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # === SEATS SECTION ===
        seats_frame = tk.LabelFrame(self.root, text="Player Seats", 
                                   font=("Arial", 12, "bold"), fg="blue")
        seats_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Add seat button
        self.add_seat_btn = tk.Button(seats_frame, text="+ Add Seat", 
                                     command=self.add_seat,
                                     bg="#4CAF50", fg="black", 
                                     font=("Arial", 11))
        self.add_seat_btn.pack(pady=5)
        
        # Seat list
        listbox_frame = tk.Frame(seats_frame)
        listbox_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.seat_listbox = tk.Listbox(listbox_frame, 
                                      yscrollcommand=scrollbar.set,
                                      font=("Arial", 9), height=6)
        self.seat_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.seat_listbox.yview)
        
        # Seat control buttons
        seat_control_frame = tk.Frame(seats_frame)
        seat_control_frame.pack(pady=5)
        
        self.record_btn = tk.Button(seat_control_frame, text="Record Location",
                                   command=self.record_location,
                                   bg="#2196F3", fg="black",
                                   font=("Arial", 10))
        self.record_btn.pack(side="left", padx=3)
        
        self.delete_btn = tk.Button(seat_control_frame, text="Delete Seat",
                                   command=self.delete_seat,
                                   bg="#f44336", fg="black",
                                   font=("Arial", 10))
        self.delete_btn.pack(side="left", padx=3)
        
        self.check_seats_btn = tk.Button(seat_control_frame, text="Check Seats",
                                        command=self.check_all_seats,
                                        bg="#FF9800", fg="black",
                                        font=("Arial", 10))
        self.check_seats_btn.pack(side="left", padx=3)
        
        # === COLOR CONFIGURATION SECTION ===
        color_frame = tk.LabelFrame(self.root, text="Seat Color Configuration",
                                  font=("Arial", 12, "bold"), fg="purple")
        color_frame.pack(pady=10, padx=20, fill="x")

        color_display_frame = tk.Frame(color_frame)
        color_display_frame.pack(pady=5)

        self.color_label = tk.Label(color_display_frame, text="Current Color:", font=("Arial", 10))
        self.color_label.pack(side="left")

        self.color_swatch = tk.Label(color_display_frame, text="    ", bg=self.get_hex_color(self.seat_color), relief="sunken")
        self.color_swatch.pack(side="left", padx=5)

        self.color_entry = tk.Entry(color_display_frame, font=("Arial", 10))
        self.color_entry.pack(side="left", padx=5)
        self.color_entry.insert(0, str(self.seat_color))

        color_btn_frame = tk.Frame(color_frame)
        color_btn_frame.pack(pady=5)

        self.set_color_btn = tk.Button(color_btn_frame, text="Set from Text",
                                     command=self.update_color_from_entry,
                                     bg="#FFC107", fg="black",
                                     font=("Arial", 10))
        self.set_color_btn.pack(side="left", padx=3)

        self.pick_color_btn = tk.Button(color_btn_frame, text="Pick Color from Screen",
                                      command=self.set_color_with_mouse,
                                      bg="#FF5722", fg="black",
                                      font=("Arial", 10))
        self.pick_color_btn.pack(side="left", padx=3)
        
        # === CARD AREAS SECTION ===
        cards_frame = tk.LabelFrame(self.root, text="Card Areas", 
                                   font=("Arial", 12, "bold"), fg="green")
        cards_frame.pack(pady=10, padx=20, fill="x")
        
        # Card areas display
        self.card_areas_text = tk.Text(cards_frame, height=4, font=("Arial", 9))
        self.card_areas_text.pack(pady=5, padx=10, fill="x")
        self.card_areas_text.config(state=tk.DISABLED)
        
        # Card control buttons
        card_control_frame = tk.Frame(cards_frame)
        card_control_frame.pack(pady=5)
        
        self.record_hole_btn = tk.Button(card_control_frame, text="🂠 Record Hole Cards",
                                        command=self.record_hole_cards,
                                        bg="#9C27B0", fg="black",
                                        font=("Arial", 10))
        self.record_hole_btn.pack(side="left", padx=3)
        
        self.record_board_btn = tk.Button(card_control_frame, text="🂡 Record Community Cards",
                                         command=self.record_community_cards,
                                         bg="#795548", fg="black",
                                         font=("Arial", 10))
        self.record_board_btn.pack(side="left", padx=3)
        
        self.check_cards_btn = tk.Button(card_control_frame, text="📸 Capture Cards",
                                        command=self.check_card_areas,
                                        bg="#607D8B", fg="black",
                                        font=("Arial", 10))
        self.check_cards_btn.pack(side="left", padx=3)
        
        # === OVERALL CONTROLS ===
        main_control_frame = tk.Frame(self.root)
        main_control_frame.pack(pady=15)

        self.check_all_btn = tk.Button(main_control_frame, text="🔍 CHECK EVERYTHING",
                                      command=self.check_everything,
                                      bg="#E91E63", fg="black",
                                      font=("Arial", 12, "bold"))
        self.check_all_btn.pack(pady=5)

        # AI Analysis button
        self.ai_analysis_btn = tk.Button(main_control_frame, text="🤖 AI WIN PROBABILITY",
                                        command=self.run_ai_analysis,
                                        bg="#00BCD4", fg="black",
                                        font=("Arial", 12, "bold"))
        self.ai_analysis_btn.pack(pady=5)

        self.clear_all_btn = tk.Button(main_control_frame, text="Clear All Settings",
                                       command=self.clear_all_config,
                                       bg="#BDBDBD", fg="black",
                                       font=("Arial", 10))
        self.clear_all_btn.pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text="Ready", 
                                    font=("Arial", 10),
                                    fg="green")
        self.status_label.pack(pady=5)
        
        # Results frame
        self.results_frame = tk.Frame(self.root)
        self.results_frame.pack(pady=10, padx=20, fill="x")
        
    def add_seat(self):
        """Add a new seat to monitor"""
        seat_name = simpledialog.askstring("Add Seat", "Enter seat name (e.g., Seat 1):")
        if seat_name and seat_name.strip():
            seat_data = {
                "name": seat_name.strip(),
                "position": None,
                "area": None
            }
            self.seats.append(seat_data)
            self.update_seat_list()
            self.save_config()
            self.status_label.config(text=f"Added seat: {seat_name}", fg="green")
        
    def record_location(self):
        """Record screen location for selected seat"""
        selection = self.seat_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a seat to record its location.")
            return
            
        seat_index = selection[0]
        seat_name = self.seats[seat_index]["name"]
        
        # Show visual countdown
        countdown = CountdownWindow(self.root, f"Position mouse over {seat_name}")
        self.root.wait_window(countdown.window)
        
        # Capture mouse position
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        
        # Define 5x5 area around the point
        area = {
            "x": x,
            "y": y,
            "x_start": x - 2,
            "y_start": y - 2,
            "x_end": x + 3,
            "y_end": y + 3
        }
        
        self.seats[seat_index]["position"] = (x, y)
        self.seats[seat_index]["area"] = area
        
        self.update_seat_list()
        self.save_config()
        self.status_label.config(text=f"Location recorded for {seat_name} at ({x}, {y})", fg="green")
        
        # Show success notification
        messagebox.showinfo("Success", f"Seat location recorded!\n{seat_name}: ({x}, {y})")
        
    def delete_seat(self):
        """Delete selected seat"""
        selection = self.seat_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a seat to delete.")
            return
            
        seat_index = selection[0]
        seat_name = self.seats[seat_index]["name"]
        
        if messagebox.askyesno("Confirm Delete", f"Delete {seat_name}?"):
            del self.seats[seat_index]
            self.update_seat_list()
            self.save_config()
            self.status_label.config(text=f"Deleted seat: {seat_name}", fg="red")
            
    def update_seat_list(self):
        """Update the seat list display"""
        self.seat_listbox.delete(0, tk.END)
        for seat in self.seats:
            position = seat["position"]
            if position:
                status = f"✓ Set at ({position[0]}, {position[1]})"
            else:
                status = "❌ Not set"
            self.seat_listbox.insert(tk.END, f"{seat['name']} - {status}")
            
    def update_card_areas_display(self):
        """Update the card areas display"""
        self.card_areas_text.config(state=tk.NORMAL)
        self.card_areas_text.delete(1.0, tk.END)
        
        hole_status = "✓ Set" if self.card_areas["hole_cards"] else "❌ Not set"
        community_status = "✓ Set" if self.card_areas["community_cards"] else "❌ Not set"
        
        display_text = f"Hole Cards: {hole_status}\nCommunity Cards: {community_status}\n"
        
        if self.card_areas["hole_cards"]:
            area = self.card_areas["hole_cards"]
            display_text += f"Hole Cards Area: ({area['x']}, {area['y']}) [{area['width']}x{area['height']}]\n"
            
        if self.card_areas["community_cards"]:
            area = self.card_areas["community_cards"]
            display_text += f"Community Cards Area: ({area['x']}, {area['y']}) [{area['width']}x{area['height']}]"
        
        self.card_areas_text.insert(1.0, display_text)
        self.card_areas_text.config(state=tk.DISABLED)
        
    def record_card_area(self, card_type, area_name):
        """Generic method to record card areas using visual selection"""
        # Show instructions
        instruction_msg = f"You will now select the {area_name} area.\n\nInstructions:\n" \
                         f"1. Click and drag to select the area\n" \
                         f"2. Press ESC to cancel selection"
        
        messagebox.showinfo("Area Selection", instruction_msg)
        
        # Visual area selection
        selector = VisualAreaSelector(self.root, area_name)
        area = selector.get_area()
        
        if area:
            self.card_areas[card_type] = area
            self.update_card_areas_display()
            self.save_config()
            self.status_label.config(text=f"{area_name} area recorded!", fg="green")
            
            # Show success with area details
            messagebox.showinfo("Success", 
                f"{area_name} area recorded!\n\n" +
                f"Position: ({area['x']}, {area['y']})\n" +
                f"Size: {area['width']} x {area['height']}")
        else:
            self.status_label.config(text=f"{area_name} recording cancelled", fg="red")
            messagebox.showinfo("Cancelled", f"{area_name} area selection was cancelled.")
            
    def record_hole_cards(self):
        """Record hole cards area"""
        self.record_card_area("hole_cards", "Hole Cards")
        
    def record_community_cards(self):
        """Record community cards area"""
        self.record_card_area("community_cards", "Community Cards")
        
    def save_card_area_screenshot(self, area, filename):
        """Save screenshot of card area to imgs folder"""
        try:
            screenshot = ImageGrab.grab(bbox=(area["x"], area["y"], 
                                            area["x"] + area["width"], 
                                            area["y"] + area["height"]))
            
            filepath = os.path.join(self.imgs_folder, filename)
            screenshot.save(filepath)
            return True
        except Exception as e:
            # Log error but don't print to console
            return False
            
    def check_card_areas(self):
        """Save screenshots of card areas"""
        if not self.card_areas["hole_cards"] and not self.card_areas["community_cards"]:
            messagebox.showinfo("No Card Areas", "No card areas configured. Set up card areas first.")
            return
            
        self.status_label.config(text="Capturing card areas...", fg="blue")
        self.root.update()
        
        results = []
        saved_images = []
        
        if self.card_areas["hole_cards"]:
            success = self.save_card_area_screenshot(self.card_areas["hole_cards"], "hand.png")
            if success:
                results.append("Hole Cards: Screenshot saved as hand.png")
                saved_images.append("hand.png")
            else:
                results.append("Hole Cards: Failed to save screenshot")
            
        if self.card_areas["community_cards"]:
            success = self.save_card_area_screenshot(self.card_areas["community_cards"], "board.png")
            if success:
                results.append("Community Cards: Screenshot saved as board.png")
                saved_images.append("board.png")
            else:
                results.append("Community Cards: Failed to save screenshot")
            
        # Display results in enhanced window
        if saved_images:
            results.append(f"\nImages saved to: {self.imgs_folder}/")
            for img in saved_images:
                results.append(f"  - {img}")
                
        # Show results in dedicated window
        ResultsWindow(self.root, "Card Screenshots Captured", results)
        
        self.status_label.config(text="Card screenshots captured!", fg="green")
        
    def check_everything(self):
        """Check both seats and card areas"""
        if not self.seats and not self.card_areas["hole_cards"] and not self.card_areas["community_cards"]:
            messagebox.showinfo("Nothing Configured", "Please configure seats or card areas first.")
            return
            
        self.status_label.config(text="Checking everything...", fg="blue")
        self.root.update()
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Results title
        results_title = tk.Label(self.results_frame, text="Complete Poker Check Results:", 
                               font=("Arial", 12, "bold"))
        results_title.pack(anchor="w")
        
        all_results = []
        
        # Check seats
        if self.seats:
            configured_seats = [seat for seat in self.seats if seat.get("area")]
            if configured_seats:
                active_count = 0
                seat_label = tk.Label(self.results_frame, text="Seats:", 
                                    font=("Arial", 11, "bold"), fg="blue")
                seat_label.pack(anchor="w")
                
                for seat in configured_seats:
                    is_active = self.check_seat_area(seat["area"])
                    status = "🟢 ACTIVE" if is_active else "🔴 INACTIVE"
                    color = "green" if is_active else "red"
                    
                    result_label = tk.Label(self.results_frame, 
                                          text=f"  {seat['name']}: {status}",
                                          font=("Arial", 10), fg=color)
                    result_label.pack(anchor="w")
                    
                    all_results.append(f"Seat {seat['name']}: {'ACTIVE' if is_active else 'INACTIVE'}")
                    if is_active:
                        active_count += 1
                        
                summary_label = tk.Label(self.results_frame, 
                                       text=f"  Active Players: {active_count}/{len(configured_seats)}",
                                       font=("Arial", 10, "bold"), fg="blue")
                summary_label.pack(anchor="w")
                
        # Capture card areas as screenshots
        if self.card_areas["hole_cards"] or self.card_areas["community_cards"]:
            card_label = tk.Label(self.results_frame, text="Card Screenshots:", 
                                font=("Arial", 11, "bold"), fg="green")
            card_label.pack(anchor="w")
            
            if self.card_areas["hole_cards"]:
                success = self.save_card_area_screenshot(self.card_areas["hole_cards"], "hand.png")
                status = "📸 SAVED as hand.png" if success else "❌ FAILED to save"
                color = "green" if success else "red"
                
                result_label = tk.Label(self.results_frame, 
                                      text=f"  Hole Cards: {status}",
                                      font=("Arial", 10), fg=color)
                result_label.pack(anchor="w")
                all_results.append(f"Hole Cards: {'Screenshot saved as hand.png' if success else 'Failed to save screenshot'}")
                
            if self.card_areas["community_cards"]:
                success = self.save_card_area_screenshot(self.card_areas["community_cards"], "board.png")
                status = "📸 SAVED as board.png" if success else "❌ FAILED to save"
                color = "green" if success else "red"
                
                result_label = tk.Label(self.results_frame, 
                                      text=f"  Community Cards: {status}",
                                      font=("Arial", 10), fg=color)
                result_label.pack(anchor="w")
                all_results.append(f"Community Cards: {'Screenshot saved as board.png' if success else 'Failed to save screenshot'}")
        
        # Show comprehensive results in dedicated window
        if all_results:
            all_results.insert(0, "=== COMPLETE POKER MONITOR RESULTS ===")
            all_results.append("\n=== END OF RESULTS ===")
            ResultsWindow(self.root, "Complete Poker Check Results", all_results)
        
        self.status_label.config(text="Complete check finished!", fg="green")

    def get_hex_color(self, rgb_color):
        """Convert RGB tuple to hex string"""
        try:
            return f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"
        except:
            return "#FFFFFF"

    def update_color_from_entry(self):
        """Update seat color from text entry"""
        color_str = self.color_entry.get()
        try:
            # Try to evaluate as a tuple
            new_color = eval(color_str)
            if isinstance(new_color, tuple) and len(new_color) == 3:
                self.seat_color = new_color
                self.color_swatch.config(bg=self.get_hex_color(self.seat_color))
                self.save_config()
                self.status_label.config(text=f"Color updated to {self.seat_color}", fg="green")
            else:
                raise ValueError
        except:
            messagebox.showerror("Invalid Color", "Please enter a valid RGB tuple, e.g., (255, 0, 0)")

    def set_color_with_mouse(self):
        """Pick seat color from screen using mouse after a countdown"""
        countdown = CountdownWindow(self.root, "Position mouse over the desired color")
        self.root.wait_window(countdown.window)

        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        try:
            screenshot = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
            color = screenshot.getpixel((0, 0))
            self.seat_color = color[:3]  # Ensure RGB format

            self.color_entry.delete(0, tk.END)
            self.color_entry.insert(0, str(self.seat_color))
            self.color_swatch.config(bg=self.get_hex_color(self.seat_color))
            self.save_config()
            self.status_label.config(text=f"Color set to {self.seat_color}", fg="green")
            messagebox.showinfo("Color Set", f"The seat color has been set to {self.seat_color}.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not get pixel color: {e}")
            
    def color_matches_target(self, rgb_color):
        """Check if RGB color matches the configured seat color with tolerance"""
        r, g, b = rgb_color
        target_r, target_g, target_b = self.seat_color

        # Check each component with tolerance
        red_tolerance = target_r * self.tolerance
        green_tolerance = target_g * self.tolerance
        blue_tolerance = target_b * self.tolerance

        return (
            abs(r - target_r) <= red_tolerance and
            abs(g - target_g) <= green_tolerance and
            abs(b - target_b) <= blue_tolerance
        )
        
    def check_seat_area(self, area):
        """Check 5x5 pixel area for target red color"""
        try:
            # Capture 5x5 area
            screenshot = ImageGrab.grab(bbox=(area["x_start"], area["y_start"], 
                                            area["x_end"], area["y_end"]))
            
            # Check each pixel in the 5x5 area
            for x in range(5):
                for y in range(5):
                    try:
                        pixel_color = screenshot.getpixel((x, y))
                        if len(pixel_color) >= 3:  # Ensure RGB format
                            r, g, b = pixel_color[:3]
                            if self.color_matches_target((r, g, b)):
                                return True
                    except:
                        continue
                        
            return False
        except Exception as e:
            # Seat check error - return False
            return False
            
    def check_all_seats(self):
        """Check all configured seats for active players"""
        if not self.seats:
            messagebox.showinfo("No Seats", "No seats configured. Add seats first.")
            return
            
        unconfigured_seats = [seat for seat in self.seats if not seat.get("area")]
        if unconfigured_seats:
            seat_names = ", ".join([seat["name"] for seat in unconfigured_seats])
            messagebox.showwarning("Incomplete Setup", 
                                 f"Please record locations for: {seat_names}")
            return
            
        self.status_label.config(text="Checking all seats...", fg="blue")
        self.root.update()
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Results title
        results_title = tk.Label(self.results_frame, text="Seat Check Results:", 
                               font=("Arial", 12, "bold"))
        results_title.pack(anchor="w")
        
        # Check each seat
        results = []
        active_count = 0
        
        for seat in self.seats:
            if seat.get("area"):
                is_active = self.check_seat_area(seat["area"])
                status = "🟢 ACTIVE" if is_active else "🔴 INACTIVE"
                color = "green" if is_active else "red"
                
                result_label = tk.Label(self.results_frame, 
                                      text=f"{seat['name']}: {status}",
                                      font=("Arial", 10),
                                      fg=color)
                result_label.pack(anchor="w")
                
                results.append(f"{seat['name']}: {'TRUE' if is_active else 'FALSE'}")
                if is_active:
                    active_count += 1
                    
        # Summary
        summary_label = tk.Label(self.results_frame, 
                               text=f"\nActive Players: {active_count}/{len(self.seats)}",
                               font=("Arial", 11, "bold"),
                               fg="blue")
        summary_label.pack(anchor="w")
        
        self.status_label.config(text="Check completed!", fg="green")
        
        # Show detailed results in popup window
        detailed_results = ["=== POKER SEAT CHECK RESULTS ==="] + results
        detailed_results.append(f"\nTotal Active: {active_count}/{len(self.seats)}")
        ResultsWindow(self.root, "Seat Check Results", detailed_results)
        
    def run_ai_analysis(self):
        """Run complete AI analysis: detect players, recognize cards, calculate win probability"""
        # Check if everything is configured
        if not self.card_areas["hole_cards"]:
            messagebox.showwarning("Setup Required", "Please configure hole cards area first!")
            return

        configured_seats = [seat for seat in self.seats if seat.get("area")]
        if not configured_seats:
            messagebox.showwarning("Setup Required", "Please configure at least one player seat!")
            return

        self.status_label.config(text="Running AI analysis...", fg="blue")
        self.root.update()

        try:
            # Import logging function from poker_ai
            from poker_ai import log_to_debug

            # Step 1: Count active opponents
            active_count = 0
            log_to_debug(f"=== AI ANALYSIS: Counting active opponents ===")
            log_to_debug(f"Total configured seats: {len(configured_seats)}")

            for seat in configured_seats:
                is_active = self.check_seat_area(seat["area"])
                status = "ACTIVE" if is_active else "INACTIVE"
                log_to_debug(f"Seat {seat['name']} at ({seat['position'][0]}, {seat['position'][1]}): {status}")
                if is_active:
                    active_count += 1

            # All detected seats are opponents (player is NOT in these seats)
            active_opponents = active_count  # Don't subtract 1!
            log_to_debug(f"Total active opponents: {active_opponents}")
            log_to_debug(f"=== Opponent counting completed ===\n")

            # Step 2: Capture card screenshots
            hand_path = os.path.join(self.imgs_folder, "hand.png")
            board_path = os.path.join(self.imgs_folder, "board.png")

            # Capture hole cards
            if not self.save_card_area_screenshot(self.card_areas["hole_cards"], "hand.png"):
                messagebox.showerror("Error", "Failed to capture hole cards screenshot!")
                self.status_label.config(text="Analysis failed", fg="red")
                return

            # Capture community cards (if area is set)
            community_cards = ""
            if self.card_areas["community_cards"]:
                self.save_card_area_screenshot(self.card_areas["community_cards"], "board.png")

            # Step 3: Recognize cards (2 parallel Haiku API calls)
            self.status_label.config(text="Recognizing cards (AI)...", fg="blue")
            self.root.update()

            player_hand, board_cards = self.poker_ai.recognize_cards_parallel(hand_path, board_path)

            if not player_hand:
                messagebox.showerror("Error", "Failed to recognize hole cards! Check the screenshot.")
                self.status_label.config(text="Analysis failed", fg="red")
                return

            # Use board cards if available
            if board_cards and board_cards.strip():
                community_cards = board_cards

            # Step 4: Calculate win probability (Monte Carlo simulation)
            self.status_label.config(text="Calculating odds (Monte Carlo ~1.5s)...", fg="blue")
            self.root.update()

            win_probability = self.poker_ai.calculate_win_probability(
                player_hand=player_hand,
                community_cards=community_cards,
                active_opponents=active_opponents
            )

            if not win_probability:
                messagebox.showerror("Error", "Failed to calculate win probability!")
                self.status_label.config(text="Analysis failed", fg="red")
                return

            # Step 5: Display result
            self.status_label.config(text="Analysis complete!", fg="green")

            # Show detailed info in console/log
            analysis_details = [
                "=== AI POKER ANALYSIS (Monte Carlo) ===",
                f"Player Hand: {player_hand}",
                f"Community Cards: {community_cards if community_cards else 'None (pre-flop)'}",
                f"Active Opponents: {active_opponents}",
                f"Win Probability: {win_probability}",
                f"Method: Monte Carlo (100k iterations, ±0.15% accuracy)",
                "========================================"
            ]

            # Show detailed results window
            ResultsWindow(self.root, "AI Poker Analysis", analysis_details)

            # Show large probability popup
            WinProbabilityPopup(self.root, win_probability, duration=5)

        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Analysis failed", fg="red")

    def clear_all_config(self):
        """Clear all configurations: seats, card areas, and color"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all settings?"):
            self.seats = []
            self.card_areas = {"hole_cards": None, "community_cards": None}
            self.seat_color = (149, 73, 70)  # Reset to default

            self.update_seat_list()
            self.update_card_areas_display()
            
            # Update color UI
            self.color_entry.delete(0, tk.END)
            self.color_entry.insert(0, str(self.seat_color))
            self.color_swatch.config(bg=self.get_hex_color(self.seat_color))

            self.save_config()
            self.status_label.config(text="All settings cleared!", fg="red")

    def save_config(self):
        """Save complete configuration to JSON file"""
        try:
            config_data = {
                "seats": self.seats,
                "card_areas": self.card_areas,
                "seat_color": self.seat_color
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            # Config save error - could show GUI notification if needed
            pass
            
    def load_config(self):
        """Load complete configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Handle both old and new config formats
                if isinstance(config_data, list):
                    # Old format - just seats
                    self.seats = config_data
                    self.card_areas = {"hole_cards": None, "community_cards": None}
                else:
                    # New format - seats and card areas
                    self.seats = config_data.get("seats", [])
                    self.card_areas = config_data.get("card_areas", {"hole_cards": None, "community_cards": None})
                    self.seat_color = tuple(config_data.get("seat_color", (149, 73, 70))) # Load color, default to red

        except Exception as e:
            # Config load error - show error and use defaults
            messagebox.showerror("Config Error", f"Could not load config: {e}")
            self.seats = []
            self.card_areas = {"hole_cards": None, "community_cards": None}

        # Update UI with loaded color
        self.color_entry.delete(0, tk.END)
        self.color_entry.insert(0, str(self.seat_color))
        self.color_swatch.config(bg=self.get_hex_color(self.seat_color))

def main():
    """Main application entry point"""
    lock_file_path = os.path.expanduser("~/.poker_monitor.lock")

    # Check if lock file exists and if the process is actually running
    if os.path.exists(lock_file_path):
        try:
            with open(lock_file_path, "r") as f:
                pid = int(f.read().strip())

            # Check if process is actually running
            import signal
            try:
                os.kill(pid, 0)  # Doesn't kill, just checks if process exists
                messagebox.showwarning("Already Running", "An instance of Poker Monitor is already running.")
                return
            except OSError:
                # Process not running, remove stale lock file
                os.remove(lock_file_path)
        except (ValueError, IOError):
            # Invalid lock file, remove it
            os.remove(lock_file_path)

    try:
        with open(lock_file_path, "w") as f:
            f.write(str(os.getpid()))

        root = tk.Tk()
        app = PokerSeatMonitor(root)
        
        # Set window to always stay on top
        root.attributes('-topmost', True)
        
        # Center the window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        
        root.mainloop()
    finally:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)


if __name__ == "__main__":
    main()
