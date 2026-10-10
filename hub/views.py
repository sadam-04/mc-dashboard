import json

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from pisscraft import settings

from mcrcon import MCRcon
from mcsmp.client import Client

from django.contrib.auth.models import User

import asyncio

from users.models import PlayerProfile


@login_required
def home(request):
    return render(request, 'hub/home.html')

@login_required
@ensure_csrf_cookie
def places(request):
    return render(request, 'hub/places.html')

@login_required
def map_view(request):
    return render(request, 'hub/map.html')

@login_required
@require_POST
def say_hello_view(request):
    django_user = request.user.username
    # mc_username = settings.MC_USER_ASSOCS.get(django_user)
    mc_username = PlayerProfile.objects.get(user=request.user).mc_username
    if not mc_username:
        return JsonResponse({"status": "failure", "error": "No Minecraft account linked."}, status=403)

    cmd = f"tellraw @a \"{mc_username} says hi!\""

    try:
        with MCRcon('10.6.7.32', 'amoge', port=25575) as svr:
            response = svr.command(cmd)
            return JsonResponse({"status": "success", "mc_response": response})
    except Exception as e:
        return JsonResponse({"status": "failure", "error": "Rcon connection failed: {str(e)}"},  status=500)

@login_required
@require_POST
def teleport(request):
    tpLocs = {
        "fall-ow": "33921.5 71 5784.5",
        "gtc-ow": "36755.5 70 3630.5",
        "gtc-ne": "4583.5 75 443.5",
        "tt-ow": "-350.5 65 -1942.5",
        "tt-ne": "-35.5 80 -246.5",
        "rb-ow": "-3121 176 -1889.5",
        "rb-ne": "-388 101 -242.5",
        "cnb-ow": "-2814.5 74 -6867.5",
        "cnb-ne": "-359 34 -848",
        "porc-ow": "-3866.5 72 1763.5",
        "porc-ne": "-488 61 217.5",
        "s2-ow": "-8588.5 64 -4154.5",
        "s2-ne": "-1086.5 58 -527",
        "2c-ow": "4172.5 63 1355.5",
        "2c-ne": "513 80 180.5",
        "bn-ow": "10332.5 69 -2107.5",
    }

    print("Request body object:" + str(request.body))

    data = json.loads(request.body)

    tpId = data.get("tpdest")
    tpDim = ""
    if tpId[-2:] == "ne":
        tpDim = "the_nether"
    else:
        tpDim = "overworld"

    tpLoc = tpLocs.get(tpId)

    # django_user = request.user.username
    # mc_username = settings.MC_USER_ASSOCS.get(django_user)
    mc_username = PlayerProfile.objects.get(user=request.user).mc_username

    if not mc_username:
        return JsonResponse({"status": "failure", "error": "i couldn't find your minecraft account oopsy"}, status=403)

    cmd = f"execute as {mc_username} in minecraft:{tpDim} run tp {mc_username} {tpLoc}"

    try:
        with MCRcon('10.6.7.32', 'amoge', port=25575) as svr:
            response = svr.command(cmd)
            return JsonResponse({"status": "success", "mc_response": response})
    except Exception as e:
        return JsonResponse({"status": "failure", "error": f"Rcon connection failed: {str(e)}"},  status=500)

@login_required
@require_POST
async def status_view(request):
    # print("yoooooo")
    client = Client(settings.MC_IP, settings.MC_PORT, settings.MC_SMP_TOKEN)
    try:
        # print("##### START")
        await client.connect()
        players = await client.players.get()
        motd = await client.server_settings.motd()
        await client.close()
        # print("###### END")
    except RuntimeError as e:
        # print("CREEEEEEEEEEEEEEEEEEEEEEEE")
        return JsonResponse({
            "status": "failure",
            "error": str(e),
        })

    namesList = list(map(lambda p: (p.name, p.id), players))
    lastFormatterIdx = motd.rfind('§')
    chopped_motd = motd[lastFormatterIdx + 2:] if lastFormatterIdx != -1 else motd
    
    return JsonResponse({
        "status": "success",
        "players": json.dumps(namesList),
        "motd": chopped_motd
    })
    