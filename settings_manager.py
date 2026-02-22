#!/usr/bin/env python

import os
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString as DQ
from InquirerPy import inquirer

# YAML directory
YAML_DIR = "inventory/group_vars/all"

yaml_loader = YAML()
yaml_loader.preserve_quotes = True
yaml_loader.default_flow_style = False

# --- Load and save YAML ---
def load_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml_loader.load(f) or CommentedMap()

def save_yaml(file_path, data):
    with open(file_path, "w") as f:
        yaml_loader.dump(data, f)

def get_yaml_files():
    if not os.path.isdir(YAML_DIR):
        print(f"Directory {YAML_DIR} does not exist!")
        return []
    return [
        os.path.join(YAML_DIR, f)
        for f in os.listdir(YAML_DIR)
        if f.endswith((".yml", ".yaml")) and os.path.isfile(os.path.join(YAML_DIR, f))
    ]

# --- Type-aware value input ---
def input_value(current_value, key_name=None):
    """Get user input matching the type of current_value"""
    # Determine the type
    if current_value is None:
        val_type = str
    elif isinstance(current_value, bool):
        val_type = bool
    elif isinstance(current_value, int):
        val_type = int
    elif isinstance(current_value, float):
        val_type = float
    elif isinstance(current_value, (list, CommentedSeq)):
        val_type = list
    elif isinstance(current_value, (dict, CommentedMap)):
        val_type = dict
    else:
        # String - check if it's a string representation of bool
        if isinstance(current_value, str) and current_value.lower() in ("yes", "no", "true", "false"):
            val_type = bool
        else:
            val_type = str

    prompt_msg = f"Enter value for '{key_name}'" if key_name else "Enter value"

    # Handle booleans
    if val_type == bool:
        # Determine current value for default
        if isinstance(current_value, str):
            current_bool = current_value.lower() in ("yes", "true")
        else:
            current_bool = bool(current_value)

        choice = inquirer.select(
            message=f"{prompt_msg} (current: {current_value}):",
            choices=["true", "false"],
            default="true" if current_bool else "false"
        ).execute()
        return choice == "true"

    # Handle other types
    while True:
        if val_type in (int, float, str):
            val = inquirer.text(
                message=f"{prompt_msg} (current: {current_value}):",
                default=str(current_value) if current_value is not None else ""
            ).execute()
        else:
            val = inquirer.text(
                message=f"{prompt_msg}:",
                default=""
            ).execute()

        if val_type == int:
            try:
                return int(val)
            except ValueError:
                print("❌ Invalid integer. Please try again.")
                continue

        elif val_type == float:
            try:
                return float(val)
            except ValueError:
                print("❌ Invalid float. Please try again.")
                continue

        elif val_type == list:
            if not val.strip():
                return CommentedSeq()
            try:
                lst = yaml_loader.load(val)
                if isinstance(lst, list):
                    return CommentedSeq(lst)
                else:
                    print("❌ Value must be a YAML list (e.g., [item1, item2]).")
                    continue
            except Exception as e:
                print(f"❌ Invalid YAML list format: {e}")
                continue

        elif val_type == dict:
            if not val.strip():
                return CommentedMap()
            try:
                d = yaml_loader.load(val)
                if isinstance(d, dict):
                    return CommentedMap(d)
                else:
                    print("❌ Value must be a YAML dict (e.g., {key: value}).")
                    continue
            except Exception as e:
                print(f"❌ Invalid YAML dict format: {e}")
                continue

        else:  # string
            # Preserve quoting style if original was quoted
            if isinstance(current_value, str) and current_value and current_value[0] in ('"', "'"):
                return DQ(val)
            return val

# --- Search functionality ---
def search_in_data(data, query, current_path=None):
    """
    Recursively search for keys or values matching query.
    Returns list of (path, key, value) tuples.
    """
    if current_path is None:
        current_path = []

    results = []
    query_lower = query.lower()

    if isinstance(data, (dict, CommentedMap)):
        for key, value in data.items():
            # Check if key matches
            if query_lower in str(key).lower():
                results.append((current_path + [key], key, value))

            # Check if value matches (for scalar values)
            if not isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                if query_lower in str(value).lower():
                    results.append((current_path + [key], key, value))

            # Recurse into nested structures
            if isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                results.extend(search_in_data(value, query, current_path + [key]))

    elif isinstance(data, (list, CommentedSeq)):
        for i, value in enumerate(data):
            # Check if value matches (for scalar values)
            if not isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                if query_lower in str(value).lower():
                    results.append((current_path + [f"[{i}]"], f"[{i}]", value))

            # Recurse into nested structures
            if isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                results.extend(search_in_data(value, query, current_path + [f"[{i}]"]))

    return results

def search_all_files(files_map, query):
    """Search across all YAML files and return results."""
    all_results = []

    for file_name, file_path in files_map.items():
        try:
            data = load_yaml(file_path)
            results = search_in_data(data, query)

            for path, key, value in results:
                all_results.append({
                    'file': file_name,
                    'file_path': file_path,
                    'path': path,
                    'key': key,
                    'value': value
                })
        except Exception as e:
            print(f"⚠️  Error searching {file_name}: {e}")

    return all_results

