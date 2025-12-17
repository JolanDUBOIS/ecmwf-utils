import itertools
import subprocess
import time
from pathlib import Path
import csv
import yaml

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

ROOT_PATH = Path(__file__).parent.parent

CONFIG_PATH = ROOT_PATH / "config/config.yml"
COST_DIR = ROOT_PATH / "data/landing-test-costs-2/queries_cost"

CMD = [
    "/home/jolan/miniforge3/bin/mamba", "run", "-n", "ecmwf-utils",
    "python", "-m", "src", "retrieval", "--skip-query"
]

# Full variable list (uncommented variables or all possible ones)
ALL_VARIABLES = [
    'mx2t3','mn2t3','10fg3','10fg','mx2t6','mn2t6','10fg6','sd','sf','cp',
    'lsp','msl','10u','10v','2t','2d','mx2t','mn2t','tp','100u','100v'
]

OUTPUT_CSV = "variable_costs.csv"


def update_config(vars_list):
    with open(CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)

    data["variables"] = vars_list

    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(data, f)


def latest_cost_file():
    files = sorted(COST_DIR.glob("ecmwf_cost_*.txt"),
                   key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def parse_all_cost_fields(path):
    """Parse all key=value; lines into a dict."""
    out = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and line.endswith(";"):
                key, val = line[:-1].split("=", 1)
                key = key.strip()
                val = val.strip()
                # convert to int when possible
                try:
                    val = int(val)
                except ValueError:
                    pass
                out[key] = val
    return out


def main():
    header_written = False

    with open(OUTPUT_CSV, "w", newline="") as f:
        pass

    combinations = []

    for v in ALL_VARIABLES:
        combinations.append([v])

    for a, b in itertools.combinations(ALL_VARIABLES, 2):
        combinations.append([a, b])

    print(f"Total runs: {len(combinations)}")

    for i, combo in enumerate(combinations, 1):
        print(f"[{i}/{len(combinations)}] {combo}")

        update_config(combo)

        print("Running command:", " ".join(CMD))
        subprocess.run(CMD, check=True)

        time.sleep(1.2)
        cost_file = latest_cost_file()

        if not cost_file:
            print("No cost file found.")
            continue

        fields = parse_all_cost_fields(cost_file)

        timestamp = cost_file.stat().st_mtime
        fields["timestamp"] = timestamp

        fields["variables"] = ",".join(combo)

        if not header_written:
            with open(OUTPUT_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields.keys())
                writer.writeheader()
                writer.writerow(fields)
            header_written = True
        else:
            with open(OUTPUT_CSV, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields.keys())
                writer.writerow(fields)


if __name__ == "__main__":
    main()