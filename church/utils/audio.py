import logging
import os
from io import BytesIO

from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

DEFAULT_BITRATE = '128k'
# MP3 déjà légers : on évite une double compression inutile.
SKIP_MP3_UNDER_BYTES = 5 * 1024 * 1024


def audio_field_changed(instance, field_name='audio'):
    field = getattr(instance, field_name, None)
    if not field:
        return False
    if not instance.pk:
        return True
    old_name = (
        instance.__class__.objects.filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )
    return field.name != old_name


def _should_compress(audio_file):
    name = (audio_file.name or '').lower()
    if name.endswith('.mp3'):
        try:
            if audio_file.size < SKIP_MP3_UNDER_BYTES:
                return False
        except (AttributeError, TypeError, OSError):
            pass
    return True


def _guess_format(filename):
    ext = os.path.splitext(filename or '')[1].lower().lstrip('.')
    return ext or 'mp3'


def compress_audio_file(audio_file, *, bitrate=DEFAULT_BITRATE, mono=True):
    try:
        from pydub import AudioSegment
    except ImportError:
        logger.warning('pydub not installed; skipping audio compression')
        return None

    if not _should_compress(audio_file):
        return None

    try:
        audio_file.open('rb')
        data = audio_file.read()
        audio_file.close()
    except Exception:
        logger.exception('Could not read audio file for compression')
        return None

    try:
        segment = AudioSegment.from_file(
            BytesIO(data),
            format=_guess_format(audio_file.name),
        )
    except Exception:
        logger.exception(
            'Audio compression failed (ffmpeg may be missing). '
            'Install with: brew install ffmpeg'
        )
        return None

    if mono and segment.channels > 1:
        segment = segment.set_channels(1)

    out = BytesIO()
    segment.export(out, format='mp3', bitrate=bitrate)
    out.seek(0)

    base = os.path.splitext(os.path.basename(audio_file.name))[0]
    return ContentFile(out.read(), name=f'{base}.mp3')


def maybe_compress_audio_field(instance, field_name='audio', **kwargs):
    field = getattr(instance, field_name, None)
    if not field or not audio_field_changed(instance, field_name):
        return
    compressed = compress_audio_file(field, **kwargs)
    if compressed:
        setattr(instance, field_name, compressed)


class AudioCompressionMixin:
    audio_field_name = 'audio'

    def save(self, *args, **kwargs):
        maybe_compress_audio_field(self, self.audio_field_name)
        super().save(*args, **kwargs)
