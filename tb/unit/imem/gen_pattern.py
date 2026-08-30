#!/usr/bin/env python3
import sys

def main():
    depth = int(sys.argv[1])
    for addr in range(depth):
        word = 0x00000000 | addr
        print(f"{word:08x}")

if __name__ == "__main__":
    main()