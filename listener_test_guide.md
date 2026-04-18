# Listener Experience Guide — Music Generation Listening Tests

> **What a participant sees, screen by screen, across all three sub-tests.**
> This document also covers technical implementation details and how results are stored.

The full study consists of three independent tests:

| Test | Purpose | Pages |
|------|---------|-------|
| **MOS** | Rate individual clips on multiple musical quality criteria | 9 stimulus pages |
| **A/B** | Compare pairs of clips on two criteria | 9 pair pages |
| **Turing** | Classify each clip as human-composed or AI-generated | 10 stimulus pages |

Each test is a separate webMUSHRA session with its own URL:
- `http://localhost:8000/?config=randomized/l{N}_mos.yaml`
- `http://localhost:8000/?config=randomized/l{N}_ab.yaml`
- `http://localhost:8000/?config=randomized/l{N}_turing.yaml`

---

## Participant Groups

| Group | Listener IDs | MOS criteria rated |
|-------|--------------|--------------------|
| **Expert** | 1 – 20 | 5 criteria |
| **Non-Expert** | 21 – 30 | 3 criteria |

A/B and Turing tests are identical for both groups.

---

## Shared Element — Consent Page

**webMUSHRA page type:** `consent`  
**Used in:** all three tests, after the Welcome page.

**Content shown (6 numbered statements):**

> 1. I have understood the information about the project, and the researchers have explained it to me.
> 2. I understand that my responses will be recorded anonymously.
> 3. I understand that my participation is voluntary.
> 4. I understand that I will not have any personal benefit from the research, but it would benefit the research community.
> 5. I understand that I am free to contact any of the people involved in the research to seek further clarification and information.
> 6. I have the right to withdraw the data I have provided at any time, to the extent that they have not been used in any publication at the time of withdrawal.

**Answer method:** Single **"I Agree"** button. `mustConsent: true` — the listener cannot proceed without clicking it.

---

---

## Test 1 — MOS (Mean Opinion Score)

### Implementation

**webMUSHRA page type:** `likert_single_stimulus` (multi-scale variant)

Each clip is presented on a **single page** with **one audio player**. All rating criteria appear as stacked Likert scale rows below the player. The listener hears the clip **once** and rates all criteria before clicking Next.

**YAML structure per clip page:**
```yaml
- type: likert_single_stimulus
  id: mos_xlstm_clip5
  name: "Clip Rating"
  content: "<p>Listen to the clip fully, then rate it on each criterion below...</p>"
  showWaveform: false
  mustRate: true
  mustPlayback: ended
  stimuli:
    Clip: configs/audio/xlstm/clip5.wav
  response:
    -                         # Row 1 — Structural Coherence
      - value: 1
        label: Bad
      - value: 2
        label: Poor
      - value: 3
        label: Fair
      - value: 4
        label: Good
      - value: 5
        label: Excellent
    -                         # Row 2 — Musical Flow (same options)
      - value: 1
        label: Bad
      - value: 2
        label: Poor
      - value: 3
        label: Fair
      - value: 4
        label: Good
      - value: 5
        label: Excellent
    -                         # Row 3 — Overall Musical Quality (same)
      ...
    -                         # Row 4 — Motivic Consistency (experts only)
      ...
    -                         # Row 5 — Harmonic Coherence (experts only)
      ...
```

**Key constraints:**
- `mustPlayback: ended` — clip must finish playing before rating rows activate
- `mustRate: true` — all rows must be filled before Next is enabled
- Clip order is pre-shuffled in Python per listener (no YAML `random` block needed)

---

### Page Flow

#### Page 1 — Welcome
**Content (Expert version):**
> This test has **9 clips**. Listen to each clip fully, then rate it on **5 criteria** using a 1–5 scale.
>
> **Criteria:**
> 1. Structural Coherence — *The piece feels organized and coherent over time.*
> 2. Musical Flow — *The music progresses naturally.*
> 3. Overall Musical Quality — *Overall, this is a good musical composition.*
> 4. Motivic Consistency — *The piece repeats and develops musical ideas in a consistent way.*
> 5. Harmonic Coherence — *The chord progression sounds natural and makes musical sense.*
>
> **Wear headphones.**

**Content (Non-Expert version):** Same but lists only criteria 1–3.

#### Page 2 — Consent *(see shared section)*

#### Page 3 — Volume Calibration
**webMUSHRA page type:** `volume`

> Please set your volume to a comfortable level using the clip below.

Audio player with a volume slider (default 50%). No rating required.

#### Pages 4–12 — Clip Rating Pages *(9 pages, randomized order)*

**Title:** Clip N of 9

