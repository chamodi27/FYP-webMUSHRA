"""
generate_randomized_configs.py

Generates per-listener YAML configs for webMUSHRA.
Each listener gets a random subset of the 20 clips per model.

Listeners 1–20  → Expert   (5 MOS criteria)
Listeners 21–30 → Non-expert (3 MOS criteria)

Usage:
    python generate_randomized_configs.py [num_listeners]
    (default: 30)
"""

import os
import random
import sys
from pathlib import Path

NUM_LISTENERS     = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SAMPLES_PER_MODEL = 20
OUTPUT_DIR        = Path("configs/randomized")
NUM_EXPERTS       = 20          # listeners 1-20 are experts

MODELS = ["xlstm", "museformer", "lookback"]

# ── Response scales ──────────────────────────────────────────────────────────

SCALE_OPTIONS = [
    ("1", "Bad"),
    ("2", "Poor"),
    ("3", "Fair"),
    ("4", "Good"),
    ("5", "Excellent"),
]

TURING_RESPONSE_BLOCK = """\
  response:
  - value: 0
    label: AI-generated
  - value: 1
    label: Human-composed"""

# ── MOS criteria ─────────────────────────────────────────────────────────────
# (key, display name, description)
# First 3 shown to everyone; last 2 are expert-only.

CRITERIA = [
    ("structural_coherence", "Structural Coherence",
     "The piece feels organized and coherent over time."),
    ("musical_flow", "Musical Flow",
     "The music progresses naturally."),
    ("overall_quality", "Overall Musical Quality",
     "Overall, this is a good musical composition."),
    ("motivic_consistency", "Motivic Consistency",       # expert only
     "The piece repeats and develops musical ideas in a consistent way."),
    ("harmonic_coherence", "Harmonic Coherence",         # expert only
     "The chord progression sounds natural and makes musical sense."),
]

NUM_EXPERT_CRITERIA    = 5
NUM_NONEXPERT_CRITERIA = 3

# ── Page builders ─────────────────────────────────────────────────────────────

def header(testname, testid):
    return f"""\
testname: {testname}
testId: {testid}
bufferSize: 4096
stopOnErrors: true
showButtonPreviousPage: true
remoteService: service/write.php
pages:
"""

def generic_page(page_id, title, content):
    return f"""\
- type: generic
  id: {page_id}
  name: {title}
  content: "{content}"
"""

def consent_page():
    return """\
- type: consent
  id: consent
  name: Consent
  mustConsent: true
  content: >
    <ol>
      <li>I have understood the information about the project, and the researchers have explained it to me.</li>
      <li>I understand that my responses will be recorded anonymously.</li>
      <li>I understand that my participation is voluntary.</li>
      <li>I understand that I will not have any personal benefit from the research, but it would benefit the research community.</li>
      <li>I understand that I am free to contact any of the people involved in the research to seek further clarification and information.</li>
      <li>I have the right to withdraw the data I have provided at any time, to the extent that they have not been used in any publication at the time of withdrawal.</li>
    </ol>
"""

def volume_page(path):
    return f"""\
- type: volume
  id: volume
  name: Volume Calibration
  content: "Please set your volume to a comfortable level using the clip below."
  defaultVolume: 0.5
  stimulus: {path}
"""

def finish_page(content, popup_content=None):
    popup_block = ""
    if popup_content:
        popup_block = f"""  popupContent: >\n    {popup_content}\n"""
    return f"""\
- type: finish
  name: Finish
  showResults: false
  writeResults: true
  content: "{content}"
{popup_block}  questionnaire:
    - type: text
      label: Participant ID
      name: participant_id
"""

def _scale_block():
    """One YAML list item (one Likert scale row) for the multi-scale response."""
    lines = ["  -"]
    for val, lbl in SCALE_OPTIONS:
        lines.append(f"    - value: {val}")
        lines.append(f"      label: {lbl}")
    return "\n".join(lines)


