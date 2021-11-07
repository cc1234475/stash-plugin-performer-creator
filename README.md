# Stash plugin: Performer Creator

This is a plugin for stash. It adds a `Parse all scenes for performers` task. This task processes all scenes and using Natural Language Processing tries to detect performer names and tries to find/add them.

# How to set it up

Add the python files too your `.stash/plugins` directory

create a `virtualenv`

```bash
virtualenv -p python3 --system-site-packages ~/.stash/plugins/env
source ~/.stash/plugins/env/bin/activate
pip install ~/.stash/plugins/requirements.txt
python -m spacy download en_core_web_md
```

# How to use

Rescan the plugins, you will find a new button in the `Tasks` sections in the settings.

# Setup on Unraid

SSH to your server or if you use the webui to open Stash's console then start at the second line.

```sh
docker exec -i -t Stash sh
apk update
apk add git
cd /root/.stash/plugins/
git clone https://github.com/com1234475/stash-plugin-performer-creator.git
cd stash-plugin-performer-creator/
###
# dont know if subversion/python3-dev is needed but this worked.
###
apk add make automake gcc g++ subversion python3-dev
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
python -m spacy download en_core_web_md
```

# Known limitations/Gotcha's

- It uses the file names, not the titles.
