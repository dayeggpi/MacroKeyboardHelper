import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import ctypes
import keyboard
import queue
import os
import sys
import time
import pystray
import threading
import configparser
from tkinter import ttk
from tkinter import messagebox

# Config defaults
HOTKEY = 'ctrl+shift+i'
DISPLAY_TIME = 3000
FADE_DURATION = 1000
FADE_STEPS = 20
IMAGE_FOLDER = '.'
IMAGE_PATTERN = '{:02}.png'
SETTINGS_FILE = "settings.ini"

event_queue = queue.Queue()

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(".")

def center_window_main(win, width=1200, height=600):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    
    
def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def load_images():
    images = []
    index = 1
    while True:
        path = os.path.join(IMAGE_FOLDER, IMAGE_PATTERN.format(index))
        if os.path.exists(path):
            images.append(path)
            index += 1
        else:
            break
    if not images:
        tk.messagebox.showerror("Macro Keyboard Helper", "No images were found in the folder.\nMake sure files like 01.png, 02.png exist then restart the app.")
        root.destroy()
        sys.exit()        
    return images


config = configparser.ConfigParser()

def load_settings():
    global HOTKEY, DISPLAY_TIME
    if not os.path.exists(SETTINGS_FILE):
        config['Settings'] = {
            'hotkey': HOTKEY,
            'display_time': str(DISPLAY_TIME)
        }
        with open(SETTINGS_FILE, 'w') as f:
            config.write(f)
    else:
        config.read(SETTINGS_FILE)
        HOTKEY = config.get("Settings", "hotkey", fallback=HOTKEY)
        DISPLAY_TIME = config.getint("Settings", "DISPLAY_TIME", fallback=DISPLAY_TIME)



load_settings()

def save_settings(hotkey, DISPLAY_TIME):
    config["Settings"] = {
        "hotkey": hotkey,
        "display_time": str(DISPLAY_TIME)
    }
    with open(SETTINGS_FILE, 'w') as f:
        config.write(f)
        
        
