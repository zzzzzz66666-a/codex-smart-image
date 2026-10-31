"""Bounded structural validation without third-party image decoders."""
import struct
import zlib


def valid_png(data):
    pos, compressed, header = 8, [], None
    try:
        while pos + 12 <= len(data):
            n = struct.unpack('>I', data[pos:pos+4])[0]
            tag = data[pos+4:pos+8]
            end = pos + 12 + n
            if end > len(data):
                return False
            body = data[pos+8:pos+8+n]
            crc = struct.unpack('>I', data[pos+8+n:end])[0]
            if zlib.crc32(tag + body) & 0xffffffff != crc:
                return False
            if header is None:
                if tag != b'IHDR' or n != 13:
                    return False
                header = struct.unpack('>IIBBBBB', body)
                w, h, depth, color, compression, filtering, interlace = header
                depths = {0:(1,2,4,8,16),2:(8,16),3:(1,2,4,8),4:(8,16),6:(8,16)}
                if (not 0 < w <= 32768 or not 0 < h <= 32768 or w*h > 100_000_000
                        or depth not in depths.get(color, ()) or compression or filtering or interlace not in (0,1)):
                    return False
            elif tag == b'IHDR':
                return False
            if tag == b'IDAT':
                compressed.append(body)
            if tag == b'IEND':
                if n or end != len(data) or not compressed:
                    return False
                channels = {0:1,2:3,3:1,4:2,6:4}[color]
                passes = [(0,0,1,1)] if interlace == 0 else [
                    (0,0,8,8),(4,0,8,8),(0,4,4,8),(2,0,4,4),
                    (0,2,2,4),(1,0,2,2),(0,1,1,2)]
                rows = []
                for x,y,dx,dy in passes:
                    pw = max(0,(w-x+dx-1)//dx)
                    ph = max(0,(h-y+dy-1)//dy)
                    if pw and ph:
                        rows.append((1+(pw*channels*depth+7)//8,ph))
                expected = sum(stride*count for stride,count in rows)
                if expected > 256*1024*1024:
                    return False
                decoder = zlib.decompressobj()
                decoded = decoder.decompress(b''.join(compressed), expected + 1)
                if not decoder.eof or decoder.unused_data or len(decoded) != expected:
                    return False
                cursor = 0
                for stride,count in rows:
                    for _ in range(count):
                        if decoded[cursor] > 4:
                            return False
                        cursor += stride
                return True
            pos = end
    except (ValueError, struct.error, zlib.error):
        pass
    return False


def valid_jpeg(data):
    pos, frame, scan = 2, False, False
    try:
        while pos < len(data):
            if data[pos] != 255:
                return False
            while pos < len(data) and data[pos] == 255:
                pos += 1
            marker = data[pos]
            pos += 1
            if marker == 0xd9:
                return frame and scan and pos == len(data)
            if marker == 0xd8 or marker == 0 or 0xd0 <= marker <= 0xd7:
                return False
            n = struct.unpack('>H', data[pos:pos+2])[0]
            if n < 2 or pos+n > len(data):
                return False
            if marker in (0xc0,0xc1,0xc2):
                if n < 8:
                    return False
                h,w = struct.unpack('>HH',data[pos+3:pos+7])
                frame = h > 0 and w > 0
            pos += n
            if marker == 0xda:
                if not frame:
                    return False
                scan = True
                while pos < len(data):
                    if data[pos] != 255:
                        pos += 1
                        continue
                    if pos+1 >= len(data):
                        return False
                    following = data[pos+1]
                    if following == 0 or 0xd0 <= following <= 0xd7:
                        pos += 2
                    else:
                        break
    except (IndexError,struct.error):
        pass
    return False


def valid_webp(data):
    if struct.unpack('<I',data[4:8])[0] + 8 != len(data):
        return False
    pos, frame = 12, False
    while pos + 8 <= len(data):
        tag = data[pos:pos+4]
        n = struct.unpack('<I',data[pos+4:pos+8])[0]
        end = pos+8+n
        if end > len(data):
            return False
        body = data[pos+8:end]
        if tag == b'VP8 ':
            frame = n >= 10 and body[3:6] == b'\x9d\x01\x2a' and struct.unpack('<H',body[6:8])[0]&0x3fff > 0 and struct.unpack('<H',body[8:10])[0]&0x3fff > 0
        elif tag == b'VP8L':
            frame = n >= 5 and body[0] == 0x2f
        pos = end + (n % 2)
    return frame and pos == len(data)
