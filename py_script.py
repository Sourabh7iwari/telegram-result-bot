import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import os, ast

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to split messages if they exceed Telegram's message length limit
def split_message(message, max_length=4096):
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]

# Function to format result data into a tabular string
def format_result(result_data):
    # Define header
    result_text = "IGNOU Result:\n\n"
    result_text += "{:<10} {:<4} {:<5} {:<7}\n".format("Subject", "A", "T/V", "Status")
    result_text += "-" * 28 + "\n"
    
    # Populate the rows
    for subject in result_data:
        status = "✅" if subject['status'] == "COMPLETED" else "☑️"
        result_text += "{:<10} {:<4} {:<5} {:<7}\n".format(
            subject['subject_name'], 
            subject['assignment_marks'], 
            subject['theory_or_viva_marks'], 
            status
        )
    
    return result_text


# Function to scrape IGNOU result by enrollment number
def fetch_result(input):
    dic = os.getenv("MY_DICT")
    
    try:
        dictt = ast.literal_eval(dic)
    except :
        return("Error parsing the dictionary")
    
    
    if input.upper() in dictt.keys():
        enrollment_no=dictt[input.upper()]
    else:
        enrollment_no=int(input)

    url = f"https://gradecard.ignou.ac.in/gradecard/view_gradecard.aspx?eno={enrollment_no}&prog=BCA&type=1"

    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all <tr> elements with valign="middle"
        rows = soup.find_all('tr', {'valign': 'middle'})
        if len(rows)>0:
            result_data = []
            for row in rows:
                columns = row.find_all('td')
                if columns:
                    subject_name = columns[0].text.strip()
                    assignment_marks = columns[1].text.strip()
                    if "L" in subject_name:
                        # Adjust the column index for lab subjects
                        theory_or_viva_marks = columns[7].text.strip()  # Adjust for lab/practical subjects
                    else:
                        # Default case for theory subjects
                        theory_or_viva_marks = columns[6].text.strip()
                    status = columns[8].text.strip()
                
                    # Append the parsed data
                    result_data.append({
                        'subject_name': subject_name,
                        'assignment_marks': assignment_marks,
                        'theory_or_viva_marks': theory_or_viva_marks,
                        'status': status
                    })
            return format_result(result_data)
        else:
            return "Enrollment  number not found"
    else:
        return " Try again later."
      

# Command handler for /start
async def start(update: Update, context):
    await update.message.reply_text("Welcome! Please enter your enrollment number to get your IGNOU result.")

# Function to handle user input (enrollment number)
async def handle_input(update: Update, context):
    user_input = update.message.text
    
    # Fetch the result based on the enrollment number
    result = fetch_result(user_input)
    
    # Split the message if it's too long
    result_chunks = split_message(result)
    
    # Send each chunk as a separate message
    for chunk in result_chunks:
        await update.message.reply_text(chunk)

if __name__ == '__main__':
    # Load the token from environment variables for security
    token = os.getenv('TELEGRAM_BOT_TOKEN')  # Ensure the token is stored securely in the environment

    # Create the bot using the token
    application = ApplicationBuilder().token(token).build()
    
    # Define the command and message handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    # Start the bot
    application.run_polling()
