import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re

from database import SessionLocal
import models


STOPWORDS = {
    "the", "and", "is", "a", "an", "of", "to", "in", "it", "that",
    "for", "on", "with", "as", "be", "at", "by", "this", "are", "was",
    "i", "me", "my", "we", "our", "you", "your", "he", "his", "him",
    "they", "them", "their", "not", "but", "from", "or", "if"
}


def get_all_quotes_df():
    db = SessionLocal()
    try:
        quotes = db.query(models.Quote).all()
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


def filter_quotes(search_text, author, category):
    df = get_all_quotes_df()

    if df.empty:
        return pd.DataFrame(columns=["id", "text", "author", "category"])

    if search_text:
        search_text = search_text.lower()
        df = df[
            df["text"].str.lower().str.contains(search_text, na=False)
            | df["author"].str.lower().str.contains(search_text, na=False)
            | df["category"].str.lower().str.contains(search_text, na=False)
        ]

    if author and author != "All":
        df = df[df["author"] == author]

    if category and category != "All":
        df = df[df["category"] == category]

    return df[["id", "text", "author", "category"]]


def get_dropdown_data():
    df = get_all_quotes_df()

    if df.empty:
        return (
            gr.update(choices=["All"], value="All"),
            gr.update(choices=["All"], value="All"),
            "### No data yet"
        )

    authors = ["All"] + sorted(df["author"].dropna().unique().tolist())
    categories = ["All"] + sorted(df["category"].dropna().unique().tolist())

    stats = f"""
### Project Statistics

**Total quotes:** {len(df)}  
**Authors:** {df["author"].nunique()}  
**Categories:** {df["category"].nunique()}  
**Average quote length:** {round(df["text"].str.len().mean(), 1)} characters
"""

    return (
        gr.update(choices=authors, value="All"),
        gr.update(choices=categories, value="All"),
        stats
    )


def add_quote(text, author, category):
    if not text or not author or not category:
        return "Fill in all fields."

    db = SessionLocal()
    try:
        new_quote = models.Quote(
            text=text.strip(),
            author=author.strip(),
            category=category.strip()
        )
        db.add(new_quote)
        db.commit()
        return "Quote added successfully."
    finally:
        db.close()


def delete_quote(quote_id):
    if not quote_id:
        return "Enter quote ID."

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
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]

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


def random_quote():
    df = get_all_quotes_df()

    if df.empty:
        return "No quotes found."

    quote = df.sample(1).iloc[0]

    return f"""
## Random Quote

> {quote["text"]}

**Author:** {quote["author"]}  
**Category:** {quote["category"]}
"""


custom_css = """
body {
    background: #f5f7fb;
}

.gradio-container {
    max-width: 1200px !important;
    margin: auto;
}

#title {
    text-align: center;
    padding: 20px;
    border-radius: 18px;
    background: linear-gradient(135deg, #1f2937, #4f46e5);
    color: white;
    margin-bottom: 20px;
}

.stat-box {
    padding: 18px;
    border-radius: 16px;
    background: white;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
}
"""


def build_gradio():
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
# Quotes Management and Analysis
### Search, manage and analyze quotes
""",
            elem_id="title"
        )

        with gr.Row():
            refresh_btn = gr.Button("Refresh Data", variant="primary")
            random_btn = gr.Button("Show Random Quote")

        random_output = gr.Markdown()

        with gr.Row():
            stats_output = gr.Markdown(elem_classes="stat-box")

        with gr.Tabs():
            with gr.Tab("Quote Table"):
                with gr.Row():
                    search_input = gr.Textbox(
                        label="Search",
                        placeholder="Search by quote text, author, or category"
                    )
                    author_filter = gr.Dropdown(
                        label="Author",
                        choices=["All"],
                        value="All"
                    )
                    category_filter = gr.Dropdown(
                        label="Category",
                        choices=["All"],
                        value="All"
                    )

                table_output = gr.Dataframe(
                    headers=["id", "text", "author", "category"],
                    datatype=["number", "str", "str", "str"],
                    interactive=False,
                    wrap=True
                )

                search_btn = gr.Button("Apply Filter", variant="primary")

            with gr.Tab("Add Quote"):
                text_input = gr.Textbox(
                    label="Quote Text",
                    lines=4,
                    placeholder="Enter quote text"
                )
                author_input = gr.Textbox(
                    label="Author",
                    placeholder="Enter author name"
                )
                category_input = gr.Textbox(
                    label="Category",
                    placeholder="Enter category"
                )

                add_btn = gr.Button("Add Quote", variant="primary")
                add_status = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("Delete Quote"):
                delete_id = gr.Number(label="Quote ID", precision=0)
                delete_btn = gr.Button("Delete Quote", variant="stop")
                delete_status = gr.Textbox(label="Status", interactive=False)

            with gr.Tab("Analysis"):
                with gr.Row():
                    word_btn = gr.Button("Word Frequency")
                    category_btn = gr.Button("Category Distribution")
                    author_btn = gr.Button("Author Ranking")

                plot_output = gr.Plot()

        demo.load(
            fn=get_dropdown_data,
            outputs=[author_filter, category_filter, stats_output]
        )

        demo.load(
            fn=filter_quotes,
            inputs=[search_input, author_filter, category_filter],
            outputs=table_output
        )

        refresh_btn.click(
            fn=get_dropdown_data,
            outputs=[author_filter, category_filter, stats_output]
        ).then(
            fn=filter_quotes,
            inputs=[search_input, author_filter, category_filter],
            outputs=table_output
        )

        search_btn.click(
            fn=filter_quotes,
            inputs=[search_input, author_filter, category_filter],
            outputs=table_output
        )

        random_btn.click(
            fn=random_quote,
            outputs=random_output
        )

        add_btn.click(
            fn=add_quote,
            inputs=[text_input, author_input, category_input],
            outputs=add_status
        ).then(
            fn=get_dropdown_data,
            outputs=[author_filter, category_filter, stats_output]
        ).then(
            fn=filter_quotes,
            inputs=[search_input, author_filter, category_filter],
            outputs=table_output
        )

        delete_btn.click(
            fn=delete_quote,
            inputs=delete_id,
            outputs=delete_status
        ).then(
            fn=get_dropdown_data,
            outputs=[author_filter, category_filter, stats_output]
        ).then(
            fn=filter_quotes,
            inputs=[search_input, author_filter, category_filter],
            outputs=table_output
        )

        word_btn.click(fn=word_count_plot, outputs=plot_output)
        category_btn.click(fn=category_plot, outputs=plot_output)
        author_btn.click(fn=author_plot, outputs=plot_output)

    return demo