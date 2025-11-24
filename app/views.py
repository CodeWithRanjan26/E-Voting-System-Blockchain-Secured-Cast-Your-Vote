import datetime
import json
import requests
import csv
from io import StringIO
from flask import Blueprint, render_template, redirect, request, flash, make_response

# -----------------------------
# Create Blueprint
# -----------------------------
views = Blueprint("views", __name__)

# Blockchain backend API address
CONNECTED_SERVICE_ADDRESS = "http://127.0.0.1:5000/api"

# Allowed political parties
POLITICAL_PARTIES = [
    "Democratic Party",
    "Republican Party",
    "Socialist Party"
]

# Valid voter IDs
VOTER_IDS = [
    'VOID001', 'VOID002', 'VOID003', 'VOID004', 'VOID005',
    'VOID006', 'VOID007', 'VOID008', 'VOID009', 'VOID010',
    'VOID011', 'VOID012', 'VOID013', 'VOID014', 'VOID015'
]

# Local variables
vote_check = []
posts = []


# ----------------------------------------------------
# Fetch blockchain posts
# ----------------------------------------------------
def fetch_posts():
    global posts
    try:
        response = requests.get(f"{CONNECTED_SERVICE_ADDRESS}/chain")
        if response.status_code == 200:
            chain = response.json()
            content = []

            for block in chain["chain"]:
                for tx in block["transactions"]:
                    tx["index"] = block["index"]
                    tx["hash"] = block["previous_hash"]
                    content.append(tx)

            posts = sorted(
                content,
                key=lambda k: k.get("timestamp", 0),
                reverse=True
            )
    except Exception as e:
        print("Chain fetch error:", e)


# ----------------------------------------------------
# Index page
# ----------------------------------------------------
@views.route("/")
def index():
    fetch_posts()
    vote_gain = [post.get("party", "") for post in posts]

    return render_template(
        "index.html",
        title="E-Voting System using Blockchain",
        posts=posts,
        vote_gain=vote_gain,
        node_address=CONNECTED_SERVICE_ADDRESS,
        readable_time=timestamp_to_string,
        political_parties=POLITICAL_PARTIES,
        voter_ids=VOTER_IDS
    )


# ----------------------------------------------------
# Submit vote
# ----------------------------------------------------
@views.route("/submit", methods=["POST"])
def submit():
    party = request.form.get("party")
    voter_id = request.form.get("voter_id")

    if not party or not voter_id:
        flash("Invalid request!", "error")
        return redirect("/")

    if voter_id not in VOTER_IDS:
        flash("Invalid Voter ID!", "error")
        return redirect("/")

    if voter_id in vote_check:
        flash(f"Voter ID {voter_id} has already voted!", "error")
        return redirect("/")

    vote_check.append(voter_id)

    tx_obj = {
        "voter_id": voter_id,
        "party": party,
        "timestamp": datetime.datetime.now().timestamp()
    }

    try:
        requests.post(
            f"{CONNECTED_SERVICE_ADDRESS}/new_transaction",
            json=tx_obj,
            headers={"Content-Type": "application/json"}
        )
    except Exception:
        flash("Blockchain node offline!", "error")
        return redirect("/")

    flash(f"Vote submitted for {party}", "success")
    return redirect("/")


# ----------------------------------------------------
# Mine a block manually
# ----------------------------------------------------
@views.route("/mine_block")
def mine_block():
    try:
        r = requests.get(f"{CONNECTED_SERVICE_ADDRESS}/mine")
        if r.status_code == 200:
            flash("Block mined successfully!", "success")
        else:
            flash("Mining failed!", "error")
    except Exception:
        flash("Blockchain node offline!", "error")

    return redirect("/")


# ----------------------------------------------------
# View chain in raw JSON
# ----------------------------------------------------
@views.route("/view_chain")
def view_chain():
    try:
        r = requests.get(f"{CONNECTED_SERVICE_ADDRESS}/chain")
        if r.status_code == 200:
            return r.text
    except:
        return "Could not reach blockchain node."
    return "Could not retrieve chain."


# ----------------------------------------------------
# Convert timestamp
# ----------------------------------------------------
def timestamp_to_string(epoch_time):
    try:
        return datetime.datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M")
    except:
        return "N/A"


# ============================================================
#                   ⭐ NEW ADMIN + RESULTS APIs ⭐
# ============================================================

# ----------------------------------------------------
# Compute vote results from chain
# ----------------------------------------------------
def compute_results_from_chain():
    counts = {}
    total = 0
    try:
        r = requests.get(f"{CONNECTED_SERVICE_ADDRESS}/chain")
        if r.status_code != 200:
            return {"counts": {}, "total": 0}

        data = r.json()
        for block in data.get("chain", []):
            for tx in block.get("transactions", []):
                party = tx.get("party")
                if not party:
                    continue
                counts[party] = counts.get(party, 0) + 1
                total += 1

    except Exception as e:
        print("Results fetch error:", e)

    return {"counts": counts, "total": total}


# ----------------------------------------------------
# JSON results API (for charts)
# ----------------------------------------------------
@views.route("/results")
def results_json():
    res = compute_results_from_chain()
    return {
        "counts": res["counts"],
        "total": res["total"]
    }


# ----------------------------------------------------
# Admin results page
# ----------------------------------------------------
@views.route("/admin")
def admin_page():
    res = compute_results_from_chain()
    return render_template(
        "admin.html",
        counts=res["counts"],
        total=res["total"]
    )


# ----------------------------------------------------
# Export results to CSV
# ----------------------------------------------------
@views.route("/export_results")
def export_results():
    res = compute_results_from_chain()
    counts = res["counts"]

    rows = [["party", "votes"]]
    for party, v in counts.items():
        rows.append([party, v])

    s = StringIO()
    writer = csv.writer(s)
    writer.writerows(rows)

    response = make_response(s.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=vote_results.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
