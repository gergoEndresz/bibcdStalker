import configparser
import os

if __name__ == "__main__":
    reader = configparser.ConfigParser()
    reader.read("config.ini")
    OUTPUT_DIR = reader.get("APP", "OUTPUT_DIR")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
