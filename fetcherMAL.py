from urllib.request import Request, urlopen
import json
import pprint

SHOW_ID = 38472

request = Request(f'https://api.jikan.moe/v3/anime/{SHOW_ID}/characters_staff')
#request = 'https://api.jikan.moe/v3/anime/40839/characters_staff'

response_body = urlopen(request).read()
response_body = json.loads(response_body)

# at this point, the response should be in the form of a JSON

# get the list of chracter objects
charList = response_body['characters']

# a single character object is a dict contains the keys:
#   name: character name
#   voice_actors: list of voice actors objects (dicts) with the keys:
#       name: voice actor name
#       language: the language the VA is associated with

# get all chars and their japanese VAs
actorToChar = {}
for char in charList:
    charName = char['name']
    voice_actors = char['voice_actors']

    # create a Japanese VA -> char mapping
    for actor in voice_actors:
        if actor['language'] == 'Japanese':
            nameVA = actor['name']
            actorToChar.setdefault(nameVA, [])
            actorToChar[nameVA].append(charName)

#print(actorToChar)
pprint.pprint(actorToChar)