**Content:**
> Listen to the clip fully, then rate it on each criterion below (one row per criterion):
> 1. **Structural Coherence** — *The piece feels organized and coherent over time.*
> 2. **Musical Flow** — *The music progresses naturally.*
> 3. **Overall Musical Quality** — *Overall, this is a good musical composition.*
> *(Experts also see:)*
> 4. **Motivic Consistency** — *The piece repeats and develops musical ideas in a consistent way.*
> 5. **Harmonic Coherence** — *The chord progression sounds natural and makes musical sense.*

**UI:** One audio player (no waveform). Must finish playing before rating rows activate.

**Answer method:** Stacked 5-point Likert rows — one per criterion.

| Value | Label |
|-------|-------|
| 1 | Bad |
| 2 | Poor |
| 3 | Fair |
| 4 | Good |
| 5 | Excellent |

**Page counts:**
- Non-experts: 9 pages (3 criteria × 1 row each)
- Experts: 9 pages (5 criteria × 1 row each)

#### Final Page — Finish & Questionnaire
**webMUSHRA page type:** `finish` with `questionnaire`

> Thank you for completing the MOS test! Your results have been saved.

**Follow-up questionnaire:**

| Participant ID | Free text | Identifier assigned by researcher |

Results are written to the server automatically on this page.
---

### MOS Results Storage

**File path:** `results/mos_l{N}/lss.csv`

> [!WARNING]
> The MOS CSV contains **two different row formats** depending on when results were flushed. Use only the **multi-column rows** (which include participant info) for analysis — they are the complete records written at the end of the session.

---

#### Row Type A — Intermediate rows (written per page, older format)

These rows exist if the test was ever run with an older single-scale config. They have **5 columns**:

```
session_test_id , trial_id              , stimuli_rating , stimuli , rating_time
mos_l1          , mos_lookback_clip17   ,              2 , Clip    ,       73344
mos_l1          , mos_xlstm_clip17      ,              4 , Clip    ,       73067
```

| Column | Type | Description |
|--------|------|-------------|
| `session_test_id` | string | Test session ID — matches `testId` in the YAML (e.g. `mos_l1`) |
| `trial_id` | string | Page ID — encodes model and clip (e.g. `mos_xlstm_clip17` = xLSTM, clip 17) |
| `stimuli_rating` | integer 1–5 | Single overall rating (old single-scale format only) |
| `stimuli` | string | Always `Clip` (the stimulus label from the YAML) |
| `rating_time` | integer (ms) | Time spent on this page in milliseconds |

---

#### Row Type B — Final rows (written at finish page, current format)

These are the rows produced by the **current multi-scale config**. They have **extra columns** because webMUSHRA prepends the finish-page questionnaire answers, and the multi-scale response writes one value per criterion:

```
session_test_id , participant_id , age , music_background , trial_id              , [rating1, rating2, ...] , stimuli , rating_time
mos_l1          , 01             ,  25 , novice           , mos_xlstm_clip8       , 4, 4, 4, 4, 4           , Clip    ,       77827
mos_l1          , 01             ,  25 , novice           , mos_museformer_clip4  , 4, 5, 4, 5, 4           , Clip    ,       75119
```

| Column | Type | Description |
|--------|------|-------------|
| `session_test_id` | string | Test session ID (e.g. `mos_l1`) |
| `participant_id` | string | ID entered by listener in the finish questionnaire |
| `age` | integer | Age entered in the finish questionnaire |
| `music_background` | string | `novice` / `intermediate` / `expert` from finish questionnaire |
| `trial_id` | string | Page ID — encodes model and clip (e.g. `mos_xlstm_clip8`) |
| `rating1` | integer 1–5 | **Structural Coherence** rating |
| `rating2` | integer 1–5 | **Musical Flow** rating |
| `rating3` | integer 1–5 | **Overall Musical Quality** rating |
| `rating4` | integer 1–5 | **Motivic Consistency** rating *(experts only; absent for non-experts)* |
| `rating5` | integer 1–5 | **Harmonic Coherence** rating *(experts only; absent for non-experts)* |
| `stimuli` | string | Always `Clip` |
| `rating_time` | integer (ms) | Time spent on this page |

> [!NOTE]
> The ratings appear in the **same order as the criteria defined in the YAML** — Structural Coherence first, Harmonic Coherence last. Non-expert rows have 3 rating columns; expert rows have 5.

**How to decode `trial_id`:**

| `trial_id` example | Model | Clip |
|--------------------|-------|------|
| `mos_xlstm_clip8` | xLSTM | clip8.wav |
| `mos_museformer_clip4` | Museformer | clip4.wav |
| `mos_lookback_clip11` | Lookback RNN | clip11.wav |

---
---

## Test 2 — A/B Pairwise Preference

### Implementation

**webMUSHRA page type:** `likert_multi_stimulus`

Each pair of clips is presented on a **single page** with **two audio players** (one per clip). Two response rows below allow the listener to answer Q1 and Q2 without replaying audio.

