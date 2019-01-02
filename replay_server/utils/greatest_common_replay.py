from io import RawIOBase, SEEK_END, FileIO
from plistlib import Dict
from typing import List

from replay_server.logger import logger
from replay_server.replay_parser.replay_parser.parser import parse

__all__ = (
    'get_greatest_common_stream',
    'get_replay',
)


def _get_stream_part(buffer: RawIOBase, position: int, size: int) -> bytearray:
    """
    Reads reads part of stream from position, with some size
    """
    previous_position = buffer.tell()
    buffer.seek(position)
    stream_part = buffer.read(size)
    buffer.seek(previous_position)
    return bytearray(stream_part)


def get_greatest_common_stream(
        buffers: List[RawIOBase],
        buffers_positions: List[int],
        position: int,
        size: int =-1
) -> bytearray:
    """
    That method will return greatest common stream from position, with some size.
    """

    greatest_common_stream = None
    greatest_common_count = 0

    # for one or two streams no reason to check if there is any common part
    if len(buffers) == 1:
        return _get_stream_part(buffers[0], buffers_positions[0] + position, size)

    stream_information = get_common_buffers_info(buffers, buffers_positions, position, size)
    stream_keys = stream_information.keys()

    # choose which part has most common hits.
    for file_no in stream_keys:
        common_size = len(stream_information[file_no]["common_file_nos"])
        if greatest_common_count < common_size:
            greatest_common_stream = stream_information[file_no]["stream_part"]
            greatest_common_count = common_size

    return greatest_common_stream


def get_common_buffers_info(
        buffers: List[RawIOBase],
        buffers_positions: List[int],
        position: int,
        size: int = -1
) -> Dict:
    """
    Collects "common" data
    """
    # file handler id, file length, common stream matches
    stream_information: Dict[int, Dict[str, int]] = {}

    # get buffers information: file handler id and file length
    for i, buffer in enumerate(buffers):
        file_no = buffer.fileno()
        current_position = buffer.tell()
        buffer.seek(0, SEEK_END)
        file_size = buffer.tell()
        buffer.seek(current_position)
        stream_part = _get_stream_part(buffer, buffers_positions[i] + position, size)
        stream_information[file_no] = {"file_size": file_size, "stream_part": stream_part}

    # compare everybody to everybody
    stream_file_nos = stream_information.keys()
    for file_no1 in stream_file_nos:
        for file_no2 in stream_file_nos:
            stream_information[file_no1].setdefault("common_file_nos", [])
            if file_no1 == file_no2:
                continue
            stream_part1 = stream_information[file_no1]["stream_part"]
            stream_part2 = stream_information[file_no2]["stream_part"]
            if stream_part2 in stream_part1:
                # register common hit count
                stream_information[file_no1]["common_file_nos"].append(file_no2)

    return stream_information


def get_replay(paths: List[str]) -> str:
    """
    Problem: during the game some people can loose connectivity between them, so somebody being dropped out.
    But all of them are still streaming replays. So there are multiple "truth" created.

    Method will return sorted list of common groups, with biggest common replay.
    That biggest one should be saved and streamed.
    """
    logger.debug("Finding greatest common replay stream for paths: %s", str(paths))
    file_nos: Dict[int, str] = {}  # list of buffers file handler ids
    buffers: List[RawIOBase] = []
    try:
        for path in paths:
            buffer = FileIO(path, "rb")
            buffers.append(buffer)
            file_nos[buffer.fileno()] = path

        body_positions = []
        for buffer in buffers:
            try:
                replay = parse(buffer)
                body_positions.append(replay['body_offset'])
            except ValueError as e:
                logger.exception("Wrong replay structure")
                continue

        # get replay common map
        buffers_common_info = get_common_buffers_info(
            buffers,
            body_positions,
            0
        )

        # delete unused parts
        for file_no in buffers_common_info:
            del buffers_common_info[file_no]["stream_part"]

        # sort buffers by their
        sorted_buffers_by_most_common_use = sorted(
            buffers_common_info,
            key=lambda file_no: len(buffers_common_info[file_no]["common_file_nos"]),
            reverse=True
        )

        # remove less common replays from map
        for file_no in sorted_buffers_by_most_common_use:
            if file_no in buffers_common_info:
                for sub_part_file_no in buffers_common_info[file_no]["common_file_nos"]:
                    del buffers_common_info[sub_part_file_no]

        return [file_nos[buffer.fileno()]
                for buffer in buffers
                if buffer.fileno() in buffers_common_info.keys()][0]

    finally:
        # behave like a good boy
        for buffer in buffers:
            buffer.close()
