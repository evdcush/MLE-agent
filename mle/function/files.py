import os


def read_file(file_path: str):
    """
    Reads the contents of a file and returns it as a string.

    Args:
    file_path (str): The path to the file that needs to be read.

    Returns:
    str: The contents of the file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None


def create_file(path, content=""):
    """
    Create a file with the given path and content.
    Args:
        path (str): The path to the file to create.
        content (str): The initial content to write to the file.
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"[green]File created: {path}"
    except Exception as e:
        return f"[red]Error creating file: {str(e)}"


def write_file(path, content):
    """
    Write content to a file.
    Args:
        path (str): The path to the file to write to.
        content (str): The content to write to the file.
    """
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"[green]Content written to file: {path}"
    except Exception as e:
        return f"[red]Error writing to file: {str(e)}"


def list_files(path="."):
    """
    Lists all files and directories under the given path if it is a directory.
    If the path is a file, returns None.

    Args:
    path (str): The file system path to check and list contents from.

    Returns: A string containing the list of file and directory names under the given path, or None if the path is a file.
    """
    if os.path.isfile(path):
        return None

    file_list = []
    for root, dirs, files in os.walk(path):
        for name in files:
            file_list.append(os.path.join(root, name))
        for name in dirs:
            file_list.append(os.path.join(root, name))

    return "\n".join(file_list)


def create_directory(path: str):
    """
    Create a directory if it does not exist.
    Args:
        path (str): The path to the directory to create.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"[green]Directory '{path}' created successfully. Use 'mle start' to start the project."
    except OSError as error:
        return f"[red]Creation of the directory '{path}' failed due to: {error}"
