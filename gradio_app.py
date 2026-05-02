import html
import re
from collections import Counter

import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd

from database import SessionLocal
import models


STOPWORDS = {
    "the", "and", "is", "a", "an", "of", "to", "in", "it", "that",
    "for", "on", "with", "as", "be", "at", "by", "this", "are", "was",
    "i", "me", "my", "we", "our", "you", "your", "he", "his", "him",
    "they", "them", "their", "not", "but", "from", "or", "if", "so",
    "what", "when", "where", "who", "why", "how", "all", "one", "out",
    "up", "down", "there", "than", "then", "into", "can", "could"
}


def get_df():
    db = SessionLocal()
    try:
        quotes = db.query(models.Quote).order_by(models.Quote.id.desc()).all()
        return pd.DataFrame([
            {
                "id": q.id,
                "text": q.text,
                "author": q.author,
                "category": q.category
            }
            for q in quotes
        ])
    finally:
        db.close()


def category_update(df, current="All"):
    if df.empty:
        return gr.update(choices=["All"], value="All")

    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())

    if current not in categories:
        current = "All"

    return gr.update(choices=categories, value=current)


def build_stats(df):
    if df.empty:
        total, authors, categories, avg_len = 0, 0, 0, 0
    else:
        total = len(df)
        authors = df["author"].nunique()
        categories = df["category"].nunique()
        avg_len = round(df["text"].str.len().mean(), 1)

    return f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0;">
    <div style="background:white;padding:22px;border-radius:20px;box-shadow:0 8px 25px rgba(0,0,0,0.08);">
        <h2 style="margin:0;color:#4f46e5;font-size:32px;">{total}</h2>
        <p style="margin:6px 0 0;color:#6b7280;">Total Quotes</p>
    </div>
    <div style="background:white;padding:22px;border-radius:20px;box-shadow:0 8px 25px rgba(0,0,0,0.08);">
        <h2 style="margin:0;color:#4f46e5;font-size:32px;">{authors}</h2>
        <p style="margin:6px 0 0;color:#6b7280;">Authors</p>
    </div>
    <div style="background:white;padding:22px;border-radius:20px;box-shadow:0 8px 25px rgba(0,0,0,0.08);">
        <h2 style="margin:0;color:#4f46e5;font-size:32px;">{categories}</h2>
        <p style="margin:6px 0 0;color:#6b7280;">Categories</p>
    </div>
    <div style="background:white;padding:22px;border-radius:20px;box-shadow:0 8px 25px rgba(0,0,0,0.08);">
        <h2 style="margin:0;color:#4f46e5;font-size:32px;">{avg_len}</h2>
        <p style="margin:6px 0 0;color:#6b7280;">Avg. Length</p>
    </div>
</div>
"""


def empty_box(text):
    return f"""
<div style="padding:32px;border-radius:20px;background:#f9fafb;border:1px dashed #d1d5db;text-align:center;color:#6b7280;font-size:18px;">
    {html.escape(text)}
</div>
"""


def make_card(row):
    quote_id = html.escape(str(row["id"]))
    text = html.escape(str(row["text"]))
    author = html.escape(str(row["author"]))
    category = html.escape(str(row["category"]))

    return f"""
<div style="position:relative;background:white;padding:26px;border-radius:24px;box-shadow:0 10px 30px rgba(0,0,0,0.09);border:1px solid #e5e7eb;min-height:220px;">
    <div style="position:absolute;top:16px;right:18px;color:#9ca3af;font-size:13px;">#{quote_id}</div>
    <div style="font-size:20px;line-height:1.55;font-weight:700;color:#111827;margin:18px 0 28px;">
        “{text}”
    </div>
    <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">
        <span style="color:#374151;font-weight:700;">— {author}</span>
        <span style="background:#eef2ff;color:#4338ca;padding:7px 12px;border-radius:999px;font-size:12px;font-weight:700;">
            {category}
        </span>
    </div>
</div>
"""


def filter_df(df, category="All", keyword=""):
    if df.empty:
        return df

    if category and category != "All":
        df = df[df["category"] == category]

    if keyword:
        keyword = keyword.lower().strip()
        df = df[
            df["text"].str.lower().str.contains(keyword, na=False)
            | df["author"].str.lower().str.contains(keyword, na=False)
            | df["category"].str.lower().str.contains(keyword, na=False)
        ]

    return df


def random_quote(category="All"):
    df = get_df()

    if df.empty:
        return empty_box("No quotes found. Use /docs and crawl quotes first.")

    df = filter_df(df, category)

    if df.empty:
        return empty_box("No quotes in this category.")

    row = df.sample(1).iloc[0]

    text = html.escape(str(row["text"]))
    author = html.escape(str(row["author"]))
    category = html.escape(str(row["category"]))

    return f"""
