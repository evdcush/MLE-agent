import os
import yaml
import click
import questionary
from pathlib import Path
from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown

import mle
from mle.model import load_model
from mle.agents import CodeAgent

console = Console()
CONFIG_FILE = 'project.yml'


def check_config(config_path: str):
    """
    check_config: check if the configuration file exists.
    :param config_path: the path to the configuration file.
    :return: True if the configuration file exists, False otherwise.
    """""
    if not os.path.exists(config_path):
        console.log("Configuration file not found. Please run 'mle new' first.")
        return False
    return True


@click.group()
@click.version_option(version=mle.__version__)
def cli():
    """
    MLE-Agent: The CLI tool to build machine learning projects.
    """
    pass


@cli.command()
@click.argument('mode', default='general')
def start(mode):
    """
    start: start the chat with LLM.
    """
    if mode == 'kaggle':
        console.log("Kaggle mode is not supported yet. Aborted.")
        return
    else:
        current_work_dir = os.getcwd()
        config_path = os.path.join(current_work_dir, CONFIG_FILE)
        if not check_config(config_path):
            return


@cli.command()
def chat():
    """
    chat: start an interactive chat with LLM to work on your ML project.
    """
    current_work_dir = os.getcwd()
    config_path = os.path.join(current_work_dir, CONFIG_FILE)
    if not check_config(config_path):
        return

    model = load_model(current_work_dir, model_name='gpt-3.5-turbo')
    coder = CodeAgent(model)

    while True:
        try:
            user_pmpt = questionary.text("[Exit/Ctrl+D]: ").ask()
            if user_pmpt:
                with Live(console=Console()) as live:
                    for text in coder.handle_response(user_pmpt.strip()):
                        live.update(
                            Panel(Markdown(text), title="[bold magenta]MLE-Agent[/]", border_style="magenta"),
                            refresh=True
                        )
        except (KeyboardInterrupt, EOFError):
            exit()


@cli.command()
@click.argument('name')
def new(name):
    """
    new: create a new machine learning project with the given NAME.
    """
    if not name:
        console.log("Please provide a valid project name. Aborted.")
        return

    platform = questionary.select(
        "Which language model platform do you want to use?",
        choices=['OpenAI', 'Ollama']
    ).ask()

    api_key = None
    if platform == 'OpenAI':
        api_key = questionary.text("What is your OpenAI API key?").ask()
        if not api_key:
            console.log("API key is required. Aborted.")
            return

    # make a directory for the project
    project_dir = os.path.join(os.getcwd(), name)
    Path(project_dir).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(project_dir, CONFIG_FILE), 'w') as outfile:
        yaml.dump({'platform': platform, 'api_key': api_key}, outfile, default_flow_style=False)
