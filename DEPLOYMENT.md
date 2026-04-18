# FYP — webMUSHRA Listening Tests

Subjective listening test platform for evaluating AI-generated music.
Three test types are run per listener: **MOS**, **A/B Preference**, and **Turing Test**.

---

## Folder Structure

```
fyp-webMUSHRA/
├── webMUSHRA/                  ← the web app (built on the open-source webMUSHRA platform)
│   ├── configs/
│   │   ├── audio/              ← audio clips served to listeners (NOT in git — add manually, see below)
│   │   │   ├── xlstm/          ← clip1.wav … clip20.wav
│   │   │   ├── museformer/     ← clip1.wav … clip20.wav
│   │   │   ├── lookback/       ← clip1.wav … clip20.wav
│   │   │   └── human/          ← human_clip1.wav … human_clip20.wav
│   │   └── randomized/         ← per-listener YAML configs (generated — see below)
│   ├── results/                ← participant results are saved here as CSV
│   ├── service/write.php       ← backend that writes results to disk
│   ├── Dockerfile              ← Docker image definition
│   ├── docker-compose.yml      ← runs the app on port 8000
│   └── generate_randomized_configs.py  ← script to generate per-listener configs
│
└── configs/
    └── randomized/             ← mirror copy of per-listener configs (also generated)
```

---

## Audio Files (not in git)

`.wav` files are excluded from this repository because they are too large.

You need to manually place the audio folders at:

```
webMUSHRA/configs/audio/
    xlstm/        → clip1.wav to clip20.wav
    museformer/   → clip1.wav to clip20.wav
    lookback/     → clip1.wav to clip20.wav
    human/        → human_clip1.wav to human_clip20.wav
```

Get these from the team (shared drive / USB).

---

## Generating Per-Listener Configs

Each listener gets their own randomly-assigned set of clips. Run this once after placing the audio files:

```bash
cd webMUSHRA
python generate_randomized_configs.py 30
```

This generates 30 sets of configs (listeners 1–30) inside `webMUSHRA/configs/randomized/`:
- `l1_mos.yaml`, `l1_ab.yaml`, `l1_turing.yaml`
- `l2_mos.yaml`, `l2_ab.yaml`, `l2_turing.yaml`
- … and so on up to `l30_*`

> **Listeners 1–20** are *Expert* (5 MOS criteria).  
> **Listeners 21–30** are *Non-Expert* (3 MOS criteria).

---

## Running the App (Docker)

```bash
cd webMUSHRA
docker-compose up
```

The app will be available at **http://localhost:8000**

To run in the background:

```bash
docker-compose up -d
```

To stop:

```bash
docker-compose down
```

---

## Assigning Tests to Listeners

Each listener should be given a URL for each of their three tests:

| Test | URL |
|------|-----|
| MOS | `http://<host>:8000?config=configs/randomized/l{N}_mos.yaml` |
| A/B | `http://<host>:8000?config=configs/randomized/l{N}_ab.yaml` |
| Turing | `http://<host>:8000?config=configs/randomized/l{N}_turing.yaml` |

Replace `{N}` with the listener number (e.g. `l3_mos.yaml` for listener 3).

---

## Collecting Results

Results are saved automatically to `webMUSHRA/results/` as CSV files when a participant submits their test.

These files persist on the host machine because `docker-compose.yml` mounts `./results` as a volume.

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.x (only needed to regenerate configs)
