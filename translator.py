import string
import argparse


BLACKLIST = ">? "
TO_CONVERT = [chr(i) for i in range(0x40) if chr(i) not in BLACKLIST] + ["~", chr(0x7F)]

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", type=argparse.FileType("r"),
                        help="The file to translate")

    return parser.parse_args()

def translate(decoded):
    encoded = ""
    for c in decoded:
        if c not in TO_CONVERT:
            encoded += c
        else:
            encoded += "!" + chr(ord(c) ^ 0x40)
    return encoded

def main():
    args = parse_args()
    print(translate(args.input_file.read()))

if __name__ == "__main__":
    main()
