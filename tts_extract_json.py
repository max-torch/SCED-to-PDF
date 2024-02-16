import argparse
import json
import logging
import os
import sys
import tkinter as tk
from tkinter import filedialog, BooleanVar
import webbrowser

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageFilter
import requests
from urllib.request import urlopen


# Define preset page and card sizes in pixels at 300dpi
SHEET_SIZES = {
    "A4": (2480, 3508),
    "Letter": (2550, 3300),
    "Legal": (2550, 4200),
}
CARD_SIZES = {"standard": (734, 1045), "mini": (500, 734)}

# Define common card back urls
COMMON_ENCOUNTER_BACK_URL = "https://i.imgur.com/sRsWiSG.jpg/"
COMMON_PLAYER_BACK_URL = "https://i.imgur.com/EcbhVuh.jpg/"


def parse_args():
    # Create a new tkinter window
    window = tk.Tk()
    window.title("TTS Extract JSON")

    # Create variables to store the input values
    filepath = tk.StringVar()
    cachepath = tk.StringVar()
    verbose = BooleanVar(value=True)
    back = BooleanVar()
    card_quantity_source = tk.StringVar(value="arkhamdb")
    image_size = tk.StringVar(value="standard")
    custom_image_size = [tk.IntVar(), tk.IntVar()]
    sheet_size = tk.StringVar(value="Letter")
    margin_size = tk.IntVar(value=30)
    dpi = tk.IntVar(value=300)
    exclude_player_card_backs = BooleanVar()
    exclude_encounter_card_backs = BooleanVar()
    sharpen_text = BooleanVar()  # Checkbox for sharpening text

    # Read the cache path from cachepath.txt if it exists
    if os.path.exists("cachepath.txt"):
        with open("cachepath.txt", "r") as f:
            cachepath.set(f.read().strip())

    # Create a button to select the file
    def select_file():
        filepath.set(filedialog.askopenfilename())

    select_file_button = tk.Button(
        window, text="Select TTS Object file", command=select_file
    )
    select_file_button.pack(pady=10, padx=10, anchor='w')

    # Create a button to select the cache folder of tabletop simulator
    def select_cache_folder():
        cachepath.set(filedialog.askdirectory())
        with open("cachepath.txt", "w") as f:
            f.write(cachepath.get())

    select_cache_folder_button = tk.Button(
        window, text="Select TTS mod images cache folder", command=select_cache_folder
    )
    select_cache_folder_button.pack(pady=10, padx=10, anchor='w')

    # Add a separator
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Add a label
    label = tk.Label(window, text="Select Card Quantity Source:")
    label.pack(pady=5, padx=5, anchor='w')

    # Create radio buttons for the card quantity source
    arkhamdb_radio = tk.Radiobutton(
        window, text="ArkhamDB", variable=card_quantity_source, value="arkhamdb"
    )
    arkhamdb_radio.pack(pady=5, padx=5, anchor='w')
    tts_object_radio = tk.Radiobutton(
        window,
        text="TTS Saved Object",
        variable=card_quantity_source,
        value="tts_saved_object",
    )
    tts_object_radio.pack(pady=5, padx=5, anchor='w')

    # Add a separator between the radio groups
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Add a label
    label = tk.Label(window, text="Select Preset Card Size:")
    label.pack(pady=5, padx=5, anchor='w')

    # Create radio buttons for the image size
    standard_radio = tk.Radiobutton(
        window, text="Standard", variable=image_size, value="standard"
    )
    standard_radio.pack(pady=5, padx=5, anchor='w')
    mini_radio = tk.Radiobutton(window, text="Mini", variable=image_size, value="mini")
    mini_radio.pack(pady=5, padx=5, anchor='w')

    # Add a separator
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Create entry fields for the custom image size
    custom_size_frame = tk.Frame(window)
    custom_size_frame.pack(pady=5, padx=5, anchor='w')

    custom_size_label = tk.Label(custom_size_frame, text="Custom Card Size:")
    custom_size_label.pack(side=tk.TOP, anchor='w')

    custom_size_width_frame = tk.Frame(custom_size_frame)
    custom_size_width_frame.pack(side=tk.TOP, anchor='w')
    custom_size_width_label = tk.Label(custom_size_width_frame, text="Width:")
    custom_size_width_label.pack(side=tk.LEFT, anchor='w')
    custom_size_width_entry = tk.Entry(
        custom_size_width_frame, textvariable=custom_image_size[0]
    )
    custom_size_width_entry.pack(side=tk.LEFT, anchor='w')

    custom_size_length_frame = tk.Frame(custom_size_frame)
    custom_size_length_frame.pack(side=tk.TOP, anchor='w')
    custom_size_length_label = tk.Label(custom_size_length_frame, text="Length:")
    custom_size_length_label.pack(side=tk.LEFT, anchor='w')
    custom_size_length_entry = tk.Entry(
        custom_size_length_frame, textvariable=custom_image_size[1]
    )
    custom_size_length_entry.pack(side=tk.LEFT, anchor='w')

    # Add a separator
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Add a label
    label = tk.Label(window, text="Select Sheet Size:")
    label.pack(pady=5, padx=5, anchor='w')

    # Create radio buttons for the sheet size
    a4_radio = tk.Radiobutton(window, text="A4", variable=sheet_size, value="A4")
    a4_radio.pack(pady=5, padx=5, anchor='w')
    letter_radio = tk.Radiobutton(
        window, text="Letter", variable=sheet_size, value="Letter"
    )
    letter_radio.pack(pady=5, padx=5, anchor='w')
    legal_radio = tk.Radiobutton(
        window, text="Legal", variable=sheet_size, value="Legal"
    )
    legal_radio.pack(pady=5, padx=5, anchor='w')

    # Add a separator
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Create entry fields for the margin size and dpi
    margin_size_frame = tk.Frame(window)
    margin_size_frame.pack(pady=5, padx=5, anchor='w')

    margin_size_label = tk.Label(margin_size_frame, text="Margin Size:")
    margin_size_label.pack(side=tk.LEFT, anchor='w')
    margin_size_entry = tk.Entry(margin_size_frame, textvariable=margin_size)
    margin_size_entry.pack(side=tk.LEFT, anchor='w')

    dpi_frame = tk.Frame(window)
    dpi_frame.pack(pady=5, padx=5, anchor='w')

    dpi_label = tk.Label(dpi_frame, text="DPI:")
    dpi_label.pack(side=tk.LEFT, anchor='w')
    dpi_entry = tk.Entry(dpi_frame, textvariable=dpi)
    dpi_entry.pack(side=tk.LEFT, anchor='w')

    # Add a separator
    separator = tk.Frame(window, height=2, bd=1, relief=tk.SUNKEN)
    separator.pack(fill=tk.X, padx=5, pady=5)

    # Create checkboxes for the boolean options
    verbose_checkbox = tk.Checkbutton(window, text="Verbose", variable=verbose)
    verbose_checkbox.pack(pady=5, padx=5, anchor='w')

    back_checkbox = tk.Checkbutton(window, text="Back card extraction", variable=back)
    back_checkbox.pack(pady=5, padx=5, anchor='w')

    exclude_player_card_backs_checkbox = tk.Checkbutton(
        window,
        text="Exclude common player card backs",
        variable=exclude_player_card_backs,
    )
    exclude_player_card_backs_checkbox.pack(pady=5, padx=5, anchor='w')

    exclude_encounter_card_backs_checkbox = tk.Checkbutton(
        window,
        text="Exclude common encounter card backs",
        variable=exclude_encounter_card_backs,
    )
    exclude_encounter_card_backs_checkbox.pack(pady=5, padx=5, anchor='w')

    sharpen_text_checkbox = tk.Checkbutton(  # Checkbox for sharpening text
        window,
        text="Sharpen Text (Experimental)",
        variable=sharpen_text,
    )
    sharpen_text_checkbox.pack(pady=5, padx=5, anchor='w')

    # Create a button to start the script
    args = argparse.Namespace()

    def start_script():
        args.filepath = filepath.get()
        args.cachepath = cachepath.get()
        args.verbose = verbose.get()
        args.back = back.get()
        args.card_quantity_source = card_quantity_source.get()

        # Initialize custom_image_size to None
        args.custom_image_size = None

        # Check if custom image size is provided
        if custom_size_width_entry.get() and custom_size_length_entry.get():
            custom_size_width = custom_size_width_entry.get()
            custom_size_length = custom_size_length_entry.get()
            if custom_size_width != "0" and custom_size_length != "0":
                args.custom_image_size = (custom_size_width, custom_size_length)

        # Use presets if custom image size is not provided
        args.image_size = image_size.get()

        args.sheet_size = sheet_size.get()
        args.margin_size = margin_size.get()
        args.dpi = dpi.get()
        args.exclude_player_card_backs = exclude_player_card_backs.get()
        args.exclude_encounter_card_backs = exclude_encounter_card_backs.get()
        args.sharpen_text = sharpen_text.get()  # Store the value of sharpen_text

        window.quit()

    start_button = tk.Button(window, text="Start script", command=start_script)
    start_button.pack(pady=10, padx=10, anchor='w')

    # Handle the window close event
    def on_close():
        window.quit()
        sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_close)

    # Start the tkinter main loop
    window.mainloop()

    # Return the arguments
    return args


