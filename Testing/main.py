import tkinter as tk
from tkinter import messagebox

class StepperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Numpad CNC Controller")
        self.root.geometry("450x400")
        self.root.configure(bg="#f0f0f0")

        # --- UI Elements ---
        tk.Label(root, text="ВНЕСИ ДИМЕНЗИЈА", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=(20, 5))
        
        # Input Frame to hold Entry + "mm" label side-by-side
        input_frame = tk.Frame(root, bg="#f0f0f0")
        input_frame.pack(pady=10)

        self.entry_dim = tk.Entry(input_frame, width=10, font=("Arial", 24), justify='center')
        self.entry_dim.pack(side=tk.LEFT)
        
        tk.Label(input_frame, text="mm", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(side=tk.LEFT, padx=10)

        # Last Position Display (Read-only feel)
        tk.Label(root, text="Моментална Позиција:", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(20, 0))
        self.lbl_current_pos = tk.Label(root, text="0 mm", font=("Arial", 20, "bold"), fg="#2c3e50", bg="#f0f0f0")
        self.lbl_current_pos.pack()

        # --- Debug / Home Section ---
        # Since you use a numpad, we can bind a specific key (like 'H' or '/') to Home
        self.btn_home = tk.Button(root, text="[*] Почетна позиција", command=self.home_motor, 
                                  bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), pady=10)
        self.btn_home.pack(pady=30)

        # --- KEY BINDINGS ---
        self.entry_dim.focus_set()
        self.root.bind('<Return>', self.handle_movement)    # Standard Enter
        self.root.bind('<KP_Enter>', self.handle_movement) # Numpad Enter
        self.root.bind('*', lambda e: self.home_motor())   # Press '*' to Home
       
        # --- STARTUP LOGIC ---
        # This runs as soon as the window opens
        self.root.after(500, self.initial_homing)

    def initial_homing(self):
        """Automatically called on power-up."""
        print("System Start: Commencing Initial Homing...")
        self.home_motor()

    def home_motor(self):
        """Logic to move motor until it hits the limit switch."""
        print("DEBUG: Moving motor to Home (Limit Switch)...")
        # --- Your Stepper Homing Code Goes Here ---
        # 1. Spin motor backwards slowly
        # 2. Wait for GPIO Pin (Limit Switch) to go HIGH
        # 3. Stop motor and set position to 0
        
        self.current_position = 0
        self.update_ui(0)
        self.entry_dim.delete(0, tk.END)
        print("System Homed.")

    def handle_movement(self, event=None):
        try:
            target_val = self.entry_dim.get()
            if not target_val: return
            
            target = float(target_val)
            current = float(self.lbl_current_pos.cget("text").replace(" mm", ""))
            
            distance = target - current
            
            # --- Hardware Movement ---
            self.execute_stepper_logic(distance)
            
            # Update UI
            self.update_ui(target)
            self.entry_dim.delete(0, tk.END)
            
        except ValueError:
            messagebox.showerror("Error", "Enter numbers only")
            self.entry_dim.delete(0, tk.END)

    def update_ui(self, pos):
        """Helper to keep the display clean."""
        self.lbl_current_pos.config(text=f"{int(pos)} mm")

    def execute_stepper_logic(self, distance):
        # We will paste your motor code here
        print(f"Moving motor {distance} mm")

if __name__ == "__main__":
    root = tk.Tk()
    app = StepperApp(root)
    root.mainloop()