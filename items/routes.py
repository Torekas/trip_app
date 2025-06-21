import io
import re
import pandas as pd
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    current_app, request, jsonify, send_file
)
from flask_login import login_required, current_user
from bson import ObjectId

from items.forms import ItemForm, UploadForm

items_bp = Blueprint("items", __name__)


@items_bp.route("/", methods=["GET"])
@login_required
def list_items():
    """
    Render the Excel-style table of items, grouped by category,
    parsing any trailing " x<number>" out of item_name.
    """
    raw_items = list(current_app.items_col.find({
        "user_id": ObjectId(current_user.id)
    }))

    processed = []
    pattern = re.compile(r"\s*x\s*(\d+)$", flags=re.IGNORECASE)
    for it in raw_items:
        raw_name = it["item_name"]
        m = pattern.search(raw_name)
        if m:
            qty = int(m.group(1))
            name = pattern.sub("", raw_name).strip()
        else:
            qty = it.get("quantity", 1)
            name = raw_name
        processed.append({
            **it,
            "parsed_name": name,
            "parsed_quantity": qty
        })

    grouped: dict[str, list[dict]] = {}
    for it in processed:
        grouped.setdefault(it["category"], []).append(it)

    return render_template("items.html", grouped=grouped)


@items_bp.route("/item/api", methods=["POST"])
@login_required
def add_item_api():
    """
    JSON POST to add an item inline.
    Expects { category, item_name, quantity }.
    Returns the new item’s _id, category, parsed_name, parsed_quantity.
    """
    data = request.get_json() or {}
    category = (data.get("category") or "").strip()
    item_name = (data.get("item_name") or "").strip()
    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if not category or not item_name:
        return jsonify(error="category and item_name are required"), 400

    raw_name = f"{item_name} x {quantity}" if quantity and "x" not in item_name.lower() else item_name

    doc = {
        "user_id": ObjectId(current_user.id),
        "category": category,
        "item_name": raw_name,
        "quantity": quantity
    }
    res = current_app.items_col.insert_one(doc)
    new_id = str(res.inserted_id)

    pattern = re.compile(r"\s*x\s*(\d+)$", flags=re.IGNORECASE)
    m = pattern.search(raw_name)
    if m:
        parsed_quantity = int(m.group(1))
        parsed_name = pattern.sub("", raw_name).strip()
    else:
        parsed_quantity = quantity
        parsed_name = raw_name

    return jsonify({
        "_id": new_id,
        "category": category,
        "parsed_name": parsed_name,
        "parsed_quantity": parsed_quantity
    }), 200


@items_bp.route("/item/<item_id>/api", methods=["PATCH"])
@login_required
def update_item_api(item_id: str):
    """
    JSON PATCH to update an existing item inline.
    Accepts { parsed_name, parsed_quantity }.
    """
    data = request.get_json() or {}
    updates = {}
    if "parsed_name" in data:
        updates["item_name"] = data["parsed_name"].strip()
    if "parsed_quantity" in data:
        try:
            updates["quantity"] = int(data["parsed_quantity"])
        except ValueError:
            return jsonify(error="Quantity must be an integer"), 400

    if not updates:
        return jsonify(error="No valid fields provided"), 400

    result = current_app.items_col.update_one(
        {"_id": ObjectId(item_id), "user_id": ObjectId(current_user.id)},
        {"$set": updates}
    )
    if result.matched_count == 0:
        return jsonify(error="Item not found"), 404

    return jsonify(
        parsed_name=updates.get("item_name"),
        parsed_quantity=updates.get("quantity")
    ), 200


@items_bp.route("/item/<item_id>/api", methods=["DELETE"])
@login_required
def delete_item_api(item_id: str):
    """
    JSON DELETE to remove an item inline.
    """
    result = current_app.items_col.delete_one({
        "_id": ObjectId(item_id),
        "user_id": ObjectId(current_user.id)
    })
    if result.deleted_count == 0:
        return jsonify(error="Item not found"), 404
    return jsonify(success=True), 200


@items_bp.route("/clear", methods=["POST"])
@login_required
def clear_items():
    """
    Delete *all* items for the current user.
    """
    current_app.items_col.delete_many({"user_id": ObjectId(current_user.id)})
    return jsonify(success=True), 200


@items_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """
    Upload an Excel file and import each column’s non-empty cells
    as items with quantity=1, dynamically determining categories.
    """
    form = UploadForm()
    if form.validate_on_submit():
        storage = form.file.data
        try:
            df = pd.read_excel(io.BytesIO(storage.read()))
            headers = [h.strip() for h in df.columns]
            username = current_user.username.lower()

            for header in headers:
                col = df[header]
                lower = header.lower()
                if username in lower:
                    category = header[: lower.rfind(username)].strip()
                else:
                    category = header

                for cell in col.dropna():
                    name = str(cell).strip()
                    if not name:
                        continue
                    current_app.items_col.insert_one({
                        "user_id": ObjectId(current_user.id),
                        "category": category,
                        "item_name": name,
                        "quantity": 1
                    })

            flash("Excel data imported", "success")
        except Exception as e:
            current_app.logger.exception("Failed to parse Excel")
            flash(f"Upload failed: {e}", "danger")
        return redirect(url_for("items.list_items"))

    return render_template("upload.html", form=form)


@items_bp.route("/download", methods=["GET"])
@login_required
def download_packing_list():
    """
    Rebuild the Excel file in-memory from the current user's items,
    grouping by category into columns, and download 1:1.
    """
    # 1) Fetch & parse
    raw_items = list(current_app.items_col.find({
        "user_id": ObjectId(current_user.id)
    }))
    pattern = re.compile(r"\s*x\s*(\d+)$", flags=re.IGNORECASE)
    grouped: dict[str, list[str]] = {}
    for it in raw_items:
        raw_name = it["item_name"]
        m = pattern.search(raw_name)
        if m:
            name = pattern.sub("", raw_name).strip()
            qty = int(m.group(1))
            entry = f"{name} x {qty}"
        else:
            entry = raw_name
        grouped.setdefault(it["category"], []).append(entry)

    # 2) Build DataFrame: one column per category
    if grouped:
        max_len = max(len(lst) for lst in grouped.values())
        padded = {
            cat: lst + [""] * (max_len - len(lst))
            for cat, lst in grouped.items()
        }
        df = pd.DataFrame(padded)
    else:
        df = pd.DataFrame()

    # 3) Write to an in-memory Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Packing List")
    output.seek(0)

    # 4) Stream it back
    filename = f"{current_user.username}_packing_list.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,                     # <-- changed here
        mimetype=(
            "application/vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        )
    )