def build_dict(obj, result):
    # If the object is a dictionary
    if isinstance(obj, dict):
        # If the dictionary has 'Nickname', 'CardID', and 'CustomDeck' keys, add an entry to the result
        if obj.get("Nickname") != "" and "CardID" in obj and "CustomDeck" in obj:
            arkhamdb_id = None
            if "GMNotes" in obj:
                try:
                    gmnotes = json.loads(obj["GMNotes"]) if "GMNotes" in obj else None
                    arkhamdb_id = gmnotes["id"] if gmnotes else None
                except json.decoder.JSONDecodeError:
                    logging.warning(f"JSON decode error for the following object: {obj}")
                    arkhamdb_id = None
            obj_key = arkhamdb_id if arkhamdb_id else obj["Nickname"]
            # If the nickname is not yet in the result, add it with a new dictionary as value
            if obj_key not in result:
                result[obj_key] = {
                    "CardID": obj["CardID"],
                    "CustomDeck": obj["CustomDeck"],
                    "quantity": 1,
                    "Nickname": obj["Nickname"],
                    "GMNotes": obj["GMNotes"] if "GMNotes" in obj else None,
                    "arkhamdb_id": arkhamdb_id,
                }
            else:
                # If the nickname is already in the result, increment the quantity
                result[obj_key]["quantity"] += 1
        # Recursively search the dictionary's values
        for value in obj.values():
            build_dict(value, result)
    # If the object is a list
    elif isinstance(obj, list):
        # Recursively search the list's items
        for item in obj:
            build_dict(item, result)


