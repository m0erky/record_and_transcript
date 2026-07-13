"""Einstiegspunkt der Audio-Transkriptions-App."""

from app.gui import AudioTranscriptionApp


def main() -> None:
    app = AudioTranscriptionApp()
    app.mainloop()


if __name__ == "__main__":
    main()
