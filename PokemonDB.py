import os
from PIL import Image
import requests
from io import BytesIO
import re
import cv2 as cv
import numpy as np
import sys

# Downloading, resizing, preprocessing and augmenting Pokemon sprites from pokemondb.net by Mateusz Kolinski MateuszPKolinski@gmail.com
# Downloads only generation 3-6 Pokemon because the art is very similar, but can easily be upgraded to download them all

WIDTH_MAX = 4096
HEIGHT_MAX = 4096


def download_sprites():
    # Get URL and list all possible sprite combinations
    # Following lists are designed for crawling through this site's url's to get all sprites
    url = "https://pokemondb.net/sprites"
    type_strings = ["normal", "shiny"]
    main_string = "https://img.pokemondb.net/sprites/"
    extension_string = ".png"

    # Connect to the site and get a list of all Pokemon
    headers = {'Accept-Encoding': 'identity'}

    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP error: {e}")
        sys.exit(1)

    # Chespin is 6th generation. We don't want him or any Pokemon of higher gen than 5 so we cut them
    html_string = r.text.split("Chespin")[0]

    # Divide our html response by generation, because newer Pokemon weren't around in older generations

    generation5 = html_string.split("Generation 6")[0]
    generation4 = generation5.split("Generation 5")[0]
    generation3 = generation4.split("Generation 4")[0]
    generation2 = generation3.split("Generation 3")[0]
    generation1 = generation2.split("Generation 2")[0]

    # Find all Pokemon names with regex
    matches_gen1 = re.findall("<br> ([\w♀♂:'-. ]+)</a>", generation1)
    matches_gen2 = re.findall("<br> ([\w♀♂:'-. ]+)</a>", generation2)
    matches_gen3 = re.findall("<br> ([\w♀♂:'-. ]+)</a>", generation3)
    matches_gen4 = re.findall("<br> ([\w♀♂:'-. ]+)</a>", generation4)
    matches_gen5 = re.findall("<br> ([\w♀♂:'-. ]+)</a>", generation5)

    # Gen 5 has all the Pokemon we want
    matches = matches_gen5

    # A dictionary to replace pokemon names, because some Pokemon names have different URL names
    replacement_dictionary = {}
    replacement_dictionary["♀"] = "-f"
    replacement_dictionary["♂"] = "-m"
    replacement_dictionary[":"] = "-"
    replacement_dictionary[" "] = "-"
    replacement_dictionary["."] = ""
    replacement_dictionary["'"] = ""

    # Arceus has a special list because it has many forms
    arceus_list = ["normal", "bug", "dark", "dragon", "electric", "fighting", "fire", "flying", "ghost", "grass", "ground", "ice", "poison", "psychic", "rock", "steel", "water"]

    # Loop over all Pokemon
    i = 0
    sprite_urls = []
    for match in matches:
        # Loop over normal/shiny sprites
        for type_string in type_strings:
            # Loop over generations those Pokemon are available in
            if match in matches_gen5:
                game_strings = ["black-white"]
            if match in matches_gen4:
                game_strings = ["black-white", "heartgold-soulsilver", "platinum", "diamond-pearl"]
            if match in matches_gen3:
                game_strings = ["black-white", "heartgold-soulsilver", "platinum", "diamond-pearl", "emerald", "ruby-sapphire"]
            if match in matches_gen2:
                game_strings = ["black-white", "heartgold-soulsilver", "platinum", "diamond-pearl", "emerald", "ruby-sapphire"]
            if match in matches_gen1:
                game_strings = ["black-white", "heartgold-soulsilver", "platinum", "diamond-pearl", "emerald", "ruby-sapphire", "firered-leafgreen"]

            for game_string in game_strings:
                # Replace Pokemon names for url names
                for key, value in replacement_dictionary.items():
                    if key in match:
                        match = match.replace(key, value)

                # Special clause for Arceus
                if match == "Arceus":
                    # Loop over Arceus's types
                    for arceus_type in arceus_list:

                        # Create its name
                        match = "arceus-" + arceus_type
                        sprite_urls.append(main_string + game_string + "/" + type_string + "/" + match + extension_string)

                        # Save the sprite on our PC
                        save_sprite(sprite_urls[i], str(i+1) + match + ".png")
                        i = i + 1

                # Rest Pokemon
                else:
                    # Create URL name
                    sprite_urls.append(main_string + game_string + "/" + type_string + "/" + match + extension_string)

                    # Save the sprite on our PC
                    save_sprite(sprite_urls[i], str(i+1) + match + ".png")

                    i = i + 1


# Download and save selected sprite locally
def save_sprite(sprite_url, file_name):
    # Connect to the site
    try:
        response = requests.get(sprite_url.lower())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP error: {e}")
        sys.exit(1)

    try:
        # Get an image from the site
        img = Image.open(BytesIO(response.content))

        # Save it locally
        img.save(os.path.join("PokemonSprites", file_name))

        print("Saved locally ", sprite_url)
    except (OSError, IOError) as e:
        print(f"Error saving {file_name}: {e}")


