# Project Name
Netflix Job applying bot. 

## Description
This is a bot that applies to any Netflix jobs by filling in your details in the application. On a Sunday, I was trying to apply to jobs at Netflix and found many opportunities relevant to my skills. Instead of wasting my time applying to all of them, I wasted my time building this bot that does the work for me and you too, so you don't waste your time. All you have to do is go through the repo.

## Getting Started

### Prerequisites
Make sure you have the following installed on your system:
- Python 
- Git

### Installation

1. **Clone the repository:**
    ```sh
    git clone (https://github.com/chetanreddyv/netflix-jobs_applying_bot.git)
    cd netflix-jobs_applying_bot
    ```

2. **Create and activate a virtual environment:**
    ```sh
    python -m venv netbot
    source netbot/bin/activate  # On Windows use `netbot\Scripts\activate`
    ```

3. **Install the required libraries:**
    ```sh
    pip install -r requirements.txt
    ```

4. **Fill in your details in the `.env` file:**
    Create a `.env` file in the root directory of the project and add your configuration details. For example:
    ```plaintext
RESUME_PATH=/Users/chetan/Documents/Resume.pdf
FIRST_NAME=Chetan
LAST_NAME=Valluru
PHONE_NUMBER=xxxxxxxxxx
LOCATION=New Brunswick, NJ
DROPDOWN_1_1=No
DROPDOWN_1_2=No
DROPDOWN_2_0=No
DROPDOWN_2_1=No
DROPDOWN_2_2=No
CHECKBOX_1=Man
CHECKBOX_2=Heterosexual
CHECKBOX_3=Asian
CHECKBOX_4=No Military Service
    ```

5. **Run the application:**
    ```sh
    python main.py
    ```
