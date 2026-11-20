"""
    Compteur d'usage agrégé : compteurs de vues par page.

    - PageViewsTotal : une ligne par page (chemin) avec le compteur total.
    - PageViewsDaily : une ligne par page et par jour ("/notes|2026-11-21"),
      ce qui permet de filtrer par jour / mois / année.

    Aucune donnée personnelle : pas d'utilisateur, pas de hash, pas de timestamp
    individuel. On sait quelles pages vivent et quand, pas qui les regarde.
"""

import datetime

from flask import request, jsonify
from flask_login import login_required, current_user

from app import app, mongodb


@app.route('/track', methods=['POST'])
@login_required
def track():
    """
        Incrémente le compteur de vues de la page demandée (chemin uniquement).
    """
    data = request.get_json(silent=True) or {}
    page = str(data.get("page", ""))

    # On ne garde que des chemins sûrs : pas de query string, longueur limitée.
    if "?" in page:
        page = page.split("?")[0]
    page = page.strip()[:100]
    if not page.startswith("/"):
        return jsonify({"error": "page invalide"}), 400

    # Les admins ne sont pas comptés.
    if current_user.est_admin():
        return jsonify({"ok": True})

    today = datetime.date.today().isoformat()
    mongodb.db.PageViewsTotal.update_one(
        {"_id": page}, {"$inc": {"count": 1}}, upsert=True)
    mongodb.db.PageViewsDaily.update_one(
        {"_id": f"{page}|{today}"}, {"$inc": {"count": 1}}, upsert=True)
    return jsonify({"ok": True})


def _aggregate(coll, suffix):
    """Agrège les buckets 'page|suffix' d'une collection en {page: count}."""
    counts = {}
    for doc in coll.find({"_id": {"$regex": f"\\|{suffix}"}}):
        page = doc["_id"].split("|")[0]
        counts[page] = counts.get(page, 0) + doc["count"]
    return counts


def _time_series(granularity):
    """Série temporelle des vues agrégées par jour, mois ou année."""
    width = {"day": 10, "month": 7, "year": 4}[granularity]
    series = {}
    for doc in mongodb.db.PageViewsDaily.find({}):
        date = doc["_id"].split("|")[1]
        label = date[:width]
        series[label] = series.get(label, 0) + doc["count"]
    return [{"label": k, "count": series[k]} for k in sorted(series)]


@app.route('/admin/analytics')
@login_required
def analytics():
    """
        Api réservée aux admins : compteurs de vues agrégés par page,
        filtrables par période (day, month, year, all).
    """
    if not current_user.est_admin():
        return "Forbidden", 403

    period = request.args.get("period", "all")
    today = datetime.date.today()

    # date explicite optionnelle : "2026-11-21" (day), "2026-11" (month), "2026" (year)
    date_arg = request.args.get("date", "")

    if period == "all":
        counts = {d["_id"]: d["count"]
                  for d in mongodb.db.PageViewsTotal.find({})}
    elif period in ("day", "month", "year"):
        if date_arg:
            try:
                if period == "day":
                    suffix = datetime.date.fromisoformat(date_arg).isoformat()
                elif period == "month":
                    datetime.date.fromisoformat(date_arg + "-01")
                    suffix = date_arg
                else:
                    suffix = str(int(date_arg))
            except ValueError:
                return jsonify({"error": "date invalide"}), 400
        else:
            suffix = {"day": today.isoformat(),
                      "month": today.strftime("%Y-%m"),
                      "year": str(today.year)}[period]
        counts = _aggregate(mongodb.db.PageViewsDaily, suffix)
    else:
        return jsonify({"error": "période invalide"}), 400

    granularity = request.args.get("series", "day")
    if granularity not in ("day", "month", "year"):
        return jsonify({"error": "granularité invalide"}), 400

    pages = sorted(
        ({"page": p, "count": c} for p, c in counts.items()),
        key=lambda x: -x["count"])
    return jsonify({
        "period": period,
        "total_views": sum(p["count"] for p in pages),
        "pages": pages,
        "series": _time_series(granularity),
        "series_granularity": granularity,
    })