The stimuli slots are labelled to double as question identifiers:
- Slot `"Clip A — Q1 Structural Coherence"` → plays one model's clip
- Slot `"Clip B — Q2 Overall Quality"` → plays the other model's clip

The listener plays both, then answers Q1 in Row 1 and Q2 in Row 2.

**YAML structure per pair page:**
```yaml
- type: likert_multi_stimulus
  id: ab_xlstm_museformer_0
  name: "A vs B Comparison"
  content: "<p>Use the play buttons to listen to Clip A and Clip B...</p>"
  mustRate: true
  stimuli:
    "Clip A — Q1 Structural Coherence": configs/audio/xlstm/clip5.wav
    "Clip B — Q2 Overall Quality":      configs/audio/museformer/clip3.wav
  response:
    - value: prefer_a
      label: "Prefer A"
    - value: prefer_b
      label: "Prefer B"
```

**Key design decisions:**
- A/B assignment is **randomly flipped** per pair in Python to eliminate positional bias
- Pair order is **pre-shuffled** per listener in Python
- **Forced choice** — no "No Preference" option; listener must pick A or B for each question
- `mustRate: true` — both rows must be answered before Next activates

---

### Page Flow

#### Page 1 — Welcome
> This test has **9 pairs** of music clips. Listen to both clips in each pair, then answer 2 questions about which you prefer.
>
> **Wear headphones.**

#### Page 2 — Consent *(see shared section)*

#### Pages 3–11 — Pair Comparison Pages *(9 pages, shuffled order)*

**Title:** Pair N of 9

**Content:**
> Use the play buttons to listen to **Clip A** and **Clip B**, then answer each question in the row below it:
> - **Row 1 (Clip A button):** Q1 — *Which clip has better structural coherence?*
> - **Row 2 (Clip B button):** Q2 — *Which clip has better overall musical quality?*

**UI:** Two audio players (one per clip), each with its own Play/Pause button. No waveform.

**Answer method:** Two forced-choice rows (one per question)

| Value | Label |
|-------|-------|
| prefer_a | Prefer A |
| prefer_b | Prefer B |

**Pair breakdown:**

| Comparison | Pairs |
|------------|-------|
| xLSTM vs Museformer | 3 pairs |
| xLSTM vs Lookback | 3 pairs |
| Museformer vs Lookback | 3 pairs |

#### Final Page — Finish & Questionnaire
> Thank you for completing the A/B preference test!

**Follow-up questionnaire:** Participant ID only (free text).

---

### A/B Results Storage

**File path:** `results/ab_l{N}/lms.csv`

The A/B CSV has a **consistent format** — one row per stimulus slot per page (2 rows per pair page):

```
session_test_id , participant_id , age , music_background , trial_id              , stimuli_rating , stimuli                             , rating_time
ab_l1           , 01             ,  25 , novice           , ab_xlstm_museformer_0 ,  prefer_a      , Clip A — Q1 Structural Coherence    ,        4010
ab_l1           , 01             ,  25 , novice           , ab_xlstm_museformer_0 ,  prefer_a      , Clip B — Q2 Overall Quality         ,        4010
```

| Column | Type | Description |
|--------|------|-------------|
| `session_test_id` | string | Test session ID (e.g. `ab_l1`) |
| `participant_id` | string | ID entered in finish questionnaire |
| `age` | integer | Age from finish questionnaire |
| `music_background` | string | `novice` / `intermediate` / `expert` |
| `trial_id` | string | Pair page ID — encodes which models are compared and which pair index (e.g. `ab_xlstm_museformer_0` = xLSTM vs Museformer, pair 0) |
| `stimuli_rating` | string | `prefer_a` or `prefer_b` — listener's choice for this question |
| `stimuli` | string | **Which question this row answers** — `"Clip A — Q1 Structural Coherence"` or `"Clip B — Q2 Overall Quality"` |
| `rating_time` | integer (ms) | Time spent on this page (same value for both rows of a pair) |

**How to decode `trial_id`:**

| `trial_id` example | Comparison | Pair index |
|--------------------|------------|------------|
| `ab_xlstm_museformer_0` | xLSTM vs Museformer | 0 |
| `ab_xlstm_lookback_2` | xLSTM vs Lookback | 2 |
| `ab_museformer_lookback_1` | Museformer vs Lookback | 1 |

**How to interpret `stimuli_rating`:**

> [!IMPORTANT]
> `prefer_a` and `prefer_b` refer to the **A/B slot**, NOT to a fixed model. Because clips are randomly swapped per pair (to avoid positional bias), you must check the generated YAML (`configs/randomized/l{N}_ab.yaml`) to find which model's clip was assigned to the A slot and which to the B slot for each pair.

