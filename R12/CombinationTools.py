from itertools import product
import easygui


def get_file_name():
    while True:
        msg = "Please enter the following information:"
        title = "File Information"
        field_names = ["File Name", "Description"]
        field_values = easygui.multenterbox(msg, title, field_names)
        # If the user cancels the dialog, field_values will be None
        if field_values is None:
            easygui.msgbox("You must complete both fields to proceed.", "Error")
            continue
        # Unpack field values
        file_name, description = field_values
        # Check if both fields are filled
        if file_name.strip() and description.strip():
            return file_name, description
        else:
            easygui.msgbox("Both fields are required. Please try again.", "Error")


def ask_action():
    prompt = "Matching Data file already exists. What do you want to do?"
    choices = ["Continue existing data", "Start from scratch", "Stop script"]
    choice = easygui.buttonbox(prompt, choices=choices)
    return choice


def print_as_integers(label, array):
    int_array = array.astype(int)
    print(f'{label}:\t{int_array}')


def generate_combinations(x_vals, y_vals, yaw_vals):
    combinations = []
    for (i, x), (j, y), (k, yaw) in product(enumerate(x_vals), enumerate(y_vals), enumerate(yaw_vals)):
        combinations.append(((x, y, yaw), (i, j, k)))
    return combinations