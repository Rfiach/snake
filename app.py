"""Gradio share host for the browser version of Snake."""
from __future__ import annotations

import html
from pathlib import Path

import gradio as gr

INDEX_FILE = Path(__file__).with_name("index.html")
GAME_HTML = html.escape(INDEX_FILE.read_text(encoding="utf-8"), quote=True)

with gr.Blocks(title="Snake") as demo:
    gr.HTML(
        f"""
        <iframe
            srcdoc="{GAME_HTML}"
            title="Snake-Spiel"
            style="display:block;width:100%;height:860px;border:0"
        ></iframe>
        """
    )


if __name__ == "__main__":
    demo.launch(share=True, inbrowser=True)
