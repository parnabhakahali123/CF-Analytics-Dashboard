from flask import Flask, render_template, request
import requests
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/profile", methods=["POST"])
def profile():

    username = request.form.get("username")

    try:

        # ---------------- USER INFO ----------------

        user_url = (
            f"https://codeforces.com/api/user.info"
            f"?handles={username}"
        )

        user_response = requests.get(
            user_url,
            timeout=5
        )

        user_data = user_response.json()

        if user_data.get("status") != "OK":

            return render_template(
                "index.html",
                error="User not found!"
            )

        user = user_data["result"][0]

        rank_class = (
            user.get(
                "rank",
                "newbie"
            )
            .replace(" ", "-")
        )

        # ---------------- RATING HISTORY ----------------

        rating_url = (
            f"https://codeforces.com/api/user.rating"
            f"?handle={username}"
        )

        rating_response = requests.get(
            rating_url,
            timeout=5
        )

        rating_data = rating_response.json()

        contests = []
        ratings = []
        recent_contests = []

        if rating_data.get("status") == "OK":

            for contest in rating_data["result"]:

                contests.append(
                    contest["contestName"]
                )

                ratings.append(
                    contest["newRating"]
                )

            recent_contests = (
                rating_data["result"][-5:]
            )

            recent_contests.reverse()

        contest_count = len(contests)

        # ---------------- SUBMISSION HEATMAP ----------------

        submissions_url = (
            f"https://codeforces.com/api/user.status"
            f"?handle={username}"
        )

        submissions_response = requests.get(
            submissions_url,
            timeout=10
        )

        submissions_data = (
            submissions_response.json()
        )

        activity = defaultdict(int)

        three_years_ago = (
            datetime.utcnow()
            - timedelta(days=365 * 3)
        ).date()

        if (
            submissions_data.get("status")
            == "OK"
        ):

            for submission in (
                submissions_data["result"]
            ):

                timestamp = submission[
                    "creationTimeSeconds"
                ]

                date = (
                    datetime
                    .utcfromtimestamp(
                        timestamp
                    )
                    .date()
                )

                if date >= three_years_ago:

                    activity[date] += 1

        today = datetime.utcnow().date()

        heatmap_data = []

        for i in reversed(range(365 * 3)):

            current_day = (
                today
                - timedelta(days=i)
            )

            count = activity.get(
                current_day,
                0
            )

            if count == 0:
                level = 0
            elif count <= 3:
                level = 1
            elif count <= 7:
                level = 2
            elif count <= 15:
                level = 3
            else:
                level = 4

            heatmap_data.append({
                "date": str(current_day),
                "count": count,
                "level": level
            })

        return render_template(
            "profile.html",
            user=user,
            contests=contests,
            ratings=ratings,
            contest_count=contest_count,
            rank_class=rank_class,
            recent_contests=recent_contests,
            heatmap_data=heatmap_data
        )

    except requests.exceptions.RequestException:

        return render_template(
            "index.html",
            error="Network error! Please try again."
        )

    except Exception as e:

        print(e)

        return render_template(
            "index.html",
            error="Something went wrong!"
        )

@app.route("/compare", methods=["POST"])
def compare():

    user1 = request.form.get("user1")
    user2 = request.form.get("user2")

    try:

        # Fetch both users
        info_url = (
            f"https://codeforces.com/api/user.info"
            f"?handles={user1};{user2}"
        )

        info_response = requests.get(
            info_url,
            timeout=5
        )

        info_data = info_response.json()

        if info_data.get("status") != "OK":

            return render_template(
                "index.html",
                error="One or both users not found!"
            )

        users = info_data["result"]

        # Add extra information
        for user in users:

            rank = user.get(
                "rank",
                "newbie"
            )

            user["rank_class"] = (
                rank.replace(
                    " ",
                    "-"
                )
            )

            # Contest count
            rating_url = (
                f"https://codeforces.com/api/user.rating"
                f"?handle={user['handle']}"
            )

            rating_response = requests.get(
                rating_url,
                timeout=5
            )

            rating_data = (
                rating_response.json()
            )

            if (
                rating_data.get("status")
                == "OK"
            ):

                user["contest_count"] = len(
                    rating_data["result"]
                )

            else:

                user["contest_count"] = 0

        # Sort by current rating
        users = sorted(
            users,
            key=lambda x: x.get(
                "rating",
                0
            ),
            reverse=True
        )

        return render_template(
            "compare.html",
            users=users
        )

    except requests.exceptions.RequestException:

        return render_template(
            "index.html",
            error="Network error! Please try again."
        )

    except Exception as e:

        print(e)

        return render_template(
            "index.html",
            error="Something went wrong!"
        )


if __name__ == "__main__":
    app.run(
        debug=True
    )