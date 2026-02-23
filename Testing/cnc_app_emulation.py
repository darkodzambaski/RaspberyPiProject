import tkinter as tk
from tkinter import messagebox
import time

# --- SIMULATION LOGIC ---
try:
    import RPi.GPIO as GPIO
    IS_SIMULATION = False
except ImportError:
    import unittest.mock as mock
    GPIO = mock.MagicMock()
    GPIO.BOARD = 'BOARD'; GPIO.OUT = 'OUT'; GPIO.IN = 'IN'; GPIO.PUD_UP = 'PUD_UP'
    GPIO.HIGH = 1; GPIO.LOW = 0
    GPIO.input.return_value = 1 
    IS_SIMULATION = True
    print("--- RUNNING IN SIMULATION MODE ---")

class StepperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CNC Precision Controller")
        
        if IS_SIMULATION:
            self.root.geometry("700x500")
        else:
            self.root.attributes('-fullscreen', True) 
            
        self.root.configure(bg="#121212")

        # --- GPIO SETUP ---
        self.out1, self.out2, self.out3, self.out4 = 13, 11, 15, 12
        self.limit_switch = 16
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([self.out1, self.out2, self.out3, self.out4], GPIO.OUT)
        GPIO.setup(self.limit_switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.motor_state = 0  
        # Calibration: How many steps to move exactly 1 cm?
        # Use a float here too for high precision
        self.steps_per_cm = 80

        # --- UI LAYOUT ---
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(root, bg="#121212")
        main_frame.grid(row=1, column=0)

        tk.Label(main_frame, text="ВНЕСИ ДИМЕНЗИЈА", font=("Arial", 24, "bold"), bg="#121212", fg="#aaaaaa").pack()
        
        input_frame = tk.Frame(main_frame, bg="#121212")
        input_frame.pack(pady=10)

        # Entry now accepts floats
        self.entry_dim = tk.Entry(input_frame, width=10, font=("Arial", 70, "bold"), justify='center', bg="#1e1e1e", fg="#ffffff", borderwidth=0)
        self.entry_dim.pack(side=tk.LEFT)
        tk.Label(input_frame, text="cm", font=("Arial", 40, "bold"), bg="#121212", fg="#ffffff").pack(side=tk.LEFT, padx=15)

        tk.Label(main_frame, text="Моментална Позиција:", font=("Arial", 16, "bold"), bg="#121212", fg="#aaaaaa").pack(pady=(40, 0))
        # Formatted to 0.00
        self.lbl_current_pos = tk.Label(main_frame, text="--- cm", font=("Arial", 60, "bold"), fg="#39ff14", bg="#121212")
        self.lbl_current_pos.pack()

        self.lbl_status = tk.Label(main_frame, text="READY", font=("Arial", 12), fg="#f1c40f", bg="#121212")
        self.lbl_status.pack(pady=10)

        # --- BINDINGS ---
        self.entry_dim.focus_set()
        self.root.bind('<Return>', self.handle_movement)
        self.root.bind('<KP_Enter>', self.handle_movement)
        self.root.bind('*', lambda e: self.home_motor()) 
        self.root.bind('/', lambda e: self.cleanup_and_exit())
        #self.root.bind('<Escape>', lambda e: self.cleanup_and_exit())

        # Auto-home on startup
        self.root.after(1000, self.home_motor)

    def set_pins(self, state):
        sequences = [(1,0,0,1), (1,0,0,0), (1,1,0,0), (0,1,0,0), (0,1,1,0), (0,0,1,0), (0,0,1,1), (0,0,0,1)]
        s = sequences[state]
        GPIO.output(self.out1, s[0])
        GPIO.output(self.out2, s[1])
        GPIO.output(self.out3, s[2])
        GPIO.output(self.out4, s[3])

    def move_one_step(self, direction):
        self.motor_state = (self.motor_state + direction) % 8
        self.set_pins(self.motor_state)
        time.sleep(0.001 if IS_SIMULATION else 0.003)

    def home_motor(self):
        self.lbl_status.config(text="СЕ ВРАЌАМ НА ПОЧЕТОК...", fg="#e74c3c")
        self.root.update()
        
        if IS_SIMULATION:
            time.sleep(1)
        else:
            while GPIO.input(self.limit_switch) == GPIO.HIGH:
                self.move_one_step(-1)

        GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
        self.lbl_current_pos.config(text="0.00 cm")
        self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")
        self.entry_dim.delete(0, tk.END)

    def handle_movement(self, event=None):
        try:
            val_str = self.entry_dim.get()
            if not val_str: return
            
            # Use float instead of int
            target = float(val_str)
            current_str = self.lbl_current_pos.cget("text").split()[0]
            if current_str == "---": return
            
            current = float(current_str)
            
            if target < 0:
                self.entry_dim.delete(0, tk.END)
                return

            self.execute_move(current, target)
            self.entry_dim.delete(0, tk.END)
        except ValueError:
            self.entry_dim.delete(0, tk.END)

    def execute_move(self, current, target):
        cm_to_move = target - current
        if abs(cm_to_move) < 0.001: return # Ignore tiny movements

        steps = cm_to_move * self.steps_per_cm
        direction = 1 if steps > 0 else -1
        
        self.lbl_status.config(text="ВО ДВИЖЕЊЕ...", fg="#3498db")
        self.root.update()

        # abs(int(steps)) rounds to the nearest whole step
        for _ in range(abs(int(steps))):
            if not IS_SIMULATION and direction == -1 and GPIO.input(self.limit_switch) == GPIO.LOW:
                target = 0.0
                break
            self.move_one_step(direction)
        
        GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
        
        # Display formatted to 2 decimal places
        self.lbl_current_pos.config(text="{:.1f} cm".format(target))
        self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")

    def cleanup_and_exit(self):
        if not IS_SIMULATION:
            GPIO.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StepperApp(root)
    root.mainloop()