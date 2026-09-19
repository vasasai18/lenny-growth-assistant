import argparse
import subprocess
from pathlib import Path


DEFAULT_REPOSITORY = (
    "https://github.com/LennysNewsletter/lennys-newsletterpodcastdata.git"
)
DEFAULT_DESTINATION = Path("data/raw/lennys-newsletterpodcastdata")


def run_git(*args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def download(repository: str, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if (destination / ".git").is_dir():
        existing_remote = run_git("remote", "get-url", "origin", cwd=destination)
        if existing_remote != repository:
            raise RuntimeError(
                f"Existing data source uses {existing_remote}, expected {repository}. "
                "Choose another destination instead of overwriting it."
            )
        print(f"Updating existing transcript source at {destination}...")
        run_git("pull", "--ff-only", cwd=destination)
    elif destination.exists():
        raise RuntimeError(
            f"Destination exists but is not a Git repository: {destination}"
        )
    else:
        print(f"Cloning transcript source into {destination}...")
        run_git("clone", "--depth", "1", repository, str(destination))

    revision = run_git("rev-parse", "HEAD", cwd=destination)
    transcript_count = len(list((destination / "podcasts").rglob("*.md")))
    if transcript_count == 0:
        raise RuntimeError("Download completed, but no podcast Markdown files were found.")

    print(f"Source revision: {revision}")
    print(f"Podcast transcript files: {transcript_count}")
    print("Transcript download: PASS")
    return revision


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official transcript starter pack.")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    download(args.repository, args.destination)


if __name__ == "__main__":
    main()

