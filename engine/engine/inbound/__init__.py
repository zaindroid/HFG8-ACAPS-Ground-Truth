"""Inbound: answers that arrive as replies rather than as taps (section 6e).

`POST /inbound/{email,whatsapp,sms,voice}` all come through `parse`, which reads a probability, a
likelihood word, a confidence, an abstention, a mask choice or a STOP out of whatever somebody
actually wrote, in English or French, and reports what it could not read.

Guarantees. An unparseable reply is never dropped and never guessed at: it goes to the analyst
with the original text. A STOP or PAUSE word anywhere in a reply is honoured before anything else
in it is read, so "stop, I'm not the right person for this" stops the messages and does not
record an answer. A voice note is read back in one line before the deadline passes, because a
transcription is a guess and committing one silently puts a number on the record the expert never
said.

Does not. Transcribe. `POST /inbound/voice` takes the text a transcription service produced; this
build has no speech model and the payload says the transcript came from the request.
"""
from __future__ import annotations

from .parse import PARSED_FIELDS, Parsed, parse

__all__ = ["parse", "Parsed", "PARSED_FIELDS"]