class PopupWindow:
    def __init__(self, root):
        self.popup = root
        self.force_closed = False
        self.popup.withdraw() 

        self.popup = tk.Toplevel(self.popup)
        self.popup.overrideredirect(True)
        self.popup.attributes('-topmost', True)
        self.popup.attributes('-toolwindow', True)  # removes taskbar icon
        self.popup.withdraw()

        self.images = load_images()
        self.current_image_index = 0
        self.fade_after_id = None

        self.frame = tk.Frame(self.popup, bg="white", bd=1, relief="solid")
        self.frame.pack()
        
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)

        self.label = tk.Label(self.frame, bd=1, bg="black", relief="solid") #keep bg black
        self.label.grid(row=0, column=1, sticky="nsew")

        self.pagination = tk.Label(self.frame, text="", bg="white", fg="black")
        self.pagination.grid(row=1, column=0, columnspan=4)

        self.icon_prev = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "prev.png")).resize((20, 20)))
        self.icon_next = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "next.png")).resize((20, 20)))

        self.btn_prev = tk.Button(
            self.frame, image=self.icon_prev, command=self.prev_image,
            relief="flat", borderwidth=0, bg="white", activebackground="black"
        )
        self.btn_next = tk.Button(
            self.frame, image=self.icon_next, command=self.next_image,
            relief="flat", borderwidth=0, bg="white", activebackground="black"
        )    

        self.update_navigation_buttons()
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Custom.Horizontal.TProgressbar", thickness=5, troughcolor='black', background='white')

        self.progress = ttk.Progressbar(self.frame, style="Custom.Horizontal.TProgressbar", orient='horizontal', mode='determinate', length=200)

        self.progress.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(5, 0))

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)

        self.update_image()

        self.icon_close = ImageTk.PhotoImage(Image.open(os.path.join(BASE_DIR, "close.png")).resize((20, 20)))
        
        self.close_button = tk.Button(
            self.frame, image=self.icon_close, command=self.force_close,
            relief="flat", borderwidth=0, bg="white", activebackground="white"
        )
        
        self.close_button.grid(row=0, column=3, sticky="ne", padx=5)
        
        self.popup.bind("<Enter>", self.reset_fade_timer)
        self.popup.bind("<Leave>", self.start_fade_timer)
        self.label.bind("<Enter>", self.reset_fade_timer)
        self.label.bind("<Leave>", self.reset_fade_timer)  # Don't restart timer when leaving image

        # Bind to all widgets to handle hover properly
        for widget in [self.popup, self.frame, self.label, self.btn_prev, self.btn_next, self.progress, self.pagination, self.close_button]:
            widget.bind("<Enter>", self.reset_fade_timer)
            widget.bind("<Leave>", self.check_mouse_leave)
            

    def force_close(self):
        self.force_closed = True
        if self.fade_after_id:
            self.popup.after_cancel(self.fade_after_id)
            self.fade_after_id = None
        self.popup.withdraw()


    def reset_fade_timer(self, event=None):
        if self.fade_after_id:
            self.popup.after_cancel(self.fade_after_id)
            self.fade_after_id = None
        self.popup.attributes('-alpha', 1.0)

    def start_fade_timer(self, event=None):
        if self.force_closed:
            return
        self.show()

    def check_mouse_leave(self, event=None):
        # Delay the check to see if mouse entered another widget
        self.popup.after(10, self._delayed_mouse_check)

    def _delayed_mouse_check(self):
        # Get mouse position relative to popup window
        try:
            x = self.popup.winfo_pointerx() - self.popup.winfo_rootx()
            y = self.popup.winfo_pointery() - self.popup.winfo_rooty()
            
            # Check if mouse is still within popup bounds
            if 0 <= x <= self.popup.winfo_width() and 0 <= y <= self.popup.winfo_height():
                # Mouse is still inside popup, keep timer paused
                self.reset_fade_timer()
            else:
                # Mouse has left popup, restart timer
                self.start_fade_timer()
        except:
            # If there's any error, just restart the timer
            self.start_fade_timer()    
    
    def update_image(self):
        if not self.images:
            return


        screen_width, screen_height = get_screen_size()
        img = Image.open(self.images[self.current_image_index])

        max_width = screen_width // 2
        max_height = screen_height // 2
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        img_width, img_height = img.size
        button_margin = 80  # 40 on each side
        self.photo = ImageTk.PhotoImage(img)
        self.label.configure(image=self.photo)
        x = screen_width - img_width - button_margin - 20
        y = screen_height - img_height - 120 #move notif area higher by increasing that number
    
        # Reserve extra space for buttons and progress bar
        extra_height = 40  # adjust if needed
        self.popup.geometry(f'{img_width + button_margin}x{img_height + extra_height}+{x}+{y}')
        self.frame.pack_propagate(False)
        
        self.pagination.config(
            text=f"{self.current_image_index + 1}/{len(self.images)}" if self.images else "0/0"
        )
        
    def update_navigation_buttons(self):
        
        if len(self.images) <= 1:
            self.btn_prev.grid_remove()
            self.btn_next.grid_remove()
        else:
            self.btn_prev.grid(row=0, column=0, sticky="w")
            self.btn_next.grid(row=0, column=2, sticky="e")
            
    def show(self):
        if self.force_closed:
            return
        self.update_image()
        self.popup.deiconify()
        self.popup.attributes('-alpha', 1.0)
        self.popup.lift()

        if self.fade_after_id:
            self.popup.after_cancel(self.fade_after_id)
            self.fade_after_id = None

        self.progress['maximum'] = DISPLAY_TIME
        self.progress['value'] = 0
        self.update_progress()

    def update_progress(self):
        if self.fade_after_id:
            self.popup.after_cancel(self.fade_after_id)

        start = time.time()

        def progress_loop():
            elapsed = (time.time() - start) * 1000
            if elapsed >= DISPLAY_TIME:
                self.fade_step(0)
                return
            self.progress['value'] = elapsed
            self.fade_after_id = self.popup.after(50, progress_loop)

        progress_loop()


    def fade_step(self, step):
        if step >= FADE_STEPS:
            self.popup.withdraw()
            return
        alpha = 1.0 - (step + 1) / FADE_STEPS
        self.popup.attributes('-alpha', alpha)
        delay = FADE_DURATION // FADE_STEPS
        self.fade_after_id = self.popup.after(delay, self.fade_step, step + 1)

    def next_image(self):
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.update_image()

    def prev_image(self):
        self.current_image_index = (self.current_image_index - 1) % len(self.images)
        self.update_image()

