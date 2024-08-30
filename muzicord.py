import tkinter as tk
import threading
import requests
import time
from queue import Queue
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import certifi

# Global variables
tokens = []
current_token_index = 0
message_count = 0  # Counter to track the number of messages sent
stop_sending = False  # Flag to control the sending loop
message_queue = Queue()  # Queue to manage messages

def load_initial_token():
    if tokens:
        token_entry.delete(0, tk.END)
        token_entry.insert(0, tokens[current_token_index][1])  # Display username instead of token

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session

def send_message(session, token, channel_id, message):
    headers = {
        'Authorization': token.strip(),  # Strip any extraneous whitespace
        'Content-Type': 'application/json'
    }
    data = {
        'content': message
    }
    try:
        response = session.post(
            f'https://discord.com/api/v9/channels/{channel_id}/messages',
            json=data,
            headers=headers,
            verify=certifi.where()
        )
        response.raise_for_status()
        print(f"Sent message: {message}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {message}")
        print(f"Error: {e}")

def message_sender():
    global current_token_index, message_count, stop_sending
    channel_id = channel_id_entry.get()
    session = create_session()

    while not stop_sending:
        if not message_queue.empty():
            message = message_queue.get()
            token = tokens[current_token_index][0]  # Get current token
            send_message(session, token, channel_id, message)
            message_count += 1

            # Switch token every 10 messages
            if message_count % 10 == 0:
                current_token_index = (current_token_index + 1) % len(tokens)
                token_entry.delete(0, tk.END)
                token_entry.insert(0, tokens[current_token_index][1])  # Display username instead of token

        # Minimal delay to prevent overwhelming the system
        time.sleep(0.1)

def add_token():
    token = token_entry.get().strip()  # Strip any extraneous whitespace
    if token and all(token not in t for t in tokens):
        tokens.append((token, token))
        token_listbox.insert(tk.END, token)
        token_entry.delete(0, tk.END)

def delete_selected_token():
    selected_token_index = token_listbox.curselection()
    if selected_token_index:
        tokens.pop(selected_token_index[0])
        token_listbox.delete(selected_token_index)

def switch_token(event=None):
    global current_token_index
    if tokens:
        current_token_index = (current_token_index + 1) % len(tokens)
        token_entry.delete(0, tk.END)
        token_entry.insert(0, tokens[current_token_index][1])  # Display username instead of token

def start_sending(event=None):
    global stop_sending
    stop_sending = False
    threading.Thread(target=message_sender, daemon=True).start()

def stop_sending_messages():
    global stop_sending
    stop_sending = True

def restart_sending():
    stop_sending_messages()
    start_sending()

# Create the main window
root = tk.Tk()
root.title("muzicord")
root.configure(bg='#800080')  # Set the background color to purple

# Token entry
tk.Label(root, text="Token:", bg='#800080', fg='white').grid(row=0, column=0, padx=10, pady=10)
token_entry = tk.Entry(root, width=50, bg='black', fg='white', insertbackground='white')
token_entry.grid(row=0, column=1, padx=10, pady=10)

# Token Listbox
token_listbox = tk.Listbox(root, height=5, width=50, bg='black', fg='white')
token_listbox.grid(row=1, column=1, padx=10, pady=10)

# Add Token Button
add_token_button = tk.Button(root, text="Add Token", command=add_token, bg='#800080', fg='white')
add_token_button.grid(row=0, column=1, padx=10, pady=10)

# Delete Token Button
delete_token_button = tk.Button(root, text="Delete Selected Token", command=delete_selected_token, bg='#800080', fg='white')
delete_token_button.grid(row=1, column=2, padx=10, pady=10)

# Channel ID entry
tk.Label(root, text="Channel ID:", bg='#800080', fg='white').grid(row=2, column=0, padx=10, pady=10)
channel_id_entry = tk.Entry(root, width=50, bg='black', fg='white', insertbackground='white')
channel_id_entry.grid(row=2, column=1, padx=10, pady=10)

# Messages entry
tk.Label(root, text="Messages:", bg='#800080', fg='white').grid(row=3, column=0, padx=10, pady=10)
messages_entry = tk.Text(root, height=5, width=50, bg='black', fg='white', insertbackground='white')
messages_entry.grid(row=3, column=1, padx=10, pady=10)

# Send button
send_button = tk.Button(root, text="Send Messages", command=start_sending, bg='#800080', fg='white')
send_button.grid(row=4, column=1, pady=10)

# Stop button
stop_button = tk.Button(root, text="END", command=stop_sending_messages, bg='#800080', fg='white')
stop_button.grid(row=4, column=2, pady=10)

# Restart button
restart_button = tk.Button(root, text="Restart", command=restart_sending, bg='#800080', fg='white')
restart_button.grid(row=4, column=3, pady=10)

# Bind the Enter key to send messages
def send_message_from_entry(event):
    message = messages_entry.get("1.0", tk.END).strip()
    if message:
        message_queue.put(message)  # Add the message to the queue
        messages_entry.delete("1.0", tk.END)  # Clear the message entry

messages_entry.bind('<Return>', send_message_from_entry)

# Load initial token
load_initial_token()

# Start the GUI event loop
root.mainloop()
