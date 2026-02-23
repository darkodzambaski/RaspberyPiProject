import tkinter as tk
from tkinter import messagebox
import RPi.GPIO as GPIO
import time

class StepperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CNC Precision Controller")
        
        # Set to fullscreen for the industrial look
        self.root.attributes('-fullscreen', True) 
        self.root.config(cursor="none") # Hides mouse cursor
        self.root.configure(bg="#121212")

        # --- GPIO SETUP ---
        self.out1, self.out2, self.out3, self.out4 = 13, 11, 15, 12
        self.limit_switch = 16
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([self.out1, self.out2, self.out3, self.out4], GPIO.OUT)
        # Internal pull-up means the switch should connect Pin 16 to Ground (GND)
        GPIO.setup(self.limit_switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.motor_state = 0  
        self.steps_per_cm = 80.0 

        # --- UI LAYOUT ---
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(root, bg="#121212")
        main_frame.grid(row=1, column=0)

        tk.Label(main_frame, text="ВНЕСИ ДИМЕНЗИЈА", font=("Arial", 24, "bold"), bg="#121212", fg="#aaaaaa").pack()
        
        input_frame = tk.Frame(main_frame, bg="#121212")
        input_frame.pack(pady=10)

        self.entry_dim = tk.Entry(input_frame, width=10, font=("Arial", 70, "bold"), justify='center', bg="#1e1e1e", fg="#ffffff", borderwidth=0)
        self.entry_dim.pack(side=tk.LEFT)
        tk.Label(input_frame, text="cm", font=("Arial", 40, "bold"), bg="#121212", fg="#ffffff").pack(side=tk.LEFT, padx=15)

        tk.Label(main_frame, text="Моментална Позиција:", font=("Arial", 16, "bold"), bg="#121212", fg="#aaaaaa").pack(pady=(40, 0))
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
        time.sleep(0.003) # Speed control

    def home_motor(self):
        print("\n[HOME] Moving to physical zero...")
        self.lbl_status.config(text="СЕ ВРАЌАМ НА ПОЧЕТОК...", fg="#e74c3c")
        self.root.update()
        
        step_count = 0
        # Loop runs as long as limit switch is NOT pressed (HIGH)
        while GPIO.input(self.limit_switch) == GPIO.HIGH:
            self.move_one_step(-1)
            step_count += 1
            if step_count % 50 == 0:
                print(f"Homing steps: {step_count}")

        # Shut off coils and update UI
        GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
        self.lbl_current_pos.config(text="0.00 cm")
        self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")
        self.entry_dim.delete(0, tk.END)
        print(f"[HOME] Done. Steps: {step_count}\n")

    def handle_movement(self, event=None):
        try:
            val_str = self.entry_dim.get()
            if not val_str: return
            
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
        dist = target - current
        if abs(dist) < 0.001: return 

        steps = int(abs(dist * self.steps_per_cm))
        direction = 1 if dist > 0 else -1
        
        print(f"[MOVE] {current:.2f} -> {target:.2f} | Total Steps: {steps}")
        self.lbl_status.config(text="ВО ДВИЖЕЊЕ...", fg="#3498db")
        self.root.update()

        for i in range(steps):
            # Physical safety: stop if moving back and switch is triggered
            if direction == -1 and GPIO.input(self.limit_switch) == GPIO.LOW:
                print("!! LIMIT REACHED EARLY !!")
                target = 0.0
                break
            self.move_one_step(direction)
            if i % 100 == 0:
                print(f"Step: {i} / {steps}")
        
        GPIO.output([self.out1, self.out2, self.out3, self.out4], GPIO.LOW)
        self.lbl_current_pos.config(text="{:.2f} cm".format(target))
        self.lbl_status.config(text="ПОДГОТВЕНО", fg="#39ff14")
        print("[MOVE] Finished.\n")

    def cleanup_and_exit(self):
        GPIO.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StepperApp(root)
    root.mainloop()