# ACCESS LOG PARSER
## Class Description
> > #### The script contains a class named `LogParser` which is used to parse log files from a remote server. The class has several methods for connecting to the remote server, retrieving the log file, and parsing the log file into a pandas DataFrame.

## Required Libraries
 > > #### These are the libraries that are required to run this script:

> - > `os`: This is a built-in Python library used for interacting with the operating system.
> - > `re`: This is a built-in Python library used for regular expression operations.
> - > `pandas`: This is a third-party library used for data manipulation and analysis.
> - > `paramiko`: This is a third-party library used for SSH2 protocol.
> - > `argparse`: This is a built-in Python library used for command-line option and argument parsing.


## Usage
> > #### The script can be run from the command line. The following arguments are required:

> - > `--username <Optional>`: The username to use for connecting to the remote server.
> - > `--host <Optional>`: The hostname or IP address of the remote server.
> - > `--password <Optional>`: The password to use for connecting to the remote server.
> - > `--dir <Optional>`: The local directory where the log files will be saved.

# *Note* 
> > #### The arguments are optional, because if they are not provided, the script will get the values from the environment variables.

## Example
    
```
python3 --username <username> --host <host name> --password <password> --dir <local log dir> code_parser.py
```
