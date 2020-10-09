import requests
import json
import pprint

query = '''
fragment titleCharVA on Media {
    title {
        romaji
    }
    characters(page: $page) {
        pageInfo {
            total
            perPage
            currentPage
            lastPage
            hasNextPage
        }
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

query ($id: Int, $page: Int, $doList: Boolean!, $user: String) {
    Media(id: $id, type: ANIME) @skip(if: $doList) {
        ...titleCharVA
    }
    MediaListCollection(userName: $user, type: ANIME, status: COMPLETED, forceSingleCompletedList: true) @include(if: $doList) {
  	    lists {
  	        name
  	        status
            entries {
                progress
                # media {
                #     ...titleCharVA
                # }
            }
  	    }
    }
}
'''
url = 'https://graphql.anilist.co'

# given an id for a show on anilist, return a pair (title, dictionary)
# output dictionary contains mappings for the shows VAs -> chars
def getAniVAs(id):

    # default page values (this is the usual case, having 25+ chars is rare)
    currPage = 1
    lastPage = 1

    numChars = 0
    actorToChar = {}

    # while there are still characters to be fetched
    while currPage <= lastPage:

        # inside the loop since the page can change
        variables = {
            'id': id,
            'page': currPage,
            'doList': False
        }

        # Make the HTTP Api request
        print(f"Making a query for page {currPage}")
        response = requests.post(url, json={'query': query, 'variables': variables})
        response = json.loads(response.text)

        # response is converted to JSON at this point
        # process the response and convert to VA -> char map

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
        info = anime['characters']['pageInfo']

        # reassign these so the loop runs again if needed
        currPage = info['currentPage']
        lastPage = info['lastPage']

        # a single edge connects a char node to a list of voice actors
        # edge is a dict with keys 'node' and 'voiceActors'
        edges = anime['characters']['edges']
        for edge in edges:
            charName = edge['node']['name']['full']
            voice_actors = edge['voiceActors']

            numChars += 1

            for actor in voice_actors:
                nameVA = f"{actor['name']['last']}, {actor['name']['first']}"
                actorToChar.setdefault(nameVA, [])
                actorToChar[nameVA].append(charName)

        # pprint.pprint(actorToChar)
        # print(len(actorToChar))

        print(f"{title} has {info['total']} chars, {numChars} found")
        print(f"currently on page {info['currentPage']} of {info['lastPage']}")

        # if incrementing this exceeds 'lastPage' then loop terminates
        # otherwise, it will make another query for subsequent pages
        currPage += 1

    pprint.pprint(actorToChar)
    return (title, actorToChar)

# implement a query to retrieve a user's Completed List
# userName -> a user with an anime list on AniList
# outputs a
#
def getVAsFromList(userName):
    # query variables
    variables = {
        'user': userName,
        'doList': True
    }

    # Make the HTTP Api request
    print(f"Making a query for user {userName}")
    response = requests.post(url, json={'query': query, 'variables': variables})
    response = json.loads(response.text)
    return response

#id: 113813 # Kanokari, 8 chars
#id: 104454, # isekai quartet, 43 chars, 40 VAs (3 VAs have 2 roles)
#id: 20992, haikyuu2, 35 chars

# id = 20992
# (aniTitle, seiyuus) = getAniVAs(id)
# print(f'\n{aniTitle} has {len(seiyuus)} voice actors\n')

data = getVAsFromList("Swagocytosis")

print(data)
