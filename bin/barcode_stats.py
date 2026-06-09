#!/usr/bin/env python
"""Summarise demultiplexed barcode output files."""

import argparse
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys


BARCODE_RE = re.compile(r"^(barcode\d+|unclassified)$", re.IGNORECASE)
BARCODE_SEARCH_RE = re.compile(r"(barcode\d+|unclassified)", re.IGNORECASE)


def infer_barcode(path):
    """Infer barcode name from a demultiplexed output path."""
    for part in reversed(Path(path).parts):
        if BARCODE_RE.match(part):
            return part
    match = BARCODE_SEARCH_RE.search(str(path))
    if match:
        return match.group(1)
    return "unknown"


def count_fastq(path):
    """Count reads in a FASTQ file."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle) // 4


def count_xam(path):
    """Count records in a BAM/CRAM file with samtools."""
    result = subprocess.run(
        ["samtools", "view", "-c", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip() or 0)


def count_reads(path):
    """Count reads in supported demux output files."""
    suffixes = "".join(Path(path).suffixes).lower()
    if suffixes.endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz")):
        return count_fastq(path)
    if suffixes.endswith((".bam", ".cram")):
        return count_xam(path)
    sys.stderr.write(f"WARNING: unsupported barcode output skipped: {path}\n")
    return 0


def main(args):
    """Run entry point."""
    summaries = {}
    for fname in args.inputs:
        path = Path(fname)
        barcode = infer_barcode(path)
        if barcode not in summaries:
            summaries[barcode] = {
                "barcode": barcode,
                "files": 0,
                "reads": 0,
            }
        summaries[barcode]["files"] += 1
        summaries[barcode]["reads"] += count_reads(path)

    barcodes = sorted(summaries.values(), key=lambda item: item["barcode"])
    output = {
        "barcodes": barcodes,
        "total_reads": sum(item["reads"] for item in barcodes),
        "total_files": sum(item["files"] for item in barcodes),
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle)


def argparser():
    """Argument parser for entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs", nargs="*", help="Demultiplexed BAM/CRAM/FASTQ files.")
    parser.add_argument(
        "--output", required=True, help="Output JSON summary.")
    return parser


if __name__ == "__main__":
    parser = argparser()
    main(parser.parse_args())
