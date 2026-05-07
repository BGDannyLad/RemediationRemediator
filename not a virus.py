import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
from pynput import mouse, keyboard
import threading
import time
import random
import sys
import subprocess
import platform

# --- SPEED OPTIMIZATION ---
pyautogui.PAUSE = 0 

# macOS specific imports
if platform.system() == "Darwin":
    try:
        from AppKit import NSWorkspace, NSApplicationActivationPolicyRegular, NSApplication
    except ImportError:
        pass

# ---------------- CONFIG & DATA ----------------

HARDCODED_MESSAGES = [
    "I bet those professors feel dumb now",
    "Remediate my behind, professor",
    "Even wonder if you've been to your grave?",
    "This is not stealing your credit card information, trust me.",
    "Have fun storming the castle",
    "Muhhamed is the most common name in the world, read a book",
    "Youre breathing manually now :)",
    "Buy me a coffee if you want - venmo BGDannyLad",
    "This app has collected your ssn, shh",
    "technology, boom.",
    "prfsr pwnr",
    "If there are problems with this then its not my fault"
]

click_position = None
running = False

# ---------------- FUNCTIONS ----------------

def show_info():
    """Displays a custom information popup with copyable text."""
    info_window = tk.Toplevel(root)
    info_window.title("Info & Instructions")
    info_window.geometry("340x480")
    info_window.configure(bg="#1e1e1e")
    info_window.transient(root)
    
    # Text widget instead of Label to allow highlighting/copying
    # cursor="arrow" makes it feel less like a text editor
    txt_area = tk.Text(info_window, bg="#1e1e1e", fg="white", 
                       font=("Arial", 10), padx=20, pady=20, 
                       wrap="word", bd=0, highlightthickness=0,
                       cursor="arrow")
    
    info_text = (
        "THE REMEDIATOR\n"
        "------------------\n\n"
        "1. Click 'Pick Your Location' and then click the target on your screen.\n\n"
        "2. (macOS Only) Select the app you want to focus from the dropdown.\n\n"
        "3. Set your interval (seconds between clicks).\n\n"
        "4. Set a stop limit (optional) or leave at 0 for infinite.\n\n"
        "5. Press START. \n\n"
        "Press the 'ESC' key on your keyboard to stop immediately.\n\n"
        "------------------\n"
        "If you're on mac and it is not clicking, go to:\n"
        "Settings -> System and Security -> Accessibility -> add this app\n"
        "If there are any problems or you want new features contact me\n"
        "If you dont know how to then too bad\n"
        "Link to Repo: https://github.com/BGDannyLad/RemediationRemediator.git"
    )
    txt_area.insert("1.0", info_text)
    
    # Set to 'disabled' so the user can't delete or change the text, 
    # but they CAN still highlight and copy it.
    txt_area.config(state="disabled")
    txt_area.pack(expand=True, fill="both")
    
    tk.Button(info_window, text="Got it", command=info_window.destroy, highlightbackground="#1e1e1e").pack(pady=10)

def get_running_apps():
    system = platform.system()
    if system == "Darwin":
        apps = NSWorkspace.sharedWorkspace().runningApplications()
        gui_apps = [app.localizedName() for app in apps 
                    if app.activationPolicy() == NSApplicationActivationPolicyRegular]
        return sorted(list(set(gui_apps)))
    elif system == "Windows":
        return ["Not supported for Windows"]
    return ["Unsupported OS"]

def refresh_app_list():
    current_apps = get_running_apps()
    app_dropdown['values'] = current_apps
    if current_apps:
        if app_dropdown.get() not in current_apps:
            app_dropdown.set(current_apps[0])

def focus_target_app(app_name):
    system = platform.system()
    if not app_name: return
    try:
        if system == "Darwin":
            script = f'tell application "{app_name}" to activate'
            subprocess.run(["osascript", "-e", script])
    except Exception as e:
        print(f"Focus error: {e}")

def on_escape(key):
    global running
    if key == keyboard.Key.esc:
        if running:
            running = False
            root.after(0, stop_via_esc)

def stop_via_esc():
    btn.config(text="Start", fg="black")
    messagebox.showinfo("Boom, Stopped", "Remediator rudely interrupted.")

def capture_click():
    global click_position
    root.attributes("-topmost", True)
    label_status.config(text="CHOOSE TARGET COORDINATE", fg="#ffcc00")
    label_status.pack(pady=10)
    label_pos.pack_forget()
    btn_pick.config(state="disabled")

    def on_click(x, y, button, pressed):
        global click_position
        if pressed:
            click_position = (x, y)
            root.after(0, lambda: finish_capture(x, y))
            return False 

    listener = mouse.Listener(on_click=on_click)
    listener.start()

def finish_capture(x, y):
    label_status.config(text="Target Set!", fg="#5cb85c")
    root.after(1500, lambda: reset_ui_labels(x, y))

def reset_ui_labels(x, y):
    label_status.pack_forget()
    label_pos.config(text=f"Position: {int(x)}, {int(y)}")
    label_pos.pack(pady=10)
    btn_pick.config(state="normal")
    root.attributes("-topmost", False)