def mos_clip_page(page_id, path, criteria):
    """
    Single page per clip: plays audio once, shows one Likert scale row per criterion.
    criteria — list of (key, display_name, description) tuples.
    """
    # Build the numbered criteria list shown above the scales
def mos_clip_page(page_id, path, criteria, page_num, total=9):
    criteria_html = "".join(
        f"<li><strong>{name}</strong> &mdash; <em>{desc}</em></li>"
        for _, name, desc in criteria
    )
    content = (
        "<p>Listen to the clip fully, then rate it on each criterion below "
        "(one row per criterion):</p>"
        f"<ol>{criteria_html}</ol>"
    )

    # Build multi-scale response block — one sub-list per criterion
    scale_yaml = "  response:\n"
    for _ in criteria:
        scale_yaml += _scale_block() + "\n"

    return f"""\
- type: likert_single_stimulus
  id: {page_id}
  name: "Clip {page_num} of {total}"
  content: "{content}"
  showWaveform: false
  mustRate: true
  mustPlayback: ended
  stimuli:
    Clip: {path}
{scale_yaml}"""

def turing_likert_page(page_id, path, page_num, total=10):
    return f"""\
- type: likert_single_stimulus
  id: {page_id}
  name: "Clip {page_num} of {total}"
  content: "<p>Is this clip <strong>AI-generated</strong> or <strong>Human-composed</strong>?</p>"
  showWaveform: false
  mustRate: true
  mustPlayback: ended
  stimuli:
    Clip: {path}
{TURING_RESPONSE_BLOCK}
"""

AB_PREFERENCE_SCALE = (
    "  -\n"
    "    - value: prefer_a\n"
    "      label: \"Prefer A\"\n"
    "    - value: no_preference\n"
    "      label: \"No Preference\"\n"
    "    - value: prefer_b\n"
    "      label: \"Prefer B\""
)


def ab_pair_page(page_id, path_a, path_b, page_num, total=9):
    """
    One page per pair using likert_multi_stimulus.
    Both clips have their own play button.
    Q1 stimulus slot (path_a) answers structural coherence.
    Q2 stimulus slot (path_b) answers overall musical quality.
    """
    content = (
        "<p>Listen to both clips (Clip A and Clip B), then answer each question below:</p>"
        "<ul>"
        "<li><strong>Q1 &mdash; Structural Coherence:</strong> "
        "<em>Which clip feels more organized and coherent over time?</em></li>"
        "<li><strong>Q2 &mdash; Overall Musical Quality:</strong> "
        "<em>Which clip has better overall musical quality?</em></li>"
        "</ul>"
    )
    return f"""\
- type: likert_multi_stimulus
  id: {page_id}
  name: "Pair {page_num} of {total}"
  content: "{content}"
  mustRate: true
  mustPlayback: ended
  stimuli:
    "Q1 \u2014 Structural Coherence (Clip A)": {path_a}
    "Q2 \u2014 Overall Quality (Clip B)": {path_b}
  response:
    - value: prefer_a
      label: "Prefer A"
    - value: prefer_b
      label: "Prefer B"
"""

# ── Welcome text helpers ──────────────────────────────────────────────────────

def mos_welcome_content(is_expert):
    n = NUM_EXPERT_CRITERIA if is_expert else NUM_NONEXPERT_CRITERIA
    criteria_html = "".join(
        f"<li><strong>{name}</strong> — <em>{desc}</em></li>"
        for _, name, desc in CRITERIA[:n]
    )
    return (
        f"<p>This test has <strong>9 clips</strong>. "
        f"Listen to each clip fully, then rate it on <strong>{n} criteria</strong> "
        "using a 1–5 scale.</p>"
        f"<p><strong>Criteria:</strong></p><ol>{criteria_html}</ol>"
        "<p><strong>Wear headphones.</strong></p>"
    )

# ── Main generator ────────────────────────────────────────────────────────────

