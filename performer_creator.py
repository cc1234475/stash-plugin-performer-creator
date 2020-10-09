import os
import sys
import time
import json
import string
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
            performers_in_scene = [s["name"] for s in scene["performers"]]
            file_name = os.path.basename(path)
            file_name, _ = os.path.splitext(file_name)
            file_name = file_name.replace("-", ",").replace(",", " ,")
            file_name = " ".join(file_name.split('.')[3:])
            doc = nlp(file_name)
            performers_names = set()
            for w in doc.ents:
                if w.label_ == "PERSON":
                    performers_names.add(w.text.title())

            if len(file_name.split()) == 2 and not any(
                char.isdigit() for char in file_name
            ):
                performers_names.add(file_name.title())

            for p in performers_names:
                if (
                    p not in performers_in_scene
                    and p not in performers
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
        except:
            log.LogError(str(e))
            continue

        # Add a little random sleep so we don't flood the services
        time.sleep(random.uniform(0.2, 1))
        if not data:
            continue

        if "gender" in data:
            data["gender"] = data["gender"].upper()

        data = {k: v for k, v in data.items() if v is not None}

        log.LogInfo("Adding: " + performer)
        try:
            result = client.createPerformer(data)
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
        query = """query{allPerformersSlim{name}}"""
        result = self.__callGraphQL(query)
        return [p["name"] for p in result["allPerformersSlim"]]

    def listScenes(self, offset=0):
        query = """
query{
    findScenes(filter: {per_page:1000, page: %d}){
          scenes{
            id
            title
            path
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
        if IGNORE_TAGS:
            scenes = []
            for scene in result["findScenes"]["scenes"]:
                if not any([t in IGNORE_TAGS for t in scene["tags"]]):
                    scenes.append(scene)
        else:
            scenes = result["findScenes"]["scenes"]
        return scenes

    def findPerformer(self, name, scraper="Babepedia"):

        # # Write your query or mutation here
        # {
        #   scrapePerformerList(scraper_id: "ThePornDB",query: "Aaliyah Hadid"){
        #     name
        #     url
        #   }
        # }

        query = """
query{
  scrapePerformer(scraper_id: "%s", scraped_performer: {name: "%s", url: "https://www.babepedia.com/babe/%s"}){
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
        url_name = name.replace(" ", "_")
        query = query % (scraper, name, url_name)
        result = self.__callGraphQL(query)
        if not result["scrapePerformer"]["name"]:
            return

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