def auto_click(interval, limit_val, limit_type, app_name, immediate):
    global running
    start_time = time.time()
    clicks_count = 0
    
    focus_target_app(app_name)
    if platform.system() == "Darwin":
        time.sleep(0.4) 

    if immediate and running and click_position:
        pyautogui.click(click_position[0], click_position[1])
        clicks_count += 1

    while running:
        if limit_val > 0:
            if limit_type == "Seconds" and (time.time() - start_time) >= limit_val:
                running = False
                root.after(0, lambda: [btn.config(text="Start", fg="black"), 
                                       messagebox.showinfo("Wham, Done", "Your time has run out.")])
                break
            if limit_type == "Clicks" and clicks_count >= limit_val:
                running = False
                root.after(0, lambda: [btn.config(text="Start", fg="black"), 
                                       messagebox.showinfo("definitely done", "Got tired of clicking and stopped.")])
                break

        if click_position:
            try:
                pyautogui.click(click_position[0], click_position[1])
                clicks_count += 1
            except Exception as e:
                print("Click error:", e)

        if interval > 0:
            if interval < 0.05:
                time.sleep(interval)
            else:
                stop_time = time.time() + interval
                while time.time() < stop_time and running:
                    time.sleep(0.01)
        if not running: break

def start_stop():
    global running
    if not running:
        if click_position is None:
            messagebox.showerror("Error", "Pick a location first you silly goose.")
            return
        try:
            interval = float(interval_entry.get())
            limit_val = float(limit_entry.get())
            limit_type = limit_type_dropdown.get()
            app_name = app_dropdown.get()
            immediate = bool(immediate_var.get())
        except ValueError:
            messagebox.showerror("Huh?", "No.")
            return

        running = True
        btn.config(text="Stop", fg="red")
        threading.Thread(target=auto_click, args=(interval, limit_val, limit_type, app_name, immediate), daemon=True).start()
    else:
        running = False
        btn.config(text="Start", fg="black")

# ---------------- UI SETUP ----------------

root = tk.Tk()
if platform.system() == "Darwin":
    try:
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyRegular)
    except: pass
    
root.title("The Remediator")
root.geometry("380x650")
main_bg = "#1e1e1e"
text_color = "white"
root.configure(bg=main_bg)

esc_listener = keyboard.Listener(on_press=on_escape)
esc_listener.start()

header_msg = tk.Label(root, text=random.choice(HARDCODED_MESSAGES), bg=main_bg, fg="#00ffcc", 
                      font=("Arial", 11, "italic"), wraplength=320, justify="center")
header_msg.pack(pady=(30, 10))

btn_pick = tk.Button(root, text="Pick Your Location", command=capture_click, highlightbackground=main_bg)
btn_pick.pack(pady=(10, 5))

label_status = tk.Label(root, text="", bg=main_bg, font=("Arial", 10, "bold"))
label_pos = tk.Label(root, text="Position: None", bg=main_bg, fg="lightgray")
label_pos.pack(pady=5)

tk.Label(root, text="Select Target App:", bg=main_bg, fg="cyan").pack(pady=(15, 0))
app_dropdown = ttk.Combobox(root, width=25, state="readonly")
app_dropdown.pack(pady=5)

btn_refresh = tk.Button(root, text="Refresh App List", command=refresh_app_list, 
                        font=("Arial", 8), highlightbackground=main_bg)
btn_refresh.pack(pady=2)

refresh_app_list()

tk.Label(root, text="Interval (seconds):", bg=main_bg, fg=text_color).pack(pady=(10, 0))
interval_entry = tk.Entry(root, justify="center", width=10, bg="#333333", fg="white")
interval_entry.insert(0, "1.0")
interval_entry.pack(pady=5)

tk.Label(root, text="Stop after (0 for infinite):", bg=main_bg, fg=text_color).pack(pady=(10, 0))
limit_frame = tk.Frame(root, bg=main_bg)
limit_frame.pack(pady=5)

limit_entry = tk.Entry(limit_frame, justify="center", width=10, bg="#333333", fg="white")
limit_entry.insert(0, "0")
limit_entry.pack(side="left", padx=5)

limit_type_dropdown = ttk.Combobox(limit_frame, values=["Seconds", "Clicks"], width=8, state="readonly")
limit_type_dropdown.set("Seconds")
limit_type_dropdown.pack(side="left", padx=5)

immediate_var = tk.IntVar(value=0)
cb_immediate = tk.Checkbutton(root, text="Click immediately on start", variable=immediate_var, 
                              bg=main_bg, fg=text_color, selectcolor="#333333", activebackground=main_bg)
cb_immediate.pack(pady=10)

btn = tk.Button(root, text="Start", command=start_stop, width=15, height=2, highlightbackground=main_bg)
btn.pack(pady=10)

# Bottom Row for Info and Stop Notice
bottom_frame = tk.Frame(root, bg=main_bg)
bottom_frame.pack(side="bottom", fill="x", pady=10)

btn_info = tk.Button(bottom_frame, text="Info", command=show_info, font=("Arial", 9), 
                     highlightbackground=main_bg)
btn_info.pack(side="left", padx=15)

footer = tk.Label(bottom_frame, text="Press 'ESC' to stop", bg=main_bg, fg="#555555", font=("Arial", 9))
footer.pack(side="right", padx=15)

root.mainloop()