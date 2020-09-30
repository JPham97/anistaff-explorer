#from collections import defaultdict
#import csv

# write the basic algorithm with a small database

# read in the database file
aniDB = {}
with open('smallDatabase.txt') as db:
    for line in db:
        idx = line.find(',')
        start = line.find('[') + 1
        end = line.find(']')
        anime = line[0:idx]
        listVA = line[start:end].split(',')
        aniDB[anime] = listVA

# dict with mappings show -> [VA1, VA2,...]
print('Database has {} entries'.format(len(aniDB)))

# should only work on p3.6+ cause of ordered dicts
first = list(aniDB.keys())[0]
print('First entry: {} has VAs {}'.format(first, aniDB[first]))

watchList = []
watchListSource = input('Enter your watched list as a filename: ')
with open(watchListSource) as wl:
    for line in wl:
        watchList.append(line.strip())
print('Your watched list: {}'.format(watchList))


# user inputs an anime name that they want VA info on
reqAni = input('Enter an anime name to get VA info: ')
reqAniVAs = aniDB[reqAni]
print('VAs for this anime: {}'.format(reqAniVAs))

# use defaultdict to initialize values as lists
#outputAniMap = defaultdict(list)
outputAniMap = {}

for actor in reqAniVAs:
    for entry in watchList:
        # an actor in the requested anime is also in user's WL
        # TODO: handle error when entry is not found
        #   entry is not in database
        if actor in aniDB[entry]:
            #outputAniMap[entry].append(actor)
            outputAniMap.setdefault(entry, [])
            outputAniMap[entry].append(actor)

print('***Anime you have seen with shared voice actors: ')
for anime in outputAniMap.keys():
    print('\t{}: shared VAs: {}'.format(anime, outputAniMap[anime]))


# TODO: test the simple version using many combos of watch lists and reqs

# TODO: think about separating functionality using functions & different files
# TODO: learn how to create database using MAL data (jikan)
# TODO: be able to use own anilist data as watch list (need API)
