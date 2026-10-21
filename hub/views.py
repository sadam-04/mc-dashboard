import json
import os

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from mcdashboard import settings

from mcrcon import MCRcon
from mcsmp.client import Client

import asyncio
from asgiref.sync import sync_to_async

from hub.process import get_stat

import logging

logger = logging.getLogger(__name__)

# def read_file_sync(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         return f.read()

@login_required
def home(request):
    logger.info("Processing home page request")
    return render(request, 'hub/home.html')

@login_required
@ensure_csrf_cookie
def places(request):
    logger.info("Processing places page request")

    locationDataPath = os.path.join(settings.BASE_DIR, 'locations.json')
    # locationFile = await read_file_sync(locationDataPath)
    locationFile = open(locationDataPath, 'r', encoding='utf-8')
    locations = json.load(locationFile)

    return render(request, 'hub/places.html', {"locations": locations})

@login_required
def map_view(request):
    logger.info("Processing map page request")
    return render(request, 'hub/map.html')

@login_required
@require_POST
def say_hello_view(request):
    logger.info("Processing home page request")
    try:

    # django_user = request.user.username
    # mc_username = settings.MC_USER_ASSOCS.get(django_user)
        mc_username = request.user.username
        if not mc_username:
            return JsonResponse({"status": "failure", "error": "No Minecraft account linked."}, status=403)

        cmd = f"tellraw @a \"{mc_username} waved to you\""

        with MCRcon(settings.MC_IP, settings.MC_RCON_PW, settings.MC_RCON_PORT) as svr:
            response = svr.command(cmd)
            return JsonResponse({"status": "success", "mc_response": response})
    except Exception as e:
        logger.error("Error in say_hello_view: " + str(e))
        return JsonResponse({"status": "failure", "error": "error: there is a problem"},  status=500)

@login_required
@require_POST
def teleport(request):
    logger.info("Processing teleport request")
    try:
        svrStatus = asyncio.run(get_server_status())
        thisUser = asyncio.run(request.auser())
        playerList = list(map(lambda p: p.name, svrStatus["players"]))
        if thisUser.username not in playerList:
            # print(f"svrStatus[\"players\"]={["players"]}")
            logger.info(f"User {thisUser.username} attempted to teleport while not logged into MC server.")
            return JsonResponse({"status": "failure", "error": "Not logged into MC server"}, status=403)

        locationDataPath = os.path.join(settings.BASE_DIR, 'locations.json')
        with open(locationDataPath, 'r', encoding='utf-8') as locationFile:
            locations = json.load(locationFile)

        data = json.loads(request.body)

        locationId = data.get("tpid")
        locationDim = data.get("tpdim")

        if None in (locationId, locationDim):
            logger.error("Bad tpdim was posted to the teleport view: " + locationDim)
            return JsonResponse({"status": "failure", "error": "Internal server error"})

        # tpDim = ""
        if locationDim not in ("overworld", "the_nether", "the_end"):
            logger.error("Bad tpdim was posted to the teleport view: " + locationDim)
            return JsonResponse({"status": "failure", "error": "YOOO"})

        logger.info(str(locations))

        try:
            logger.info(f"Trying to get {locationId} in {locationDim}")
            tpCoords = locations.get(locationId).get(locationDim)
        except Exception as e:
            logger.error("2: Error while processing teleport request: " + str(e))
            return JsonResponse({"status": "failure", "error": "Internal server error"},  status=500)

        if not tpCoords:
            logger.error(f"Unable to get coords for the given parameters: (id={locationId}, dim={locationDim})")
            return JsonResponse({"status": "failure", "error": "YOO"})

        # django_user = request.user.username
        # mc_username = settings.MC_USER_ASSOCS.get(django_user)
        mc_username = request.user.username

        # if not mc_username:
        #     logger.error(f"No PlayerProfile object found for this user ({str(request.user)})")
        #     return JsonResponse({"status": "failure", "error": "i couldn't find your minecraft account oopsy"}, status=403)

        cmd = f"execute as {mc_username} in minecraft:{locationDim} run tp {mc_username} {tpCoords}"

        with MCRcon(settings.MC_IP, settings.MC_RCON_PW, settings.MC_RCON_PORT) as svr:
            response = svr.command(cmd)
            return JsonResponse({"status": "success"})
    except Exception as e:
        logger.error("Error while processing teleport request: " + str(e))
        return JsonResponse({"status": "failure", "error": "It didn't work :( sowwy"},  status=500)

