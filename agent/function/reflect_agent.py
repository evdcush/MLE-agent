import os
import sys
import subprocess
import importlib.util

from .base import BaseAgent
from .search_agent import SearchAgent
from agent.utils import Config, read_file_to_string

config = Config()


class ReflectAgent(BaseAgent):

    def gen_running_cmd(self):
        """
        Generate the running command for the current project.
        :return: the running command.
        """
        return f"python {os.path.basename(self.project.entry_file)}"

    def run_local(self):
        """
        Run a command in the shell, print the output and error logs in real time, and return the results.
        :return: A tuple containing the output, error, and exit status.
        """
        command = self.gen_running_cmd()
        os.chdir(self.project.path)
        output_log = ""
        error_log = ""
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                output_line = process.stdout.readline()
                if output_line:
                    print(output_line, end='')
                    output_log += output_line

                error_line = process.stderr.readline()
                if error_line:
                    print(f"{error_line}", end='', file=sys.stderr)
                    error_log += error_line
                if output_line == '' and error_line == '' and process.poll() is not None:
                    break

            exit_code = process.wait()
            return output_log, error_log, exit_code
        except Exception as e:
            print(f"Exception occurred while running command: {command}\n Error: {str(e)}")
            return "", str(e), -1

    def run_cloud(self, cloud_type: str, dependency_list: list = None):
        """
        Debug the code script on the cloud service.
        :param cloud_type: the type of cloud service to use.
        :param dependency_list: the list of dependencies to install.
        :return:
        """

        dependency = "sky"
        spec = importlib.util.find_spec(dependency)
        if spec is not None:
            sky = importlib.import_module(dependency)
        else:
            raise ImportError(
                "It seems you didn't install the 'skypilot' package."
                f" Please install it using 'pip install skypilot-nightly[{cloud_type}]' command."
            )

        # check the workspace
        if not os.path.exists(self.project.path) or not os.path.isdir(self.project.path):
            self.console.log(f"The directory '{self.project.path}' does not exist or is not a directory.")
            return

        # generate the setup according to the dependency list.
        setup = ''
        if dependency_list:
            setup = f"pip install {' '.join(dependency_list)}"

        task_name = "task_" + os.path.basename(self.project.entry_file)
        task = sky.Task(
            name=task_name,
            setup=setup,
            workdir=self.project.path,
            run=self.gen_running_cmd()
        )

        # set the cloud resource.
        if cloud_type == 'aws':
            task.set_resources(sky.Resources(cloud=sky.AWS()))
        elif cloud_type == 'gcp':
            task.set_resources(sky.Resources(cloud=sky.GCP()))
        elif cloud_type == 'azure':
            task.set_resources(sky.Resources(cloud=sky.Azure()))
        else:
            self.console.log(f"Cloud type '{cloud_type}' is not supported.")
            return

        code, _ = sky.launch(task, cluster_name=self.project.name)
        return None, code

    def run(self, cloud_type: str = None, dependency_list: list = None):
        """
        Run the code script.

        :param cloud_type: the type of cloud service to use, if None, run locally.
        :param dependency_list: the list of dependencies to install.
        """
        if cloud_type:
            run_log, exit_code = self.run_cloud(cloud_type, dependency_list)
        else:
            with self.console.status(f"Running the code script..."):
                run_log, error_log, exit_code = self.run_local()
        return run_log, exit_code

    def invoke(self, dependency_list, max_attempts: int = 3, cloud_type: str = None):
        """
        Run and debug the code script.

        :param cloud_type: the type of cloud service to use, if None, run locally.
        :param dependency_list: the list of dependencies to install.
        :param max_attempts: the max number of attempts to debug the code.
        :return:
        """
        pmpt_code_debug = f"""
        You are a Machine Learning engineer tasked with debugging a script.
        Your goal is to modify the code so that it meets the task requirements and runs successfully.
        You should modify the existing code based on the user's requirements, logs, and web search results.

        The output format should only with the updated code:

        Code: {{code}}
        """
        debug_success = False
        entry_file = self.project.entry_file
        run_log, exit_code = self.run(cloud_type)

        if exit_code != 0:
            enable_web_search = False if config.read().get('general').get('search_engine') == "no_web_search" else True
            search_agent = SearchAgent(enable_web_search)

            for attempt in range(max_attempts):
                self.console.log("Debugging the code script...")
                existing_code = read_file_to_string(entry_file)
                search_results = search_agent.invoke(run_log)

                user_prompt = f"""
                Task Requirements: {self.project.requirement}\n
                Existing Code: {existing_code}\n
                Log: {run_log}\n
                Web Search: {search_results}
                """

                self.chat_history.extend(
                    [
                        {"role": 'system', "content": pmpt_code_debug},
                        {"role": 'user', "content": user_prompt}
                    ]
                )

                self.handle_streaming()
                run_log, exit_code = self.run(cloud_type)

                if exit_code == 0:
                    debug_success = True
                    self.console.log("Debugging successful, the code script has been saved.")
                    break

            if not debug_success:
                self.console.log(f"Debugging failed after {max_attempts} attempts.")
                return
        else:
            self.console.log("The code script has been run successfully.")
            return
