# cspell:ignore Exif GPSTAGS exifread Pixbuf titlebar pixbuf scrollbars
# cspell:ignore jpegtran cropspec cairo keyval exif exiftool

import gi
import argparse
import os
import sys
import math
import subprocess

from crop_gui_neu.jpeg_info import get_image_attributes

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib  # noqa: E402


def dict_to_string_aligned(dictionary, column_width=16):
    """Formats a dictionary into a string with aligned columns.

    Args:
        attributes (dict): The dictionary to format.
        column_width (int, optional): The desired column width. Defaults to 16.

    Returns:
        str: The formatted string.
    """

    lines = (
        f"{key}: {' ' * (column_width - len(key))} {value}"
        for key, value in dictionary.items()
    )
    return "\n".join(lines)


class CropJpegApp(Gtk.Window):
    def __init__(self, image_path=None):
        super().__init__(title="Crop GUI Neu")
        self.set_position(Gtk.WindowPosition.CENTER)

        # Apply event mask to the window to capture key press events
        self.set_events(Gdk.EventMask.KEY_PRESS_MASK)

        # Connect key press event to the window
        self.connect("key-press-event", self.on_key_press)

        # Set minimal initial window size
        self.set_default_size(800, 600)

        # Header bar setup
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.set_title("Crop GUI Neu")
        self.set_titlebar(self.header_bar)

        # Load Image Button
        self.load_button = Gtk.Button()
        self.load_button.set_image(
            Gtk.Image.new_from_icon_name(
                "document-open-symbolic", Gtk.IconSize.BUTTON
            )
        )
        self.load_button.set_tooltip_text("Load Image")
        self.load_button.connect("clicked", self.on_file_selected)
        self.header_bar.pack_start(self.load_button)

        # Save Image Button
        self.save_button = Gtk.Button()
        self.save_button.set_image(
            Gtk.Image.new_from_icon_name(
                "document-save-symbolic", Gtk.IconSize.BUTTON
            )
        )
        self.save_button.set_tooltip_text("Save Cropped Image")
        self.save_button.connect("clicked", self.on_crop_clicked)
        self.save_button.set_sensitive(False)
        self.header_bar.pack_end(self.save_button)

        # Show Info Button
        # self.info_button = Gtk.Button(label="Show Info")
        self.info_button = Gtk.Button()
        self.info_button.set_image(
            Gtk.Image.new_from_icon_name(
                "document-page-setup-symbolic", Gtk.IconSize.BUTTON
            )
        )
        self.info_button.set_tooltip_text("Show Image Info")
        self.info_button.connect("clicked", self.show_image_info)
        self.info_button.set_sensitive(False)
        self.header_bar.pack_start(self.info_button)

        # Scrollable window setup
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )

        # Image drawing area
        self.image = Gtk.DrawingArea()
        self.image.connect("draw", self.on_draw)
        self.image.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )

        self.image.connect("button-press-event", self.on_button_press)
        self.image.connect("motion-notify-event", self.on_mouse_move)
        self.image.connect("button-release-event", self.on_button_release)

        self.scrolled_window.add(self.image)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.pack_start(self.scrolled_window, True, True, 0)
        self.add(vbox)

        self.image_surface = None
        self.crop_coords = None
        self.dragging = False
        self.resizing = False
        self.active_handle = None
        self.jpeg_block_size = (
            8  # Default block size for JPEG images (usually 8x8)
        )
        self.handle_size = 10  # Size of the corner handles
        self.image_path = image_path

        # If an image path is provided via argparse, load it
        if image_path:
            self.load_image(image_path)

    def load_image(self, image_path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            self.image_surface = Gdk.cairo_surface_create_from_pixbuf(
                pixbuf, 1
            )
            self.image.set_size_request(
                pixbuf.get_width(), pixbuf.get_height()
            )
            self.info_button.set_sensitive(True)
            self.save_button.set_sensitive(True)
            self.crop_coords = None
            self.image.queue_draw()  # Redraw the image with the new surface

            # Update the header bar title with the file name
            self.header_bar.set_title(
                os.path.basename(image_path) + " — Crop GUI Neu"
            )

            # Adjust window size to image, with scrollbars if necessary
            screen = Gdk.Screen.get_default()
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            self.set_default_size(
                min(pixbuf.get_width(), screen_width),
                min(pixbuf.get_height(), screen_height),
            )
        except Exception as e:
            print(f"Failed to load image: {e}")

    def on_file_selected(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select a JPEG file",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        # Set up file chooser to only show JPG/JPEG files
        filter_jpeg = Gtk.FileFilter()
        filter_jpeg.set_name("JPEG files")
        filter_jpeg.add_mime_type("image/jpeg")
        filter_jpeg.add_pattern("*.jpg")
        filter_jpeg.add_pattern("*.jpeg")
        dialog.add_filter(filter_jpeg)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.image_path = dialog.get_filename()
            self.load_image(self.image_path)
        dialog.destroy()

    def on_draw(self, widget, cr):
        if not self.image_surface:
            return

        # Draw the image
        cr.set_source_surface(self.image_surface, 0, 0)
        cr.paint()

        if self.crop_coords:
            x1, y1, x2, y2 = self.crop_coords

            # Darken the outer area
            cr.set_source_rgba(0, 0, 0, 0.25)
            cr.rectangle(0, 0, self.image_surface.get_width(), y1)  # Top
            cr.rectangle(0, y1, x1, y2 - y1)  # Left
            cr.rectangle(
                x2, y1, self.image_surface.get_width() - x2, y2 - y1
            )  # Right
            cr.rectangle(
                0,
                y2,
                self.image_surface.get_width(),
                self.image_surface.get_height() - y2,
            )  # Bottom
            cr.fill()

            # Draw crop area outline with black and white lines

            # Draw black outline with 50% opacity
            cr.set_source_rgba(0, 0, 0, 0.25)
            cr.set_line_width(3)
            cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.stroke()

            # Draw white line on top
            cr.set_source_rgba(1, 1, 1, 1)
            cr.set_line_width(1)
            cr.rectangle(x1, y1, x2 - x1, y2 - y1)
            cr.stroke()

            # Draw handles as triangles at the corners
            self._draw_handle(cr, x1, y1, "top-left")
            self._draw_handle(cr, x2, y1, "top-right")
            self._draw_handle(cr, x1, y2, "bottom-left")
            self._draw_handle(cr, x2, y2, "bottom-right")

    def _draw_handle(self, cr, x, y, position):
        # Create a path for a triangle pointing to the corner
        cr.set_source_rgba(1, 1, 1, 1)  # White color for handles
        cr.new_path()

        if position == "top-left":
            cr.move_to(x - self.handle_size, y)
            cr.line_to(x, y - self.handle_size)
            cr.line_to(x, y)
        elif position == "top-right":
            cr.move_to(x + self.handle_size, y)
            cr.line_to(x, y - self.handle_size)
            cr.line_to(x, y)
        elif position == "bottom-left":
            cr.move_to(x - self.handle_size, y)
            cr.line_to(x, y + self.handle_size)
            cr.line_to(x, y)
        elif position == "bottom-right":
            cr.move_to(x + self.handle_size, y)
            cr.line_to(x, y + self.handle_size)
            cr.line_to(x, y)
        cr.close_path()
        cr.fill()

    def _get_active_handle(self, x, y):
        x1, y1, x2, y2 = self.crop_coords
        if self._is_within_handle(x, y, x1, y1, "top-left"):
            return "top-left"
        elif self._is_within_handle(x, y, x2, y1, "top-right"):
            return "top-right"
        elif self._is_within_handle(x, y, x1, y2, "bottom-left"):
            return "bottom-left"
        elif self._is_within_handle(x, y, x2, y2, "bottom-right"):
            return "bottom-right"
        return None

    def _is_within_handle(self, x, y, handle_x, handle_y, position):
        # Adjust sensitivity area around the handle point
        sensitivity = 10
        if position == "top-left":
            return (
                handle_x - sensitivity <= x <= handle_x
                and handle_y - sensitivity <= y <= handle_y
            )
        elif position == "top-right":
            return (
                handle_x <= x <= handle_x + sensitivity
                and handle_y - sensitivity <= y <= handle_y
            )
        elif position == "bottom-left":
            return (
                handle_x - sensitivity <= x <= handle_x
                and handle_y <= y <= handle_y + sensitivity
            )
        elif position == "bottom-right":
            return (
                handle_x <= x <= handle_x + sensitivity
                and handle_y <= y <= handle_y + sensitivity
            )
        return False

    def on_button_press(self, widget, event):
        if not self.image_surface:
            return

        if event.button == 1:  # Left mouse button
            if self.crop_coords:
                self.active_handle = self._get_active_handle(
                    int(event.x), int(event.y)
                )
                if self.active_handle:
                    self.resizing = True
                    return

            self.dragging = True
            self.crop_coords = (
                self._snap_to_block(int(event.x)),
                self._snap_to_block(int(event.y)),
                self._snap_to_block(int(event.x)),
                self._snap_to_block(int(event.y)),
            )
            self.image.queue_draw()

    def on_mouse_move(self, widget, event):
        if not self.image_surface:
            return

        if self.resizing:
            x1, y1, x2, y2 = self.crop_coords
            if self.active_handle == "top-left":
                x1, y1 = self._snap_to_block(
                    max(0, int(event.x))
                ), self._snap_to_block(max(0, int(event.y)))
            elif self.active_handle == "top-right":
                x2, y1 = self._snap_to_block(
                    min(self.image_surface.get_width(), int(event.x))
                ), self._snap_to_block(max(0, int(event.y)))
            elif self.active_handle == "bottom-left":
                x1, y2 = self._snap_to_block(
                    max(0, int(event.x))
                ), self._snap_to_block(
                    min(self.image_surface.get_height(), int(event.y))
                )
            elif self.active_handle == "bottom-right":
                x2, y2 = self._snap_to_block(
                    min(self.image_surface.get_width(), int(event.x))
                ), self._snap_to_block(
                    min(self.image_surface.get_height(), int(event.y))
                )
            self.crop_coords = (x1, y1, x2, y2)
            self.image.queue_draw()

        elif self.dragging and self.crop_coords:
            x1, y1, _, _ = self.crop_coords
            self.crop_coords = (
                x1,
                y1,
                self._snap_to_block(
                    min(self.image_surface.get_width(), int(event.x))
                ),
                self._snap_to_block(
                    min(self.image_surface.get_height(), int(event.y))
                ),
            )
            self.image.queue_draw()

    def on_button_release(self, widget, event):
        if not self.image_surface:
            return

        if event.button == 1:
            self.dragging = False
            self.resizing = False
            x1, y1, x2, y2 = self.crop_coords
            if x2 < x1:  # Ensure proper coordinates if dragged backwards
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            self.crop_coords = (x1, y1, x2, y2)
            self.image.queue_draw()

    def _snap_to_block(self, value):
        return math.floor(value / self.jpeg_block_size) * self.jpeg_block_size

    def get_cropspec(self):
        """Generate the cropspec string for jpegtran."""
        x1, y1, x2, y2 = self.crop_coords
        w = x2 - x1
        h = y2 - y1
        return f"{w}x{h}+{x1}+{y1}"

    def on_crop_clicked(self, widget):
        if self.crop_coords and self.image_path:
            try:
                # Generate the save path with the "_cropped" suffix
                save_path = self._generate_cropped_filename(self.image_path)

                # Get the crop specification string
                cropspec = self.get_cropspec()

                # Use jpegtran for lossless cropping
                command = [
                    "jpegtran",
                    "-copy",
                    "all",
                    "-crop",
                    cropspec,
                    "-outfile",
                    save_path,
                    self.image_path,
                ]

                subprocess.run(command, check=True)

                save_dialog = Gtk.FileChooserDialog(
                    "Save Cropped Image",
                    self,
                    Gtk.FileChooserAction.SAVE,
                    (
                        Gtk.STOCK_CANCEL,
                        Gtk.ResponseType.CANCEL,
                        Gtk.STOCK_SAVE,
                        Gtk.ResponseType.OK,
                    ),
                )
                save_dialog.set_current_name(os.path.basename(save_path))
                save_dialog.set_current_folder(os.path.dirname(save_path))
                response = save_dialog.run()
                if response == Gtk.ResponseType.OK:
                    final_save_path = save_dialog.get_filename()
                    os.rename(save_path, final_save_path)
                    print(f"Image saved to {final_save_path}")
                else:
                    os.remove(
                        save_path
                    )  # Clean up the temporary file if not saved
                save_dialog.destroy()
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while running jpegtran: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

    def _generate_cropped_filename(self, original_path):
        """Generate a filename with '_cropped' before the file extension."""
        base, ext = os.path.splitext(original_path)
        return f"{base}_cropped{ext}"

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.crop_coords = None  # Remove the current crop overlay
            self.image.queue_draw()  # Redraw the image without overlay
        elif (
            event.state & Gdk.ModifierType.CONTROL_MASK
            and event.keyval == Gdk.KEY_q
        ):
            Gtk.main_quit()

    def show_image_info(self, widget):
        if self.image_path:
            image_attributes = get_image_attributes(self.image_path)
            popover_message = "Image attributes:\n\n" + dict_to_string_aligned(
                image_attributes
            )

            # Add crop coordinates if they exist
            if self.crop_coords:
                x1, y1, x2, y2 = self.crop_coords
                crop_info = (
                    f"Crop coordinates:\n\n"
                    f"Left:   {x1} px\n"
                    f"Top:    {y1} px\n"
                    f"Right:  {x2} px\n"
                    f"Bottom: {y2} px"
                )
                popover_message = f"{popover_message}\n\n\n{crop_info}"

            # Show the information in a popover with monospace font
            self._show_info_popover(widget, popover_message)

    def _show_info_popover(self, widget, text):
        popover = Gtk.Popover.new(widget)
        # label = Gtk.Label(label=text)
        label = Gtk.Label()
        label.set_markup(f"<tt>{GLib.markup_escape_text(text)}</tt>")
        label.set_padding(10, 10)
        label.set_selectable(True)  # Allow text selection
        popover.add(label)
        popover.show_all()
        popover.popup()


def main():
    parser = argparse.ArgumentParser(
        description="Crop a JPEG image using a GUI."
    )
    parser.add_argument(
        "image", nargs="?", help="Path to the JPEG image to crop"
    )
    args = parser.parse_args()

    # Validate the input file
    if args.image:
        if not os.path.isfile(args.image):
            print(f"Error: File '{args.image}' does not exist.")
            sys.exit(1)
        if not args.image.lower().endswith((".jpg", ".jpeg")):
            print("Error: The file must be a JPEG image.")
            sys.exit(1)

    app = CropJpegApp(image_path=args.image)
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
