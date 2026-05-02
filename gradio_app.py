import html
import random
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
    "i", "me", "my", "we", "our", "you", "your",
    "he", "his", "him", "they", "them", "their",
    "not", "but", "from", "or", "if", "so", "what", "when", "where",
    "who", "why", "how", "all", "one", "out", "up", "down"
}


def get_all_quotes_df():
    db = SessionLocal()
    try:
        quotes = db.query(models.Quote).order_by(models.Quote.id.desc()).all()

        data = [
            {
                "id": q.id,
                "text": q.text,
                "author": q.author,
                "category": q.category
            }
            for q in quotes
        ]

        return pd.DataFrame(data)
    finally:
        db.close()


def get_categories():
    df = get_all_quotes_df()

    if df.empty:
        return gr.update(choices=["All"], value="All")

    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
    return gr.update(choices=categories, value="All")


def get_stats():
    df = get_all_quotes_df()

    if df.empty:
        return """
<div class="stats-grid">
    <div class="stat-card"><h2>0</h2><p>Total Quotes</p></div>
    <div class="stat-card"><h2>0</h2><p>Authors</p></div>
    <div class="stat-card"><h2>0</h2><p>Categories</p></div>
</div>
"""

    total_quotes = len(df)
    total_authors = df["author"].nunique()
    total_categories = df["category"].nunique()
    avg_length = round(df["text"].str.len().mean(), 1)

    return f"""
<div class="stats-grid">
    <div class="stat-card"><h2>{total_quotes}</h2><p>Total Quotes</p></div>
    <div class="stat-card"><h2>{total_authors}</h2><p>Authors</p></div>
    <div class="stat-card"><h2>{total_categories}</h2><p>Categories</p></div>
    <div class="stat-card"><h2>{avg_length}</h2><p>Avg. Length</p></div>
</div>
"""


def make_quote_card(row):
    quote_id = html.escape(str(row["id"]))
    text = html.escape(str(row["text"]))
    author = html.escape(str(row["author"]))
    category = html.escape(str(row["category"]))

    return f"""
<div class="quote-card">
    <div class="quote-id">#{quote_id}</div>
    <div class="quote-text">“{text}”</div>
    <div class="quote-footer">
        <span class="quote-author">— {author}</span>
        <span class="quote-category">{category}</span>
    </div>
</div>
"""


def show_quote_gallery(category="All", keyword=""):
    df = get_all_quotes_df()

    if df.empty:
        return "<div class='empty-box'>No quotes found. Add or crawl quotes first.</div>"

    if category and category != "All":
        df = df[df["category"] == category]

    if keyword:
        keyword = keyword.lower()
        df = df[
            df["text"].str.lower().str.contains(keyword, na=False)
            | df["author"].str.lower().str.contains(keyword, na=False)
            | df["category"].str.lower().str.contains(keyword, na=False)
        ]

    if df.empty:
        return "<div class='empty-box'>No matching quotes found.</div>"

    cards = "".join(make_quote_card(row) for _, row in df.iterrows())

    return f"""
<div class="gallery">
    {cards}
</div>
"""


def random_quote(category="All"):
    df = get_all_quotes_df()

    if df.empty:
        return "<div class='empty-box'>No quotes found.</div>"

    if category and category != "All":
        df = df[df["category"] == category]

    if df.empty:
        return "<div class='empty-box'>No quotes in this category.</div>"

    row = df.sample(1).iloc[0]

    return f"""
<div class="hero-card">
    <div class="hero-label">Random Quote</div>
    <div class="hero-text">“{html.escape(str(row["text"]))}”</div>
    <div class="hero-author">— {html.escape(str(row["author"]))}</div>
    <div class="hero-category">{html.escape(str(row["category"]))}</div>
</div>
"""


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
    df = get_all_quotes_df()
    fig = plt.figure(figsize=(10, 5))

    if df.empty:
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    text = " ".join(df["text"].tolist()).lower()
    words = re.findall(r"[a-zA-Z']+", text)
    words = [word for word in words if word not in STOPWORDS and len(word) > 2]

    counter = Counter(words).most_common(10)

    if not counter:
        plt.text(0.5, 0.5, "No words to analyze", ha="center", va="center")
        plt.axis("off")
        return fig

    labels = [item[0] for item in counter]
    values = [item[1] for item in counter]

    plt.bar(labels, values)
    plt.title("Top 10 Most Frequent Words")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=35)
    plt.tight_layout()

    return fig


def category_plot():
    df = get_all_quotes_df()
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
    df = get_all_quotes_df()
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


def quote_length_plot():
    df = get_all_quotes_df()
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


