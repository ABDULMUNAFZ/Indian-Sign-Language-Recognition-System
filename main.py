#!/usr/bin/env python3
"""
Indian Sign Language Recognition System
Main Entry Point

Run with: python main.py
"""

import sys
import os
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.pastebin import upload_file_to_pastebin, delete_paste
from ui.app import main

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ISL Recognition System with Pastebin CLI Integration", add_help=False)
    parser.add_argument("--paste", type=str, help="Upload a file to Pastebin")
    parser.add_argument("--delete", type=str, help="Delete a paste by its key (requires User Key)")
    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="Show this help message and exit")
    
    # We only want to parse args if arguments are provided, otherwise run the GUI
    if len(sys.argv) > 1:
        args, unknown = parser.parse_known_args()
        
        if getattr(args, "paste", None):
            logging.info(f"Uploading {args.paste} to Pastebin...")
            result = upload_file_to_pastebin(args.paste)
            print(f"\nResponse: {result}\n")
            sys.exit(0)
            
        elif getattr(args, "delete", None):
            logging.info(f"Deleting paste {args.delete}...")
            success = delete_paste(args.delete)
            if success:
                print(f"\nResponse: Successfully deleted paste {args.delete}\n")
            else:
                print(f"\nResponse: Failed to delete paste {args.delete}\n")
            sys.exit(0 if success else 1)

    # Run the GUI app if no relevant CLI arguments are provided
    main()
