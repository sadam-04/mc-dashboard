import json
import logging

from mcdashboard.settings import BASE_DIR, MC_ROOT_DIR

logger = logging.getLogger(__name__)

def get_stat(datapoint_addr):
    leaderboard = {}
    filenames = {}

    file_prefix = MC_ROOT_DIR

    with open(file_prefix / "usercache.json", "r", encoding="utf-8") as file:
        users = json.load(file)
        for user in users:
            filenames[user["name"]] = f"{user["uuid"]}.json"

    for friendly, fn in filenames.items():
        try:
            with open(file_prefix / "world/players/stats" / fn, "r", encoding="utf-8") as file:
                stats = json.load(file)
                seeker = stats["stats"]
                for key in datapoint_addr:
                    seeker = seeker[key]
                leaderboard[friendly] = seeker
        except Exception as e:
            logger.warning(f"Unable to get stat value {datapoint_addr[-1]} for player {friendly} ({fn}). Assuming 0: {str(e)}")
            leaderboard[friendly] = 0

    lb_sorted = sorted(leaderboard.items(), key=lambda item: -item[1])
    return lb_sorted

if __name__ == "__main__":
    lb = get_stat(["minecraft:custom", "minecraft:play_time"])
    for name, score in lb:
        print(f"{name:<20}: {score}")