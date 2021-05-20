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

Use a normal ssh session to your unraid server. or if you really want then use the webui to get to stash's console and start at the second line.

```
docker exec -i -t Stash bash
apt-get update
apt-get install git
cd /root/.stash/plugins/
git clone https://github.com/com1234475/stash-plugin-performer-creator.git
apt-get install virtualenv
virtualenv -p python3 --system-site-packages /root/.stash/plugins/env
source /root/.stash/plugins/env/bin/activate
python -m pip install spacy==2.3.5
python -m pip install requests
python -m spacy download en_core_web_md
```

# Known limitations/Gotcha's

- It uses the file names, not the titles.