| `stimuli` value | Question answered |
|-----------------|------------------|
| `Clip A — Q1 Structural Coherence` | Which clip has better structural coherence? |
| `Clip B — Q2 Overall Quality` | Which clip has better overall musical quality? |

---
---

## Test 3 — Turing Test (Human or AI?)

### Implementation

**webMUSHRA page type:** `likert_single_stimulus` (single-scale variant)

Each clip is presented on a **single page** with **one audio player**. One binary-choice row (AI-generated / Human-composed) appears below. The listener must finish listening before the choice activates.

**YAML structure per clip page:**
```yaml
- type: likert_single_stimulus
  id: turing_ai_xlstm_clip9
  name: Human or AI?
  content: "<p>Listen to the clip. Is it AI-generated or Human-composed?</p>"
  showWaveform: false
  mustRate: true
  mustPlayback: ended
  stimuli:
    Clip: configs/audio/xlstm/clip9.wav
  response:
    - value: 0
      label: AI-generated
    - value: 1
      label: Human-composed
```

**Clip composition per listener (randomized):**
- 4 AI-generated clips (drawn from unused clips across xLSTM, Museformer, Lookback)
- 6 human-composed clips (drawn from `configs/audio/human/`)
- All 10 presented in random order pre-shuffled in Python

---

### Page Flow

#### Page 1 — Welcome
> This test has **10 clips**. Some are composed by humans, others are AI-generated.
>
> Listen to each clip fully, then choose: **AI-generated** or **Human-composed**?
>
> **Wear headphones.**

#### Page 2 — Consent *(see shared section)*

#### Pages 3–12 — Clip Judgement Pages *(10 pages, randomized order)*

**Title:** Clip N of 10

**Content:**
> Is this clip **AI-generated** or **Human-composed**?

**UI:** One audio player (no waveform). Must finish playing before choice activates.

**Answer method:** Binary forced choice

| Value | Label |
|-------|-------|
| 0 | AI-generated |
| 1 | Human-composed |

#### Final Page — Finish & Questionnaire
> Thank you for completing the Turing test!

**Follow-up questionnaire:** Participant ID only (free text).

---

### Turing Results Storage

**File path:** `results/turing_l{N}/lss.csv`

**Format — one row per clip:**

```
session_test_id, trial_id, stimuli_rating, stimuli, rating_time
```

**Example:**
```
session_test_id  , trial_id                      , stimuli_rating , stimuli , rating_time
turing_l1        , turing_ai_xlstm_clip9         ,             0  , Clip    ,       45320
turing_l1        , turing_human_human_clip3       ,             1  , Clip    ,       38900
```

**Column reference:**

| Column | Description |
|--------|-------------|
| `session_test_id` | Test session ID (e.g. `turing_l1`) |
| `trial_id` | Page ID — encodes whether the clip is AI or human and which model/clip |
| `stimuli_rating` | `0` = chose AI-generated, `1` = chose Human-composed |
| `stimuli` | Always `Clip` |
| `rating_time` | Time spent on the page in milliseconds |

> [!NOTE]
> Ground truth: page IDs starting with `turing_ai_` are AI clips; `turing_human_` are human clips. Compare `stimuli_rating` against this ground truth to compute detection accuracy.

---

## Summary — Page Types Used

| Test | webMUSHRA page type | Why chosen |
|------|---------------------|------------|
| MOS rating pages | `likert_single_stimulus` (multi-scale) | Plays one clip; supports stacked Likert rows for multiple criteria on one page |
| A/B pair pages | `likert_multi_stimulus` | Renders one play button per stimulus — both Clip A and Clip B are independently playable; one response row per stimulus doubles as Q1/Q2 |
| Turing pages | `likert_single_stimulus` (single-scale) | Plays one clip; single binary-choice row |
| Consent | `consent` | Renders 6-statement list with a mandatory "I Agree" button |
| Volume calibration | `volume` | Volume slider + audio preview |
| Welcome/intro | `generic` | Plain HTML content, no audio |
| End of test | `finish` | Writes results to server; renders demographic questionnaire |

---

## Summary — Constraints & UX Rules

| Rule | Applies to |
|------|-----------|
| Clip must finish before rating activates (`mustPlayback: ended`) | MOS pages, Turing pages |
| All rating rows must be filled before Next activates (`mustRate: true`) | MOS pages, A/B pages, Turing pages |
| Consent must be given (`mustConsent: true`) | Consent pages in all tests |
| Clip order pre-shuffled per listener (Python) | MOS, Turing |
| Pair order pre-shuffled per listener (Python) | A/B |
| A/B clip-to-slot assignment randomly flipped per pair | A/B |
| No waveform shown (`showWaveform: false`) | All stimulus pages |
| Previous Page button available | All tests |
| Expert listeners (1–20): 5 MOS criteria | MOS |
| Non-expert listeners (21–30): 3 MOS criteria | MOS |