async def get_server_status():
    client = Client(settings.MC_IP, settings.MC_PORT, settings.MC_SMP_TOKEN)
    try:
        await client.connect()
        players = await client.players.get()
        motd = await client.server_settings.motd()
        await client.close()
        return {"players": players, "motd": motd}
    except RuntimeError as e:
        logger.error("Failed to get server status. Check that the server is online and your password is correct: " + str(e))
        return None

@login_required
@require_POST
async def status_view(request):
    svrStatus = await get_server_status()
    if svrStatus is not None:
        players = svrStatus["players"]
        motd = svrStatus["motd"]

    namesList = list(map(lambda p: (p.name, p.id), players))
    lastFormatterIdx = motd.rfind('§')
    chopped_motd = motd[lastFormatterIdx + 2:] if lastFormatterIdx != -1 else motd
    
    return JsonResponse({
        "status": "success",
        "players": json.dumps(namesList),
        "motd": chopped_motd
    })

# def sec_to_pretty(seconds):
#     hours, remainder = divmod(seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{hours}, minutes, seconds)

@login_required
@require_POST
def get_leaderboard(request):
    try:
        categoryIds = {
            "playtime": ["minecraft:custom", "minecraft:play_time"],
            "deaths": ["minecraft:custom", "minecraft:deaths"],
            "time_since_death": ["minecraft:custom", "minecraft:time_since_death"],
            "mobs_killed": ["minecraft:custom", "minecraft:mob_kills"],
            "slept": ["minecraft:custom", "minecraft:sleep_in_bed"],            
            "animals_bred": ["minecraft:custom", "minecraft:animals_bred"],
            "fish_caught": ["minecraft:custom", "minecraft:fish_caught"],
            "damage_taken": ["minecraft:custom", "minecraft:damage_taken"],
            "minecart_distance": ["minecraft:custom", "minecraft:minecart_one_cm"],
            "distance_fallen": ["minecraft:custom", "minecraft:fall_one_cm"],
            "records_played": ["minecraft:custom", "minecraft:play_record"],
            
            # "distance_walked": ["minecraft:custom", "minecraft:walk_one_cm"],
            # "killed_by_skeleton": ["minecraft:killed_by", "minecraft:skeleton"],
            # "shield_damage": ["minecraft:custom", "minecraft:damage_blocked_by_shield"],
            # "distance_flown": ["minecraft:custom", "minecraft:aviate_one_cm"],
            # "jumps": ["minecraft:custom", "minecraft:jump"],
            # "distance_sprinted": ["minecraft:custom", "minecraft:sprint_one_cm"],
            # "items_enchanted": ["minecraft:custom", "minecraft:enchant_item"],
            # "": ["minecraft:custom", "minecraft:"],
            # "": ["minecraft:custom", "minecraft:"],
            # "": ["minecraft:custom", "minecraft:"],
            # "": ["minecraft:custom", "minecraft:"],
        }

        data = json.loads(request.body)
        categoryId = data.get("category")
        logger.info(f"Processing request for the {categoryId} leaderboard")

        if categoryId not in categoryIds:
            return JsonResponse({
                "status": "failure",
                "error": "Unknown leaderboard category requested",
            })
        leaderboard = get_stat(categoryIds[categoryId])

        if categoryId in ("playtime", "time_since_death"):
            leaderboard = [(name, f"{round(score/72000, 1)} hours") for (name, score) in leaderboard] 
        elif categoryId in ("minecart_distance", "distance_fallen"):
            leaderboard = [(name, f"{round(score/100, 2)} meters") for (name, score) in leaderboard]

        return JsonResponse({
            "status": "success",
            "scores": json.dumps(leaderboard)
        })
    except Exception as e:
        return JsonResponse({
            "status": "failure",
            "error": str(e)
        })