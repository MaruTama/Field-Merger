import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import subprocess
import threading
import tempfile
import os

class FieldMerger:
    def __init__(self, root):
        self.root = root
        self.root.title("Field Merger")
        
        self.canvas_width = 600
        self.canvas_height = 400
        
        self.zoom_level = 1.0
        self.zoom_step = 0.1
        
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg='white')
        self.canvas.grid(row=0, column=1, rowspan=2, padx=(20, 0), pady=(20, 0))
        
        self.vertical_slider = tk.Scale(root, from_=-5, to=5, orient=tk.VERTICAL, resolution=1, command=self.update_image)
        self.vertical_slider.grid(row=0, column=2, padx=(0, 20), pady=(100, 0))
        
        self.horizontal_slider = tk.Scale(root, from_=-10, to=10, orient=tk.HORIZONTAL, resolution=1, command=self.update_image)
        self.horizontal_slider.grid(row=2, column=1, padx=(20, 0), pady=(0, 20), sticky='ew')
        
        control_frame = tk.Frame(root)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        self.load_button1 = tk.Button(control_frame, text="Load Field 1", command=self.load_field1)
        self.load_button1.pack(side=tk.LEFT)
        
        self.load_button2 = tk.Button(control_frame, text="Load Field 2", command=self.load_field2)
        self.load_button2.pack(side=tk.LEFT)
        
        self.save_button = tk.Button(control_frame, text="Save Merged Image", command=self.save_image)
        self.save_button.pack(side=tk.LEFT)
        
        self.deinterlace_button = tk.Button(control_frame, text="Save with De-interlaced", command=self.deinterlace_image)
        self.deinterlace_button.pack(side=tk.LEFT)
        
        self.field1 = None
        self.field2 = None
        self.merged_image = None
        
        self.image_x = 0
        self.image_y = 0
        self.last_x = 0
        self.last_y = 0
        
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        
        # Bind mousewheel events
        self.root.bind_all("<MouseWheel>", self.mouse_wheel_zoom)
        self.root.bind_all("<Button-4>", self.mouse_wheel_zoom)  # X11 systems
        self.root.bind_all("<Button-5>", self.mouse_wheel_zoom)  # X11 systems

    def load_field1(self):
        file_path = filedialog.askopenfilename(initialdir="/mnt/windows")
        if file_path:
            try:
                self.field1 = Image.open(file_path).convert('RGB')
                self.load_button1.config(bg="lightgreen")
                self.update_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def load_field2(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                self.field2 = Image.open(file_path).convert('RGB')
                self.load_button2.config(bg="lightgreen")
                self.update_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")

    def update_image(self, value=None):
        if self.field1 and self.field2:
            try:
                arr1 = np.array(self.field1)
                arr2 = np.array(self.field2)

                if arr1.shape != arr2.shape:
                    messagebox.showerror("Error", "Field images must be the same size and have the same number of channels")
                    return

                horizontal_shift = self.horizontal_slider.get()
                vertical_shift = self.vertical_slider.get()

                merged_arr = np.zeros_like(arr1)

                for i in range(arr1.shape[0]):
                    if i % 2 == 0:
                        merged_arr[i] = arr1[i]
                    else:
                        row_index = (i + vertical_shift) % arr1.shape[0]
                        row = np.roll(arr2[row_index], horizontal_shift, axis=0)  # Horizontal shift for field 2
                        merged_arr[i] = row

                self.merged_image = Image.fromarray(merged_arr)
                self.display_image(move_to_origin=False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to merge images: {e}")

    def display_image(self, move_to_origin=False):
        if self.merged_image:
            width, height = self.merged_image.size
            new_size = (int(width * self.zoom_level), int(height * self.zoom_level))
            zoomed_image = self.merged_image.resize(new_size, Image.Resampling.LANCZOS)

            self.tk_image = ImageTk.PhotoImage(zoomed_image)

            if move_to_origin:
                self.image_x = (self.canvas_width - new_size[0]) // 2
                self.image_y = (self.canvas_height - new_size[1]) // 2

            self.canvas.delete("all")
            self.canvas.create_image(self.image_x, self.image_y, anchor=tk.NW, image=self.tk_image)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def start_drag(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def do_drag(self, event):
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        self.image_x += dx
        self.image_y += dy
        self.canvas.move(tk.ALL, dx, dy)
        self.last_x = event.x
        self.last_y = event.y

    def mouse_wheel_zoom(self, event):
        if event.num == 5 or event.delta < 0:  # scroll down
            self.zoom_level = max(0.1, self.zoom_level - self.zoom_step)
        elif event.num == 4 or event.delta > 0:  # scroll up
            self.zoom_level += self.zoom_step
        self.display_image(move_to_origin=False)

    def save_image(self):
        if self.merged_image:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                                     filetypes=[("PNG files", "*.png"), 
                                                                ("JPEG files", "*.jpg"), 
                                                                ("All files", "*.*")])
            if file_path:
                try:
                    self.merged_image.save(file_path)
                    messagebox.showinfo("Success", "Image saved successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save image: {e}")
        else:
            messagebox.showwarning("Warning", "No merged image to save")

    def deinterlace_image(self):
        if self.merged_image:
            output_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                       filetypes=[("PNG files", "*.png"),
                                                                  ("JPEG files", "*.jpg"),
                                                                  ("All files", "*.*")])
            if not output_path:
                return

            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_input_file:
                    temp_input_path = temp_input_file.name
                    self.merged_image.save(temp_input_path)

                def run_ffmpeg():
                    try:
                        ffmpeg_command = [
                            "ffmpeg",
                            "-y",
                            "-i", temp_input_path,
                            "-vf", "yadif",
                            output_path
                        ]
                        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        stdout, stderr = process.communicate()

                        if process.returncode != 0:
                            self.show_error(f"Failed to deinterlace image: {stderr}")
                        else:
                            self.show_info("Success", "Image deinterlaced and saved successfully")
                    except Exception as e:
                        self.show_error(f"Failed to deinterlace image: {e}")
                    finally:
                        os.remove(temp_input_path)

                threading.Thread(target=run_ffmpeg).start()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to deinterlace image: {e}")
        else:
            messagebox.showwarning("Warning", "No merged image to deinterlace")

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def show_error(self, message):
        messagebox.showerror("Error", message)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FieldMerger(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {e}")
