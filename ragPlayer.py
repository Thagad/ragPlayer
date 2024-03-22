import tkinter as tk
#import tkinter.ttk as ttk
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
from PIL import Image, ImageTk
import base64
from tkinter import PhotoImage

class rag_ui:
    def __init__(self, master=None):
        # Initialize pygame mixer
        pygame.mixer.init()
        # Global variables
        self.current_index = 0
        self.playlist = []
        self.cropped = []
        self.current_song = None
        self.paused = False
        self.song_directory = os.getcwd()  # Default song directory
        self.downloading = False  # Flag to track if downloading is in progress
        self.running = True
        self.shuffle_on = True

        # Build UI
        self.mainwindow = ttk.Window(themename='ragard_dark') if master is None else tk.Toplevel(master)
        self.mainwindow.configure(height=500, width=400)
        self.mainwindow.resizable(False, False)
        self.mainwindow.title("ragPlayer")

        self.frame_main = ttk.Frame(self.mainwindow, name="frame_main")
        self.frame_main.configure(height=500, width=400)

        label1 = ttk.Label(self.frame_main)
        label1.configure(font="{BigNoodleTitling} 36 {}", text='ragPlayer')
        label1.pack(side="top")

        self.download_frame = tk.LabelFrame(
            self.frame_main, name="download_frame")
        self.download_frame.configure(height=200, width=200)

        self.url_label = ttk.Label(self.download_frame, name="url_label")
        self.url_label.configure(
            font="{BigNoodleTitling} 14 {}",
            text='Song Url:')
        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.url_entry = ttk.Entry(self.download_frame, name="url_entry")
        self.url_entry.configure(font="{BigNoodleTitling} 12 {}")
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        self.download_status_label = ttk.Label(self.download_frame, name="download_status_label")
        self.download_status_label.configure(text="", foreground="red", font="{BigNoodleTitling} 12 {}")
        self.download_status_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")

        self.button4 = ttk.Button(self.download_frame, name="button4")
        self.button4.configure(text='𝗥𝗮𝗴 𝗶𝘁', command=self.download_song, width=6)  # Adjusted width
        self.button4.grid(row=2, column=0, padx=(10, 5), sticky="ew")

        # Add the new button next to the "Rag it" button
        self.clear_url_button = ttk.Button(self.download_frame, name="clear_url_button")
        self.clear_url_button.configure(text='𝗖𝗹𝗲𝗮𝗿', command=self.clear_url, width=6)  # Adjusted width
        self.clear_url_button.grid(row=2, column=1, padx=(5, 10), sticky="ew")

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

        self.open_folder_button = ttk.Button(
            self.folder_frame, image=self.folder_image, command=self.open_folder, padding=0, compound=tk.CENTER)
        self.open_folder_button.pack(side="left", padx=5)
        self.open_folder_button.config(width=5)  # Set button width

        self.change_location_button = ttk.Button(
            self.folder_frame, image=self.eye_image, command=self.change_location, padding=0, compound=tk.CENTER)
        self.change_location_button.pack(side="right", padx=5)
        self.change_location_button.config(width=5)  # Set button width
        
        self.refresh_button = ttk.Button(
            self.folder_frame, image=self.refresh_image, command=self.reload_playlist,padding=0, compound=tk.CENTER)
        self.refresh_button.pack(side="right", padx=5)
        self.refresh_button.config(width=5)  # Set button width

        self.folder_frame.pack(side="top")

        self.playlist_frame = tk.Frame(
            self.frame_main, name="playlist_frame")
        self.playlist_frame.configure(height=200, width=200)

        self.playlist_label = ttk.Label(
            self.playlist_frame, name="playlist_label")
        self.playlist_label.configure(
            font="{BigNoodleTitling} 20 {italic underline}",
            text=os.path.basename(self.song_directory))  # Set label text to folder name
        self.playlist_label.pack(side="top")

        self.listbox = tk.Listbox(self.playlist_frame, name="listbox")
        self.listbox.configure(font="{BigNoodleTitling} 14 {}", width=70)  # Adjust width as needed
        self.listbox.pack(side="top", fill="both", expand=True)
        self.populate_playlist()  # Populate playlist initially
        self.listbox.bind("<<ListboxSelect>>", self.play_selected_song)  # Bind selection event to play_selected_song

        self.playlist_frame.pack(side="top", pady= 20)

        self.button_frame = ttk.Frame(
            self.frame_main, name="button_frame")
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

        self.button_frame.pack(side="top", pady=5)

        self.volume_panel = ttk.Frame(
            self.frame_main, name="volume_panel")
        self.volume_panel.configure(height=200, width=200)
        self.album_art = PhotoImage(file=os.path.join(self.song_directory, "default_image.png")) 
        self.album_art_label = ttk.Label(self.volume_panel, name="album_art_label", image=self.album_art)
        self.album_art_label.pack(side="top")

        self.scale1 = ttk.Scale(self.volume_panel)
        self.scale1.configure(length=150, orient="horizontal", from_= 0, to=50, command=self.set_volume)
        self.scale1.set(25)
        self.scale1.pack(side="top", pady=20)

        self.progressbar = ttk.Progressbar(
            self.volume_panel, name="progressbar")
        self.progressbar.configure(length=450, orient="horizontal", mode='determinate')
        self.progressbar.pack(side="top")

        self.progressbar_label = ttk.Label(
            self.volume_panel, name="progressbar_label")
        self.progressbar_label.configure(
            font="{BigNoodleTitling} 14 {}",
            text='00:00 / 00:00')
        self.progressbar_label.pack(side="top")
        self.song_label = ttk.Label(self.volume_panel, name="song_label")
        self.song_label.configure(width=60, font="{BigNoodleTitling} 16 {}", text='Now playing: ')
        self.song_label.pack(side="top", pady= 20)
        self.mainwindow.bind("<space>", self.toggle_pause_unpause)

        self.get_time()  # Start updating the time and progress bar

        self.volume_panel.pack(side="top")
        self.frame_main.pack(side="top")
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.close_window)

        self.mainwindow.mainloop()
    
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
    
    def update_album_art(self, img_path):
        self.album_art_label.config(image=self.album_art)
        self.album_art_label.image = self.album_art
        
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
            self.update_playlist()
            self.playlist_label.config(text=os.path.basename(self.song_directory))  # Update playlist label


    def download_song(self):
        url = self.url_entry.get()
        source = self.detect_source(url)
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
                'outtmpl': os.path.join(self.song_directory, '%(title)s.%(ext)s'),  # Save to current directory
                'progress_hooks': [progress_hook],
                'skip_unavailable_fragments': True,
                'writethumbnail': True,  # Write video thumbnail,
                'ignoreerrors' : True
            }

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_url])


        except Exception as e:
            messagebox.showerror("Error", f"Failed to download songs: {str(e)}")
        finally:
            self.reload_playlist()
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
            'outtmpl': f"%(title)s.%(ext)s",
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
                img = Image.open(png_path)
                # Resize the image to fit the label if needed
                img = img.resize((250, 250), resample=Image.Resampling.LANCZOS)  # Adjust desired_width and desired_height as needed
                # Convert the image to Tkinter PhotoImage
                self.album_art = ImageTk.PhotoImage(img)
                # Update the album art label
                self.album_art_label.config(image=self.album_art)
                self.album_art_label.image = self.album_art
            else:
                # Use default image if no embedded image found
                self.update_album_art(os.path.join(self.song_directory, "default_image.png"))  # Replace "path_to_default_image.png" with your default image path

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
        if self.listbox.size() == 0:
            # If the playlist is empty, do nothing
            return
        
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
        if self.listbox.size() == 0:
            # If the playlist is empty, do nothing
            return
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


    def play_selected_song(self, event):
        self.play_song()
        self.pause_unpause_button.configure(image=self.pause_image)
            
    def set_volume(self, val):
        volume = float(val) / 50
        pygame.mixer.music.set_volume(volume)
        
    def close_window(self):
        self.running = False  # Update the flag when the window is closed
        self.mainwindow.destroy()  # Destroy the main window

        
    def get_time(self):
        if self.running:  # Check if the application is still running
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
                self.song_label.configure(text=f"Now playing: {song}")  # Add this line

                self.progressbar["maximum"] = song_length
                self.progressbar["value"] = int(current_time)

                # Check if current time equals or exceeds song length
                if int(current_time) >= song_length:
                    # Stop the current song
                    pygame.mixer.music.stop()

                    if self.shuffle_on:
                        # Select a random song from the playlist
                        next_index = random.randint(0, len(self.playlist) - 1)  # Select a random song index
                        while next_index == index:  # Ensure the next song is not the same as the current one
                            next_index = random.randint(0, len(self.playlist) - 1)
                    else:
                        # Select the next song in the playlist
                        next_index = (index + 1) % len(self.playlist)

                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(next_index)
                    self.current_index = next_index

                    # Play the next song
                    self.play_song()

            # Check if the current song has finished playing
            if not pygame.mixer.music.get_busy():
                # Play the next song
                self.next_song()

            self.mainwindow.after(100, self.get_time)




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

if __name__ == "__main__":
    app = rag_ui()
    app.run()
