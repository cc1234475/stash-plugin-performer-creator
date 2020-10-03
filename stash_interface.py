import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import log

class StashInterface:
	port = ""
	url = ""
	headers = {
		"Accept-Encoding": "gzip, deflate, br",
		"Content-Type": "application/json",
		"Accept": "application/json",
		"Connection": "keep-alive",
		"DNT": "1"
		}

	def __init__(self, conn):
		self.port = conn['Port']
		scheme = conn['Scheme']

		self.url = scheme + "://localhost:" + str(self.port) + "/graphql"

	def __callGraphQL(self, query, variables = None):
		json = {}
		json['query'] = query
		if variables != None:
			json['variables'] = variables
		
		# handle cookies
		response = requests.post(self.url, json=json, headers=self.headers, verify=False)

		if response.status_code == 200:
			result = response.json()
			if result.get("error", None):
				for error in result["error"]["errors"]:
					raise Exception("GraphQL error: {}".format(error))
			if result.get("data", None):
				return result.get("data")
		else:
			raise Exception("GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(response.status_code, response.content, query, variables))

	def listPerformers(self):
		query = """query{allPerformersSlim{name}}"""
		result = self.__callGraphQL(query)
		return [ p['name'] for p in result["allPerformersSlim"]]

	def listScenes(self):
		query = """
query{findScenes(filter: {per_page:100000}){
  count
  scenes{
    id
	title
    path
    performers{
		name
    }
  }
}}
"""
		result = self.__callGraphQL(query)
		return  result['findScenes']['scenes']

	def findPerformer(self, name, scraper='Babepedia'):
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
		url_name = name.replace(' ', "_")
		query = query % (scraper, name, url_name)
		result = self.__callGraphQL(query)
		if not result['scrapePerformer']['name']:
			return

		return  result['scrapePerformer']


	def createPerformer(self, data):
		query = """
mutation performerCreate($input: PerformerCreateInput!) {
  performerCreate(input: $input){
	  id
  }
}
"""
		variables = {'input': data}
		result = self.__callGraphQL(query, variables)
		return result