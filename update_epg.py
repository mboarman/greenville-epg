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

    # EPGShare may reject requests without browser-style headers.
    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Referer": "https://epgshare01.online/",
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        compressed_data = response.read()

    print(
        f"Downloaded {len(compressed_data) / 1024 / 1024:.2f} MB"
    )

    # Decompress the XMLTV data
    xml_data = gzip.decompress(compressed_data)

    print("Parsing XMLTV data...")

    root = ET.fromstring(xml_data)

    output = ET.Element(
        "tv",
        {
            "generator-info-name": "Greenville SC EPG",
            "source-info-name": "EPGShare US_LOCALS1",
        },
    )

    # Find requested channel definitions
    found_channels = set()

    for channel in root.findall("channel"):
        channel_id = channel.get("id")

        if channel_id in WANTED:
            output.append(channel)
            found_channels.add(channel_id)
            print(f"Found channel: {channel_id}")

    # Make sure all three channels were found
    missing_channels = set(WANTED) - found_channels

    if missing_channels:
        raise RuntimeError(
            "Missing channel IDs in upstream EPG: "
            + ", ".join(sorted(missing_channels))
        )

    # Extract program listings
    program_counts = {
        channel_id: 0
        for channel_id in WANTED
    }

    for program in root.findall("programme"):
        channel_id = program.get("channel")

        if channel_id in WANTED:
            output.append(program)
            program_counts[channel_id] += 1

    # Make sure each station actually has listings
    empty_channels = [
        channel_id
        for channel_id, count in program_counts.items()
        if count == 0
    ]

    if empty_channels:
        raise RuntimeError(
            "No program listings found for: "
            + ", ".join(empty_channels)
        )

    # Format XML nicely
    ET.indent(output, space="  ")

    tree = ET.ElementTree(output)

    # Create normal XMLTV file
    tree.write(
        "epg.xml",
        encoding="utf-8",
        xml_declaration=True,
    )

    # Create compressed XMLTV file for TiviMate
    with open("epg.xml", "rb") as source_file:
        with gzip.open(
            "epg.xml.gz",
            "wb",
            compresslevel=9,
        ) as compressed_file:
            compressed_file.write(source_file.read())

    print()
    print("EPG successfully created.")
    print()

    for channel_id, count in program_counts.items():
        print(
            f"{WANTED[channel_id]} "
            f"({channel_id}): {count} programs"
        )

    print()
    print("Created:")
    print("  epg.xml")
    print("  epg.xml.gz")


if __name__ == "__main__":
    main()
