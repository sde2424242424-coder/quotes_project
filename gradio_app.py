import html
import re
from collections import Counter

import gradio as gr
import matplotlib.pyplot as plt

from database import SessionLocal
import models


STOPWORDS = {
    "the", "and", "is", "a", "an", "of", "to", "in", "it", "that",
    "for", "on", "with", "as", "be", "at", "by", "this", "are", "was",
    "i", "me", "my", "we", "our", "you", "your", "he", "his", "him",
    "they", "them", "their", "not", "but", "from", "or", "if", "so"
}


def get_quotes():
    db = SessionLocal()
    try:
        return db.query(models.Quote).order_by(models.Quote.id.desc()).all()
    finally:
        db.close()


def get_categories_list():
    quotes = get_quotes()
    categories = sorted(list({q.category for q in quotes if q.category}))
    return ["All"] + categories


def stats_html():
    quotes = get_quotes()

    total = len(quotes)
    authors = len(set(q.author for q in quotes))
    categories = len(set(q.category for q in quotes))
    avg_len = round(sum(len(q.text) for q in quotes) / total, 1) if total else 0

    return f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:15px 0;">
    <div style="background:white;padding:20px;border-radius:18px;box-shadow:0 6px 18px #ddd;">
        <h2>{total}</h2><p>Total Quotes</p>
    </div>
    <div style="background:white;padding:20px;border-radius:18px;box-shadow:0 6px 18px #ddd;">
        <h2>{authors}</h2><p>Authors</p>
    </div>
    <div style="background:white;padding:20px;border-radius:18px;box-shadow:0 6px 18px #ddd;">
        <h2>{categories}</h2><p>Categories</p>
    </div>
    <div style="background:white;padding:20px;border-radius:18px;box-shadow:0 6px 18px #ddd;">
        <h2>{avg_len}</h2><p>Avg Length</p>
    </div>
</div>
"""


def quote_card(q):
    return f"""
<div style="
    background:white;
    padding:24px;
    border-radius:22px;
    box-shadow:0 8px 25px rgba(0,0,0,0.10);
    border:1px solid #e5e7eb;
    min-height:180px;
">
    <div style="color:#9ca3af;font-size:13px;text-align:right;">#{q.id}</div>
    <div style="font-size:19px;line-height:1.5;font-weight:700;color:#111827;margin:12px 0 20px;">
        “{html.escape(q.text)}”
    </div>
    <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;">
        <b>— {html.escape(q.author)}</b>
        <span style="background:#eef2ff;color:#4338ca;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:700;">
            {html.escape(q.category)}
        </span>
    </div>
</div>
"""


def show_gallery(category, keyword, limit):
    quotes = get_quotes()

    if category and category != "All":
        quotes = [q for q in quotes if q.category == category]

    if keyword:
        key = keyword.lower().strip()
        quotes = [
            q for q in quotes
            if key in q.text.lower()
            or key in q.author.lower()
            or key in q.category.lower()
        ]

    quotes = quotes[:int(limit)]

    if not quotes:
        return """
<div style="padding:30px;text-align:center;color:gray;border:1px dashed #ccc;border-radius:18px;">
    No quotes found.
</div>
"""

    cards = "".join(quote_card(q) for q in quotes)

    return f"""
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:18px;">
    {cards}
</div>
"""


def random_quote(category):
    quotes = get_quotes()

    if category and category != "All":
        quotes = [q for q in quotes if q.category == category]

    if not quotes:
        return """
<div style="padding:30px;text-align:center;color:gray;border:1px dashed #ccc;border-radius:18px;">
    No quotes found.
</div>
"""

    q = quotes[0]

    return f"""
