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
    MediaListCollection(userName: $user, type: ANIME, status_in: [COMPLETED, PLANNING, CURRENT], forceSingleCompletedList: true) @include(if: $doList) {
  	    lists {
  	        name
  	        status
            entries {
                media {
                    ...titleCharVA
                }
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

        # use pageInfo to determine if another query needs to be made since
        # there are too many characters (25+)
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

            # in case a character has multiple listed VAs
            for actor in voice_actors:
                nameVA = f"{actor['name']['last']}, {actor['name']['first']}"
                actorToChar.setdefault(nameVA, [])
                actorToChar[nameVA].append(charName)

        print(f"{title} has {info['total']} chars, {numChars} found")
        print(f"currently on page {info['currentPage']} of {info['lastPage']}")

        # if incrementing this exceeds 'lastPage' then loop terminates
        # otherwise, it will make another query for subsequent pages
        currPage += 1

    #pprint.pprint(actorToChar)
    return (title, actorToChar)

# implement a query to retrieve a user's Completed List
# userName -> a user with an anime list on AniList
# outputs a dict that maps keys nameVA -> showDict
# the show dict maps keys nameShow -> [character list]
# the [character list] is all of the roles nameVA has in nameShow
#
# output = a dict where keys are all VAs from userName's COMPLETED list
# output[VA] = a dict where the keys are all shows that have VA
# output[VA][SHOW] = a list of all chars voiced by VA in SHOW
def getVAsFromList(userName):

    # default page values
    currPage = 1
    largestPage = 1

    actorToShow = {}

    # while there are still characters to be fetched
    while currPage <= largestPage:

        # query variables
        variables = {
            'user': userName,
            'page': currPage,
            'doList': True
        }

        # Make the HTTP Api request
        print(f"Making query number {currPage} for user {userName}")
        response = requests.post(url, json={'query': query, 'variables': variables})
        response = json.loads(response.text)

        # the user's completed list of shows
        #entries = response['data']['MediaListCollection']['lists'][0]['entries']

        numLists = len(response['data']['MediaListCollection']['lists'])
        for i in range(0, numLists):
            # curr = response['data']['MediaListCollection']['lists'][i]['entries']
            # entries.extend(curr)
            entries = response['data']['MediaListCollection']['lists'][i]['entries']

            # loop through the shows and get the chars and VAs on the currPage
            for entry in entries:
                title =(i*'*') + entry['media']['title']['romaji']

                # pageInfo is a dict with keys
                # 'total' => total number of items
                # 'perPage'
                # 'currentPage'
                # 'lastPage'
                # 'hasNextPage'
                pageInfo = entry['media']['characters']['pageInfo']

                # update this until the largest page number is found
                # outer while loop needs to run until this page of chars is read
                largestPage = max(largestPage, pageInfo['lastPage'])

                # a single edge connects a char node to a list of voice actors
                # edge is a dict with keys 'node' and 'voiceActors'
                edges = entry['media']['characters']['edges']

                # skip this show since there are no chars on this page
                # all chars have already been read for this show
                if not edges:
                    continue

                # loop through the list of chars
                for edge in edges:
                    charName = edge['node']['name']['full']
                    voice_actors = edge['voiceActors']

                    # loop in case a character has multiple listed VAs
                    for actor in voice_actors:
                        nameVA = f"{actor['name']['last']}, {actor['name']['first']}"

                        # if the VA is not in the map already, create a new dict
                        # showToRoles = actorToShow.setdefault(nameVA, {})
                        actorToShow.setdefault(nameVA, {})

                        # create a new list for chars for key 'title' if needed
                        # use a list since actors may have multiple roles in 1 show
                        actorToShow[nameVA].setdefault(title, [])

                        # add the char to the list of chars for current 'title'
                        actorToShow[nameVA][title].append(charName)

        # if incrementing this exceeds 'largestPage' then loop terminates
        # otherwise, it will make another query for subsequent pages
        currPage += 1

    print(f'largest page number is {largestPage}')
    return actorToShow

# given the id of an anilist show and the username of an anilist user,
# return a dict containing a map of VA -> showTitle -> characterRoles
# all VAs in the dict have a role in the id show and a show in the user's list
def getCommonVAs(id, db):
    title, showVAs = getAniVAs(id)

    commonVAs = {}
    for actor in showVAs.keys():
        if actor in db:
            actorEntry = db[actor]
            newEntry = {}

            # remove duplicate roles for the same voice actor
            # shows with multiple seasons only show a single one
            # season kept is determined by the first one lexicographically
            for k,v in sorted(actorEntry.items(), key=lambda x: x[0]):
                # remove dupes and do not add the entry for the query title
                if v not in newEntry.values() and k[k.rfind('*')+1:] != title:
                    newEntry[k] = v
            commonVAs[actor] = newEntry

    return (title, showVAs, commonVAs)

# does not remove duplicates like in getCommonVAs()
def actorQuery(actor, db):
    pprint.pprint(db[actor], indent=4, width=100)

# change id to show title later
# use title to search for a show and give the user a list to choose from
def showQuery(id, user, db):
    # should be a 3-tuple (title, showVAs, commonVAs)
    title, showVAs, commonVAs = getCommonVAs(id, db)
    printCommonVAs(user, title, showVAs, commonVAs)

# print the results of a show query by a user
# user wants to see what VAs are in their query and their list
def printCommonVAs(user, title, showVAs, commonVAs):
    print(f'{len(commonVAs)} VAs found in both {title} and {user}\'s list:\n')

    for actor,roles in showVAs.items():
        actorEntry = commonVAs.get(actor)
        if not actorEntry:
            continue
        print(f'{actor} ({roles})')
        print(f'{pprint.pformat(actorEntry, indent=4, width=100)}\n\n')

def userPrompt():
    user = input("Username: ")
    if not user:
        # default
        user = "JeremyAL"
    print(f"User is {user}")
    print(f"starting queries to ({url}) to populate database")
    db = getVAsFromList(user)

    while True:
        query = input("Query (VA name 'Last, First') or (show id #####): ")

        if query.isdigit():
            showQuery(query, user, db)

        elif isinstance(query, str) and ',' in query:
            try:
                actorQuery(query, db)
            except KeyError as e:
                print("no such actor")
                # do not raise e so the loop continues

        else:
            print("invalid input")

#id: 113813 # Kanokari, 8 chars
#id: 104454, # isekai quartet, 43 chars, 40 VAs (3 VAs have 2 roles)
#id: 20992, haikyuu2, 35 chars
#id: 113415, jujutsu kaisen


userPrompt()

# TODO: allow user to enter show name and get the id using that
# sort the final list of common VAs by: number of roles, by main/side char, etc
# add WATCHING list option instead of just COMPLETED