custom_css = """
.gradio-container {
    max-width: 1250px !important;
    margin: auto !important;
}

#app-title {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(135deg, #111827, #4f46e5, #fb923c);
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.15);
}

#app-title h1 {
    font-size: 38px;
    margin-bottom: 8px;
}

#app-title p {
    font-size: 16px;
    opacity: 0.9;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 16px 0;
}

.stat-card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}

.stat-card h2 {
    margin: 0;
    font-size: 30px;
    color: #4f46e5;
}

.stat-card p {
    margin: 4px 0 0;
    color: #6b7280;
}

.hero-card {
    padding: 32px;
    border-radius: 26px;
    background: radial-gradient(circle at top left, #fef3c7, #ffffff 45%, #eef2ff);
    border: 1px solid #e5e7eb;
    box-shadow: 0 14px 35px rgba(0,0,0,0.12);
    min-height: 230px;
}

.hero-label {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #4f46e5;
    color: white;
    font-size: 13px;
    margin-bottom: 20px;
}

.hero-text {
    font-size: 30px;
    line-height: 1.4;
    font-weight: 700;
    color: #111827;
    margin-bottom: 20px;
}

.hero-author {
    font-size: 18px;
    color: #374151;
    margin-bottom: 12px;
}

.hero-category {
    display: inline-block;
    padding: 7px 14px;
    border-radius: 999px;
    background: #ffedd5;
    color: #c2410c;
    font-weight: 700;
}

.gallery {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
}

.quote-card {
    position: relative;
    padding: 24px;
    border-radius: 22px;
    background: white;
    border: 1px solid #e5e7eb;
    box-shadow: 0 10px 28px rgba(0,0,0,0.08);
    transition: 0.2s;
    min-height: 210px;
}

.quote-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 16px 36px rgba(0,0,0,0.14);
}

.quote-id {
    position: absolute;
    top: 14px;
    right: 16px;
    color: #9ca3af;
    font-size: 13px;
}

.quote-text {
    font-size: 18px;
    line-height: 1.55;
    color: #111827;
    font-weight: 600;
    margin-bottom: 24px;
}

.quote-footer {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    margin-top: auto;
}

.quote-author {
    color: #374151;
    font-weight: 700;
}

.quote-category {
    padding: 6px 10px;
    border-radius: 999px;
    background: #eef2ff;
    color: #4338ca;
    font-size: 12px;
    font-weight: 700;
}

.empty-box {
    padding: 30px;
    border-radius: 20px;
    background: #f9fafb;
    border: 1px dashed #d1d5db;
    color: #6b7280;
    text-align: center;
    font-size: 18px;
}

@media (max-width: 900px) {
    .gallery {
        grid-template-columns: 1fr;
    }

    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .hero-text {
        font-size: 23px;
    }
}
"""


def build_gradio():
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
        gr.HTML("""
<div id="app-title">
    <h1>Quotes Management and Analysis</h1>
    <p>FastAPI + SQLite + Gradio dashboard for quote management, visual cards, and text analytics.</p>
</div>
""")

        stats_output = gr.HTML()

        with gr.Row():
            refresh_btn = gr.Button("Refresh Data", variant="primary")
            random_btn = gr.Button("Show Random Quote", variant="secondary")

        with gr.Tabs():
            with gr.Tab("Home"):
                home_category = gr.Dropdown(
                    label="Category",
                    choices=["All"],
                    value="All"
                )
                random_output = gr.HTML()
                gr.Markdown("Use this screen during presentation: it looks cleaner than a table.")

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

                gallery_btn = gr.Button("Show Quote Cards", variant="primary")
                gallery_output = gr.HTML()

            with gr.Tab("Manage Quotes"):
                gr.Markdown("### Add New Quote")
                add_text = gr.Textbox(label="Quote Text", lines=4, placeholder="Enter quote text")
                add_author = gr.Textbox(label="Author", placeholder="Enter author name")
                add_category = gr.Textbox(label="Category", placeholder="Enter category")
                add_btn = gr.Button("Add Quote", variant="primary")
                add_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("### Update Quote")
                update_id = gr.Number(label="Quote ID", precision=0)
                update_text = gr.Textbox(label="New Quote Text", lines=3)
                update_author = gr.Textbox(label="New Author")
                update_category = gr.Textbox(label="New Category")
                update_btn = gr.Button("Update Quote")
                update_status = gr.Textbox(label="Status", interactive=False)

                gr.Markdown("### Delete Quote")
                delete_id = gr.Number(label="Quote ID", precision=0)
                delete_btn = gr.Button("Delete Quote", variant="stop")
                delete_status = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("Analytics"):
                with gr.Row():
                    word_btn = gr.Button("Word Count", variant="primary")
                    category_btn = gr.Button("Category Distribution")
                    author_btn = gr.Button("Top Authors")
                    length_btn = gr.Button("Quote Lengths")

                plot_output = gr.Plot()

        demo.load(fn=get_stats, outputs=stats_output)

        demo.load(fn=get_categories, outputs=home_category)
        demo.load(fn=get_categories, outputs=gallery_category)

        demo.load(fn=random_quote, inputs=home_category, outputs=random_output)
        demo.load(fn=show_quote_gallery, inputs=[gallery_category, keyword_input], outputs=gallery_output)

        refresh_btn.click(
            fn=get_stats,
            outputs=stats_output
        ).then(
            fn=get_categories,
            outputs=home_category
        ).then(
            fn=get_categories,
            outputs=gallery_category
        ).then(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
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
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        gallery_category.change(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        keyword_input.change(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        add_btn.click(
            fn=add_quote,
            inputs=[add_text, add_author, add_category],
            outputs=add_status
        ).then(
            fn=get_stats,
            outputs=stats_output
        ).then(
            fn=get_categories,
            outputs=home_category
        ).then(
            fn=get_categories,
            outputs=gallery_category
        ).then(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        update_btn.click(
            fn=update_quote,
            inputs=[update_id, update_text, update_author, update_category],
            outputs=update_status
        ).then(
            fn=get_stats,
            outputs=stats_output
        ).then(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        delete_btn.click(
            fn=delete_quote,
            inputs=delete_id,
            outputs=delete_status
        ).then(
            fn=get_stats,
            outputs=stats_output
        ).then(
            fn=get_categories,
            outputs=home_category
        ).then(
            fn=get_categories,
            outputs=gallery_category
        ).then(
            fn=show_quote_gallery,
            inputs=[gallery_category, keyword_input],
            outputs=gallery_output
        )

        word_btn.click(fn=word_count_plot, outputs=plot_output)
        category_btn.click(fn=category_plot, outputs=plot_output)
        author_btn.click(fn=author_plot, outputs=plot_output)
        length_btn.click(fn=quote_length_plot, outputs=plot_output)

    return demo