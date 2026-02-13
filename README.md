# Back-of-the-Envelope Calculator

A Streamlit web app for quick back-of-the-envelope estimations during system design. Type informal math expressions like `30 billion * 500 bytes` and instantly see human-friendly results like `15 TB`.

## How to run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Features

- **Natural expressions** — write math the way you speak: `500 million / month`, `30 billion * 500 bytes`
- **Auto-formatting** — results are shown in the most readable unit (bytes to PB, numbers to billions)
- **Time shorthands** — divide by `month`, `day`, `hour`, `minute`, `year` directly in expressions
- **Rate conversion** — use the Rate dropdown to convert between /s, /min, /hour, /day, /month, /year
- **Copyable summary** — all estimates displayed in a code block with a built-in copy button

## Supported syntax

| Type | Supported values |
|------|-----------------|
| Scale words | `thousand`, `million`, `billion`, `trillion` |
| Scale suffixes | `K`, `M`, `B`, `T` (e.g., `20K`, `1.7B`) |
| Data units | `bytes`, `KB`, `MB`, `GB`, `TB`, `PB` |
| Time divisors | `/ second`, `/ minute`, `/ hour`, `/ day`, `/ month`, `/ year` |
| Rate dropdown | `/s`, `/min`, `/hour`, `/day`, `/month`, `/year` |
| Operators | `+`, `-`, `*`, `/`, `()` |

## Examples

Below are real-world examples from a URL shortening service system design, grouped by estimate type.

### Traffic estimates

| # | Label | Expression | Rate | Result |
|---|-------|-----------|------|--------|
| 1 | Total redirections | `100 * 500 million` | none | 50 billion |
| 2 | New URLs per second | `500 million / month` | /s | ~193/s |
| 3 | New URLs per minute | `500 million / month` | /min | ~12K/min |
| 4 | Redirections per second | `100 * 200` | /s | 20K/s |
| 5 | Daily redirections | `20000 * 3600 * 24` | none | ~1.7 billion |

### Storage estimates

| # | Label | Expression | Rate | Result |
|---|-------|-----------|------|--------|
| 6 | Objects over 5 years | `500 million * 5 * 12` | none | 30 billion |
| 7 | Total storage | `30 billion * 500 bytes` | none | 15 TB |
| 8 | Storage per month | `500 million * 500 bytes` | none | 250 GB |

### Bandwidth estimates

| # | Label | Expression | Rate | Result |
|---|-------|-----------|------|--------|
| 9 | Incoming data | `200 * 500 bytes` | /s | 100 KB/s |
| 10 | Outgoing data | `20000 * 500 bytes` | /s | 10 MB/s |
| 11 | Daily incoming | `200 * 500 bytes` | /day | 100 KB/day |

### Memory estimates

| # | Label | Expression | Rate | Result |
|---|-------|-----------|------|--------|
| 12 | Daily requests | `20000 * 3600 * 24` | none | ~1.7 billion |
| 13 | Cache size (20%) | `0.2 * 1.7 billion * 500 bytes` | none | 170 GB |

### More examples

| # | Label | Expression | Rate | Result |
|---|-------|-----------|------|--------|
| 14 | Messages per day | `1 billion / month` | /day | ~33 million/day |
| 15 | Image storage/year | `10 million * 200 KB` | none | 2 TB |
| 16 | Writes per hour | `500 million / month` | /hour | ~694K/hour |
| 17 | Video bandwidth | `1000 * 5 MB` | /s | 5 GB/s |
| 18 | Log volume per day | `50000 * 1 KB` | /day | 50 MB/day |

### Typical summary output

After entering estimates, the summary section shows all results in a copyable block:

```
Total redirections: 100 * 500 million = 50 billion
New URLs/s: 500 million / month = ~193/s
Redirections/s: 100 * 200 = 20K/s
Total storage (5y): 30 billion * 500 bytes = 15 TB
Incoming data: 200 * 500 bytes = 100 KB/s
Outgoing data: 20000 * 500 bytes = 10 MB/s
Cache size: 0.2 * 1.7 billion * 500 bytes = 170 GB
```