<div style="padding:38px;border-radius:30px;background:linear-gradient(135deg,#fff7ed,#eef2ff);box-shadow:0 16px 40px rgba(0,0,0,0.12);border:1px solid #e5e7eb;">
    <div style="display:inline-block;background:#4f46e5;color:white;padding:8px 14px;border-radius:999px;font-size:13px;font-weight:700;margin-bottom:22px;">
        Random Quote
    </div>
    <div style="font-size:34px;line-height:1.45;font-weight:800;color:#111827;margin-bottom:24px;">
        “{text}”
    </div>
    <div style="font-size:20px;color:#374151;margin-bottom:14px;">— {author}</div>
    <div style="display:inline-block;background:#ffedd5;color:#c2410c;padding:8px 15px;border-radius:999px;font-weight:800;">
        {category}
    </div>
</div>
"""


def show_gallery(category="All", keyword="", limit=9):
    df = get_df()

    if df.empty:
        return empty_box("No quotes found. Use crawler first.")

    df = filter_df(df, category, keyword)

    if df.empty:
        return empty_box("No matching quotes found.")

    df = df.head(int(limit))

    cards = "".join(make_card(row) for _, row in df.iterrows())

    return f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:18px;">
    {cards}
</div>
"""


def refresh_screen(home_category, gallery_category, keyword, limit):
    df = get_df()

    return (
        build_stats(df),
        category_update(df, home_category),
        category_update(df, gallery_category),
        random_quote(home_category),
        show_gallery(gallery_category, keyword, limit)
    )


def add_quote(text, author, category):
    if not text or not author or not category:
        return "Please fill in all fields."

    db = SessionLocal()
    try:
        quote = models.Quote(
            text=text.strip(),
            author=author.strip(),
            category=category.strip()
        )
        db.add(quote)
        db.commit()
        return "Quote added successfully."
    finally:
        db.close()


def update_quote(quote_id, text, author, category):
    if not quote_id:
        return "Please enter quote ID."

    db = SessionLocal()
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == int(quote_id)).first()

        if not quote:
            return "Quote not found."

        if text:
            quote.text = text.strip()
        if author:
            quote.author = author.strip()
        if category:
            quote.category = category.strip()

        db.commit()
        return "Quote updated successfully."
    finally:
        db.close()


def delete_quote(quote_id):
    if not quote_id:
        return "Please enter quote ID."

    db = SessionLocal()
    try:
        quote = db.query(models.Quote).filter(models.Quote.id == int(quote_id)).first()

        if not quote:
            return "Quote not found."

        db.delete(quote)
        db.commit()
        return "Quote deleted successfully."
    finally:
        db.close()


