import tkinter as tk
from tkinter import messagebox
import RPi.GPIO as GPIO
import time

class StepperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CNC Controller")
        self.root.attributes('-fullscreen', True) 
        self.root.configure(bg="#121212")

        # --- GPIO SETUP ---
        self.out1, self.out2, self.out3, self.out4 = 13, 11, 15, 12
        self.limit_switch = 16  
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([self.out1, self.out2, self.out3, self.out4], GPIO.OUT)
        GPIO.setup(self.limit_switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.motor_state = 0  
        self.steps_per_mm = 8 # CALIBRATION: Change this so 1mm on screen = 1mm real life

        # --- UI LAYOUT ---
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(root, bg="#121212")
        main_frame.grid(row=1, column=0)

        tk.Label(main_frame, text="ВНЕСИ ДИМЕНЗИЈА", font=("Arial", 24, "bold"), bg="#121212", fg="#aaaaaa").pack()
        
        input_frame = tk.Frame(main_frame, bg="#121212")
        input_frame.pack(pady=10)

        self.entry_dim = tk.Entry(input_frame, width=8, font=("Arial", 70, "bold"), justify='center', bg="#1e1e1e", fg="#ffffff", borderwidth=0)
        self.entry_dim.pack(side=tk.LEFT)
        tk.Label(input_frame, text="mm", font=("Arial", 40, "bold"), bg="#121212", fg="#ffffff").pack(side=tk.LEFT, padx=15, pady=(25,0))

        tk.Label(main_frame, text="Моментална Позиција:", font=("Arial", 16, "bold"), bg="#121212", fg="#aaaaaa").pack(pady=(40, 0))
        self.lbl_current_pos = tk.Label(main_frame, text="--- mm", font=("Arial", 60, "bold"), fg="#39ff14", bg="#121212")
        self.lbl_current_pos.pack()

        self.lbl_status = tk.Label(main_frame, text="ПОТРЕБЕН Е ХОМИНГ", font=("Arial", 12), fg="#f1c40f", bg="#121212")
        self.lbl_status.pack(pady=10)

        # --- BINDINGS ---
        self.entry_dim.focus_set()
        self.root.bind('<Return>', self.handle_movement)
        self.root.bind('<KP_Enter>', self.handle_movement)
        self.root.bind('*', lambda e: self.home_motor())
        self.root.bind('-', lambda e: self.cleanup_and_exit())

        # Auto-home on startup
        self.root.after(1000, self.home_motor)

    def set_pins(self, state):
        # Full 8-step half-step sequence
        sequences = [
            (1,0,0,1), (1,0,0,0), (1,1,0,0), (0,1,0,0),
            (0,1,1,0), (0,0,1,0), (0,0,1,1), (0,0,0,1)
        ]
        s = sequences[state]
        GPIO.output(self.out1, s[0])
        GPIO.output(self.out2, s[1])
        GPIO.output(self.out3, s[2])
        GPIO.output(self.out4, s[3])

    def move_one_step(self, direction):
        self.motor_state = (self.motor_state + direction) % 8
        self.set_pins(self.motor_state)
        time.sleep(0.003) # Adjust for motor speed/torque

    def home_motor(self):
        """Physical homing using the taster."""
        self.lbl_status.config(text="СЕ ВРАЌАМ НА ПОЧЕТОК...", fg="#e74c3c")
        self.root.update()

        # Move backwards (-1) until switch is pressed (LOW)
        while GPIO.input(self.limit_switch) == GPIO.HIGH:
            self.move_one_step(-1)

        # Stop and zero out
        GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
        self.lbl_current_pos.config(text="0 mm")
        self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")
        self.entry_dim.delete(0, tk.END)

    def handle_movement(self, event=None):
        try:
            target_val = self.entry_dim.get()
            if not target_val: return
            
            target = int(target_val)
            current_str = self.lbl_current_pos.cget("text").split()[0]
            if current_str == "---": 
                messagebox.showwarning("Внимание", "Прво направете Хоминг (*)")
                return
            
            current = int(current_str)
            mm_to_move = target - current
            steps_to_move = mm_to_move * self.steps_per_mm
            
            if steps_to_move == 0: return

            direction = 1 if steps_to_move > 0 else -1
            self.lbl_status.config(text="ВО ДВИЖЕЊЕ...", fg="#3498db")
            self.root.update()

            for _ in range(abs(steps_to_move)):
                # Safety: if moving backward, stop if switch is hit
                if direction == -1 and GPIO.input(self.limit_switch) == GPIO.LOW:
                    target = 0 # Force target to 0 if we hit the wall early
                    break
                self.move_one_step(direction)
            
            GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
            self.lbl_current_pos.config(text=f"{target} mm")
            self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")
            self.entry_dim.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Грешка", "Внеси само цели броеви")
            self.entry_dim.delete(0, tk.END)

    def cleanup_and_exit(self):
        GPIO.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StepperApp(root)
    root.mainloop()