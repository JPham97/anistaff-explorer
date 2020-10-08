import requests
import json
import pprint

query = '''
fragment titleCharVA on Media {
    title {
        romaji
    }
    characters {
        edges {
            node {
                name {
                    full
                }
            }
            voiceActors(language: JAPANESE) {
                name {
                    first
                    last
                }
            }
        }
    }
}

query ($id: Int) {
    Media(id: $id, type: ANIME) {
        ...titleCharVA
        characters {
            pageInfo {
                total
                perPage
                currentPage
                lastPage
                hasNextPage
            }
        }
    }
}
'''
variables = {
    'id': 113813
}
url = 'https://graphql.anilist.co'

# Make the HTTP Api request
response = requests.post(url, json={'query': query, 'variables': variables})
response = json.loads(response.text)

# response is converted to JSON at this point

anime = response['data']['Media']
title = anime['title']['romaji']

# use pageInfo to determine if another query needs to be made since there
# are too many characters (25+)
#
# pageInfo is a dict with keys
# 'total' => total number of items
# 'perPage'
# 'currentPage'
# 'lastPage'
# 'hasNextPage'
pageInfo = anime['characters']['pageInfo']

actorToChar = {}

# a single edge connects a char node to a list of voice actors
# edge is a dict with keys 'node' and 'voiceActors'
edges = anime['characters']['edges']
for edge in edges:
    charName = edge['node']['name']['full']
    voice_actors = edge['voiceActors']

    for actor in voice_actors:
        nameVA = f"{actor['name']['last']}, {actor['name']['first']}"
        actorToChar.setdefault(nameVA, [])
        actorToChar[nameVA].append(charName)

# pprint.pprint(actorToChar)
# print(len(actorToChar))

print(pageInfo.keys())

## TODO: map VA name (Last, First) --> [List of chars]

# need to implement functionality to deal with pagination
# implement a query to retrieve a user's Completed List