def navigate_to_path(root_data, path_list):
    """Navigate to a specific path in the data structure."""
    current = root_data
    for key in path_list[:-1]:  # Navigate to parent
        if isinstance(key, str) and key.startswith('[') and key.endswith(']'):
            # List index
            index = int(key[1:-1])
            current = current[index]
        else:
            current = current[key]
    return current

def display_search_results(results):
    """Display search results and allow user to select one to edit."""
    if not results:
        print("❌ No results found.")
        return None

    print(f"\n✅ Found {len(results)} result(s):\n")

    # Build display choices
    display_choices = []
    choice_map = {}

    for i, result in enumerate(results):
        file = result['file']
        path = ' → '.join(str(p) for p in result['path'])
        value = str(result['value'])
        if len(value) > 60:
            value = value[:57] + "..."

        display = f"📄 {file} | {path} = {value}"
        display_choices.append(display)
        choice_map[display] = i

    display_choices.append("🔍 New Search")
    choice_map["🔍 New Search"] = "__new_search__"
    display_choices.append("⬅️  Back to Menu")
    choice_map["⬅️  Back to Menu"] = "__back__"

    selected = inquirer.select(
        message="Select a result to edit:",
        choices=display_choices
    ).execute()

    choice = choice_map[selected]

    if choice == "__back__":
        return None
    elif choice == "__new_search__":
        return "__new_search__"
    else:
        return results[choice]

def search_mode(files_map):
    """Interactive search mode."""
    while True:
        query = inquirer.text(
            message="🔍 Enter search query (or leave empty to go back):"
        ).execute()

        if not query.strip():
            return

        print(f"\n🔎 Searching for '{query}' across all files...")
        results = search_all_files(files_map, query)

        result = display_search_results(results)

        if result is None:
            return
        elif result == "__new_search__":
            continue
        else:
            # User selected a result - navigate to it
            file_path = result['file_path']
            path_list = result['path']
            target_value = result['value']

            print(f"\n📂 Opening {result['file']}...")

            try:
                root_data = load_yaml(file_path)

                # Navigate to the exact location
                if len(path_list) == 0:
                    # Root level
                    navigate(root_data, root_data, [], file_path)
                else:
                    # Navigate to the container of the matched item
                    # If the matched item is a dict/list, show it
                    # If it's a scalar, show its parent

                    if isinstance(target_value, (dict, CommentedMap, list, CommentedSeq)):
                        # Navigate into the matched container
                        current = root_data
                        for key in path_list:
                            if isinstance(key, str) and key.startswith('[') and key.endswith(']'):
                                index = int(key[1:-1])
                                current = current[index]
                            else:
                                current = current[key]
                        navigate(root_data, current, path_list, file_path)
                    else:
                        # Navigate to parent (so user can see and edit the matched scalar)
                        if len(path_list) > 1:
                            parent = navigate_to_path(root_data, path_list)
                            navigate(root_data, parent, path_list[:-1], file_path)
                        else:
                            # Top-level scalar - show root
                            navigate(root_data, root_data, [], file_path)

                print(f"✅ Changes saved to {file_path}\n")
            except Exception as e:
                print(f"❌ Error: {e}\n")

