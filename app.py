
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# 資料庫位置：部署時可透過環境變數指定
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get(
    "DB_PATH",
    str(BASE_DIR / "accounting.db")
)


def get_db():
    """連接 SQLite 資料庫"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建立記帳資料表"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                item TEXT NOT NULL,
                amount REAL NOT NULL
            )
        """)


@app.route("/")
def index():
    """顯示所有記帳紀錄"""
    with get_db() as conn:
        records = conn.execute(
            "SELECT * FROM records ORDER BY date DESC, id DESC"
        ).fetchall()

        result = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM records"
        ).fetchone()

    total = result[0]

    return render_template(
        "index.html",
        records=records,
        total=total,
        today=date.today().isoformat()
    )


@app.route("/add", methods=["POST"])
def add():
    """新增記帳紀錄"""
    record_date = request.form.get("date", "").strip()
    item = request.form.get("item", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if not record_date or not item or not amount_text:
        flash("請完整填寫所有欄位！", "error")
        return redirect(url_for("index"))

    try:
        # 確認日期格式正確
        date.fromisoformat(record_date)

        # 確認金額為有效數字
        amount = float(amount_text)

        if not (-1e12 < amount < 1e12):
            raise ValueError

    except ValueError:
        flash("日期或金額格式不正確！", "error")
        return redirect(url_for("index"))

    with get_db() as conn:
        conn.execute(
            "INSERT INTO records (date, item, amount) VALUES (?, ?, ?)",
            (record_date, item, amount)
        )

    flash("記帳紀錄新增成功！", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    """刪除記帳紀錄"""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM records WHERE id = ?",
            (record_id,)
        )

    flash("紀錄已刪除！", "success")
    return redirect(url_for("index"))


# 啟動時建立資料表
init_db()


if __name__ == "__main__":
    app.run(debug=True)
