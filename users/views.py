import json
import random
import traceback

from django.core.cache import cache
from django.views.decorators.http import require_POST

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from mcsmp import Client
import asyncio

# from mcrcon import MCRcon
from aiomcrcon import Client as rconClient

from django.conf import settings

from users.forms import MySignupForm
from users.models import PlayerProfile

import logging

logger = logging.getLogger(__name__)

# Create your views here.
def login_view(request):
    if request.method == 'POST':
        logger.info("Handling a request for user login")
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                logger.info("User logged in: " + username)
                login(request, user)
                return redirect('home')
        else:
            logger.warning("Received a POSTed login form that is NOT VALID" + form.errors)
    else:
        logger.info("Handling a request for the blank login page")
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logger.info("logging out user: " + request.user.username)
    logout(request)
    return redirect('home')

# def new_user_a(request):
#     form = MySignupForm()
#     return render(request, 'users/new_user_a.html', {'form': form})

@require_POST
async def create_pin_view(request):
    logger.info("Processing request for a new signup PIN")
    try:
        reqBody = json.loads(request.body)
        unverifiedMcUsername = reqBody.get('mcusername')

        # check if a player profile already exists for this mc account
        profileConflict = await PlayerProfile.objects.filter(mc_username=unverifiedMcUsername).aexists()
        if profileConflict:
            return JsonResponse({
                "status": "failure",
                "error": "profile already exists",
            })

        # overview: open connection, check if player is online, then generate pin, send to player, close connection

        client = Client(settings.MC_IP, settings.MC_PORT, settings.MC_SMP_TOKEN)
        await client.connect()
        players = await client.players.get()
        await client.close()

        # print("Player list: " + str(players))

        player_uuid = ""
        for p in players:
            if p.name == unverifiedMcUsername:
                player_uuid = p.id
            # else:
            #     print("Player not a match. name=" + str(p.name) + ", looking for " + unverifiedMcUsername)

        if player_uuid == "":
            return JsonResponse({
                "status": "failure",
                "error": "player not found, are you logged into the server?",
            })

        pin = str(random.randint(1000, 9999))
        cache_key = f"mc_registration_{unverifiedMcUsername}"
        cache.set(cache_key, pin, timeout=900)

        # TODO send pin to player
        # with MCRcon(settings.MC_IP, settings.MC_RCON_PW, port=settings.MC_RCON_PORT) as svr:
        async with rconClient(settings.MC_IP, settings.MC_RCON_PORT, settings.MC_RCON_PW) as client:
            await client.connect()
            send_pin_command = f'tellraw {unverifiedMcUsername} {{"text":"Your PIN is {pin}","color":"aqua"}}'
            await client.send_cmd(send_pin_command)
            await client.close()

        print(f"new pin ({pin}) generated for user {unverifiedMcUsername} with timeout {900}")

        return JsonResponse({
            "status": "success",
            "player_uuid": player_uuid,
        }) 
    except Exception as e:
        logger.error("Error encountered in create_pin_view: " + str(e))
        traceback.print_exc()
        return JsonResponse({
            "status": "failure",
            "error": "i'm afraid that's an HTTP 500"
        }, status=500)

def signup_view(request):
    if request.method == "POST":
        logger.info("Processing POST request for new user creation")
        form = MySignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            logger.error("Request for user creation contained form data that is NOT VALID: " + form.errors)
            return render(request, 'users/new_user_a.html', {"form": form})
            # return JsonResponse({"status": "failure", "error": "Bad form data: " + str(form.errors)}, status=400)
    else:
        logger.info("Processing request for the blank signup page")
        form = MySignupForm()
        return render(request, 'users/new_user_a.html', {"form": form})
        # return JsonResponse({"status": "failure", "error": "Expected POST request, got something else."}, status=405)