# --- Navigate and edit YAML data ---
def navigate(root_data, current_data, path, file_path):
    """
    Navigate through YAML structure and edit values.

    Args:
        root_data: The root YAML document (always saved)
        current_data: Current position in the structure
        path: List of keys showing current location
        file_path: Path to YAML file
    """
    while True:
        choice_map = {}
        display_choices = []

        # Build menu based on current data type
        if isinstance(current_data, (dict, CommentedMap)):
            for k, v in current_data.items():
                if isinstance(v, (dict, CommentedMap)):
                    display = f"📁 {k} (dict with {len(v)} items)"
                elif isinstance(v, (list, CommentedSeq)):
                    display = f"📋 {k} (list with {len(v)} items)"
                else:
                    # Truncate long values
                    val_str = str(v)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    display = f"📝 {k}: {val_str}"
                display_choices.append(display)
                choice_map[display] = k

        elif isinstance(current_data, (list, CommentedSeq)):
            for i, v in enumerate(current_data):
                if isinstance(v, (dict, CommentedMap)):
                    display = f"📁 [{i}] (dict with {len(v)} items)"
                elif isinstance(v, (list, CommentedSeq)):
                    display = f"📋 [{i}] (list with {len(v)} items)"
                else:
                    val_str = str(v)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    display = f"📝 [{i}]: {val_str}"
                display_choices.append(display)
                choice_map[display] = i
        else:
            # Scalar value - shouldn't reach here
            return

        # Add actions
        if isinstance(current_data, (dict, CommentedMap)) and len(path) > 0:
            display_choices.append("➕ Add New Key")
            choice_map["➕ Add New Key"] = "__add__"
        elif isinstance(current_data, (list, CommentedSeq)) and len(path) > 0:
            display_choices.append("➕ Add New Item")
            choice_map["➕ Add New Item"] = "__add__"

        display_choices.append("⬅️  Go Back")
        choice_map["⬅️  Go Back"] = "__back__"

        # Show current path
        path_display = " → ".join(path) if path else "Root"

        selected_display = inquirer.select(
            message=f"📂 {os.path.basename(file_path)} / {path_display}",
            choices=display_choices
        ).execute()

        choice_key = choice_map[selected_display]

        if choice_key == "__back__":
            return

        elif choice_key == "__add__":
            if isinstance(current_data, (dict, CommentedMap)):
                new_key = inquirer.text(message="Enter new key name:").execute()
                if new_key and new_key not in current_data:
                    # Ask for type
                    type_choice = inquirer.select(
                        message="Select value type:",
                        choices=["String", "Integer", "Float", "Boolean", "List", "Dict"]
                    ).execute()

                    if type_choice == "String":
                        current_data[new_key] = ""
                    elif type_choice == "Integer":
                        current_data[new_key] = 0
                    elif type_choice == "Float":
                        current_data[new_key] = 0.0
                    elif type_choice == "Boolean":
                        current_data[new_key] = False
                    elif type_choice == "List":
                        current_data[new_key] = CommentedSeq()
                    elif type_choice == "Dict":
                        current_data[new_key] = CommentedMap()

                    save_yaml(file_path, root_data)
                    print(f"✅ Added key '{new_key}'")
                elif new_key in current_data:
                    print(f"❌ Key '{new_key}' already exists")

            elif isinstance(current_data, (list, CommentedSeq)):
                type_choice = inquirer.select(
                    message="Select item type to add:",
                    choices=["String", "Integer", "Float", "Boolean", "List", "Dict"]
                ).execute()

                if type_choice == "String":
                    val = inquirer.text(message="Enter string value:").execute()
                    current_data.append(val)
                elif type_choice == "Integer":
                    val = inquirer.text(message="Enter integer value:").execute()
                    current_data.append(int(val))
                elif type_choice == "Float":
                    val = inquirer.text(message="Enter float value:").execute()
                    current_data.append(float(val))
                elif type_choice == "Boolean":
                    val = inquirer.select(message="Select value:", choices=["true", "false"]).execute()
                    current_data.append(val == "true")
                elif type_choice == "List":
                    current_data.append(CommentedSeq())
                elif type_choice == "Dict":
                    current_data.append(CommentedMap())

                save_yaml(file_path, root_data)
                print("✅ Added new item")

        else:
            # Navigate into or edit the selected item
            if isinstance(current_data, (dict, CommentedMap)):
                key = choice_key
                value = current_data[key]

                if isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                    # Navigate deeper
                    navigate(root_data, value, path + [str(key)], file_path)
                else:
                    # Edit scalar value
                    new_value = input_value(value, key)
                    current_data[key] = new_value
                    save_yaml(file_path, root_data)
                    print(f"✅ Updated {key} = {new_value}")

            elif isinstance(current_data, (list, CommentedSeq)):
                index = choice_key
                value = current_data[index]

                if isinstance(value, (dict, CommentedMap, list, CommentedSeq)):
                    # Navigate deeper
                    navigate(root_data, value, path + [f"[{index}]"], file_path)
                else:
                    # Edit scalar value
                    new_value = input_value(value, f"[{index}]")
                    current_data[index] = new_value
                    save_yaml(file_path, root_data)
                    print(f"✅ Updated [{index}] = {new_value}")

# --- Main program ---
def main():
    print("🔧 YAML Configuration Editor\n")

    files_full = get_yaml_files()
    if not files_full:
        print(f"❌ No YAML files found in {YAML_DIR}.")
        return

    files_map = {os.path.splitext(os.path.basename(f))[0]: f for f in files_full}
    sorted_names = sorted(files_map.keys())

    while True:
        display_choices = ["🔍 Search Across All Files"]
        display_choices.extend([f"📄 {name}" for name in sorted_names])
        display_choices.append("🚪 Exit")

        choice_map = {"🔍 Search Across All Files": "__search__"}
        choice_map.update({f"📄 {name}": name for name in sorted_names})
        choice_map["🚪 Exit"] = "__exit__"

        selected_display = inquirer.select(
            message="Select an option:",
            choices=display_choices
        ).execute()

        selected_name = choice_map[selected_display]

        if selected_name == "__exit__":
            print("\n👋 Goodbye!")
            break
        elif selected_name == "__search__":
            search_mode(files_map)
        else:
            file_path = files_map[selected_name]
            print(f"\n📂 Loading {file_path}...")

            try:
                root_data = load_yaml(file_path)
                navigate(root_data, root_data, [], file_path)
                print(f"✅ Changes saved to {file_path}\n")
            except Exception as e:
                print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()
