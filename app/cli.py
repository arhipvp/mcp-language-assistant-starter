
import typer
from .orchestration.pipeline import LessonConfig, build_lesson

app = typer.Typer(help="MCP Language Assistant CLI")


@app.command("youtube-to-anki")
def youtube_to_anki(
    url: str = typer.Option(..., help="YouTube URL"),
    deck: str = typer.Option(..., help="Anki deck name"),
    tag: str = typer.Option("auto-mcp", help="Tag for notes"),
    limit: int = typer.Option(10, help="How many words to add"),
):
    cfg = LessonConfig(url=url, deck=deck, tag=tag, limit=limit)
    result = build_lesson(cfg)
    typer.echo({k: (len(v) if isinstance(v, list) else v) for k, v in result.items()})


if __name__ == "__main__":
    app()
