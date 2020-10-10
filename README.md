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

# Known limitations/Gotcha's

- It uses the file names, not the titles.
