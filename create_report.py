import argparse
import sqlite3
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# -----------------------------
# Вспомогательные функции
# -----------------------------

def load_table(conn, table):
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)

def format_date_ru(series):
    return series.dt.strftime("%d.%m.%Y")

# -----------------------------
# Основная логика
# -----------------------------

def generate_sales_report(db_path, start_date=None, end_date=None, output_dir="."):
    conn = sqlite3.connect(db_path)

    orders = load_table(conn, "Orders")
    order_parts = load_table(conn, "OrderParts")
    parts = load_table(conn, "AutoPart")
    categories = load_table(conn, "CategoryPart")

    # Дата заказа
    orders["Дата"] = pd.to_datetime(orders["date"], errors="coerce")

    if start_date:
        start = pd.to_datetime(start_date)
    else:
        start = orders["Дата"].min()

    if end_date:
        end = pd.to_datetime(end_date)
    else:
        end = orders["Дата"].max()

    orders = orders[(orders["Дата"] >= start) & (orders["Дата"] <= end)]

    # Объединения
    df = order_parts.merge(
        orders[["id", "Дата"]],
        left_on="order_id",
        right_on="id"
    )

    df = df.merge(
        parts[["id", "title", "category_id"]],
        left_on="part_id",
        right_on="id",
        suffixes=("", "_part")
    )

    df = df.merge(
        categories,
        left_on="category_id",
        right_on="id",
        suffixes=("", "_category")
    )

    # Выручка
    df["Выручка"] = df["count"] * df["unit_retail_price"]

    # -----------------------------
    # SUMMARY
    # -----------------------------
    summary = pd.DataFrame([{
        "Дата начала": start.strftime("%d.%m.%Y"),
        "Дата окончания": end.strftime("%d.%m.%Y"),
        "Общая выручка": round(df["Выручка"].sum(), 2),
        "Количество заказов": df["order_id"].nunique(),
        "Продано товаров (шт.)": int(df["count"].sum()),
        "Средний чек": round(df["Выручка"].sum() / df["order_id"].nunique(), 2)
    }])

    # -----------------------------
    # TOP PRODUCTS
    # -----------------------------
    top_products = (
        df.groupby("title")
        .agg({
            "count": "sum",
            "Выручка": "sum",
            "order_id": "nunique"
        })
        .reset_index()
        .rename(columns={
            "title": "Товар",
            "count": "Продано (шт.)",
            "order_id": "Количество заказов"
        })
        .sort_values("Выручка", ascending=False)
    )

    # -----------------------------
    # DAILY SALES
    # -----------------------------
    daily = (
        df.groupby(df["Дата"].dt.date)
        .agg({
            "Выручка": "sum",
            "order_id": "nunique",
            "count": "sum"
        })
        .reset_index()
        .rename(columns={
            "Дата": "Дата",
            "order_id": "Заказы",
            "count": "Товары (шт.)"
        })
    )

    daily["Дата"] = pd.to_datetime(daily["Дата"])

    # -----------------------------
    # LINES (детализация)
    # -----------------------------
    lines = df[[
        "Дата",
        "title",
        "title_category",
        "count",
        "unit_retail_price",
        "Выручка"
    ]].rename(columns={
        "Дата": "Дата заказа",
        "title": "Товар",
        "title_category": "Категория",
        "count": "Количество",
        "unit_retail_price": "Цена за единицу"
    })

    lines["Дата заказа"] = format_date_ru(lines["Дата заказа"])

    # -----------------------------
    # Сохранение Excel
    # -----------------------------
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    excel_path = os.path.join(
        output_dir,
        f"Отчет_по_продажам_{start.strftime('%d.%m.%Y')}_{end.strftime('%d.%m.%Y')}.xlsx"
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Сводка", index=False)
        top_products.to_excel(writer, sheet_name="Топ товаров", index=False)
        daily.assign(Дата=format_date_ru(daily["Дата"])).to_excel(
            writer, sheet_name="Продажи по дням", index=False
        )
        lines.to_excel(writer, sheet_name="Детализация", index=False)

    # -----------------------------
    # PNG ГРАФИК
    # -----------------------------
    plt.figure(figsize=(10, 4))
    plt.plot(daily["Дата"], daily["Выручка"])
    plt.title("Выручка по дням")
    plt.xlabel("Дата")
    plt.ylabel("Выручка")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    plt.xticks(rotation=45)
    plt.tight_layout()

    png_path = os.path.join(
        output_dir,
        f"Выручка_по_дням_{start.strftime('%d.%m.%Y')}_{end.strftime('%d.%m.%Y')}.png"
    )

    plt.savefig(png_path)
    plt.close()

    print("Отчёт успешно сформирован:")
    print(excel_path)
    print(png_path)


# -----------------------------
# CLI
# -----------------------------

if __name__ == "__main__":


    generate_sales_report(
        db_path="autoparts_shop.db",
        start_date=None,
        end_date=None,
        output_dir="H:\\"
    )