def word_count_plot():
    df = get_df()
    fig = plt.figure(figsize=(10, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    text = " ".join(df["text"].tolist()).lower()
    words = re.findall(r"[a-zA-Z']+", text)
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    data = Counter(words).most_common(10)

    if not data:
        plt.text(0.5, 0.5, "No words to analyze", ha="center", va="center")
        plt.axis("off")
        return fig

    labels = [x[0] for x in data]
    values = [x[1] for x in data]

    plt.bar(labels, values)
    plt.title("Top 10 Most Frequent Words")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=35)
    plt.tight_layout()

    return fig


def category_plot():
    df = get_df()
    fig = plt.figure(figsize=(8, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    data = df["category"].value_counts()

    plt.pie(data.values, labels=data.index, autopct="%1.1f%%")
    plt.title("Quotes by Category")
    plt.tight_layout()

    return fig


def author_plot():
    df = get_df()
    fig = plt.figure(figsize=(10, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    data = df["author"].value_counts().head(10)

    plt.barh(data.index, data.values)
    plt.title("Top Authors by Number of Quotes")
    plt.xlabel("Number of Quotes")
    plt.tight_layout()

    return fig


def length_plot():
    df = get_df()
    fig = plt.figure(figsize=(10, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    lengths = df["text"].str.len()

    plt.hist(lengths, bins=10)
    plt.title("Quote Length Distribution")
    plt.xlabel("Characters")
    plt.ylabel("Number of Quotes")
    plt.tight_layout()

    return fig


def build_gradio():
    with gr.Blocks() as demo:
        gr.HTML("""
<div style="padding:34px;border-radius:30px;background:linear-gradient(135deg,#111827,#4f46e5,#fb923c);color:white;margin-bottom:22px;box-shadow:0 14px 40px rgba(0,0,0,0.18);">
    <h1 style="font-size:40px;margin:0 0 10px;">Quotes Management and Analysis</h1>
    <p style="font-size:17px;margin:0;opacity:0.92;">
        FastAPI + SQLite + Gradio dashboard with visual quote cards, CRUD management, and text analytics.
    </p>
</div>
""")

        stats_output = gr.HTML()

        with gr.Row():
            refresh_btn = gr.Button("Refresh Dashboard", variant="primary")
            random_btn = gr.Button("Generate Random Quote", variant="secondary")

        with gr.Tabs():
            with gr.Tab("Home"):
                home_category = gr.Dropdown(
                    label="Category",
                    choices=["All"],
                    value="All"
                )
                random_output = gr.HTML()

            with gr.Tab("Quote Gallery"):
                with gr.Row():
                    gallery_category = gr.Dropdown(
                        label="Category",
                        choices=["All"],
                        value="All"
                    )
                    keyword_input = gr.Textbox(
                        label="Search",
                        placeholder="Search by quote, author, or category"
                    )
                    limit_input = gr.Slider(
                        label="Cards Limit",
                        minimum=3,
                        maximum=24,
                        step=3,
                        value=9
                    )

                gallery_btn = gr.Button("Show Quote Cards", variant="primary")
                gallery_output = gr.HTML()

            with gr.Tab("Manage Quotes"):
                gr.Markdown("## Add Quote")

                add_text = gr.Textbox(label="Quote Text", lines=4)
                add_author = gr.Textbox(label="Author")
                add_category = gr.Textbox(label="Category")
                add_btn = gr.Button("Add Quote", variant="primary")
                add_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("## Update Quote")

                update_id = gr.Number(label="Quote ID", precision=0)
                update_text = gr.Textbox(label="New Quote Text", lines=3)
                update_author = gr.Textbox(label="New Author")
                update_category = gr.Textbox(label="New Category")
                update_btn = gr.Button("Update Quote")
                update_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("## Delete Quote")

                delete_id = gr.Number(label="Quote ID", precision=0)
                delete_btn = gr.Button("Delete Quote", variant="stop")
                delete_status = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("Analytics"):
                gr.Markdown("## Basic Text Analytics")

                with gr.Row():
                    word_btn = gr.Button("Word Count", variant="primary")
                    category_btn = gr.Button("Category Distribution")
                    author_btn = gr.Button("Top Authors")
                    length_btn = gr.Button("Quote Lengths")

                plot_output = gr.Plot()

        outputs_all = [
            stats_output,
            home_category,
            gallery_category,
            random_output,
            gallery_output
        ]

        inputs_all = [
            home_category,
            gallery_category,
            keyword_input,
            limit_input
        ]

        demo.load(
            fn=refresh_screen,
            inputs=inputs_all,
            outputs=outputs_all
        )

        refresh_btn.click(
            fn=refresh_screen,
            inputs=inputs_all,
            outputs=outputs_all
        )

        random_btn.click(
            fn=random_quote,
            inputs=home_category,
            outputs=random_output
        )

        home_category.change(
            fn=random_quote,
            inputs=home_category,
            outputs=random_output
        )

        gallery_btn.click(
            fn=show_gallery,
            inputs=[gallery_category, keyword_input, limit_input],
            outputs=gallery_output
        )

        keyword_input.submit(
            fn=show_gallery,
            inputs=[gallery_category, keyword_input, limit_input],
            outputs=gallery_output
        )

        gallery_category.change(
            fn=show_gallery,
            inputs=[gallery_category, keyword_input, limit_input],
            outputs=gallery_output
        )

        limit_input.change(
            fn=show_gallery,
            inputs=[gallery_category, keyword_input, limit_input],
            outputs=gallery_output
        )

        add_btn.click(
            fn=add_quote,
            inputs=[add_text, add_author, add_category],
            outputs=add_status
        ).then(
            fn=refresh_screen,
            inputs=inputs_all,
            outputs=outputs_all
        )

        update_btn.click(
            fn=update_quote,
            inputs=[update_id, update_text, update_author, update_category],
            outputs=update_status
        ).then(
            fn=refresh_screen,
            inputs=inputs_all,
            outputs=outputs_all
        )

        delete_btn.click(
            fn=delete_quote,
            inputs=delete_id,
            outputs=delete_status
        ).then(
            fn=refresh_screen,
            inputs=inputs_all,
            outputs=outputs_all
        )

        word_btn.click(fn=word_count_plot, outputs=plot_output)
        category_btn.click(fn=category_plot, outputs=plot_output)
        author_btn.click(fn=author_plot, outputs=plot_output)
        length_btn.click(fn=length_plot, outputs=plot_output)

    return demo