def generate_configs(num_listeners):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_clips  = {m: [f"clip{i}.wav" for i in range(1, SAMPLES_PER_MODEL + 1)] for m in MODELS}
    all_human  = [f"human_clip{i}.wav" for i in range(1, 21)]

    print(f"Generating {num_listeners} listener config sets...")

    for lid in range(1, num_listeners + 1):
        is_expert   = (lid <= NUM_EXPERTS)
        n_criteria  = NUM_EXPERT_CRITERIA if is_expert else NUM_NONEXPERT_CRITERIA
        active_crit = CRITERIA[:n_criteria]

        # ── Select random subsets ─────────────────────────────────────────────
        # MOS: 3 clips per model + 1 volume clip (from xlstm)
        mos = {m: random.sample(all_clips[m], 4 if m == "xlstm" else 3) for m in MODELS}
        volume_clip = mos["xlstm"].pop()   # 4th xlstm clip used for volume only

        # A/B: 6 clips per model (not overlapping with MOS)
        rem  = {m: list(set(all_clips[m]) - set(mos[m]) - ({volume_clip} if m == "xlstm" else set())) for m in MODELS}
        ab   = {m: random.sample(rem[m], 6) for m in MODELS}

        # Turing: 4 AI clips + 6 human clips
        rem2_pool = []
        for m in MODELS:
            used = set(mos[m]) | set(ab[m]) | ({volume_clip} if m == "xlstm" else set())
            rem2_pool += [(m, c) for c in all_clips[m] if c not in used]
        turing_ai    = random.sample(rem2_pool, min(4, len(rem2_pool)))
        turing_human = random.sample(all_human, min(6, len(all_human)))

        # ════════════════════════════════════════════════════════════════════
        # MOS CONFIG
        # ════════════════════════════════════════════════════════════════════
        vol_path = f"configs/audio/xlstm/{volume_clip}"
        out  = header(f"MOS Test — Listener {lid}", f"mos_l{lid}")
        out += generic_page("welcome", "Welcome", mos_welcome_content(is_expert))
        out += consent_page()
        out += volume_page(vol_path)

        # Pre-shuffle clips — one page per clip, all criteria on that page
        clip_list = [(m, clip) for m in MODELS for clip in mos[m]]
        random.shuffle(clip_list)

        for page_num, (m, clip) in enumerate(clip_list, start=1):
            path    = f"configs/audio/{m}/{clip}"
            page_id = f"mos_{m}_{clip.split('.')[0]}"
            out += mos_clip_page(page_id, path, active_crit, page_num)

        mos_popup = (
            '<p style="font-size:1.1em;">\u2705 Your MOS results have been saved!</p>'
            f'<p>Please continue to the <strong>A/B Preference Test</strong> (Part 2 of 3).</p>'
            '<p><em>Use the same Participant ID for all tests.</em></p>'
            f'<p style="margin-top:1em;"><a href="?config=randomized/l{lid}_ab.yaml" '
            'data-role="button" data-inline="true" data-theme="b" '
            'style="font-size:1.1em;">Continue to A/B Test \u2192</a></p>'
        )
        out += finish_page(
            "<p>Thank you for completing the MOS test! Please fill in the details below and click <strong>Send</strong>.</p>",
            popup_content=mos_popup
        )
        (OUTPUT_DIR / f"l{lid}_mos.yaml").write_text(out, encoding="utf-8")

        # ════════════════════════════════════════════════════════════════════
        # A/B CONFIG
        # ════════════════════════════════════════════════════════════════════
        out  = header(f"A/B Preference Test — Listener {lid}", f"ab_l{lid}")
        out += generic_page("welcome", "Welcome",
            "<p>This test has <strong>9 pairs</strong> of music clips. "
            "Listen to both clips in each pair, then answer 2 questions "
            "about which you prefer.</p>"
            "<p><strong>Wear headphones.</strong></p>")
        out += consent_page()

        pair_blocks = []
        comparisons = [
            ("xlstm",      "museformer"),
            ("xlstm",      "lookback"),
            ("museformer", "lookback"),
        ]
        pair_idx = 0
        for (mA, mB) in comparisons:
            for i in range(3):
                clip_a = ab[mA][pair_idx % 3 if mA == comparisons[0][0] else i]
                clip_b = ab[mB][i]
                path_a = f"configs/audio/{mA}/{clip_a}"
                path_b = f"configs/audio/{mB}/{clip_b}"

                if random.choice([True, False]):
                    path_a, path_b = path_b, path_a

                pid = f"{mA}_{mB}_{i}"
                pair_blocks.append(
                    lambda pn, _pid=f"ab_{pid}", _pa=path_a, _pb=path_b:
                        ab_pair_page(_pid, _pa, _pb, pn)
                )
            pair_idx += 3

        random.shuffle(pair_blocks)
        for page_num, block_fn in enumerate(pair_blocks, start=1):
            out += block_fn(page_num)

        ab_popup = (
            '<p style="font-size:1.1em;">\u2705 Your A/B comparison results have been saved!</p>'
            f'<p>Please continue to the <strong>Turing Test</strong> (Part 3 of 3 \u2014 final!).</p>'
            '<p><em>Use the same Participant ID for all tests.</em></p>'
            f'<p style="margin-top:1em;"><a href="?config=randomized/l{lid}_turing.yaml" '
            'data-role="button" data-inline="true" data-theme="b" '
            'style="font-size:1.1em;">Continue to Turing Test \u2192</a></p>'
        )
        out += finish_page(
            "<p>Thank you for completing the A/B test! Please fill in the details below and click <strong>Send</strong>.</p>",
            popup_content=ab_popup
        )
        (OUTPUT_DIR / f"l{lid}_ab.yaml").write_text(out, encoding="utf-8")

        # ════════════════════════════════════════════════════════════════════
        # TURING CONFIG
        # ════════════════════════════════════════════════════════════════════
        out  = header(f"Turing Test — Listener {lid}", f"turing_l{lid}")
        out += generic_page("welcome", "Welcome",
            "<p>This test has <strong>10 clips</strong>. "
            "Some are composed by humans, others are AI-generated.</p>"
            "<p>Listen to each clip fully, then choose: "
            "<strong>AI-generated</strong> or <strong>Human-composed</strong>?</p>"
            "<p><strong>Wear headphones.</strong></p>")
        out += consent_page()

        # Pre-shuffle Turing clips in Python
        turing_clips = (
            [(m, clip, "ai") for (m, clip) in turing_ai] +
            [("human", clip, "human") for clip in turing_human]
        )
        random.shuffle(turing_clips)

        for page_num, (model_or_type, clip, clip_type) in enumerate(turing_clips, start=1):
            if clip_type == "ai":
                path    = f"configs/audio/{model_or_type}/{clip}"
                page_id = f"turing_ai_{model_or_type}_{clip.split('.')[0]}"
            else:
                path    = f"configs/audio/human/{clip}"
                page_id = f"turing_human_{clip.split('.')[0]}"
            out += turing_likert_page(page_id, path, page_num)

        turing_popup = (
            '<p style="font-size:1.3em;">\U0001f389 All done!</p>'
            '<p style="font-size:1.1em;">You have completed all 3 listening tests.<br>'
            'Thank you for your participation!</p>'
        )
        out += finish_page(
            "<p>Thank you for completing the Turing test! Please fill in the details below and click <strong>Send</strong>.</p>",
            popup_content=turing_popup
        )
        (OUTPUT_DIR / f"l{lid}_turing.yaml").write_text(out, encoding="utf-8")

    print(f"Done. {num_listeners} sets of configs written to ./{OUTPUT_DIR}/")

if __name__ == "__main__":
    generate_configs(NUM_LISTENERS)
