# This is a simple image compressor app that allows you to compress images to a desired quality.
# pip install customtkinter Pillow

import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import os


class ImageCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Image Compressor")
        self.geometry("1000x600")

        # Initialize variables
        self.original_image = None
        self.compressed_image = None
        self.original_size = 0
        self.compressed_size = 0

        # Create main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create frames
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Original image frame
        self.original_label = ctk.CTkLabel(self.left_frame, text="Original Image")
        self.original_label.pack(pady=5)

        self.original_image_label = ctk.CTkLabel(
            self.left_frame, text="No image selected"
        )
        self.original_image_label.pack(pady=10)

        # Compressed image frame
        self.compressed_label = ctk.CTkLabel(
            self.right_frame, text="Compressed Preview"
        )
        self.compressed_label.pack(pady=5)

        self.compressed_image_label = ctk.CTkLabel(
            self.right_frame, text="Compression preview will appear here"
        )
        self.compressed_image_label.pack(pady=10)

        # Controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(
            row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew"
        )

        # Select image button
        self.select_button = ctk.CTkButton(
            self.controls_frame, text="Select Image", command=self.select_image
        )
        self.select_button.pack(pady=10)

        # Quality slider
        self.quality_label = ctk.CTkLabel(
            self.controls_frame, text="Compression Quality: 85%"
        )
        self.quality_label.pack(pady=5)

        self.quality_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self.update_quality,
        )
        self.quality_slider.set(85)
        self.quality_slider.pack(pady=5)

        # Size info
        self.size_label = ctk.CTkLabel(
            self.controls_frame, text="Original Size: -- | Compressed Size: --"
        )
        self.size_label.pack(pady=5)

        # Save button
        self.save_button = ctk.CTkButton(
            self.controls_frame,
            text="Save Compressed Image",
            command=self.save_image,
            state="disabled",
        )
        self.save_button.pack(pady=10)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")]
        )

        if file_path:
            # Load and display original image
            self.original_image = Image.open(file_path)
            self.original_size = os.path.getsize(file_path)

            # Resize image for display
            display_size = (400, 400)
            display_image = self.resize_image_aspect_ratio(
                self.original_image, display_size
            )

            # Use CTkImage instead of ImageTk.PhotoImage
            photo = ctk.CTkImage(
                light_image=display_image,
                dark_image=display_image,
                size=display_image.size,
            )
            self.original_image_label.configure(image=photo)
            self.original_image_label.image = photo

            # Update compression preview
            self.update_quality(self.quality_slider.get())
            self.save_button.configure(state="normal")

    def update_quality(self, value):
        if self.original_image:
            quality = int(value)
            self.quality_label.configure(text=f"Compression Quality: {quality}%")

            # Create compressed version
            temp_path = "temp_compressed.jpg"
            if self.original_image.mode == "RGBA":
                self.original_image = self.original_image.convert(
                    "RGB"
                )  # Convert to RGB
            self.original_image.save(temp_path, "JPEG", quality=quality)
            self.compressed_size = os.path.getsize(temp_path)

            # Load and display compressed preview
            self.compressed_image = Image.open(temp_path)
            display_size = (400, 400)
            display_image = self.resize_image_aspect_ratio(
                self.compressed_image, display_size
            )

            # Use CTkImage instead of ImageTk.PhotoImage
            photo = ctk.CTkImage(
                light_image=display_image,
                dark_image=display_image,
                size=display_image.size,
            )
            self.compressed_image_label.configure(image=photo)
            self.compressed_image_label.image = photo

            # Update size information
            original_mb = self.original_size / (1024 * 1024)
            compressed_mb = self.compressed_size / (1024 * 1024)
            reduction = (
                (self.original_size - self.compressed_size) / self.original_size
            ) * 100

            size_text = f"Original: {original_mb:.2f}MB | Compressed: {compressed_mb:.2f}MB | Reduction: {reduction:.1f}%"
            self.size_label.configure(text=size_text)

            # Clean up temp file
            os.remove(temp_path)

    def save_image(self):
        if self.original_image:
            quality = int(self.quality_slider.get())
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg")]
            )

            if file_path:
                self.original_image.save(file_path, "JPEG", quality=quality)

    def resize_image_aspect_ratio(self, image, target_size):
        original_width, original_height = image.size
        target_width, target_height = target_size

        # Calculate aspect ratio
        aspect_ratio = original_width / original_height

        if original_width > original_height:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    app = ImageCompressorApp()
    app.mainloop()