# Resize all sprites to desired dimensions
def resize_sprites(width, height):
    if width > 0 and width <= WIDTH_MAX and height > 0 and height <= HEIGHT_MAX:
        # Loop over all files in directory
        for image_file in os.listdir("PokemonSprites"):
            # Read files preserving transparency channel
            image = cv.imread(os.path.join("PokemonSprites", image_file), cv.IMREAD_UNCHANGED)

            # If an image wasn't opened, skip to the next iteration
            if image is None:
                print(f"Image wasn't loaded. {image_file}")
                continue

            # If the image's dimensions are different from desired
            if image.shape[0] != width or image.shape[1] != height:
                # Resize and save
                image_resized = cv.resize(image, (width, height))

                try:
                    cv.imwrite(os.path.join("PokemonSprites", image_file), image_resized)
                    print("Resized and saved ", str(image_file))
                except Exception as e:
                    print(f"Encountered an exception while saving an image: {e}")
    else:
        print("Wrong size selected")


# Create and save new images by changing hue and saturation of original images
def augment_hue_sat():
    # Loop over all files in a directory
    for image_file in os.listdir("PokemonSprites"):

        # Read an image while preserving its transparency channel
        image = cv.imread(os.path.join("PokemonSprites", image_file), cv.IMREAD_UNCHANGED)

        # If it didn't load an image, skip to the next item in the loop
        if image is None:
            print(f"Image wasn't loaded. {image_file}")
            continue

        # Loop over rather arbitrary number of different hues
        for i in range(7):
            # Loop over rather arbitrary number of different saturations
            for j in range(3):
                # This case means that there's no change to the image, so we leave it
                if i == 3 and j == 1:
                    pass
                else:
                    # Split channels to preserve the alpha channel
                    bgr = image[:, :, :3]
                    alpha = image[:, :, 3]

                    # Convert BGR to HSV
                    hsv = cv.cvtColor(bgr, cv.COLOR_BGR2HSV)
                    
                    # Set hue and saturation levels
                    hue_shift = -60 + i * 20
                    sat_scale = 0.5 + j * 0.5

                    # Modify hue
                    hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180

                    # Modify saturation
                    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_scale, 0, 255)

                    # Convert back to BGR
                    augmented_bgr = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)

                    # Merge BGR with original alpha channel
                    augmented_image = cv.merge((augmented_bgr, alpha))

                    try:
                        # Save new image
                        cv.imwrite(os.path.join("PokemonSprites", image_file.split(".png")[0] + str(hue_shift) + str(int(sat_scale*2)) + ".png"), augmented_image)
                        print("Augmented and saved ", image_file.split(".png")[0] + str(hue_shift) + str(int(sat_scale*2)) + ".png")
                    except Exception as e:
                        print(f"Encountered an exception while saving an image: {e}")


# Mirror image existing images to augment them
def augment_mirror():
    # Loop over all files in a directory
    for image_file in os.listdir("PokemonSprites"):

        # Open image while preserving alpha channel
        image = cv.imread(os.path.join("PokemonSprites", image_file), cv.IMREAD_UNCHANGED)

        # If it didn't load an image, skip to the next item in the loop
        if image is None:
            print(f"Image wasn't loaded. {image_file}")
            continue

        # Flip / Mirror image
        mirrored_image = cv.flip(image, 1)

        try:
            # Save mirrored image
            cv.imwrite(os.path.join("PokemonSprites", "M" + image_file), mirrored_image)
            print("Mirror image'd ", str(image_file))
        except Exception as e:
            print(f"Encountered an exception while saving an image: {e}")


# Some sprites from that site do not have enough bit depth to preserve alpha channel after transforming
# This function makes sure to convert 4bit images to 32bit
def convert_to_32bit():
    # Loop over all files in a directory
    for file_name in os.listdir("PokemonSprites"):

        # Open image with PIL
        image = Image.open(os.path.join("PokemonSprites", file_name))

        if image is None:
            print(f"Image wasn't loaded. {file_name}")
            continue

        # If mode is 4bit, change it to 32bit
        if image.mode == 'P':
            image = image.convert('RGBA')

            try:
                # Save
                image.save(os.path.join("PokemonSprites", file_name))
                print("Changed 4bit image to 32bit image ", str(file_name))
            except Exception as e:
                print(f"Encountered an exception while saving an image: {e}")


def main():
    if not os.path.exists("PokemonSprites"):
        os.makedirs("PokemonSprites")

    download_sprites()
    resize_sprites(96, 96)
    augment_hue_sat()
    augment_mirror()
    convert_to_32bit()

    print("Finished")


if __name__ == "__main__":
    main()