def extract_sced_card(
    url,
    card_index,
    num_width,
    num_height,
    unique_back=False,
    cache_folder="cache",
):
    def format_url(url_string):
        for char in [
            ":",
            "/",
            ".",
            "-",
        ]:
            url_string = url_string.replace(char, "")
        return url_string

    # Check if the image file is saved locally in the cache folder
    cache_file_name = format_url(url)
    cache_file_path_png = os.path.join(cache_folder, cache_file_name + ".png")
    cache_file_path_jpg = os.path.join(cache_folder, cache_file_name + ".jpg")

    if os.path.exists(cache_file_path_png):
        # Open the PNG image file
        img = Image.open(cache_file_path_png)
    elif os.path.exists(cache_file_path_jpg):
        # Open the JPG image file
        img = Image.open(cache_file_path_jpg)
    else:
        # Open the image file
        img = Image.open(urlopen(url))

        # Save the image file to the cache folder
        os.makedirs(cache_folder, exist_ok=True)
        img.save(cache_file_path_png, "PNG")
        logging.info(f"Saved PNG image to cache: {cache_file_path_png}")

    # If unique_back is False, return the entire image without cropping
    if not unique_back:
        return img

    # Calculate the size of the card using the number of cards in the x and y directions
    card_size = (img.width // num_width, img.height // num_height)

    # Calculate the bounding box of the card
    y_coordinate = card_index // num_width
    x_coordinate = card_index % num_width

    left = x_coordinate * card_size[0]
    upper = y_coordinate * card_size[1]
    right = left + card_size[0]
    lower = upper + card_size[1]
    bbox = (left, upper, right, lower)

    # Crop out the card
    card = img.crop(bbox)

    return card


def extract_images(args):
    if args.card_quantity_source == "arkhamdb":
        all_cards_data = json.load(open('cards.json', "r"))
    
    # Load the JSON data
    data = json.load(open(args.filepath, "r"))

    # Build the dictionary
    result = {}
    build_dict(data, result)

    # Create a dictionary to store the extracted images
    images = {}

    # For each item in the dictionary, use extract_sced_card to extract the face and back cards
    for each in result.values():
        # Get the only key in the CustomDeck dictionary
        custom_deck_key = list(each["CustomDeck"])[0]

        # Extract the face card
        face_card = extract_sced_card(
            each["CustomDeck"][custom_deck_key]["FaceURL"],
            int(str(each["CardID"])[-2:]),
            int(each["CustomDeck"][custom_deck_key]["NumWidth"]),
            int(each["CustomDeck"][custom_deck_key]["NumHeight"]),
            True,
            args.cachepath,
        ).convert("RGBA")

        if args.back:
            # Extract the back card
            back_card = extract_sced_card(
                each["CustomDeck"][custom_deck_key]["BackURL"],
                int(str(each["CardID"])[-2:]),
                int(each["CustomDeck"][custom_deck_key]["NumWidth"]),
                int(each["CustomDeck"][custom_deck_key]["NumHeight"]),
                each["CustomDeck"][custom_deck_key]["UniqueBack"],
                args.cachepath,
            ).convert("RGBA")

        try:
            gmnotes = json.loads(each["GMNotes"])
            arkhamdb_id = gmnotes["id"] if gmnotes else None
        except json.decoder.JSONDecodeError:
            logging.warning(f"JSON decode error for the following object: {each}")
            arkhamdb_id = None

        if args.card_quantity_source == "arkhamdb":
            # Using arkhamdb_id, get the quantity of the card using the ArkhamDB API
            if arkhamdb_id:
                card_data = next(
                    (item for item in all_cards_data if item["code"] == arkhamdb_id), None
                )
                quantity = card_data["quantity"] if "quantity" in card_data else 1
                pack_code = card_data["pack_code"] if "pack_code" in card_data else None
            else:
                quantity = 1
                pack_code = None

            for i in range(quantity):
                images[f"{arkhamdb_id}_{i}"] = face_card
                logging.info(f"Added face card from the {pack_code} pack for {each['Nickname']}")
                if args.back:
                    # Check if the card has a common back based on the url
                    if args.exclude_encounter_card_backs:
                        if (
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_ENCOUNTER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_ENCOUNTER_BACK_URL[:-1] or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_ENCOUNTER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_ENCOUNTER_BACK_URL[:-1]
                        ):
                            continue

                    if args.exclude_player_card_backs:
                        if (
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_PLAYER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_PLAYER_BACK_URL[:-1] or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_PLAYER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_PLAYER_BACK_URL[:-1]
                        ):
                            continue
                    images[f"{arkhamdb_id}_{i}_back"] = back_card
                    logging.info(f"Added back card from the {pack_code} pack for {each['Nickname']}")
        elif args.card_quantity_source == "tts_saved_object":
            quantity = each["quantity"]
            for i in range(quantity):
                images[f"{each['Nickname']}_{i}"] = face_card
                logging.info(f"Added face card for {each['Nickname']}")
                if args.back:
                    # Check if the card has a common back based on the url
                    if args.exclude_encounter_card_backs:
                        if (
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_ENCOUNTER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_ENCOUNTER_BACK_URL[:-1] or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_ENCOUNTER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_ENCOUNTER_BACK_URL[:-1]
                        ):
                            continue

                    if args.exclude_player_card_backs:
                        if (
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_PLAYER_BACK_URL or 
                            each["CustomDeck"][custom_deck_key]["BackURL"]
                            == COMMON_PLAYER_BACK_URL[:-1] or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_PLAYER_BACK_URL or
                            each["CustomDeck"][custom_deck_key]["FaceURL"]
                            == COMMON_PLAYER_BACK_URL[:-1]
                        ):
                            continue
                    images[f"{each['Nickname']}_{i}_back"] = back_card
                    logging.info(f"Added back card for {each['Nickname']}")

    return images


def arrange_images(images, args):
    def convert_size_to_new_dpi(size, old_dpi, new_dpi):
        ratio = new_dpi / old_dpi
        return (int(size[0] * ratio), int(size[1] * ratio))
    
    dpi = args.dpi
    converted_card_sizes = {key: convert_size_to_new_dpi(value, 300, dpi) for key, value in CARD_SIZES.items()}
    converted_sheet_sizes = {key: convert_size_to_new_dpi(value, 300, dpi) for key, value in SHEET_SIZES.items()}

    # Define the size of the images and the page (in pixels)
    if args.custom_image_size:
        image_size = tuple(int(x) for x in args.custom_image_size)
    elif args.image_size:
        image_size = converted_card_sizes[args.image_size]
    else:
        image_size = converted_card_sizes["standard"]

    page_size = converted_sheet_sizes[args.sheet_size]
    margin_size = int(args.margin_size)

    # Calculate new width of first image based on the new height while maintaining aspect ratio
    first_image = list(images.values())[0]
    width, height = first_image.size
    new_height = image_size[1]
    new_width = int((new_height / height) * width)

    # Use the actual new width of the first image for calculations
    image_size = (new_width, image_size[1])

    # Calculate how many images fit on a page, considering the margin
    images_per_row = (page_size[0] - margin_size) // (image_size[0] + margin_size)
    images_per_column = (page_size[1] - margin_size) // (image_size[1] + margin_size)
    images_per_page = images_per_row * images_per_column

    # Calculate the total width and height of the images group
    total_width = images_per_row * (image_size[0] + margin_size) - margin_size
    total_height = images_per_column * (image_size[1] + margin_size) - margin_size

    # Calculate the starting position to center the group on the page
    start_x = (page_size[0] - total_width) // 2
    start_y = (page_size[1] - total_height) // 2

    # Create a new blank page with white background
    current_page = Image.new("RGB", page_size, (255, 255, 255))

    # Keep track of the current position on the page
    current_position = [start_x, start_y]

    # Keep track of the number of images on the current page
    image_count = 0

    # Create a list to store the pages
    pages = []

    for key in sorted(images.keys()):
        extracted_image = images[key]

        # Resize the image based on height while maintaining aspect ratio
        width, height = extracted_image.size
        new_height = image_size[1]
        new_width = int((new_height / height) * width)
        extracted_image = extracted_image.resize((new_width, new_height), Image.LANCZOS)

        if args.sharpen_text:  # Sharpen the image if the checkbox is checked

            # Convert PIL Image to OpenCV format
            extracted_image_cv = np.array(extracted_image)

            # Convert the image to grayscale
            gray = cv2.cvtColor(extracted_image_cv, cv2.COLOR_BGR2GRAY)

            # Use Tesseract to detect text regions
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["level"])
            mask = np.zeros_like(extracted_image_cv)
            for i in range(n_boxes):
                (x, y, w, h) = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                mask[y : y + h, x : x + w] = 1

            # Sharpen the entire image
            blurred = cv2.GaussianBlur(extracted_image_cv, (3, 3), 0)
            sharpened = cv2.addWeighted(extracted_image_cv, 2.0, blurred, -1.0, 0)

            # Apply sharpening to only the text regions
            extracted_image_cv = extracted_image_cv * (1 - mask) + sharpened * mask

            # Convert the image back to PIL Image format
            extracted_image = Image.fromarray(extracted_image_cv)

        # Paste the image onto the current page
        current_page.paste(
            extracted_image, tuple(current_position), mask=extracted_image
        )

        # Update the image count
        image_count += 1

        # Update the current position
        current_position[0] += image_size[0] + margin_size
        if current_position[0] >= start_x + total_width:
            current_position[0] = start_x
            current_position[1] += image_size[1] + margin_size

        # If the current page is full or there are no more images, add it to the list of pages
        if (
            image_count != 0
            and image_count % images_per_page == 0
            and image_count != len(images)
        ):
            current_page.info["dpi"] = (dpi, dpi)
            pages.append(current_page)
            logging.info(f"Created page {len(pages)}")

            # Reset the current page and position for the next page
            current_page = Image.new("RGB", page_size, "white")
            current_position = [start_x, start_y]

    # # Save the last page if it's not empty or if it is full
    if image_count % images_per_page != 0 or image_count == len(images):
        current_page.info["dpi"] = (dpi, dpi)
        pages.append(current_page)
        logging.info(f"Created page {len(pages)}")

    # Save all pages into a single PDF file
    pages[0].save(
        "tts_extract_out.pdf",
        "PDF",
        resolution=dpi,
        save_all=True,
        append_images=pages[1:],
    )

    logging.info("PDF file created")


def main():
    # Parse the arguments
    args = parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Extract the images
    logging.info("Extracting images...")
    images = extract_images(args)
    logging.info("Successfully extracted images")

    # Write a csv containing the keys of the images dictionary
    with open("tts_extract_out_manifest.csv", "w") as f:
        f.write("image_id\n")
        for key in images.keys():
            f.write(f"{key}\n")

    # Arrange the images into a single pdf
    arrange_images(images, args)

    # Open the pdf file
    webbrowser.open("tts_extract_out.pdf")


if __name__ == "__main__":
    main()
