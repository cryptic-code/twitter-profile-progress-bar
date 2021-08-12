from os import getenv
from typing import Any
from twitter import User
from config import Config
from actions import calculate_progress, update_progress, update_cached_avatar
from deta import app, Deta

deta = Deta(getenv("DETA_PROJECT_KEY"))
db = deta.Base("random")
db_key = "twitter-progress-bar"

@app.lib.run(action="update")
@app.lib.cron()
def cron_job(event: Any):
    """Run at set intervals and update image and cache as required.

    Parameters
    ----------
    event : Any
        An object passed by Deta that includes the event's payload (if any) and its type.
    """
    user = User()
    cache: dict = db.get(db_key)
    percent_progress, slice_angle = calculate_progress(user.followers_count, Config.track_mark)

    if not user.profile_img_url == cache["avatar_url"]:
        cache = update_cached_avatar(user, cache)
        cache = update_progress(user, cache, percent_progress, slice_angle)
        db.put(cache, db_key)
        return "Update Complete"
    elif not percent_progress == cache["percent_progress"]:
        cache = update_progress(user, cache, percent_progress, slice_angle)
        db.put(cache, db_key)
        return "Update Complete"
    else:
        return "No Updates"

@app.lib.run(action="reset-count")
def run_now(event):
    """ Manipulate cached progress to force update on next CRON. """
    db.update({"percent_progress": 0}, db_key)
    return "Count Reset"

@app.lib.run(action="full-reset")
def full_reset(event):
    """ Empty the entire cache. """
    db.put({"percent_progress": 0, "og_avatar": "", "avatar_url": ""}, db_key)
    return "Full Reset"
