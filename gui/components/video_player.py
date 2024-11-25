import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
import threading
import time
import os
import tempfile
from collections import deque
from io import BytesIO
import logging
import pygame
from pathlib import Path

try:
    from ...material_colors import MaterialColors
except ImportError:
    # Fallback colors in case import fails
    class MaterialColors:
        BACKGROUND = "#F5F5F5"
        PRIMARY_LIGHT = "#BBDEFB"
        PRIMARY_DARK = "#1976D2"
        SURFACE = "#FFFFFF"
        TEXT_SECONDARY = "#757575"
        PRIMARY = "#2196F3"

class VideoPlayer(tk.Toplevel):
    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.withdraw()
        self.title("Video Player")
        
        # Initialize audio
        pygame.mixer.init(frequency=44100)
        
        # Initialize synchronization primitives
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._seek_event = threading.Event()
        
        # Initialize variables
        self.playing = False
        self.video_thread = None
        self.frame_thread = None
        self.cap = None
        self.frame_buffer = deque(maxlen=30)
        self.seeking = False
        self.current_photo = None
        self.next_photo = None
        self.last_frame_time = 0
        self.temp_video = None
        self.audio_temp = None
        self.volume = 1.0
        
        try:
            # Get secure handle from parent's file manager
            secure_handle = parent.file_manager.get_decrypted_file(file_path)
            if not secure_handle:
                raise Exception("Failed to get secure file handle")
            
            # Read video data
            video_data = secure_handle.read()
            if not video_data:
                raise Exception("Failed to read video data")
            
            # Create temporary files for video and audio
            self.setup_media(video_data)
            
            # Initialize video properties
            self.init_video_properties()
            
            # Setup UI
            self.setup_ui()
            
            # Configure window
            self.setup_window()
            
            # Start playback
            self.start_playback()
            
            # Show window
            self.deiconify()
            
            # Bind cleanup
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
        except Exception as e:
            logging.error(f"Failed to initialize video player: {e}")
            self.cleanup()
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")
            self.destroy()
            return
      
    def setup_media(self, video_data):
        """Setup video and audio files."""
        try:
            # Get temp paths from temp manager
            video_path = self.master.temp_manager.get_temp_path(prefix="video_", suffix=".mp4")
            audio_path = self.master.temp_manager.get_temp_path(prefix="audio_", suffix=".mp4")
            
            # Create temporary video file
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            with open(video_path, 'wb') as f:
                f.write(video_data)
            self.temp_video = Path(video_path)
            
            # Create separate audio file
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            with open(audio_path, 'wb') as f:
                f.write(video_data)
            self.audio_temp = Path(audio_path)
            
            # Open video
            self.cap = cv2.VideoCapture(str(self.temp_video))
            if not self.cap.isOpened():
                raise Exception("Failed to open video file")
            
            # Initialize audio
            try:
                pygame.mixer.music.load(str(self.audio_temp))
                pygame.mixer.music.set_volume(self.volume)
                logging.info("Audio track loaded successfully")
            except Exception as e:
                logging.warning(f"Could not load audio track: {e}")
            
        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to setup media: {e}")
      
    def setup_audio(self):
        """Setup audio playback."""
        try:
            pygame.mixer.music.load(self.temp_video.name)
            pygame.mixer.music.set_volume(self.volume)
        except Exception as e:
            logging.warning(f"No audio track found: {e}")
            
    def setup_video(self, video_data):
        """Setup video capture with temporary file."""
        try:
            # Create temporary file
            self.temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            self.temp_video.write(video_data)
            self.temp_video.flush()
            
            # Open video
            self.cap = cv2.VideoCapture(self.temp_video.name)
            if not self.cap.isOpened():
                raise Exception("Failed to open video file")
                
            # Set buffer size
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to setup video: {e}")
    
    def init_video_properties(self):
        """Initialize video properties."""
        self.fps = max(1, self.cap.get(cv2.CAP_PROP_FPS))  # Ensure minimum FPS of 1
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        self.frame_time = 1.0 / self.fps
        self.current_frame = 0
        
        # Get video dimensions
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate display size
        screen_width = self.winfo_screenwidth() * 0.8
        screen_height = self.winfo_screenheight() * 0.8
        
        scale = min(screen_width/frame_width, screen_height/frame_height)
        self.display_width = int(frame_width * scale)
        self.display_height = int(frame_height * scale)
        
    def start_playback(self):
        """Start video playback."""
        # Start frame fetching thread
        self.frame_thread = threading.Thread(target=self.fetch_frames, daemon=True)
        self.frame_thread.start()
        
        # Start playing
        self.play()
    
    def setup_ui(self):
        """Setup video player UI."""
        # Configure window style
        self.configure(bg=MaterialColors.BACKGROUND)
        
        # Create main container
        self.container = ttk.Frame(self, style='Gallery.TFrame')
        self.container.pack(fill='both', expand=True)
        
        # Create video canvas
        self.setup_video_canvas()
        
        # Create controls
        self.setup_controls()
    
    def setup_video_canvas(self):
        """Setup the video display canvas."""
        self.canvas = tk.Canvas(
            self.container,
            width=self.display_width,
            height=self.display_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
        
        # Create two image items for double buffering
        self.image_a = self.canvas.create_image(
            self.display_width//2,
            self.display_height//2,
            anchor='center'
        )
        self.image_b = self.canvas.create_image(
            self.display_width//2,
            self.display_height//2,
            anchor='center'
        )
        self.current_image = self.image_a
        self.next_image = self.image_b
    
    def setup_controls(self):
        """Setup video control panel."""
        # Configure progress bar style
        style = ttk.Style()
        style.configure(
            "Video.Horizontal.TScale",
            sliderwidth=10,
            sliderlength=15,
            sliderthickness=15,
            background=MaterialColors.BACKGROUND,
            troughcolor=MaterialColors.PRIMARY_LIGHT,
            borderwidth=0
        )
        
        control_frame = ttk.Frame(self, style='Gallery.TFrame', padding=10)
        control_frame.pack(fill='x')
        
        # Play/Pause button
        self.play_button = ttk.Button(
            control_frame,
            text="⏸",  # Pause symbol
            width=3,
            command=self.toggle_play,
            style='Action.TButton'
        )
        self.play_button.pack(side='left', padx=5)
        
        # Time display
        self.time_label = ttk.Label(
            control_frame,
            text="0:00 / 0:00",
            style='Status.TLabel'
        )
        self.time_label.pack(side='right', padx=5)
        
        # Progress bar frame
        self.progress_frame = ttk.Frame(control_frame, style='Gallery.TFrame')
        self.progress_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Scale(
            self.progress_frame,
            from_=0,
            to=self.frame_count,
            variable=self.progress_var,
            orient='horizontal',
            style="Video.Horizontal.TScale"
        )
        self.progress_bar.pack(fill='x', expand=True)
        
        # Bind progress bar events
        self.progress_bar.bind('<Button-1>', self.start_seek)
        self.progress_bar.bind('<B1-Motion>', self.update_seek)
        self.progress_bar.bind('<ButtonRelease-1>', self.end_seek)
        
        # Bind keyboard shortcuts
        self.bind('<space>', lambda e: self.toggle_play())
        self.bind('<Left>', lambda e: self.seek_relative(-5))  # 5 seconds back
        self.bind('<Right>', lambda e: self.seek_relative(5))  # 5 seconds forward
        self.bind('<Escape>', lambda e: self.on_closing())  # Quick exit
        
    def _update_seek_preview(self, event):
        """Update preview frame while seeking."""
        try:
            # Get click position
            w = self.progress_bar.winfo_width()
            x = event.x
            fraction = min(max(x / w, 0), 1)
            
            # Calculate frame number
            frame = int(fraction * self.frame_count)
            
            with self._lock:
                # Save current position
                current = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                
                # Seek to new position
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                ret, preview = self.cap.read()
                
                if ret:
                    # Update preview frame
                    preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                    preview = cv2.resize(
                        preview,
                        (self.display_width, self.display_height),
                        interpolation=cv2.INTER_LINEAR
                    )
                    
                    # Show preview
                    image = Image.fromarray(preview)
                    photo = ImageTk.PhotoImage(image)
                    self.canvas.itemconfig(self.current_image, image=photo)
                    self.current_photo = photo
                    
                    # Update time display
                    current_time = frame / self.fps
                    current_str = time.strftime('%M:%S', time.gmtime(current_time))
                    total_str = time.strftime('%M:%S', time.gmtime(self.duration))
                    self.time_label.configure(text=f"{current_str} / {total_str}")
                    
                    # Update progress bar
                    self.progress_var.set(frame)
                
                # Restore position if we're still seeking
                if self.seeking:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, current)
                
        except Exception as e:
            logging.error(f"Error updating seek preview: {e}")
            
    def end_seek(self, event):
        """Handle end of seeking."""
        try:
            if not self.seeking:
                return
                
            # Get final position
            w = self.progress_bar.winfo_width()
            x = event.x
            fraction = min(max(x / w, 0), 1)
            frame = int(fraction * self.frame_count)
            time_pos = frame / self.fps
            
            # Seek video
            with self._lock:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                ret, new_frame = self.cap.read()
                
                if ret:
                    # Update display
                    new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
                    new_frame = cv2.resize(
                        new_frame,
                        (self.display_width, self.display_height),
                        interpolation=cv2.INTER_LINEAR
                    )
                    
                    image = Image.fromarray(new_frame)
                    photo = ImageTk.PhotoImage(image)
                    self.canvas.itemconfig(self.current_image, image=photo)
                    self.current_photo = photo
                    
                    # Update state
                    self.current_frame = frame
                    self.progress_var.set(frame)
                    self.update_time_label(time_pos)
                    
                    # Seek audio
                    try:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.play(start=time_pos)
                        if not self.playing:
                            pygame.mixer.music.pause()
                    except Exception as e:
                        logging.warning(f"Error seeking audio: {e}")
            
            # Resume playback if was playing
            was_playing = self.playing
            self.seeking = False
            self._seek_event.clear()
            
            if was_playing:
                self.play()
                
        except Exception as e:
            logging.error(f"Error ending seek: {e}")
            self.seeking = False
            self._seek_event.clear()
        
    def start_seek(self, event):
        """Handle start of seeking."""
        self.pause()
        self.seeking = True
        self._seek_event.set()
        self.frame_buffer.clear()
        self._update_seek_position(event)
        
    def update_seek(self, event):
        """Handle seek bar dragging."""
        if self.seeking:
            self._update_seek_position(event)
    
    def _update_seek_position(self, event):
        """Update video position during seeking."""
        try:
            # Calculate new position
            w = self.progress_bar.winfo_width()
            x = event.x
            fraction = min(max(x / w, 0), 1)
            frame = int(fraction * self.frame_count)
            
            # Update progress bar and time display
            self.progress_var.set(frame)
            current_time = frame / self.fps
            self.update_time_label(current_time)
            
        except Exception as e:
            logging.error(f"Error updating seek position: {e}")
    
    def setup_window(self):
        """Configure window properties."""
        # Make window modal
        self.transient(self.master)
        self.grab_set()
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center window on screen."""
        window_width = self.display_width
        window_height = self.display_height + 100  # Extra space for controls
        
        x = (self.winfo_screenwidth() - window_width) // 2
        y = (self.winfo_screenheight() - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def start_video_threads(self):
        """Start video playback threads."""
        # Start frame fetching thread
        self.frame_thread = threading.Thread(
            target=self.fetch_frames,
            daemon=True
        )
        self.frame_thread.start()
        
        # Start playback
        self.play()
    
    def fetch_frames(self):
        """Fetch frames in background thread."""
        while not self._stop_event.is_set():
            with self._lock:
                if not self.playing or self.seeking or len(self.frame_buffer) >= self.frame_buffer.maxlen:
                    time.sleep(0.001)
                    continue
                
                if self.cap is None:
                    break
                    
                ret, frame = self.cap.read()
                if not ret:
                    # Loop video
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Convert and resize frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.display_width != frame.shape[1] or self.display_height != frame.shape[0]:
                    frame = cv2.resize(
                        frame,
                        (self.display_width, self.display_height),
                        interpolation=cv2.INTER_LINEAR
                    )
                
                # Add to buffer
                self.frame_buffer.append(frame)
    
    def update_frame(self):
        """Update video frame."""
        while self.playing and not self._stop_event.is_set():
            try:
                if self.seeking:
                    time.sleep(0.001)
                    continue
                
                current_time = time.time()
                elapsed = current_time - self.last_frame_time
                
                if elapsed >= self.frame_time and self.frame_buffer:
                    with self._lock:
                        if not self.frame_buffer:
                            continue
                        frame = self.frame_buffer.popleft()
                        
                        # Convert to PhotoImage
                        image = Image.fromarray(frame)
                        photo = ImageTk.PhotoImage(image)
                        
                        # Update canvas
                        self.canvas.itemconfig(self.current_image, image=photo)
                        self.current_photo = photo
                        
                        # Update progress
                        if not self.seeking:
                            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                            self.progress_var.set(self.current_frame)
                            self.update_time_label()
                    
                    self.last_frame_time = current_time
                
                time.sleep(max(0, (self.frame_time - elapsed) / 2))
                
            except Exception as e:
                logging.error(f"Error updating frame: {e}")
                if not self.frame_buffer:
                    time.sleep(0.001)
    
    def play(self):
        """Start playback."""
        if not self.cap:
            return
        
        self.playing = True
        self.play_button.configure(text="⏸")
        
        # Start audio
        try:
            current_time = self.current_frame / self.fps
            pygame.mixer.music.play(start=current_time)
        except Exception as e:
            logging.warning(f"Error starting audio: {e}")
        
        # Start video thread if needed
        if not self.video_thread or not self.video_thread.is_alive():
            self.video_thread = threading.Thread(target=self.update_frame, daemon=True)
            self.video_thread.start()
    
    def pause(self):
        """Pause playback."""
        self.playing = False
        self.play_button.configure(text="▶")
        
        # Pause audio
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            logging.warning(f"Error pausing audio: {e}")
    
    def toggle_play(self):
        """Toggle between play and pause."""
        if self.playing:
            self.pause()
        else:
            self.play()
    
    def seek_relative(self, seconds):
        """Seek relative to current position."""
        try:
            with self._lock:
                target_frame = self.current_frame + int(seconds * self.fps)
                target_frame = max(0, min(target_frame, self.frame_count - 1))
                
                # Pause and clear buffer
                was_playing = self.playing
                self.pause()
                self.frame_buffer.clear()
                
                # Seek
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = self.cap.read()
                
                if ret:
                    # Update display
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(
                        frame,
                        (self.display_width, self.display_height),
                        interpolation=cv2.INTER_LINEAR
                    )
                    
                    # Show frame
                    image = Image.fromarray(frame)
                    photo = ImageTk.PhotoImage(image)
                    self.canvas.itemconfig(self.current_image, image=photo)
                    self.current_photo = photo
                    
                    # Update state
                    self.current_frame = target_frame
                    self.progress_var.set(target_frame)
                    self.update_time_label()
                    
                    # Resume if was playing
                    if was_playing:
                        self.play()
                
        except Exception as e:
            logging.error(f"Error seeking: {e}")
            if was_playing:
                self.play()
    
    def seek_relative(self, seconds):
        """Seek relative to current position."""
        target_frame = self.current_frame + int(seconds * self.fps)
        target_frame = max(0, min(target_frame, self.frame_count - 1))
        self.seek_to_frame(target_frame)
    
    def seek_to_frame(self, frame):
        """Seek to specific frame."""
        try:
            self.seeking = True
            self.frame_buffer.clear()
            
            # Calculate time position
            time_pos = frame / self.fps
            
            # Seek video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
            ret, new_frame = self.cap.read()
            
            if ret:
                # Update video frame
                new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
                if self.display_width != new_frame.shape[1] or self.display_height != new_frame.shape[0]:
                    new_frame = cv2.resize(
                        new_frame,
                        (self.display_width, self.display_height),
                        interpolation=cv2.INTER_LINEAR
                    )
                
                image = Image.fromarray(new_frame)
                photo = ImageTk.PhotoImage(image)
                
                self.canvas.itemconfig(self.current_image, image=photo)
                self.current_photo = photo
                
                self.current_frame = frame
                self.progress_var.set(frame)
                self.update_time_label()
                
                # Seek audio if playing
                if self.playing:
                    try:
                        pygame.mixer.music.play(start=time_pos)
                    except:
                        pass
            
        finally:
            self.seeking = False
    
    def on_progress_change(self, value):
        """Handle progress bar changes."""
        if not self.seeking:
            frame = int(float(value))
            self.seek_to_frame(frame)
    
    def on_volume_change(self, value):
        """Handle volume changes."""
        pass  # Implement if audio support is added
    
    def adjust_volume(self, delta):
        """Adjust volume by delta amount."""
        self.volume = max(0.0, min(1.0, self.volume + (delta / 100.0)))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except:
            pass
        self.volume_var.set(self.volume * 100)
    
    def update_time_label(self, current_time):
        """Update the time display label."""
        try:
            total_time = self.duration
            current_str = time.strftime('%M:%S', time.gmtime(current_time))
            total_str = time.strftime('%M:%S', time.gmtime(total_time))
            self.time_label.configure(text=f"{current_str} / {total_str}")
        except Exception as e:
            logging.error(f"Error updating time label: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop playback
            self.playing = False
            self._stop_event.set()
            self._seek_event.set()
            
            # Stop audio
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass
            
            # Clear frame buffer
            self.frame_buffer.clear()
            
            # Release video capture
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Remove temporary files
            for temp_file in [self.temp_video, self.audio_temp]:
                if temp_file:
                    try:
                        temp_file.close()
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                    except:
                        pass
            
            # Clear references
            self.current_photo = None
            self.next_photo = None
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        
        finally:
            import gc
            gc.collect()
            
    def on_closing(self):
        """Handle window closing."""
        try:
            # Disable all bindings first
            self.unbind_all('<space>')
            self.unbind_all('<Left>')
            self.unbind_all('<Right>')
            self.unbind_all('<Escape>')
            self.unbind_all('<Up>')
            self.unbind_all('<Down>')
            
            # Stop playback and threads immediately
            self.playing = False
            self._stop_event.set()
            
            # Stop audio immediately
            try:
                pygame.mixer.music.stop()
            except:
                pass
            
            # Schedule cleanup and destroy
            self.after(100, self._finish_closing)
            
        except Exception as e:
            logging.error(f"Error during window closing: {e}")
            self.destroy()

    def _finish_closing(self):
        """Complete the closing process."""
        try:
            # Perform cleanup
            self.cleanup()
            
            # Release modal state
            self.grab_release()
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            logging.error(f"Error finishing close: {e}")
            self.destroy()

    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            self.cleanup()
        except:
            pass
            
            
            