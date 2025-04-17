# scripts/select_from_list.py

# ==============================================================================
# Govee LAN API Plus – List Selection Utility
# -------------------------------------------
#
# Description:
# Displays a numbered list of options and prompts the user to select one.
# Gracefully handles invalid input and falls back to option labels based on
# object.name or string conversion.
#
# Author: Jimmy Hickman
# License: MIT
# ==============================================================================

def select_from_list(options, prompt_text="Select an item"):
    """
    Prompts the user to select an option from a list.

    Args:
        options (list): A list of selectable options.
        prompt_text (str): Optional custom prompt text to display.

    Returns:
        Any: The selected item from the list.

    Raises:
        ValueError: If the options list is empty.
    """
    if not options:
        raise ValueError("No options to select from.")

    print(f"\n{prompt_text}:\n")

    for i, item in enumerate(options, start=1):
        label = getattr(item, "name", str(item))
        print(f"{i}. {label}")

    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("❌ Invalid selection. Try again.")
        except ValueError:
            print("❌ Please enter a valid number.")