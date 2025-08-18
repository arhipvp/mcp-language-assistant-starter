import typer
from typing import Optional

from .orchestration.pipeline import LessonConfig, build_lesson

app = typer.Typer(help="MCP Language Assistant CLI")


@app.command("build-lesson")
def build_lesson_cmd(
    url: Optional[str] = typer.Option(None, help="YouTube URL"),
    text: Optional[str] = typer.Option(None, help="Raw text instead of URL"),
    deck: str = typer.Option(..., help="Anki deck name"),
    tag: str = typer.Option("auto-mcp", help="Tag for notes"),
    limit: int = typer.Option(15, help="How many words to add"),
    tts: bool = typer.Option(False, help="Generate audio for examples"),
    language: str = typer.Option("de", help="Grammar check language"),
):
    """Build a lesson from a YouTube video or plain text."""
    if not url and not text:
        raise typer.BadParameter("Provide either --url or --text")
    cfg = LessonConfig(
        url=url,
        text=text,
        deck=deck,
        tag=tag,
        limit=limit,
        tts=tts,
        language=language,
    )
    result = build_lesson(cfg)
    typer.echo({k: (len(v) if isinstance(v, list) else v) for k, v in result.items()})


@app.command("youtube-to-anki")
def youtube_to_anki(
    url: str = typer.Option(..., help="YouTube URL"),
    deck: str = typer.Option(..., help="Anki deck name"),
    tag: str = typer.Option("auto-mcp", help="Tag for notes"),
    limit: int = typer.Option(10, help="How many words to add"),
):
    """Backward compatible helper for the old command name."""
    cfg = LessonConfig(url=url, deck=deck, tag=tag, limit=limit)
    result = build_lesson(cfg)
    typer.echo({k: (len(v) if isinstance(v, list) else v) for k, v in result.items()})


if __name__ == "__main__":
    app()
