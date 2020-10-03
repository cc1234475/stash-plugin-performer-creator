import os
import sys
import time
import json
import string
import random

import log
import spacy
from stash_interface import StashInterface

nlp = spacy.load('en_core_web_md')


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
		input['args'] = {
			"mode": mode
		}

		# just some hard-coded values
		input['server_connection'] = {
			"Scheme": "http",
			"Port":   9999,
		}

	output = {}
	run(input, output)

	out = json.dumps(output)
	print(out + "\n")


def readJSONInput():
	input = sys.stdin.read()
	return json.loads(input)


def run(input, output):
	modeArg = input['args']["mode"]
	try:
		if modeArg == "" or modeArg == "create":
			client = StashInterface(input["server_connection"])
			createPerformers(client)
	except Exception as e:
		raise

	output["output"] = "ok"


def createPerformers(client):
	performers = client.listPerformers()
	all_scenes = client.listScenes()
	performers_to_lookup = set()

	for scene in all_scenes:
		path = scene['path']
		performers_in_scene = [s['name'] for s in scene['performers']]
		file_name = os.path.basename(path)
		file_name, _ = os.path.splitext(file_name)
		file_name = file_name.replace('-', ',').replace(',', ' ,')
		# file_name = " ".join(file_name.split('.')[3:])
		doc = nlp(file_name)
		performers_names = set()
		for w in doc.ents:
			if w.label_ == "PERSON":
				performers_names.add(w.text.title())

		# little hack to take any 2 word title and use it as an preformers name.
		if len(file_name.split()) == 2 and not any(char.isdigit() for char in file_name):
			performers_names.add(file_name.title())

		for p in performers_names:
			if p not in performers_in_scene and p not in performers and len(p.split()) != 1:
				performers_to_lookup.add(p)

	total = len(performers_to_lookup)
	total_added = 0
	log.LogInfo("Going to look up {} performers".format(total))

	for i, performer in enumerate(performers_to_lookup):
		log.LogInfo("Searching: "+ performer)
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

		if 'gender' in data:
			data['gender'] = data['gender'].upper()

		data = {k: v for k, v in data.items() if v is not None}

		log.LogInfo("Adding: "+ performer)
		try:
			result = client.createPerformer(data)
			total_added += 1
		except Exception as e:
			log.LogError(str(e))

	log.LogInfo("Added a total of {} performers".format(total_added))
	log.LogInfo("Done!")


main()