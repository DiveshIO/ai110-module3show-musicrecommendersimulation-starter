flowchart TD
    %% ── INPUT ───────────────────────────────────────────────
    subgraph INPUT["INPUT"]
        UP(["user_prefs\ngenre · mood · energy"])
        CSV(["data/songs.csv\n18 songs"])
    end

    %% ── LOAD ────────────────────────────────────────────────
    subgraph LOAD["LOAD"]
        LS["load_songs(csv_path)\n→ List[Dict]"]
    end

    %% ── PROCESS ─────────────────────────────────────────────
    subgraph PROCESS["PROCESS — Scoring Loop"]
        direction TB
        FOR["For each song in catalog"]
        SS["score_song(user_prefs, song)"]
        RET["returns (score, reasons)\ne.g. 0.73 · 'genre match, mood match'"]
        FOR --> SS --> RET
        RET -->|"next song →"| FOR
    end

    %% ── OUTPUT ──────────────────────────────────────────────
    subgraph OUTPUT["OUTPUT — Ranking"]
        SORT["Sort all scored songs\nhighest score → lowest"]
        TOPK["Slice top k  (default k = 5)"]
        REC(["Top K Recommendations\nsong · score · explanation"])
        SORT --> TOPK --> REC
    end

    %% ── CONNECTIONS ─────────────────────────────────────────
    CSV  --> LS
    LS   -->|"List[Dict] songs"| FOR
    UP   -->|"user_prefs dict"| FOR
    RET  -->|"all songs scored"| SORT

    %% ── STYLES ──────────────────────────────────────────────
    style INPUT   fill:#1e3a5f,color:#cce,stroke:#4488bb
    style LOAD    fill:#1a3a2a,color:#cec,stroke:#44bb66
    style PROCESS fill:#3a2a1a,color:#edc,stroke:#bb8844
    style OUTPUT  fill:#2a1a3a,color:#dce,stroke:#8844bb
    style UP      fill:#264d80,stroke:#4488bb,color:#fff
    style CSV     fill:#264d80,stroke:#4488bb,color:#fff
    style REC     fill:#4a2a6a,stroke:#8844bb,color:#fff
```
