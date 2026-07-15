"""Point d'entrée CLI de Goblin.

The browser UI is the default interactive experience.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import click
from openai import AuthenticationError

from goblin.audio import is_audio_file, transcribe_audio
from goblin.credentials import (
    load_saved_openai_api_key,
    save_openai_api_key,
    get_openai_api_key_path,
    delete_openai_api_key,
)
from goblin.formatter import save_transcription
from goblin.image import is_image_file, transcribe_image
from goblin.metadata import get_file_creation_date


def _launch_browser_ui(output_dir: str, port: int, offline: bool) -> None:
    log_path = Path("/tmp/goblin-web.log")
    try:
        log_path.write_text("Launching browser UI\n", encoding="utf-8")
        from goblin.gui import run_gui

        run_gui(output_dir=output_dir, port=port, offline=offline)
        log_path.write_text("Browser UI exited normally\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        log_path.write_text(f"Browser UI crash: {exc!r}\n", encoding="utf-8")
        raise


@click.command()
@click.argument("files", nargs=-1, required=False, type=str)
@click.option(
    "--output-dir",
    "-o",
    default="transcriptions",
    show_default=True,
    help="Répertoire de sortie pour les fichiers de transcription.",
)
@click.option(
    "--language",
    "-l",
    default=None,
    metavar="LANG",
    help=(
        "Code langue ISO-639-1 pour la transcription audio (ex. 'fr', 'en'). "
        "Détection automatique si non précisé."
    ),
)
@click.option(
    "--port",
    "-p",
    default=5000,
    show_default=True,
    type=int,
    help="Port utilisé par l'interface navigateur.",
)
@click.option(
    "--web",
    "browser_mode",
    is_flag=True,
    help="Lancer l'interface navigateur.",
)
@click.option(
    "--offline/--online",
    default=True,
    show_default=True,
    help=(
        "Mode hors-ligne (--offline, défaut) : modèles locaux, sans clé API. "
        "Mode en ligne (--online) : API OpenAI, nécessite OPENAI_API_KEY."
    ),
)
@click.option(
    "--whisper-model",
    type=click.Choice(["tiny", "base", "medium"], case_sensitive=False),
    default="base",
    show_default=True,
    help="Modèle Whisper pour la transcription audio hors-ligne (tiny, base, medium).",
)
@click.option(
    "--show-api-key",
    is_flag=True,
    help="Afficher l'emplacement et une version masquée de la clé API sauvegardée.",
)
@click.option(
    "--set-api-key",
    is_flag=True,
    help="Saisir et sauvegarder une nouvelle clé OpenAI (invite sécurisée).",
)
@click.option(
    "--delete-api-key",
    is_flag=True,
    help="Supprimer la clé OpenAI sauvegardée localement.",
)
def main(
    files: tuple,
    output_dir: str,
    language: Optional[str],
    port: int,
    browser_mode: bool,
    offline: bool,
    show_api_key: bool,
    set_api_key: bool,
    delete_api_key: bool,
    whisper_model: str,
) -> None:
    """Goblin – transcripteur de fichiers pour le journal Les Feuillets.

    \b
    Sans argument, lance l'interface navigateur.
    Avec des fichiers en argument, les transcrit en ligne de commande.

    \b
    Utilisez `goblin web` ou `goblin --web` pour lancer l'interface
    navigateur explicitement.

    \b
    Transcrit des enregistrements audio et des photos de textes manuscrits en
    fichiers Markdown éditables.  La date et l'heure de création du fichier
    source sont conservées dans le nom et l'en-tête de chaque sortie.

    \b
    Formats audio pris en charge : flac, m4a, mp3, mp4, ogg, wav, webm
    Formats image pris en charge  : bmp, gif, jpeg, jpg, png, tiff, webp

    \b
    Mode hors-ligne (défaut) : modèles locaux, aucune clé API requise.
    Mode en ligne             : nécessite la variable OPENAI_API_KEY.
    """
    load_saved_openai_api_key()

    # Set the whisper model for offline transcription
    if whisper_model:
        from goblin.offline import set_whisper_model_size
        set_whisper_model_size(whisper_model)

    # --- CLI helpers to manage the saved OpenAI API key -----------------
    if show_api_key:
        key = load_saved_openai_api_key()
        path = get_openai_api_key_path()
        if not key:
            click.echo(f"Aucune clé API trouvée dans {path}")
        else:
            # Mask the key for safety: show first/last 4 chars if long enough
            display = key
            if len(key) > 8:
                display = f"{key[:4]}...{key[-4:]}"
            click.echo(f"Clé sauvegardée : {display}\nEmplacement : {path}")
        return

    if set_api_key:
        new = click.prompt(
            "Entrez votre OpenAI API key",
            hide_input=True,
            confirmation_prompt=True,
        )
        try:
            save_openai_api_key(new)
            os.environ["OPENAI_API_KEY"] = new
            click.echo("Clé API sauvegardée avec succès.")
        except ValueError as exc:
            click.echo(f"Erreur : {exc}", err=True)
            sys.exit(1)
        return

    if delete_api_key:
        confirm = click.confirm(
            "Confirmer la suppression de la clé API sauvegardée ?",
            default=False,
        )
        if not confirm:
            click.echo("Suppression annulée.")
            return
        delete_openai_api_key()
        click.echo("Clé API supprimée.")
        return

    if browser_mode or (len(files) == 1 and files[0].lower() == "web"):
        _launch_browser_ui(output_dir=output_dir, port=port, offline=offline)
        return

    # ── No files given → launch the browser UI ──────────────────────────
    if not files:
        _launch_browser_ui(output_dir=output_dir, port=port, offline=offline)
        return

    # ── CLI transcription mode ───────────────────────────────────────────
    if not offline and not os.environ.get("OPENAI_API_KEY"):
        click.echo(
            "Erreur : mode en ligne sélectionné mais OPENAI_API_KEY n'est pas définie.",
            err=True,
        )
        sys.exit(1)

    if offline:
        from goblin.offline import transcribe_audio_offline, transcribe_image_offline

    processed = 0
    errors = 0

    for file_path in files:
        file_path = str(file_path)

        if file_path.lower() == "web":
            click.echo(
                "Erreur : 'web' est réservé au lancement de l'interface navigateur.\n"
                "Utilisez 'goblin web' ou 'goblin --web' sans fichier supplémentaire.",
                err=True,
            )
            errors += 1
            continue

        if not Path(file_path).exists():
            raise click.BadParameter(f"Le fichier n'existe pas : {file_path}")

        mode_label = "hors-ligne" if offline else "en ligne"
        click.echo(f"Traitement [{mode_label}] : {file_path}")

        try:
            creation_date = get_file_creation_date(file_path)
            start_time = time.perf_counter()

            if is_audio_file(file_path):
                click.echo("  → Transcription audio en cours…")
                if offline:
                    from goblin.offline import get_whisper_model_size
                    transcription = transcribe_audio_offline(file_path, language=language)
                    model_size = get_whisper_model_size()
                    transcription_metadata = {
                        "mode": "hors-ligne",
                        "model": f"faster-whisper {model_size} int8",
                    }
                else:
                    audio_result = transcribe_audio(
                        file_path,
                        language=language,
                        return_metadata=True,
                    )
                    if isinstance(audio_result, tuple):
                        transcription, api_metadata = audio_result
                    else:
                        transcription = audio_result
                        api_metadata = {"model": "whisper-1", "usage": {}}
                    transcription_metadata = {
                        "mode": "en ligne",
                        "model": api_metadata.get("model", "whisper-1"),
                    }
                    transcription_metadata.update(api_metadata.get("usage", {}))
                file_type = "enregistrement audio"
            elif is_image_file(file_path):
                click.echo("  → OCR du texte manuscrit en cours…")
                # For images: prefer GPT-4o Vision when key is available, fallback to local OCR
                has_api_key = bool(os.environ.get("OPENAI_API_KEY"))
                if offline or not has_api_key:
                    transcription = transcribe_image_offline(file_path)
                    transcription_metadata = {
                        "mode": "hors-ligne",
                        "model": "TrOCR + PaddleOCR",
                    }
                else:
                    image_result = transcribe_image(
                        file_path,
                        return_metadata=True,
                    )
                    if isinstance(image_result, tuple):
                        transcription, api_metadata = image_result
                    else:
                        transcription = image_result
                        api_metadata = {"model": "gpt-4o-mini", "usage": {}}
                    transcription_metadata = {
                        "mode": "en ligne",
                        "model": api_metadata.get("model", "gpt-4o-mini"),
                    }
                    transcription_metadata.update(api_metadata.get("usage", {}))
                file_type = "texte manuscrit"
            else:
                suffix = Path(file_path).suffix
                click.echo(
                    f"  ✗ Format non pris en charge : {suffix}",
                    err=True,
                )
                errors += 1
                continue

            output_path = save_transcription(
                transcription=transcription,
                original_path=file_path,
                creation_date=creation_date,
                file_type=file_type,
                output_dir=output_dir,
                metadata={**transcription_metadata, "duration_seconds": time.perf_counter() - start_time},
            )

            click.echo(f"  ✓ Sauvegardé : {output_path}")
            processed += 1

        except AuthenticationError as exc:
            click.echo(
                f"  ✗ Erreur d'authentification OpenAI : Votre clé API est invalide ou expirée.\n"
                f"    Veuillez vérifier votre clé sur https://platform.openai.com/account/api-keys\n"
                f"    Puis mettez à jour la clé dans le mode En ligne (ou variable OPENAI_API_KEY).\n"
                f"    Alternativement, utilisez le mode Hors-ligne pour transcrire ce fichier.",
                err=True,
            )
            errors += 1
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  ✗ Erreur lors du traitement de {file_path} : {exc}", err=True)
            errors += 1

    click.echo(
        f"\nTerminé : {processed} fichier(s) traité(s), {errors} erreur(s)."
    )


if __name__ == "__main__":
    main()
