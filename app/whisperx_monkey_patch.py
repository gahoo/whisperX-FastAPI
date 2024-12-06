from io import StringIO
from typing import TextIO
import re

LANGUAGES_WITHOUT_SPACES = ["ja", "zh"]

def result_writer_method__call__(self, result: dict, audio_path: str, options: dict):
    buffer = StringIO("")
    self.write_result(result, file=buffer, options=options)
    buffer.seek(0)
    return buffer.read()

def subtitles_writer_method_iterate_result(self, result: dict, options: dict):
    raw_max_line_width: Optional[int] = options["max_line_width"]
    max_line_count: Optional[int] = options["max_line_count"]
    highlight_words: bool = options["highlight_words"]
    max_line_width = 1000 if raw_max_line_width is None else raw_max_line_width
    preserve_segments = max_line_count is None or raw_max_line_width is None
    karaoke_style = bool = options.get("karaoke_style", False)

    if len(result["segments"]) == 0:
        return

    def iterate_subtitles():
        line_len = 0
        line_count = 1
        # the next subtitle to yield (a list of word timings with whitespace)
        subtitle: list[dict] = []
        times = []
        last = result["segments"][0]["start"]
        for segment in result["segments"]:
            for i, original_timing in enumerate(segment["words"]):
                timing = original_timing.copy()
                long_pause = not preserve_segments
                if "start" in timing:
                    long_pause = long_pause and timing["start"] - last > 3.0
                else:
                    long_pause = False
                has_room = line_len + len(timing["word"]) <= max_line_width
                seg_break = i == 0 and len(subtitle) > 0 and preserve_segments
                if line_len > 0 and has_room and not long_pause and not seg_break:
                    # line continuation
                    line_len += len(timing["word"])
                else:
                    # new line
                    timing["word"] = timing["word"].strip()
                    if (
                        len(subtitle) > 0
                        and max_line_count is not None
                        and (long_pause or line_count >= max_line_count)
                        or seg_break
                    ):
                        # subtitle break
                        yield subtitle, times
                        subtitle = []
                        times = []
                        line_count = 1
                    elif line_len > 0:
                        # line break
                        line_count += 1
                        timing["word"] = "\n" + timing["word"]
                    line_len = len(timing["word"].strip())
                subtitle.append(timing)
                times.append((segment["start"], segment["end"], segment.get("speaker")))
                if "start" in timing:
                    last = timing["start"]
        if len(subtitle) > 0:
            yield subtitle, times

    if result["language"] in LANGUAGES_WITHOUT_SPACES:
        delim = ""
    else:
        delim = " "

    if "words" in result["segments"][0]:
        for subtitle, _ in iterate_subtitles():
            sstart, ssend, speaker = _[0]
            subtitle_start = self.format_timestamp(sstart)
            subtitle_end = self.format_timestamp(ssend)
            subtitle_text = delim.join([word["word"] for word in subtitle])
            has_timing = any(["start" in word for word in subtitle])

            # add [$SPEAKER_ID]: to each subtitle if speaker is available
            prefix = ""
            if speaker is not None:
                prefix = f"[{speaker}]: "

            if highlight_words and has_timing:
                last = subtitle_start
                if karaoke_style:
                    yield subtitle_start, subtitle_end, prefix + delim.join([
                        "{word}<{end}>".format(word = each_word['word'], end = self.format_timestamp(each_word['end']))
                        for each_word in subtitle[:-1]
                        ]) + delim + subtitle[-1]['word']
                else:
                    all_words = [timing["word"] for timing in subtitle]
                    for i, this_word in enumerate(subtitle):
                        if "start" in this_word:
                            start = self.format_timestamp(this_word["start"])
                            end = self.format_timestamp(this_word["end"])
                            if last != start:
                                yield last, start, prefix + subtitle_text

                            yield start, end, prefix + delim.join(
                                [
                                    re.sub(r"^(\s*)(.*)$", r"\1<u>\2</u>", word)
                                    if j == i
                                    else word
                                    for j, word in enumerate(all_words)
                                ]
                            )
                            last = end
            else:
                yield subtitle_start, subtitle_end, prefix + subtitle_text
    else:
        for segment in result["segments"]:
            segment_start = self.format_timestamp(segment["start"])
            segment_end = self.format_timestamp(segment["end"])
            segment_text = segment["text"].strip().replace("-->", "->")
            if "speaker" in segment:
                segment_text = f"[{segment['speaker']}]: {segment_text}"
            yield segment_start, segment_end, segment_text

def write_vtt_method_write_result(self, result: dict, file: TextIO, options: dict):
    print("WEBVTT\n", file=file)
    if options['karaoke_style']:
        print("""
STYLE

::cue(:past) {
  color: yellow;
}

""", file=file)

    for start, end, text in self.iterate_result(result, options):
        print(f"{start} --> {end}\n{text}\n", file=file, flush=True)