<div style="
    padding:34px;
    border-radius:28px;
    background:linear-gradient(135deg,#fff7ed,#eef2ff);
    box-shadow:0 12px 35px rgba(0,0,0,0.14);
">
    <div style="display:inline-block;background:#4f46e5;color:white;padding:8px 14px;border-radius:999px;font-weight:700;">
        Featured Quote
    </div>
    <div style="font-size:30px;line-height:1.45;font-weight:800;margin:24px 0;color:#111827;">
        “{html.escape(q.text)}”
    </div>
    <div style="font-size:20px;color:#374151;">— {html.escape(q.author)}</div>
    <div style="display:inline-block;margin-top:15px;background:#ffedd5;color:#c2410c;padding:8px 14px;border-radius:999px;font-weight:800;">
        {html.escape(q.category)}
    </div>
</div>
"""


def refresh_data():
    categories = get_categories_list()

    return (
        gr.update(choices=categories, value="All"),
        gr.update(choices=categories, value="All"),
        stats_html(),
        random_quote("All"),
        """
<div style="padding:30px;text-align:center;color:gray;border:1px dashed #ccc;border-radius:18px;">
    Press Load Quote Cards.
</div>
"""
    )


def add_quote(text, author, category):
    if not text or not author or not category:
        return "Please fill in all fields."

    db = SessionLocal()
    try:
        q = models.Quote(
            text=text.strip(),
            author=author.strip(),
            category=category.strip()
        )
        db.add(q)
        db.commit()
        return "Quote added successfully."
    finally:
        db.close()


def update_quote(quote_id, text, author, category):
    if not quote_id:
        return "Please enter quote ID."

    db = SessionLocal()
    try:
        q = db.query(models.Quote).filter(models.Quote.id == int(quote_id)).first()

        if not q:
            return "Quote not found."

        if text:
            q.text = text.strip()

        if author:
            q.author = author.strip()

        if category:
            q.category = category.strip()

        db.commit()
        return "Quote updated successfully."
    finally:
        db.close()


def delete_quote(quote_id):
    if not quote_id:
        return "Please enter quote ID."

    db = SessionLocal()
    try:
        q = db.query(models.Quote).filter(models.Quote.id == int(quote_id)).first()

        if not q:
            return "Quote not found."

        db.delete(q)
        db.commit()
        return "Quote deleted successfully."
    finally:
        db.close()


def word_count_plot():
    quotes = get_quotes()
    fig = plt.figure(figsize=(10, 5))

    if not quotes:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    text = " ".join(q.text for q in quotes).lower()
    words = re.findall(r"[a-zA-Z']+", text)
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]

    data = Counter(words).most_common(10)

    if not data:
        plt.text(0.5, 0.5, "No words", ha="center", va="center")
        plt.axis("off")
        return fig

    labels = [x[0] for x in data]
    values = [x[1] for x in data]

    plt.bar(labels, values)
    plt.title("Top 10 Words")
    plt.xticks(rotation=35)
    plt.tight_layout()

    return fig


def category_plot():
    quotes = get_quotes()
    fig = plt.figure(figsize=(8, 5))

    if not quotes:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    counter = Counter(q.category for q in quotes)

    plt.pie(counter.values(), labels=counter.keys(), autopct="%1.1f%%")
    plt.title("Category Distribution")
    plt.tight_layout()

    return fig


def author_plot():
    quotes = get_quotes()
    fig = plt.figure(figsize=(10, 5))

    if not quotes:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    data = Counter(q.author for q in quotes).most_common(10)

    labels = [x[0] for x in data]
    values = [x[1] for x in data]

    plt.barh(labels, values)
    plt.title("Top Authors")
    plt.tight_layout()

    return fig


def build_gradio():
    categories = get_categories_list()

    with gr.Blocks() as demo:
        gr.HTML("""
<div style="padding:32px;border-radius:28px;background:linear-gradient(135deg,#111827,#4f46e5,#fb923c);color:white;margin-bottom:20px;">
    <h1 style="margin:0;font-size:38px;">Quotes Management and Analysis</h1>
    <p style="margin-top:10px;font-size:16px;">FastAPI + SQLite + Gradio visual dashboard</p>
</div>
""")

        stats = gr.HTML(value=stats_html())

        with gr.Row():
            refresh_btn = gr.Button("Refresh Data", variant="primary")
            random_btn = gr.Button("Show Quote", variant="secondary")

        with gr.Tabs():
            with gr.Tab("Home"):
                home_category = gr.Dropdown(
                    choices=categories,
                    value="All",
                    label="Category"
                )
                random_output = gr.HTML(value=random_quote("All"))

            with gr.Tab("Gallery"):
                gr.Markdown("## Quote Gallery")
                gr.Markdown("Cards are loaded only after pressing the button.")

                with gr.Row():
                    gallery_category = gr.Dropdown(
                        choices=categories,
                        value="All",
                        label="Category"
                    )
                    keyword = gr.Textbox(
                        label="Search",
                        placeholder="Author, category, or quote text"
                    )
                    limit = gr.Slider(
                        minimum=2,
                        maximum=10,
                        value=4,
                        step=2,
                        label="Card Limit"
                    )

                gallery_btn = gr.Button("Load Quote Cards", variant="primary")

                gallery_output = gr.HTML(
                    value="""
<div style="padding:30px;text-align:center;color:gray;border:1px dashed #ccc;border-radius:18px;">
    Press Load Quote Cards.
</div>
"""
                )

            with gr.Tab("Manage"):
                gr.Markdown("## Add Quote")
                add_text = gr.Textbox(label="Quote Text", lines=3)
                add_author = gr.Textbox(label="Author")
                add_category = gr.Textbox(label="Category")
                add_btn = gr.Button("Add", variant="primary")
                add_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("## Update Quote")
                update_id = gr.Number(label="Quote ID", precision=0)
                update_text = gr.Textbox(label="New Text", lines=3)
                update_author = gr.Textbox(label="New Author")
                update_category = gr.Textbox(label="New Category")
                update_btn = gr.Button("Update")
                update_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("## Delete Quote")
                delete_id = gr.Number(label="Quote ID", precision=0)
                delete_btn = gr.Button("Delete", variant="stop")
                delete_status = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("Analytics"):
                with gr.Row():
                    word_btn = gr.Button("Word Count", variant="primary")
                    category_btn = gr.Button("Categories")
                    author_btn = gr.Button("Authors")

                plot = gr.Plot()

        refresh_btn.click(
            fn=refresh_data,
            outputs=[
                home_category,
                gallery_category,
                stats,
                random_output,
                gallery_output
            ],
            queue=False
        )

        random_btn.click(
            fn=random_quote,
            inputs=home_category,
            outputs=random_output,
            queue=False
        )

        home_category.change(
            fn=random_quote,
            inputs=home_category,
            outputs=random_output,
            queue=False
        )

        gallery_btn.click(
            fn=show_gallery,
            inputs=[gallery_category, keyword, limit],
            outputs=gallery_output,
            queue=False
        )

        add_btn.click(
            fn=add_quote,
            inputs=[add_text, add_author, add_category],
            outputs=add_status,
            queue=False
        )

        update_btn.click(
            fn=update_quote,
            inputs=[update_id, update_text, update_author, update_category],
            outputs=update_status,
            queue=False
        )

        delete_btn.click(
            fn=delete_quote,
            inputs=delete_id,
            outputs=delete_status,
            queue=False
        )

        word_btn.click(fn=word_count_plot, outputs=plot, queue=False)
        category_btn.click(fn=category_plot, outputs=plot, queue=False)
        author_btn.click(fn=author_plot, outputs=plot, queue=False)

    return demo