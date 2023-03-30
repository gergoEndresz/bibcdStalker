## Intro
This is a repo for a collection of "first-man-on-the-moon" scripts that:
    1. Scan BIBCD's sdp namespace for builds
    2. Outputs the results into the `resources/output` folder.
    3. If you want to change/limit/expand the namespace, then please edit extract.py.path_components var, 
where the namespace needs to be specified as an array of directories, such as, for `sdp/ingestion-factory/caiman` it is ['sdp', 'ingestion-factory', 'caiman'].

### ReadMe on the outputs:
Due to certain data constraints (size or one-to-many relationships), the logs have been split into three files:
1. <timestamp>.culprits.csv: timestamp and task full path + culprit (if you were the one who triggered it, it will be your name).
2. <timestamp>.logs.csv: full log output with timestamp and task full path (sdp/some_lizard/stage/123).
3. <timestamp>.meta.csv: all metadata except for the full log output.

Additionally, there is an aggregation of all logs in the <subset>_all.csv files.
These files, apart from aggregating all your previous scraping history, also ensures that there are no nested values 
thus easily importable to any visualisation tool.

## Install
1. Connect to VPN
2. Navigate to the project root directory.
2. You need the following python: python >= 3.9
3. Installing python venv plugin:
```commandline
python3 -m pip install --user virtualenv
```
4. Creating venv:
```commandline
python3 -m venv my_env
```
5. Activate created venv
```commandline
source my_env/bin/activate
```
This should add a `my_env` prefix to your command line.
6. Install reqs
```commandline
pip install -r requirements.txt
```
7. Run `extract.py`
```commandline
python3 extract.py
```
8. I probably missed something and now you are cursing me while staring at an error log.
   9. If missing dependency:
   ```commandline
    pip install --upgrade pip
    pip install <missing_dependency_name>
```
   10. On python virtual envs: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/