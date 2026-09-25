#!/usr/bin/env python3

import gzip
import urllib.request
import xml.etree.ElementTree as ET

SOURCE = "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz"

# Greenville / Spartanburg / Asheville stations
WANTED = {
    "WLOS-DT.us_locals1": "WLOS 13 ABC",
    "WHNS-DT.us_locals1": "WHNS 21 FOX Carolina",
    "WYFF-DT3.us_locals1": "CBS Carolina / WYFF 4.3",
}


def main():
    print("Downloading EPGShare US_LOCALS1...")

    with urllib.request.urlopen(SOURCE, timeout=120) as response:
        compressed_data = response.read()

    xml_data = gzip.decompress(compressed_data)
    root = ET.fromstring(xml_data)

    output = ET.Element(
        "tv",
        {
            "generator-info-name": "Greenville SC EPG",
            "source-info-name": "EPGShare US_LOCALS1",
        },
    )

    # Add channel definitions
    found_channels = set()

    for channel in root.findall("channel"):
        channel_id = channel.get("id")

        if channel_id in WANTED:
            output.append(channel)
            found_channels.add(channel_id)

    # Add program listings
    program_counts = {channel_id: 0 for channel_id in WANTED}

    for program in root.findall("programme"):
        channel_id = program.get("channel")

        if channel_id in WANTED:
            output.append(program)
            program_counts[channel_id] += 1

    # Verify that every requested station exists
    missing = set(WANTED) - found_channels

    if missing:
        raise RuntimeError(
            "Missing channel IDs in upstream EPG: "
            + ", ".join(sorted(missing))
        )

    # Verify that listings were actually found
    empty = [
        channel_id
        for channel_id, count in program_counts.items()
        if count == 0
    ]

    if empty:
        raise RuntimeError(
            "No program listings found for: "
            + ", ".join(empty)
        )

    # Make XML easier to read
    ET.indent(output, space="  ")

    tree = ET.ElementTree(output)

    # Write normal XMLTV file
    tree.write(
        "epg.xml",
        encoding="utf-8",
        xml_declaration=True,
    )

    # Create compressed version for TiviMate
    with open("epg.xml", "rb") as source_file:
        with gzip.open(
            "epg.xml.gz",
            "wb",
            compresslevel=9,
        ) as compressed_file:
            compressed_file.write(source_file.read())

    print()
    print("EPG successfully created.")

    for channel_id, count in program_counts.items():
        print(f"{channel_id}: {count} programs")


if __name__ == "__main__":
    main()
