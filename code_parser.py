import os
import re
import pandas as pd
import paramiko
import argparse


class LogParser:
    """
    A class to parse the log file 
    """

    def __init__(self, arguments) -> None:
        """
        Initialize the LogParser class
        Args:
            arguments (argparse.Namespace): The arguments to initialize the class
        """
        if arguments.user:
            self.user = arguments.user
        else:
            # get the username from the environment variable
            self.user = os.environ.get('USER', None)
        if arguments.host:
            self.host = arguments.host
        else:
            # get the host from the environment variable
            self.host = os.environ.get('HOST', None)
        if arguments.password:
            self.password = arguments.password
        else:
            # get the password from the environment variable
            self.password = os.environ.get('PASSWORD', None)
        if not self.user or not self.host or not self.password:
            raise ValueError('Please provide the user, host, and password')
        self.rotation_count = 14
        self.current_path = os.path.dirname(os.path.realpath(__file__))
        self.current_path = os.path.join(self.current_path, arguments.dir)
        os.makedirs(self.current_path, exist_ok=True)
        self.file_name = None

    def get_file_from_remote_server(self, remote_path) -> str:
        """
        Get the file from the remote server

        Args:
            remote_path (str): The path of the file on the remote server

        Returns:
            str: The content of the file
        """

        print(f'Connecting to {self.host}')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.user, password=self.password)
        print(f'Connected to {self.host}')
        if ssh.get_transport().is_active():
            command = f'echo {self.password} | sudo -S cat {remote_path}'
            stdin, stdout, stderr = ssh.exec_command(command)
            file = stdout.read().decode('utf-8')
            try:
                os.remove(os.path.join(self.current_path, f'{self.file_name}.txt'))
            except FileNotFoundError:
                pass
            with open(os.path.join(self.current_path, f'{self.file_name}.txt'), 'w') as f:
                f.write(file)
            try:
                for index in range(1, self.rotation_count):
                    command = f'echo {self.password} | sudo -S cat {remote_path}.{index}'
                    stdin, stdout, stderr = ssh.exec_command(command)
                    file = stdout.read().decode('utf-8')
                    if not file:
                        break
                    try:
                        os.remove(os.path.join(self.current_path, f'{self.file_name}.txt.{index}'))
                    except FileNotFoundError:
                        pass
                    with open(os.path.join(self.current_path, f'{self.file_name}.txt.{index}'), 'w') as f:
                        f.write(file)
            except Exception as e:
                print(e)
            finally:
                ssh.close()

            data_frame = pd.DataFrame()
            for file in os.listdir(self.current_path):
                if self.file_name in file and ".txt" in file:
                    print(file)
                    file_data_frame = self.parse_log(file)
                    data_frame = pd.concat([data_frame, file_data_frame])
            try:
                os.remove(os.path.join(self.current_path, f'{self.file_name}.xlsx'))
            except FileNotFoundError:
                pass
            data_frame.to_excel(os.path.join(self.current_path, f'{self.file_name}.xlsx'), index=False)
            data_frame['Request Count'] = 1
            data_frame = data_frame.groupby(['User IP']).agg({
                'Date': 'max', 'USER Request': 'last', 'Status Code': 'last', 'Request Count': 'count'
            }).reset_index()
            try:
                os.remove(os.path.join(self.current_path, f'{self.file_name}_summary.xlsx'))
            except FileNotFoundError:
                pass
            data_frame.to_excel(os.path.join(self.current_path, f'{self.file_name}_summary.xlsx'), index=False)
        else:
            print('Connection failed')

        return file

    def parse_log(self, file_name=None) -> pd.DataFrame:
        """
        Parse the log file into a pandas DataFrame

        Args:
            file_name (str, optional): The name of the file to parse. Defaults to None.

        Returns:
            pd.DataFrame: The parsed log file as a pandas DataFrame
        """

        if not file_name:
            file_name = self.file_name + '.txt'
        with open(os.path.join(self.current_path, file_name), 'r') as file:
            access_log = file.read()
        access_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(.*?)\] "(.*?)" (\d{3})'
        data = []
        matches = re.findall(access_pattern, access_log)
        for match in matches:
            ip, timestamp, request, status_code = match
            timestamp = pd.to_datetime(timestamp, format='%d/%b/%Y:%H:%M:%S %z').strftime('%b %d, %Y %I:%M %p')
            data.append([ip, timestamp, request, status_code])

        data_frame = pd.DataFrame(data, columns=['User IP', 'Date', 'USER Request', 'Status Code'])
        return data_frame

    @staticmethod
    def parse_log_to_df(access_log) -> pd.DataFrame:
        """
        Parse the log file into a pandas DataFrame

        Args:
            access_log (str): The content of the log file

        Returns:
            pd.DataFrame: The parsed log file as a pandas DataFrame
        """

        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(.*?)\] "(.*?)" (\d{3})'
        matches = re.findall(pattern, access_log)

        data = []
        for match in matches:
            ip, timestamp, request, status_code = match
            data.append([ip, timestamp, request, status_code])

        access_log_df = pd.DataFrame(data, columns=['IP', 'Timestamp', 'Request', 'Status Code'])
        return access_log_df

    def get_log_df(self, remote_path) -> pd.DataFrame:
        """
        Get the log file as a pandas DataFrame

        Args:
            remote_path (str): The path of the log file on the remote server

        Returns:
            pd.DataFrame: The log file as a pandas DataFrame
        """

        access_log = self.get_file_from_remote_server(remote_path)
        access_log_df = self.parse_log_to_df(access_log)
        return access_log_df

    def get_log(self, remote_path) -> str:
        """
        Get the log file as a string from the remote server

        Args:
            remote_path (str): The path of the log file on the remote server

        Returns:
            str: The log file as a string
        """

        local_path = f'{self.current_path}/{self.file_name}.txt'
        access_log = self.get_file_from_remote_server(remote_path, local_path)
        return access_log

    def get_log_df_from_local(self, local_path) -> pd.DataFrame:
        """
        Get the log file as a pandas DataFrame from the local path

        Args:
            local_path (str): The path of the log file on the local machine

        Returns:
            pd.DataFrame: The log file as a pandas DataFrame
        """
        with open(local_path, 'r') as file:
            access_log = file.read()
        access_log_df = self.parse_log_to_df(access_log)
        return access_log_df

    @staticmethod
    def get_log_from_local(local_path) -> str:
        """
        Get the log file as a string from the local path

        Args:
            local_path (str): The path of the log file on the local machine

        Returns:
            str: The log file as a string
        """
        with open(local_path, 'r') as file:
            access_log = file.read()
        return access_log


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--user', type=str, help='The username to connect to the remote server', default=None)
    arg_parser.add_argument('--host', type=str, help='The host to connect to', default=None)
    arg_parser.add_argument('--password', type=str, help='The password to connect to the remote server', default=None)
    arg_parser.add_argument('--dir', type=str, help='The directory to save the log file', default='logs')
    args = arg_parser.parse_args()
    log_parser = LogParser(args)
    remote_file_path = '/var/log/nginx/access.log'
    log_parser.file_name = 'access'
    df = log_parser.get_log_df(remote_file_path)
