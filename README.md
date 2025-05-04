# Pomodoro CLI

A beautiful command line Pomodoro Timer written in Python.

## Features

- Beautiful ASCII tomato art that changes color based on the current phase
- Progress bar visualization
- Terminal bell notifications at the end of each phase
- Two interface modes: curses (default) and terminal
- Customizable work/break durations via command line arguments
- Debug mode for accelerated timing (useful for testing)

## Installation

Clone this repository:

```bash
git clone https://github.com/andreikorchagin/pomodoro-cli.git
cd pomodoro-cli
```

No additional dependencies required beyond Python 3.

## Usage

Run the timer with default settings:

```bash
python3 pomodoro.py
```

### Command Line Options

- `--work N`: Set work duration in minutes (default: 25)
- `--short-break N`: Set short break duration in minutes (default: 5)
- `--long-break N`: Set long break duration in minutes (default: 15)
- `--cycles N`: Set number of work cycles before a long break (default: 4)
- `--no-curses`: Use simple terminal mode instead of curses interface
- `--debug N`: Enable debug mode with time acceleration factor N (e.g., 10, 20, 60)

### Curses vs Terminal Mode

The app has two display modes:

**Curses Mode (Default)**: 
- Uses the Python curses library for a more interactive interface
- Provides smoother updates and better visual appearance
- Handles window resizing
- Better key input handling

**Terminal Mode** (activated with `--no-curses`):
- Uses simple terminal output with ANSI color codes
- More compatible with different terminal environments
- Less resource-intensive
- May be preferable in certain terminal emulators or when SSH'ing into a remote machine

### Examples

```bash
# Use 30 minute work periods and 10 minute breaks
python3 pomodoro.py --work 30 --short-break 10

# Run in terminal mode (without curses)
python3 pomodoro.py --no-curses

# Run with time accelerated by 60x (for testing)
python3 pomodoro.py --debug 60
```

### Controls

- `s`: Start/Resume timer
- `p`: Pause timer
- `n`: Skip to next phase
- `r`: Reset timer
- `q`: Quit

## The Pomodoro Technique

The Pomodoro Technique is a time management method developed by Francesco Cirillo. The standard technique uses:

1. 25-minute work periods (pomodoros)
2. 5-minute short breaks between pomodoros
3. 15-minute long breaks after 4 pomodoros

This app follows these standard intervals by default but allows you to customize them to your preference.

## License

MIT