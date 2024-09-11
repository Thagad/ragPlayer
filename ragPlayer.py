#pyinstaller --onedir --add-data "fonts/big_noodle_titling.ttf;BigNoodleTitling" --add-binary "ffmpeg/ffmpeg.exe;ffmpeg" --add-binary "ffmpeg/ffprobe.exe;ffmpeg" ragPlayer.py --name RagPlayer --windowed --icon=MP3_30924.ico --add-data "fonts/PlusJakartaSans-Bold.ttf;PlusJakartaSans-Bold"   

import tkinter as tk
#import tkinter.ttk as ttk
import tkinter.font as font
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
import os
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import subprocess
import json
import pygame
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, TIT2
import time
import random
import threading
import re
import eyed3
from PIL import Image, ImageDraw, ImageTk
import base64
from tkinter import PhotoImage
import shutil

class rag_ui:
    def __init__(self, master=None):
        # Initialize pygame mixer
        pygame.mixer.init()
        # Global variables
        self.current_index = 0
        self.playlist = []
        self.sorted_items = []
        self.cropped = []
        self.current_song = None
        self.paused = False
        self.song_directory = os.getcwd()  # Default song directory
        self.downloading = False  # Flag to track if downloading is in progress
        self.running = True
        self.downloadSwitch = False
        self.ffmpeg_dir = 'ffmpeg'
        self.windowsSwitch = False
        self.keybind_popup = None
        self.search_term_global = None
        self.visible_matches = []
        BigNoodleTitling = os.path.join( 'fonts', 'big_noodle_titling.ttf')

        # Build UI
        self.mainwindow = ttk.Window(themename='ragard_dark2') if master is None else tk.Toplevel(master)
        self.mainwindow.configure(height=1200, width=400)
        self.mainwindow.resizable(False, False)
        self.mainwindow.title("ragPlayer")  
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.mainwindow.attributes("-toolwindow", False)
        self.mainwindow.minsize(width=545, height=800)
        self.mainwindow.maxsize(width=545, height=1200)
        
        def start_move(event):
            self.mainwindow.x = event.x
            self.mainwindow.y = event.y

        def do_move(event):
            deltax = event.x - self.mainwindow.x
            deltay = event.y - self.mainwindow.y
            self.mainwindow.geometry(f"+{self.mainwindow.winfo_x() + deltax}+{self.mainwindow.winfo_y() + deltay}")

        # Minimize the window
        def minimize_window():
            self.mainwindow.iconify()

        # Close the window
        def close_window():
            self.mainwindow.destroy()

        self.frame_main = ttk.Frame(self.mainwindow, name="frame_main")
        self.frame_main.configure(height=500, width=400)
        # Create a frame to act as the top bar
        self.top_bar = tk.Frame(self.mainwindow, bg="gray", relief="raised", bd=2)
        

        button_bar = tk.Frame(self.top_bar, bg="gray", relief="raised", bd=0.1)
        button_bar.pack(side="right")

        # Exit button
        exit_button = tk.Button(button_bar, text="X", bg="gray", fg="white", command=close_window, relief="flat")
        exit_button.pack(side="right")

        # Bind the drag functionality to the top bar
        self.top_bar.bind("<Button-1>", start_move)
        self.top_bar.bind("<B1-Motion>", do_move)

        panelStyle = ttk.Style()
        panelStyle.configure("Panel.TFrame", background="#fd2600", borderwidth=0 ,bordercolor="#fd2600")
        
        labelStyle = ttk.Style()
        labelStyle.configure("Label.TLabel", background="#fd2600", bordercolor="#fd2600")
        
        labelStyle2 = ttk.Style()
        labelStyle2.configure("Label2.TLabel", background="#121212", bordercolor="#121212")
        
        panel = ttk.Frame(self.mainwindow, relief="raised", style="Panel.TFrame")
        panel.pack(fill="x", side="top")  # 'fill="x"' makes the panel span the entire width

        # Create the label and place it inside the panel
        label1 = ttk.Label(panel, font="{BigNoodleTitling} 36 {}", text='ragPlayer', style="Label.TLabel")
        label1.pack(side="top", padx=10)  # Add padding if needed


        self.download_frame = tk.LabelFrame(
            self.frame_main, name="download_frame")
        self.download_frame.configure(height=200, width=200)

        self.url_label = ttk.Label(self.download_frame, name="url_label")
        self.url_label.configure(
            font="{Plus Jakarta Sans} 10 {}",
            text='Song Url:')
        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.url_entry = ttk.Entry(self.download_frame, name="url_entry")
        self.url_entry.configure(font="{Plus Jakarta Sans} 8 {}")
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.download_status_label = ttk.Label(self.download_frame, name="download_status_label")
        self.download_status_label.configure(text="", foreground="red", font="{Plus Jakarta Sans} 8 {}")
        self.download_status_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")

        styleNoImg = ttk.Style()
        styleNoImg.configure("Imageless.TButton", background="#fa332e")
        
        self.import_button = ttk.Button(self.download_frame, text="𝗜𝗺𝗽𝗼𝗿𝘁 .𝗿𝗮𝗴𝗽", command=self.import_playlist, width=15)
        self.import_button.grid(row=3, column=0, padx=(10, 10), sticky="ew")

        # Create the export button
        self.export_button = ttk.Button(self.download_frame, text="𝗘𝘅𝗽𝗼𝗿𝘁 .𝗿𝗮𝗴𝗽", command=self.export_playlist, width=15)
        self.export_button.grid(row=3, column=1, padx=(10, 10), sticky="ew")
        
        self.button4 = ttk.Button(self.download_frame, name="button4", style="Imageless.TButton")
        self.button4.configure(text='𝗥𝗮𝗴 𝗶𝘁', command=self.download_song, width=6)  # Adjusted width
        self.button4.grid(row=2, column=1, padx=(10, 10), sticky="ew")

        # Add the new button next to the "Rag it" button
        self.clear_url_button = ttk.Button(self.download_frame, name="clear_url_button", style="Imageless.TButton")
        self.clear_url_button.configure(text='𝗖𝗹𝗲𝗮𝗿', command=self.clear_url, width=6)  # Adjusted width
        self.clear_url_button.grid(row=2, column=0, padx=(10, 10), sticky="ew")

        self.download_frame.pack(side="top", pady=10)

        self.folder_frame = tk.LabelFrame(
            self.frame_main, name="folder_frame")
        self.folder_frame.configure(height=200, width=200, borderwidth=0, highlightthickness=0)


        self.folder_image = PhotoImage(file="folder.png")
        self.eye_image = PhotoImage(file="eye.png")
        self.refresh_image = PhotoImage(file="refresh.png")
        self.next_image = PhotoImage(file="next.png")
        self.back_image = PhotoImage(file="back.png")
        self.select_image = PhotoImage(file="select.png")
        self.switch = PhotoImage(file="switch.png")

        # Create a style for the button
        style = ttk.Style()

        # Modify the TButton style to remove borders and padding
        style.configure("TButton", borderwidth=0, background="#121212")
        self.open_folder_button = ttk.Button(
            self.folder_frame, image=self.folder_image, command=self.open_folder, padding=0, compound=tk.CENTER)
        self.open_folder_button.pack(side="left", padx=5)
        self.open_folder_button.config(style="TButton")  # Use a custom style if you need more customization
        self.open_folder_button["padding"] = 0
        self.open_folder_button.config(width=6)  # Set button width

        self.change_location_button = ttk.Button(
            self.folder_frame, image=self.eye_image, command=self.change_location, padding=0, compound=tk.CENTER)
        self.change_location_button.pack(side="right", padx=5)
        self.change_location_button.config(width=5)  # Set button width
        
        self.refresh_button = ttk.Button(
            self.folder_frame, image=self.refresh_image, command=self.reload_playlist,padding=0, compound=tk.CENTER)
        self.refresh_button.pack(side="right", padx=5)
        self.refresh_button.config(width=5)  # Set button width
        
        self.switch_button = ttk.Button(
            self.folder_frame, image=self.switch, command=self.switch_downloadpage,padding=0, compound=tk.CENTER)
        self.switch_button.pack(side="right", padx=5)
        self.switch_button.config(width=5)  # Set button width

        self.folder_frame.pack(side="top")

        self.playlist_frame = tk.Frame(
            self.frame_main, name="playlist_frame")
        self.playlist_frame.configure(height=200, width=200)

        self.playlist_label = ttk.Label(
            self.playlist_frame, name="playlist_label")
        self.playlist_label.configure(
            font="{Plus Jakarta Sans} 16 {}",
            text=os.path.basename(self.song_directory))  # Set label text to folder name
        self.playlist_label.place(relx=0.0, rely=0.0, anchor="center")
        self.playlist_label.pack(fill="none", expand=True)
            
        self.image_path = os.path.join(self.song_directory, 'thumb.png')
        if os.path.isfile(self.image_path):
            self.playlist_art = Image.open(self.image_path)
            self.playlist_art = self.playlist_art.resize((100, 100), Image.Resampling.LANCZOS)
            self.playlist_artwork = ImageTk.PhotoImage(self.playlist_art)   
            self.playlist_image = tk.Label(
                self.playlist_frame, name="playlist_image", image=self.playlist_artwork)
            self.playlist_image.pack(side="left", before=self.playlist_label, padx=10)
        else:
            self.playlist_image = tk.Label(
                self.playlist_frame, name="playlist_image", image=None)
            self.playlist_image.pack(side="left", before=self.playlist_label, padx=10)

        self.playlist_frame.pack(side="top", pady= 20)
        
        self.search_var = tk.StringVar()
        self.search_bar = tk.Entry(self.frame_main, textvariable=self.search_var, width=50)
        self.search_bar.configure(font="{Plus Jakarta Sans} 10 {}", width=60)
        self.search_bar.pack()

        self.listbox = tk.Listbox(self.frame_main, name="listbox")
        self.listbox.configure(font="{Plus Jakarta Sans} 10 {}", width=37)  # Adjust width as needed
        self.listbox.pack(side="top", fill="both", expand=True)
        self.populate_playlist()  # Populate playlist initially
        self.listbox.bind("<<ListboxSelect>>", self.play_selected_song)  # Bind selection event to play_selected_song


        self.volume_panel = ttk.Frame(
            self.frame_main, name="volume_panel")
        self.volume_panel.configure(height=200, width=200)
        self.album_art = PhotoImage(file=os.path.join(self.song_directory, "default_image.png")) 
        self.album_art_label = ttk.Label(self.volume_panel, name="album_art_label", image=self.album_art)
        self.album_art_label.pack(side="top", pady=10)

        self.scale1 = ttk.Scale(self.volume_panel)
        self.scale1.configure(length=200, orient="horizontal", from_= 0, to=100, command=self.set_volume)
        self.scale1.set(15)
        self.scale1.pack(side="top")
        
        self.progressbar = ttk.Progressbar(
            self.volume_panel, name="progressbar")
        self.progressbar.configure(length=450, orient="horizontal", mode='determinate')
        self.progressbar.pack(side="top", pady= 10 )


        self.container_frame = ttk.Frame(self.volume_panel)
        self.container_frame.configure(height=25, width=100)
        self.container_frame.pack(fill="both", expand=True, side="bottom", pady=10)

        self.song_label = ttk.Label(self.container_frame, name="song_label", style="Label2.TLabel")
        self.song_label.configure(font="{Plus Jakarta Sans} 11 {}", text='Now playing: ')
        self.song_label.place(relx=0.5, rely=0.5, anchor="center")
        self.mainwindow.bind("<space>", self.toggle_pause_unpause)
        
        self.button_frame = ttk.Frame(self.frame_main, name="button_frame")
        self.button_frame.configure(height=100, width=100)
        
        self.previous_button = ttk.Button(
            self.button_frame, name="previous_button")
        self.previous_button.configure(image=self.back_image, command=self.previous_song, padding=0, compound=tk.CENTER)
        self.previous_button.pack(side="left", padx= 5)

        self.play_button = ttk.Button(self.button_frame, name="play_button")
        self.play_button.configure(image=self.select_image, command=self.play_song, padding=0, compound=tk.CENTER)
        self.play_button.pack(side="left", padx= 5)

        self.next_button = ttk.Button(self.button_frame, name="next_button")
        self.next_button.configure(image=self.next_image, command=self.next_song, padding=0, compound=tk.CENTER)
        self.next_button.pack(side="right", padx= 5)

        self.play_image = PhotoImage(file="play.png")
        self.pause_image = PhotoImage(file="pause.png")
        self.pause_unpause_button = ttk.Button(self.button_frame, name="pause_unpause_button")
        self.pause_unpause_button.configure(image=self.pause_image, command=self.pause_unpause_song, padding=0, compound=tk.CENTER)
        self.pause_unpause_button.pack(side="right", padx= 5)

        self.shuffle_mode = tk.BooleanVar()  # Variable to track shuffle mode
        self.shuffle_mode.set(True)
        self.shuffle_button = ttk.Checkbutton(self.button_frame, name="shuffle_button")
        self.shuffle_button.configure(text='𝘀𝗵𝘂𝗳𝗳𝗹𝗲', variable=self.shuffle_mode, command=self.toggle_shuffle)
        self.shuffle_button.pack(side="right")

        self.button_frame.pack(side="top", pady=5, before=self.container_frame)
        
        self.progressbar_label = ttk.Label(
            self.volume_panel, name="progressbar_label")
        self.progressbar_label.configure(
            font="{Plus Jakarta Sans} 10 {}",
            text='00:00 / 00:00')
        self.progressbar_label.pack(side="top")


        self.get_time()  # Start updating the time and progress bar

        self.volume_panel.pack(side="top")
        self.frame_main.pack(side="top")
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.close_window)

        def reset_listbox_colors():
            # Reset all items in the Listbox to white
            for i in range(self.listbox.size()):
                self.listbox.itemconfig(i, {'fg': 'white'})  # Reset color to white
                
        def search_listbox(search_term):
            self.visible_matches = []
            self.search_term_global = search_term
            # If search bar is empty, reset all colors to white
            if len(search_term) == 0:
                reset_listbox_colors()
            else:
                # Loop through all the items in the Listbox and apply the search filter
                for i, item in enumerate(self.playlist):
                    if search_term.lower() in item.lower():
                        self.listbox.itemconfig(i, {'fg': 'red'})  # Highlight matched items
                        self.visible_matches.append(i)  # Store the index of visible matches
                    else:
                        self.listbox.itemconfig(i, {'fg': '#3c3c3c'})  

            # Reset the cycling index if search is updated
            global current_match_index
            current_match_index = -1
            
        def cycle_matches(event):
            global current_match_index
            if self.search_term_global!=None or self.search_term_global!=0:	
                if self.visible_matches:
                    # Cycle to the next match
                    current_match_index = (current_match_index + 1) % len(self.visible_matches)
                    
                    # Scroll the Listbox to the next matching item
                    self.listbox.see(self.visible_matches[current_match_index])
                    
                    # Highlight the item in the Listbox
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(self.visible_matches[current_match_index])
                    self.listbox.activate(self.visible_matches[current_match_index])
                    self.play_song()
                
        def click_outside_search(event):
            # Check if the click was outside the search bar
            widget = event.widget
            if widget != self.search_bar:
                self.search_bar.focus_set()  # Temporarily focus on search bar (needed for focus_out to trigger)
                self.mainwindow.focus()  # Set focus to the root window, effectively deselecting the search bar
            if widget == self.url_entry:
                self.url_entry.focus_set()  # Temporarily focus on search bar (needed for focus_out to trigger)
            
        def toggle_overrideredirect(event=None):
            self.windowsSwitch = not self.windowsSwitch
            if self.windowsSwitch:
                self.mainwindow.attributes("-topmost", True)
                self.mainwindow.overrideredirect(True)
                self.top_bar.pack(side="top", fill="x", before=panel)
            else:
                self.mainwindow.overrideredirect(False)
                self.mainwindow.attributes("-topmost", False)
                self.top_bar.pack_forget()
                
        def toggle_keybind_popup(event=None):
            def start_move_keybinds(event):
                self.keybind_popup.x = event.x
                self.keybind_popup.y = event.y

            def do_move_keybinds(event):
                deltax = event.x - self.keybind_popup.x
                deltay = event.y - self.keybind_popup.y
                self.keybind_popup.geometry(f"+{self.keybind_popup.winfo_x() + deltax}+{self.keybind_popup.winfo_y() + deltay}")
            def close_keybinds(event=None):
                self.keybind_popup.destroy()
                self.keybind_popup = None
                
            if self.keybind_popup and self.keybind_popup.winfo_exists():
                close_keybinds()
            else:
                # Create a new popup window to show the keybinds
                self.keybind_popup = tk.Toplevel(self.mainwindow)
                self.keybind_popup.title("Controls")
                self.keybind_popup.geometry("280x310")

                self.keybind_popup.protocol("WM_DELETE_WINDOW", lambda: self.close_popup())
                self.keybind_popup.overrideredirect(True)
                self.keybind_popup.top_bar = tk.Frame(self.keybind_popup, bg="gray", relief="raised", bd=2)
                self.keybind_popup.top_bar.pack(side="top", fill="x")
                self.keybind_popup.button_bar = tk.Frame(self.keybind_popup.top_bar, bg="gray", relief="raised", bd=0.1)
                self.keybind_popup.button_bar.pack(side="right")
                self.keybind_popup.exit_button = tk.Button(self.keybind_popup.button_bar, text="X", bg="gray", fg="white", command=close_keybinds, relief="flat")
                self.keybind_popup.exit_button.pack(side="right")
                self.keybind_popup.top_bar.bind("<Button-1>", start_move_keybinds)
                self.keybind_popup.top_bar.bind("<B1-Motion>", do_move_keybinds)

                # Create a Label to show keybinds
                keybinds_text = """
Buttons
                
Folder: Opens current playlist location
Eye: Toggles download panel
Refresh: Refreshes playlist
Location: Choose a playlist location
Shuffle: Toggles shuffle

Rag it: Downloads song from URL
Clear: Clears URL input
                
Keybinds
                
Ctrl+A: Toggle borderless window
Ctrl+C: Toggle controls window
Up Arrow: Volume Up
Down Arrow: Volume Down
Enter: Jump between search results
                """
                keybinds_label = tk.Label(self.keybind_popup, text=keybinds_text, justify="center")
                keybinds_label.pack(side="top", fill="both", expand=True)
        
        def set_volume_kb(val):
            volume = float(val) / 200
            pygame.mixer.music.set_volume(volume)
        
        def up_volume(event=None):
            set_volume_kb(self.scale1.get()+2.5)
            self.scale1.set(self.scale1.get()+2.5)
                
        def down_volume(event=None):
            set_volume_kb(self.scale1.get()-2.5)
            self.scale1.set(self.scale1.get()-2.5)
            
        """def up_time(event=None):
            pygame.mixer.music.pause()
            pygame.mixer.music.set_pos(pygame.mixer.music.get_pos()+1)
            pygame.mixer.music.unpause()
        def down_time(event=None):
            pygame.mixer.music.pause()
            pygame.mixer.music.set_pos(pygame.mixer.music.get_pos()-1)
            pygame.mixer.music.unpause()"""
            
        #Binds
        self.mainwindow.bind("<Up>", up_volume)
        self.mainwindow.bind("<Down>", down_volume)
        #self.mainwindow.bind("<Right>", up_time)
        #self.mainwindow.bind("<Left>", down_time)
        self.mainwindow.bind("<Button-1>", click_outside_search)
        self.mainwindow.bind_all("<Control-a>", toggle_overrideredirect)
        self.mainwindow.bind_all("<Control-c>", toggle_keybind_popup)
        self.search_bar.bind('<Return>', cycle_matches)
        self.shuffle_on = True
        self.search_var.trace("w", lambda name, index, mode: search_listbox(self.search_var.get()))
        self.mainwindow.after(60, self.switch_downloadpage)
        self.mainwindow.mainloop()
    

    
    def round_corners(self,image_path, size=(200, 200)):
        # Open the image file
        radius=16
        img = Image.open(image_path).convert("RGBA")

        # Resize image to fit the desired size
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Create a mask with the same size as the resized image
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw a rounded rectangle on the mask
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)

        # Create a new image for the output
        rounded_img = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Paste the original image on the new image using the mask
        rounded_img.paste(img, (0, 0), mask)
        
        return rounded_img
    
    
    def round_corners2(self,image_path, size=(200, 200)):
        # Open the image file
        radius=16
        img = Image.open(image_path).convert("RGBA")

        # Resize image to fit the desired size
        img = img.resize(size, Image.Resampling.LANCZOS)

        # Create a mask with the same size as the resized image
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw a rounded rectangle on the mask
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius, fill=255)

        # Create a new image for the output
        rounded_img = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Paste the original image on the new image using the mask
        rounded_img.paste(img, (0, 0), mask)
        
        return rounded_img
    
    def switch_downloadpage(self):
        # Check if the url_entry widget is currently visible
        if self.url_entry.winfo_viewable():
            self.download_frame.configure(height=1, width=1)
            self.url_label.grid_remove()
            self.url_entry.grid_remove()
            self.download_status_label.grid_remove()
            self.import_button.grid_remove()
            self.export_button.grid_remove()
            self.button4.grid_remove()
            self.clear_url_button.grid_remove()
        else:
            # Show the hidden widgets by using grid again
            self.download_frame.configure(height=200, width=200)
            self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
            self.download_status_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")
            self.import_button.grid(row=3, column=1, padx=(5, 10), sticky="ew")
            self.export_button.grid(row=3, column=0, padx=(10, 5), sticky="ew")
            self.button4.grid(row=2, column=1, padx=(5, 10), sticky="ew")
            self.clear_url_button.grid(row=2, column=0, padx=(10, 5), sticky="ew")
    
    def reload_playlist(self):
        self.populate_playlist()
        self.run_convert_webp_to_png_thread()
        self.run_crop()
    
    def crop_images_to_square(self):
        for filename in os.listdir(self.song_directory):
            if filename.endswith(".png") and not self.cropped.__contains__(filename):
                self.cropped.append(filename)
                png_path = os.path.join(self.song_directory, filename)
                try:
                    # Open the PNG image
                    img = Image.open(png_path)
                    width, height = img.size
                    # Calculate the size of the square crop
                    size = min(width, height)
                    # Calculate coordinates for left and right crop
                    left = (width - size) // 2
                    right = left + size
                    # Crop the image to a square
                    img = img.crop((left, 0, right, size))
                    # Save the cropped image back to the same file
                    img.save(png_path)
                except Exception as e:
                    print(f"Error cropping {png_path}: {e}")
                    
    def run_convert_webp_to_png_thread(self):
        convert_thread = threading.Thread(target=self.convert_webp_to_png)
        convert_thread.start()
        
    def run_crop(self):
        convert_thread = threading.Thread(target=self.crop_images_to_square)
        convert_thread.start()

        
    def convert_webp_to_png(self):
        for filename in os.listdir(self.song_directory):
            if filename.endswith(".webp"):
                webp_path = os.path.join(self.song_directory, filename)
                png_path = os.path.splitext(webp_path)[0] + ".png"
                try:
                    # Open the WebP image
                    img = Image.open(webp_path)
                    # Convert and save as PNG
                    img.convert("RGB").save(png_path, "PNG")
                    # Remove the original WebP image
                    os.remove(webp_path)
                except Exception as e:
                    print(f"Error converting {webp_path} to PNG: {e}")
            if filename.endswith(".jpg"):
                jpg_path = os.path.join(self.song_directory, filename)
                png_path = os.path.splitext(jpg_path)[0] + ".png"
                try:
                    img = Image.open(jpg_path)
                    img.convert("RGB").save(png_path, "PNG")
                    os.remove(jpg_path)
                except Exception as e:
                    print(f"Error converting {jpg_path} to PNG: {e}")
        
    def clear_url(self):
        self.url_entry.delete(0, tk.END)

    def toggle_shuffle(self):
        if not self.shuffle_on:
            self.shuffle_on = True
            self.shuffle_mode.set(True)
        elif self.shuffle_on:
            self.shuffle_on = False
            self.shuffle_mode.set(False)
            
    def update_download_status(self, message):
        self.download_status_label.config(text=message, foreground="red")

    def populate_playlist(self):
        self.listbox.delete(0, tk.END)  # Clear the listbox
        self.playlist = [file for file in os.listdir(self.song_directory) if file.endswith(".mp3")]
        for song in self.playlist:
            self.listbox.insert(tk.END, song)
            
    def update_playlist(self):
        self.listbox.delete(0, tk.END)  # Clear the listbox
        self.populate_playlist()  # Repopulate the playlist

    def open_folder(self):
        if os.path.exists(self.song_directory):
            os.startfile(self.song_directory)
        else:
            messagebox.showwarning("Warning", "𝗦𝗼𝗻𝗴 𝗱𝗶𝗿𝗲𝗰𝘁𝗼𝗿𝘆 𝗱𝗼𝗲𝘀 𝗻𝗼𝘁 𝗲𝘅𝗶𝘀𝘁!")

    def change_location(self):
        new_location = filedialog.askdirectory()
        if new_location:
            self.song_directory = new_location
            
            # Copy default_image.png to the song directory if it's not already there
            default_image_path = os.path.join(os.getcwd(), "default_image.png")
            song_default_image_path = os.path.join(self.song_directory, "default_image.png")
            if not os.path.exists(song_default_image_path):
                shutil.copy(default_image_path, song_default_image_path)
                
            song_default_thumb_path = os.path.join(self.song_directory, "thumb.png")
            if not os.path.exists(song_default_thumb_path):
                shutil.copy(default_image_path, song_default_thumb_path)
            
            self.update_playlist()
            self.playlist_label.config(text=os.path.basename(self.song_directory))  # Update playlist label
            self.image_path = os.path.join(self.song_directory, 'thumb.png') 
            if(os.path.isfile(self.image_path)):
                self.playlist_art = self.round_corners(self.image_path)
                self.playlist_art = self.playlist_art.resize((100, 100), Image.Resampling.LANCZOS)
                self.playlist_artwork = ImageTk.PhotoImage(self.playlist_art)  
                self.playlist_image.config(image=self.playlist_artwork)


    def save_to_playlist(self, link):
        ragp_file = os.path.join(self.song_directory, os.path.basename(self.song_directory) + ".ragp")
        
        with open(ragp_file, 'a') as file:
            file.write(link + "\n")
    
    def import_playlist(self):
        # Ask the user to select the .ragp file
        file_path = filedialog.askopenfilename(filetypes=[("RAGP Files", "*.ragp")])

        if file_path:
            try:
                # Read all links from the .ragp file
                with open(file_path, 'r') as file:
                    links = file.readlines()

                # Remove any extra whitespace or newlines
                links = [link.strip() for link in links]

                # Download all files from the playlist
                for link in links:
                    self.download_song_from_url(link)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import playlist: {str(e)}")
                
    def export_playlist(self):
        # Get the path to the .ragp file
        ragp_file = os.path.join(self.song_directory, os.path.basename(self.song_directory) + ".ragp")
        print(ragp_file)
        if not os.path.exists(ragp_file):
            messagebox.showerror("Error", "No playlist file found to export.")
            return

        # Ask the user where they want to save the file
        destination_path = filedialog.asksaveasfilename(defaultextension=".ragp", filetypes=[("RAGP Files", "*.ragp")])

        if destination_path:
            try:
                # Copy the .ragp file to the selected destination
                with open(ragp_file, 'r') as src, open(destination_path, 'w') as dst:
                    dst.write(src.read())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export playlist: {str(e)}")
                
    def download_song_from_url(self, link):
        source = self.detect_source(link)
        self.save_to_playlist(link)
        if source in ["YouTube", "Spotify", "SoundCloud"]:
            self.downloading = True  # Set downloading flag
            # Start downloading in a separate thread
            download_thread = threading.Thread(target=self.start_download, args=(link, source))
            download_thread.start()
        else:
            messagebox.showwarning("Warning", "𝗨𝗻𝘀𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗨𝗥𝗟! 𝗣𝗿𝗼𝗴𝗿𝗮𝗺 𝗶𝘀 𝗺𝗮𝗱𝗲 𝘁𝗼 𝘄𝗼𝗿𝗸 𝘄𝗶𝘁𝗵 𝘆𝗼𝘂𝘁𝘂𝗯𝗲, 𝘀𝗽𝗼𝘁𝗶𝗳𝘆 𝗮𝗻𝗱 𝘀𝗼𝘂𝗻𝗱𝗰𝗹𝗼𝘂𝗱 𝗹𝗶𝗻𝗸𝘀.")
        
    def download_song(self):
        url = self.url_entry.get()
        source = self.detect_source(url)
        self.save_to_playlist(url)
        if source in ["YouTube", "Spotify", "SoundCloud"]:
            self.downloading = True  # Set downloading flag
            # Start downloading in a separate thread
            download_thread = threading.Thread(target=self.start_download, args=(url, source))
            download_thread.start()
        else:
            messagebox.showwarning("Warning", "𝗨𝗻𝘀𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱 𝗨𝗥𝗟! 𝗣𝗿𝗼𝗴𝗿𝗮𝗺 𝗶𝘀 𝗺𝗮𝗱𝗲 𝘁𝗼 𝘄𝗼𝗿𝗸 𝘄𝗶𝘁𝗵 𝘆𝗼𝘂𝘁𝘂𝗯𝗲, 𝘀𝗽𝗼𝘁𝗶𝗳𝘆 𝗮𝗻𝗱 𝘀𝗼𝘂𝗻𝗱𝗰𝗹𝗼𝘂𝗱 𝗹𝗶𝗻𝗸𝘀.")


    def start_download(self, url, source):
        if source == "YouTube":
            self.download_youtube_audio(url)
        elif source == "Spotify":
            self.download_spotify_audio(url)
        elif source == "SoundCloud":
            self.download_soundcloud_audio(url)

    def detect_source(self, url):
        if "youtube.com" in url or "youtu.be" in url:
            return "YouTube"
        elif "spotify.com" in url:
            return "Spotify"
        elif "soundcloud.com" in url:
            return "SoundCloud"
        else:
            return None
                
    # Modify the download_youtube_audio function to properly handle encoding
    def download_youtube_audio(self, song_url):
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '').strip()
                    speed = d.get('_speed_str', '').strip()

                    # Remove ANSI escape codes using regular expressions
                    percent = re.sub(r'\x1b\[[0-9;]*[mG]', '', percent)
                    speed = re.sub(r'\x1b\[[0-9;]*[mG]', '', speed)

                    # Format the progress message with percentage downloaded and download speed
                    message = f"[Ragging] {percent} {speed}"
                    self.update_download_status(message)

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'ffmpeg_location': self.ffmpeg_dir,
                'outtmpl': os.path.join(self.song_directory, '%(title)s.%(ext)s'),  # Save to current directory
                'progress_hooks': [progress_hook],
                'skip_unavailable_fragments': True,
                'writethumbnail': True,  # Write video thumbnail,
                'ignoreerrors' : True
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_url])

            self.reload_playlist()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download songs: {str(e)}")
        finally:
            self.reload_playlist()
            self.update_download_status("")
            self.downloading = False  # Reset downloading flag


    def download_spotify_audio(self, track_id):
        try:
            client_credentials_manager = SpotifyClientCredentials(client_id='FILL',
                                                              client_secret='FILL')
            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

            track = sp.track(track_id)
            title = track['name']
            artist = track['artists'][0]['name']

            self.search_and_download_youtube(title, artist)

            self.downloading = False
            self.update_download_status("Song ragged successfuly!")
            self.reload_playlist()
        except Exception as e:
            messagebox.showerror("Error", f"𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗿𝗮𝗴 𝘀𝗼𝗻𝗴: {str(e)}")

    def download_soundcloud_audio(self, song_url):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'ffmpeg_location': self.ffmpeg_dir,
                'outtmpl': os.path.join(self.song_directory, '%(title)s.%(ext)s'),  # Save to current directory
                'writethumbnail': True,  # Write embedded thumbnail,
                'ignoreerrors' : True
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_url])

        except Exception as e:
                        messagebox.showerror("Error", f"Failed to download songs: {str(e)}")
        finally:
                        self.reload_playlist()
                        self.downloading = False  # Reset downloading flag

    def search_and_download_youtube(self, title, artist):
        query = f'"{title}" "{artist}"'
        options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'ffmpeg_location': self.ffmpeg_dir,
            'outtmpl': os.path.join(self.song_directory, '%(title)s.%(ext)s'),
            'default_search': 'ytsearch',
            'writethumbnail': True,
            'ignoreerrors' : True
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([query])

    def play_song(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            self.current_index = selected_index[0]
            self.current_song = self.playlist[self.current_index]
            mp3_path = os.path.join(self.song_directory, self.current_song)
            
            # Check if a corresponding PNG image exists
            png_path = os.path.join(self.song_directory, os.path.splitext(self.current_song)[0] + ".png")
            if os.path.exists(png_path):
                # Open the PNG image
                self.rounded_image = self.round_corners(png_path)
                img = self.rounded_image
                # Resize the image to fit the label if needed
                img = img.resize((200, 200), resample=Image.Resampling.LANCZOS)  # Adjust desired_width and desired_height as needed
                # Convert the image to Tkinter PhotoImage
                self.album_art = ImageTk.PhotoImage(img)
                # Update the album art label
                self.album_art_label.config(image=self.album_art)
                self.album_art_label.image = self.album_art
            else:
                # Use default image if no embedded image found
                self.default_image_path = os.path.join(self.song_directory, "default_image.png")
                self.rounded_image = self.round_corners(self.default_image_path)
                
                self.album_art = ImageTk.PhotoImage(self.rounded_image)
                self.album_art_label.config(image=self.album_art)
                self.album_art_label.image = self.album_art


            pygame.mixer.music.load(mp3_path)
            pygame.mixer.music.play()


    def stop_song(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.paused = False
    
    def toggle_pause_unpause(self, event):
        if pygame.mixer.music.get_busy():
            if self.paused:
                pygame.mixer.music.unpause()  # Unpause if music is paused
                self.paused = False
                self.pause_unpause_button.configure(image=self.pause_image)
            else:
                pygame.mixer.music.pause()  # Pause if music is playing
                self.paused = True
                self.pause_unpause_button.configure(image=self.play_image)
            
    def pause_unpause_song(self):
        if self.paused:
            pygame.mixer.music.unpause()  # Unpause if music is paused
            self.paused = False
            self.pause_unpause_button.configure(image=self.pause_image)
        else:
            pygame.mixer.music.pause()  # Pause if music is playing
            self.paused = True
            self.pause_unpause_button.configure(image=self.play_image)

    def next_song(self):
        if self.shuffle_on:
            next_index = random.randint(0, self.listbox.size() - 1)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(next_index)
            self.listbox.activate(next_index)
            self.play_song()
        else:
            self.current_index = (self.current_index + 1) % self.listbox.size()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.activate(self.current_index)
            self.play_song()

    def previous_song(self):
        if self.shuffle_on:
            previous_index = random.randint(0, self.listbox.size() - 1)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(previous_index)
            self.listbox.activate(previous_index)
            self.play_song()
        else:
            self.current_index = (self.current_index - 1) % self.listbox.size()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.activate(self.current_index)
            self.play_song()

    def set_volume(self, val):
            volume = float(val) / 200
            pygame.mixer.music.set_volume(volume)

    def play_selected_song(self, event):
        self.play_song()
        self.pause_unpause_button.configure(image=self.pause_image)
        
    def close_window(self):
        self.running = False  # Update the flag when the window is closed
        self.mainwindow.destroy()  # Destroy the main window

        
    def get_time(self):
        if not self.running:  # Check if the application is closing or window is destroyed
            return
        
        try:
            current_time = pygame.mixer.music.get_pos() / 1000
            formatted_time = time.strftime("%M:%S", time.gmtime(current_time))

            next_one = self.listbox.curselection()
            if next_one:  # Check if anything is selected
                index = next_one[0]  # Get the index of the selected item
                song = self.listbox.get(index)  # Get the song name from the listbox
                song_timer = MP3(os.path.join(self.song_directory, song))
                song_length = int(song_timer.info.length)
                format_for_length = time.strftime("%M:%S", time.gmtime(song_length))
                self.progressbar_label.configure(text=f"{formatted_time} / {format_for_length}")

                # Set the name of the song under the progress bar
                self.song_label.configure(text=f"{song}")

                self.progressbar["maximum"] = song_length
                self.progressbar["value"] = int(current_time)

                # Check if current time equals or exceeds song length
                if int(current_time) >= song_length:
                    if len(self.playlist) == 1:
                        # Replay the same song if there's only one song in the playlist
                        self.play_song()
                    else:
                        if self.shuffle_on:
                            # Select a random song from the playlist
                            next_index = random.randint(0, len(self.playlist) - 1)  # Select a random song index
                            while next_index == index:  # Ensure the next song is not the same as the current one
                                next_index = random.randint(0, len(self.playlist) - 1)
                        else:
                            # Select the next song in the playlist, loop back to the first if reaching the last song
                            next_index = (index + 1) % len(self.playlist)

                        self.listbox.selection_clear(0, tk.END)
                        self.listbox.selection_set(next_index)
                        self.current_index = next_index

                        # Play the next song
                        self.play_song()

            if self.running:
                self.mainwindow.after(100, self.get_time)

        except tk.TclError as e:
            print(f"Error in get_time: {e}")

                        

    def center(self, event):
        wm_min = self.mainwindow.wm_minsize()
        wm_max = self.mainwindow.wm_maxsize()
        screen_w = self.mainwindow.winfo_screenwidth()
        screen_h = self.mainwindow.winfo_screenheight()
        x_min = min(screen_w, wm_max[0],
                    max(self.main_w, wm_min[0],
                        self.mainwindow.winfo_width(),
                        self.mainwindow.winfo_reqwidth()))
        y_min = min(screen_h, wm_max[1],
                    max(self.main_h, wm_min[1],
                        self.mainwindow.winfo_height(),
                        self.mainwindow.winfo_reqheight()))
        x = screen_w - x_min
        y = screen_h - y_min
        self.mainwindow.geometry(f"{x_min}x{y_min}+{x // 2}+{y // 2}")
        self.mainwindow.unbind("<Map>", self.center_map)

    def run(self, center=False):
        if center:
            self.main_w = self.mainwindow.winfo_reqwidth()
            self.main_h = self.mainwindow.winfo_reqheight()
            self.center_map = self.mainwindow.bind("<Map>", self.center)
        self.get_time()  # Start updating the time and progress bar
        self.mainwindow.mainloop()
        
    def on_destroy(self):
        self.running = False
        self.mainwindow.after_cancel(self.get_time)  # Cancel the ongoing get_time callback
        self.mainwindow.destroy()

if __name__ == "__main__":
    app = rag_ui()
    app.run()
    