class SettingsWindow:
    def __init__(self, master):
       
        self.top = tk.Toplevel(master)
        self.top.title("Settings for Macro Keyboard Helper")
        self.top.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
        center_window_main(self.top, 300, 150)
        tk.Label(self.top, text="Press hotkey:").pack()
        self.hotkey_var = tk.StringVar(value=HOTKEY)
        self.entry = tk.Entry(self.top, textvariable=self.hotkey_var)
        self.entry.pack()
        self.entry.configure(state='disable')
        tk.Button(self.top, text="Set Hotkey", command=self.start_recording).pack()
        tk.Label(self.top, text="Display time (ms):").pack()
        self.fade_var = tk.IntVar(value=DISPLAY_TIME)
        tk.Entry(self.top, textvariable=self.fade_var).pack()
        tk.Button(self.top, text="Save", command=self.save).pack()



    def start_recording(self):
        self.hotkey_var.set("Recording...")

        self.recording = True
        self.pressed_keys = set()
        self.all_keys = set()

        def handler(event):
            if not self.recording:
                return

            if event.event_type == 'down':
                self.pressed_keys.add(event.name)
                self.all_keys.add(event.name)

            elif event.event_type == 'up':
                self.pressed_keys.discard(event.name)

                if not self.pressed_keys:
                    # All keys released
                    combo = '+'.join(sorted(self.all_keys))
                    self.hotkey_var.set(combo)
                    keyboard.unhook_all()
                    self.recording = False

        keyboard.hook(handler)


    def save(self):
        global HOTKEY, DISPLAY_TIME
        new_hotkey = self.hotkey_var.get()

        # Do not try to add invalid hotkey
        if "recording" in new_hotkey.lower():
            print("Invalid hotkey string")
            return

        # Safely remove previous hotkey if it existed
        try:
            keyboard.remove_hotkey(HOTKEY)
        except (KeyError, ValueError):
            pass

        HOTKEY = new_hotkey
        DISPLAY_TIME = int(self.fade_var.get())

        # Try adding new hotkey
        try:
            keyboard.add_hotkey(HOTKEY, on_hotkey)
        except ValueError as e:
            print(f"Invalid hotkey: {e}")
            return

        save_settings(HOTKEY, DISPLAY_TIME)
        self.top.destroy()

def on_hotkey():
    reload_images()
    event_queue.put("show")

def check_queue():
    try:
        while True:
            event_queue.get_nowait()
            popup.force_closed = False
            popup.show()
    except queue.Empty:
        pass

    root.after(50, check_queue)

def on_quit():
    icon.stop()
    sys.exit(0)
    root.quit()

def open_settings():
    SettingsWindow(root)

def show_about():
    about = tk.Toplevel(root)
    about.title("About Macro Keyboard Helper")
    about.resizable(False, False)
    about.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
    center_window_main(about, 300, 150)
    tk.Label(about, text="Macro Keyboard Helper\nby dayeggpi\nVersion 1.0.0", padx=20, pady=20).pack()
    tk.Button(about, text="OK", command=about.destroy).pack(pady=(0, 10))
    
def reload_images():
    try:
        new_images = load_images()
        popup.images = new_images
        popup.current_image_index = 0
        popup.update_navigation_buttons()
        popup.update_image()
        print("Images reloaded successfully")
    except Exception as e:
        print(f"Error reloading images: {e}")
        
def run_systray():
    icon_image = Image.open(os.path.join(BASE_DIR, "icon.ico"))
    menu = pystray.Menu(
        pystray.MenuItem('Settings', lambda: root.after(0, open_settings)),
        # pystray.MenuItem('Reload Images', lambda: root.after(0, reload_images)),
        pystray.MenuItem('About', lambda: root.after(0, show_about)),
        pystray.MenuItem('Quit', lambda: root.after(0, on_quit))
    )
    global icon
    icon = pystray.Icon("notif", icon_image, "Notifier", menu)
    icon.run()

# Main
root = tk.Tk()
popup = PopupWindow(root)

keyboard.add_hotkey(HOTKEY, on_hotkey)

threading.Thread(target=run_systray, daemon=True).start()

root.after(50, check_queue)
root.mainloop()
