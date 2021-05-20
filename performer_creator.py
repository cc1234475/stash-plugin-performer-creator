import os
import sys
import time
import json
import random

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import log
import spacy

dir_path = os.path.dirname(os.path.realpath(__file__))
model = os.path.join(dir_path,"ner_model")
nlp = spacy.load(model)

##############################
##		 CONFIG SETTINGS
##############################
SCRAPE_ORDER = ["Babepedia", "ThePornDB"]
IGNORE_TAGS = []
##############################


def main():
    input = None

    if len(sys.argv) < 2:
        input = readJSONInput()
        log.LogDebug("Raw input: %s" % json.dumps(input))
    else:
        log.LogDebug("Using command line inputs")
        mode = sys.argv[1]
        log.LogDebug("Command line inputs: {}".format(sys.argv[1:]))

        input = {}
        input["args"] = {"mode": mode}

        # just some hard-coded values
        input["server_connection"] = {
            "Scheme": "http",
            "Port": 9999,
        }

    output = {}
    run(input, output)

    out = json.dumps(output)
    print(out + "\n")


def readJSONInput():
    input = sys.stdin.read()
    return json.loads(input)


def run(input, output):
    modeArg = input["args"]["mode"]
    try:
        if modeArg == "" or modeArg == "create":
            client = StashInterface(input["server_connection"])
            createPerformers(client)
    except Exception as e:
        raise

    output["output"] = "ok"


def createPerformers(client):
    performers = client.listPerformers()
    performers_to_lookup = set()

    idx = 0
    while True:
        scenes = client.listScenes(idx)
        idx += 1
        if not scenes:
            break

        for scene in scenes:
            path = scene["path"]
            performers_in_scene = [s["name"].lower() for s in scene["performers"]]
            file_name = os.path.basename(path)
            file_name, _ = os.path.splitext(file_name)
            file_name = file_name.replace("-", ",").replace(",", " , ")
            doc = nlp(file_name)
            performers_names = set()
            for w in doc.ents:
                if w.label_ == "PERSON":
                    performers_names.add(w.text.strip().title())

            if len(file_name.split()) == 2 and not any(
                char.isdigit() for char in file_name
            ):
                performers_names.add(file_name.strip().title())

            for p in performers_names:
                if (
                    p.lower() not in performers_in_scene
                    and p.lower() not in performers
                    and len(p.split()) != 1
                ):
                    performers_to_lookup.add(p)

    total = len(performers_to_lookup)
    total_added = 0
    log.LogInfo("Going to look up {} performers".format(total))

    for i, performer in enumerate(performers_to_lookup):
        log.LogInfo("Searching: " + performer)
        log.LogProgress(float(i) / float(total))
        try:
            data = client.findPerformer(performer)
        except Exception as e:
            log.LogError(str(e))
            continue

        # Add a little random sleep so we don't flood the services
        time.sleep(random.uniform(0.2, 1))
        if not data:
            continue

        if "gender" in data:
            data["gender"] = data["gender"].upper()

        data = {k: v for k, v in data.items() if v is not None and v != ""}

        log.LogInfo("Adding: " + performer)
        try:
            client.createPerformer(data)
            total_added += 1
        except Exception as e:
            log.LogError(str(e))

    log.LogInfo("Added a total of {} performers".format(total_added))
    log.LogInfo("Done!")


class StashInterface:
    port = ""
    url = ""
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1",
    }

    def __init__(self, conn):
        self._conn = conn
        self.ignore_ssl_warnings = True
        self.server = conn["Scheme"] + "://localhost:" + str(conn["Port"])
        self.url = self.server + "/graphql"
        self.auth_token = None
        if "SessionCookie" in self._conn:
            self.auth_token = self._conn["SessionCookie"]["Value"]

    def __callGraphQL(self, query, variables=None):
        json = {}
        json["query"] = query
        if variables != None:
            json["variables"] = variables

        if self.auth_token:
            response = requests.post(
                self.url,
                json=json,
                headers=self.headers,
                cookies={"session": self.auth_token},
                verify=not self.ignore_ssl_warnings,
            )
        else:
            response = requests.post(
                self.url,
                json=json,
                headers=self.headers,
                verify=not self.ignore_ssl_warnings,
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("error", None):
                for error in result["error"]["errors"]:
                    raise Exception("GraphQL error: {}".format(error))
            if result.get("data", None):
                return result.get("data")
        else:
            raise Exception(
                "GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(
                    response.status_code, response.content, query, variables
                )
            )

    def listPerformers(self):
        query = """query{allPerformers{name aliases}}"""
        result = self.__callGraphQL(query)
        preformers = set()
        for p in result["allPerformers"]:
            preformers.add(p["name"].lower())
            if p["aliases"] :
                for alias in p["aliases"] .replace('/', ',').split(','):
                    preformers.add(alias.strip().lower())

        return preformers

    def listScenes(self, offset=0):
        query = """
query{
    findScenes(scene_filter: {organized: false}, filter: {per_page:1000, page: %d}){
          scenes{
            id
            title
            path
            url
            performers{
                name
            }
            tags{
                name
            }
          }
    }
}
"""
        result = self.__callGraphQL(query % offset)
        all_scenes = [s for s in result["findScenes"]["scenes"] if not s['url']]
        if IGNORE_TAGS:
            scenes = []
            for scene in all_scenes:
                if not any([t in IGNORE_TAGS for t in scene["tags"]]):
                    scenes.append(scene)
        else:
            scenes = all_scenes
        return scenes

    def findPerformer(self, name):
        for scraper in SCRAPE_ORDER:
            query = """{
    scrapePerformerList(scraper_id: "%s", query: "%s"){
        name
        url
    }
    }
    """
            query = query % (scraper, name)
            result = self.__callGraphQL(query)
            performer_data = None
            for result in result["scrapePerformerList"]:
                if result['name'] == name:
                    performer_data = result
                    break
            else:
                continue

            query = """
    query{
    scrapePerformer(scraper_id: "%s", scraped_performer: {url: "%s"}){
        name
        gender
        url
        twitter
        instagram
        birthdate
        ethnicity
        country
        eye_color
        height
        measurements
        fake_tits
        career_length
        tattoos
        piercings
        aliases
        image
    }
    }
    """
            query = query % (scraper, performer_data['url'])
            result = self.__callGraphQL(query)
            if not result["scrapePerformer"]["name"]:
                continue

            return result["scrapePerformer"]

    def createPerformer(self, data):
        query = """
mutation performerCreate($input: PerformerCreateInput!) {
  performerCreate(input: $input){
      id
  }
}
"""
        variables = {"input": data}
        result = self.__callGraphQL(query, variables)
        return result

main()

# {
#   findScenes(scene_filter: {tags: [{modifier: EXCLUDES, value: 28}, {modifier: EXCLUDES, value: 10}]){
#     scenes{
#       title
#     }
#   }
# }
