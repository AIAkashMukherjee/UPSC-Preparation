import os
from pathlib import Path
import logging

# Setting up basic logging configuration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

def create_project_structure():
    """Creates the project directory structure and initializes files."""
    
    # List of files to create
    list_of_files = [
        f"app.py",  # Main Streamlit entrypoint
        f"config.py",  # Centralized settings
        f"data/raw/upsc_questions.csv",  # Sample question source
        f"data/processed/questions_bank.json",  # Processed data
        f"data/results/",  # Result storage directory
        f"src/__init__.py",  # Core logic
        f"src/question_generator.py",  # LLM generation logic
        f"src/data_handler.py",  # Data handling functions
        f"src/quiz_engine.py",  # Quiz logic
        f"utils.py",  # Utilities
        f"requirements.txt",  # Dependency list
        f".env",  # Environment variables
        f"db.sqlite",  # SQLite database
        f"Dockerfile",  # Dockerfile for deployment
        f"README.md",  # Project documentation
    ]
    
    # Create directories and files
    for filepath in list_of_files:
        filepath = Path(filepath)
        filedir, filename = os.path.split(filepath)

        # Create directory if it doesn't exist
        if filedir:
            os.makedirs(filedir, exist_ok=True)
            logging.info(f"Creating directory: {filedir} for the file {filename}")

        # Create the file if it doesn't exist or if it is empty
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, 'w') as f:
                logging.info(f"Creating empty file: {filename}")
                # Optionally, write initial content for specific files
                if filename == 'app.py':
                    f.write("import streamlit as st\n\n# Your Streamlit code goes here\n")
                elif filename == 'config.py':
                    f.write("# Configuration settings go here\n")
                elif filename == 'requirements.txt':
                    f.write("streamlit\npandas\nnumpy\n")
                elif filename == 'README.md':
                    f.write("# Project Title\n\n## Description\nYour project description goes here.\n")
        else:
            logging.info(f"{filename} is already created")

if __name__ == "__main__":
    create_project_structure()
