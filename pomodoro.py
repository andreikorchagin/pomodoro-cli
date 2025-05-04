#!/usr/bin/env python3
"""
Pomodoro CLI - A beautiful command line Pomodoro Timer
"""
import time
import sys
import os
import argparse
import threading
import datetime
from dataclasses import dataclass
from enum import Enum, auto
import curses
from curses import wrapper

# ANSI color codes
class Color:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
# State enumeration
class State(Enum):
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    PAUSED = auto()
    IDLE = auto()

@dataclass
class PomodoroSettings:
    work_duration: int = 25 * 60       # 25 minutes
    short_break_duration: int = 5 * 60  # 5 minutes
    long_break_duration: int = 15 * 60  # 15 minutes
    cycles_before_long_break: int = 4
    time_acceleration: int = 1         # Default: normal speed
    
class PomodoroTimer:
    def __init__(self, settings=None, stdscr=None):
        self.settings = settings or PomodoroSettings()
        self.stdscr = stdscr
        self.current_state = State.IDLE
        self.time_left = 0
        self.cycles_completed = 0
        self.is_running = False
        self.pause_timer = False
        self.timer_thread = None
        self.start_time = None

    def start(self):
        """Start the Pomodoro timer"""
        if self.current_state == State.IDLE or self.current_state == State.PAUSED:
            if self.current_state == State.IDLE:
                self.current_state = State.WORK
                self.time_left = self.settings.work_duration
            
            self.pause_timer = False
            self.is_running = True
            
            if self.timer_thread is None or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self._run_timer)
                self.timer_thread.daemon = True
                self.timer_thread.start()
                
            self.start_time = time.time()

    def pause(self):
        """Pause the timer"""
        if self.is_running:
            self.pause_timer = True
            self.current_state = State.PAUSED

    def resume(self):
        """Resume the timer"""
        if self.current_state == State.PAUSED:
            self.pause_timer = False
            # Restore the previous state before pausing
            self.start()

    def skip(self):
        """Skip to the next phase"""
        self._transition_to_next_state()
        self.start_time = time.time()

    def reset(self):
        """Reset the timer"""
        self.is_running = False
        self.current_state = State.IDLE
        self.cycles_completed = 0
        self.time_left = 0
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(0.1)
        self.timer_thread = None

    def _run_timer(self):
        """Run the timer in a separate thread"""
        # Variable to track when to update the display (to prevent flickering)
        last_update_time = 0
        update_interval = 0.5  # Update display every 0.5 seconds
        
        while self.is_running:
            if not self.pause_timer:
                if self.time_left <= 0:
                    self._play_bell()
                    self._transition_to_next_state()
                    self.start_time = time.time()
                    last_update_time = 0  # Force update after state transition
                else:
                    time.sleep(0.05)  # Smaller sleep for smoother acceleration
                    
                    # Calculate acceleration factor
                    accel = self.settings.time_acceleration
                    
                    # Apply acceleration to elapsed time
                    real_elapsed = time.time() - self.start_time
                    accelerated_elapsed = real_elapsed * accel
                    
                    # Calculate time left based on current state
                    if self.current_state == State.WORK:
                        self.time_left = max(0, self.settings.work_duration - int(accelerated_elapsed))
                    elif self.current_state == State.SHORT_BREAK:
                        self.time_left = max(0, self.settings.short_break_duration - int(accelerated_elapsed))
                    else:  # Long break
                        self.time_left = max(0, self.settings.long_break_duration - int(accelerated_elapsed))
                    
                    # Only update display at specified intervals to prevent flickering
                    current_time = time.time()
                    if (current_time - last_update_time) >= update_interval:
                        self._update_display()
                        last_update_time = current_time
            else:
                time.sleep(0.1)  # When paused, just sleep a bit
                
                # Always update when paused (not frequent enough to cause flickering)
                current_time = time.time()
                if (current_time - last_update_time) >= update_interval:
                    self._update_display()
                    last_update_time = current_time

    def _transition_to_next_state(self):
        """Transition to the next state based on current state"""
        if self.current_state == State.WORK:
            self.cycles_completed += 1
            if self.cycles_completed % self.settings.cycles_before_long_break == 0:
                self.current_state = State.LONG_BREAK
                self.time_left = self.settings.long_break_duration
            else:
                self.current_state = State.SHORT_BREAK
                self.time_left = self.settings.short_break_duration
        else:  # After any break, go back to work
            self.current_state = State.WORK
            self.time_left = self.settings.work_duration

    def _play_bell(self):
        """Play terminal bell sound"""
        for _ in range(3):  # Ring the bell 3 times
            print("\a", end="", flush=True)
            time.sleep(0.3)

    def get_display_color(self):
        """Get the color based on the current state"""
        if self.current_state == State.WORK:
            return Color.RED
        elif self.current_state == State.SHORT_BREAK:
            return Color.GREEN
        elif self.current_state == State.LONG_BREAK:
            return Color.BLUE
        elif self.current_state == State.PAUSED:
            return Color.YELLOW
        return Color.RESET

    def get_progress_bar(self, width=50):
        """Return a text-based progress bar"""
        if self.current_state == State.IDLE:
            return " " * width
            
        total_duration = 0
        if self.current_state == State.WORK:
            total_duration = self.settings.work_duration
        elif self.current_state == State.SHORT_BREAK:
            total_duration = self.settings.short_break_duration
        elif self.current_state == State.LONG_BREAK:
            total_duration = self.settings.long_break_duration
        elif self.current_state == State.PAUSED:
            # For paused state, use the time_left and determine what the total was
            if self.time_left <= self.settings.work_duration:
                total_duration = self.settings.work_duration
            elif self.time_left <= self.settings.short_break_duration:
                total_duration = self.settings.short_break_duration
            else:
                total_duration = self.settings.long_break_duration
                
        progress = 1 - (self.time_left / total_duration) if total_duration > 0 else 0
        completed_width = int(width * progress)
        return "█" * completed_width + "░" * (width - completed_width)

    def get_ascii_tomato(self):
        """Return ASCII art of a tomato"""
        color = self.get_display_color()
        
        tomato = [
            f"{Color.GREEN}    .,,.    ",
            f"{Color.GREEN}  ,;;'''';;,  ",
            f"{color}  ;;    ;;  ",
            f"{color} ;;      ;; ",
            f"{color} ;;      ;; ",
            f"{color}  ;;    ;;  ",
            f"{color}  ';;,,;;'  ",
            f"{Color.RESET}",
        ]
        
        if self.current_state == State.PAUSED:
            pause_line = f"{Color.YELLOW}  PAUSED  {Color.RESET}"
            tomato[3] = pause_line
            
        return "\n".join(tomato)

    def get_time_display(self):
        """Return formatted time display"""
        minutes, seconds = divmod(self.time_left, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_phase_name(self):
        """Return the name of the current phase"""
        if self.current_state == State.WORK:
            return "FOCUS TIME"
        elif self.current_state == State.SHORT_BREAK:
            return "SHORT BREAK"
        elif self.current_state == State.LONG_BREAK:
            return "LONG BREAK"
        elif self.current_state == State.PAUSED:
            return "PAUSED"
        else:
            return "READY"

    def _update_display(self):
        """Update the display with current timer state"""
        if not self.stdscr:
            # If running in terminal mode (not curses)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            color = self.get_display_color()
            
            print(f"\n{Color.BOLD}🍅 Pomodoro CLI 🍅{Color.RESET}")
            print(f"\n{color}{Color.BOLD}{self.get_phase_name()}{Color.RESET}")
            
            print(f"\n{self.get_ascii_tomato()}")
            
            print(f"\n{color}{Color.BOLD}{self.get_time_display()}{Color.RESET}")
            
            progress_bar = self.get_progress_bar(width=50)
            print(f"\n{color}[{progress_bar}]{Color.RESET}")
            
            print(f"\n{Color.CYAN}Pomodoros completed: {self.cycles_completed}{Color.RESET}")
            
            print("\nControls:")
            print(f"{Color.WHITE}s: start/resume | p: pause | n: skip to next | r: reset | q: quit{Color.RESET}")
        else:
            # Curses mode
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            # Center calculations
            center_y = height // 2 - 5
            center_x = width // 2
            
            self.stdscr.addstr(center_y - 3, center_x - 10, "🍅 Pomodoro CLI 🍅", curses.A_BOLD)
            
            # Phase name
            phase_name = self.get_phase_name()
            self.stdscr.addstr(center_y - 1, center_x - len(phase_name) // 2, phase_name, curses.A_BOLD)
            
            # ASCII tomato - in simpler form for curses
            tomato_lines = self.get_ascii_tomato().split('\n')
            for i, line in enumerate(tomato_lines):
                # Strip ANSI color codes for curses
                clean_line = line.replace(Color.GREEN, '').replace(Color.RED, '') \
                                  .replace(Color.BLUE, '').replace(Color.YELLOW, '') \
                                  .replace(Color.RESET, '')
                self.stdscr.addstr(center_y + i + 1, center_x - len(clean_line) // 2, clean_line)
            
            # Timer display
            time_display = self.get_time_display()
            self.stdscr.addstr(center_y + 10, center_x - len(time_display) // 2, time_display, curses.A_BOLD)
            
            # Progress bar
            progress_bar = self.get_progress_bar(width=40)
            self.stdscr.addstr(center_y + 12, center_x - 20, f"[{progress_bar}]")
            
            # Pomodoros completed
            completed_text = f"Pomodoros completed: {self.cycles_completed}"
            self.stdscr.addstr(center_y + 14, center_x - len(completed_text) // 2, completed_text)
            
            # Controls
            controls = "s: start/resume | p: pause | n: skip to next | r: reset | q: quit"
            self.stdscr.addstr(height - 2, center_x - len(controls) // 2, controls)
            
            self.stdscr.refresh()

def handle_key_events(timer, stdscr=None):
    """Handle keyboard input"""
    while timer.is_running:
        if stdscr:
            # Curses mode
            key = stdscr.getch()
            if key == ord('q'):
                timer.reset()
                return False
            elif key == ord('s'):
                timer.start()
            elif key == ord('p'):
                timer.pause()
            elif key == ord('n'):
                timer.skip()
            elif key == ord('r'):
                timer.reset()
                timer.start()
        else:
            # Terminal mode
            if sys.stdin.isatty():
                import termios
                import tty
                import select
                
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    
                    # Check if there's input available
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)
                        
                        if key == 'q':
                            timer.reset()
                            return False
                        elif key == 's':
                            timer.start()
                        elif key == 'p':
                            timer.pause()
                        elif key == 'n':
                            timer.skip()
                        elif key == 'r':
                            timer.reset()
                            timer.start()
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            else:
                time.sleep(0.1)  # Sleep to prevent CPU hogging in non-interactive mode
                
    return True

def curses_main(stdscr, settings):
    """Main function for curses interface"""
    # Set up curses
    curses.curs_set(0)  # Hide cursor
    stdscr.timeout(100)  # Non-blocking input
    
    # Create timer with curses screen and settings
    timer = PomodoroTimer(settings=settings, stdscr=stdscr)
    timer.is_running = True
    timer.start()
    
    # Handle key events
    running = True
    last_display_update = 0
    display_interval = 0.5  # Only update display every 0.5 seconds to prevent flickering
    
    while running:
        running = handle_key_events(timer, stdscr)
        if not timer.is_running:
            break
        
        # Only update the display at specified intervals to prevent flickering
        current_time = time.time()
        if (current_time - last_display_update) >= display_interval:
            timer._update_display()
            last_display_update = current_time
            
        time.sleep(0.05)  # Smaller sleep for better responsiveness

def terminal_main(settings):
    """Main function for terminal interface"""
    timer = PomodoroTimer(settings=settings)
    timer.is_running = True
    timer.start()
    
    running = True
    last_display_update = 0
    display_interval = 0.5  # Only update display every 0.5 seconds to prevent flickering
    
    while running:
        running = handle_key_events(timer)
        if not timer.is_running:
            break
        
        # Only update the display at specified intervals to prevent flickering
        current_time = time.time()
        if (current_time - last_display_update) >= display_interval:
            timer._update_display()
            last_display_update = current_time
            
        time.sleep(0.05)  # Smaller sleep for better responsiveness

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Pomodoro CLI - A beautiful command line Pomodoro Timer')
    
    parser.add_argument('--work', type=int, default=25,
                        help='Work duration in minutes (default: 25)')
    parser.add_argument('--short-break', type=int, default=5,
                        help='Short break duration in minutes (default: 5)')
    parser.add_argument('--long-break', type=int, default=15,
                        help='Long break duration in minutes (default: 15)')
    parser.add_argument('--cycles', type=int, default=4,
                        help='Number of work cycles before a long break (default: 4)')
    parser.add_argument('--no-curses', action='store_true',
                        help='Use terminal mode instead of curses interface')
    parser.add_argument('--debug', type=int, default=1, 
                        help='Debug mode with accelerated timing. Use values like 10, 20, 60 to speed up time (default: 1)')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create settings from arguments
    settings = PomodoroSettings(
        work_duration=args.work * 60,
        short_break_duration=args.short_break * 60,
        long_break_duration=args.long_break * 60,
        cycles_before_long_break=args.cycles,
        time_acceleration=args.debug
    )
    
    print(f"{Color.BOLD}🍅 Pomodoro CLI 🍅{Color.RESET}")
    print(f"Starting Pomodoro timer with:")
    print(f"- Work: {args.work} minutes")
    print(f"- Short break: {args.short_break} minutes")
    print(f"- Long break: {args.long_break} minutes")
    print(f"- Cycles before long break: {args.cycles}")
    
    # Show debug mode if active
    if args.debug > 1:
        print(f"{Color.YELLOW}- DEBUG MODE: Time accelerated {args.debug}x{Color.RESET}")
        
    print("\nPress any key to continue...")
    
    # Use raw mode to capture a single keypress
    if sys.stdin.isatty():
        import termios
        import tty
        
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            sys.stdin.read(1)  # Read a single character
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    else:
        # Fall back to input() if not in a terminal
        input()
    
    try:
        if args.no_curses or not sys.stdout.isatty():
            # Use terminal mode
            os.system('cls' if os.name == 'nt' else 'clear')
            terminal_main(settings)
        else:
            # Use curses interface with settings
            curses_main_wrapper = lambda stdscr: curses_main(stdscr, settings)
            wrapper(curses_main_wrapper)
    except KeyboardInterrupt:
        print("\nExiting PomoDoro CLI. Goodbye!")
    
if __name__ == "__main__":
    main()