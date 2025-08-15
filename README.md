# py-setup-tool

This tool is designed as a quick way to setup a python project and some dependency manager (pip or poetry).


## Run pysetup.sh
Run pysetup.sh to 
1. setup a new python environment
1. re-run installations

You may need to give it executions privileges first.
`chmod +x ./pysetup.sh

- No flags → you’ll be asked “Pull latest pysetup.py…?”
- -u / --update or --ci → skips the prompt and always fetches.
- -n / --no-update → skips the prompt and never fetches.
- -h / --help → shows the usage screen.

### Examples

```sh
./pysetup.sh --ci
```

```sh
./pysetup.sh
```