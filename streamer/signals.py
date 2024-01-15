from django.dispatch import Signal  # type: ignore[import]

finished_frame = Signal(["instance", "sender", "image_byte"])
