import json
import sys
import hashlib
# import bencodepy - available if you need it!
# import requests - available if you need it!

# Examples:
#
# - decode_bencode(b"5:hello") -> b"hello"
# - decode_bencode(b"10:hello12345") -> b"hello12345"
def decode_bencode(bencoded_value):
    if chr(bencoded_value[0]).isdigit():
        return decode_bencode_str(bencoded_value)
    elif chr(bencoded_value[0]) == 'i':
        return decode_bencode_int(bencoded_value)
    elif chr(bencoded_value[0]) == 'l':
        lst, p = decode_bencode_list(bencoded_value)
        return lst
    elif chr(bencoded_value[0]) == 'd':
        dct,p =decode_bencoded_dict(bencoded_value)
        return dct
    else:
        raise NotImplementedError("Only strings are supported at the moment")

def decode_bencode_str(bencoded_value):
    first_colon_index = bencoded_value.find(b":")
    if first_colon_index == -1:
        raise ValueError("Invalid encoded value")
    return bencoded_value[first_colon_index+1:]

def decode_bencode_int(bencoded_value):
    end_index = bencoded_value.find(b"e")
    if end_index == -1:
        raise ValueError("incorrect format for integer")
    return int(bencoded_value[1:end_index])

def decode_bencode_list(bencoded_value):
    decoded_list: list = []
    i=1
    while i <len(bencoded_value) and chr(bencoded_value[i])!='e':
        if(chr(bencoded_value[i]).isdigit()):
            size: int = 0
            while(chr(bencoded_value[i]).isdigit()):
                size = size*10 + (bencoded_value[i]-48)
                i +=1
            i -=1
            decoded_str = decode_bencode_str(bencoded_value[i:i+2+size])
            decoded_list.append(decoded_str)
            i = i+2+size
        elif(chr(bencoded_value[i])=='i'):
            end_index = bencoded_value[i:].find(b"e")
            decoded_int = decode_bencode_int(bencoded_value[i:i+1+end_index])
            decoded_list.append(decoded_int)
            i = i+end_index+1
        elif(chr(bencoded_value[i])=='l'):
            nested_list, pointer = decode_bencode_list(bencoded_value[i:])
            decoded_list.append(nested_list)
            i = i+ pointer+1
    return decoded_list,i

def decode_bencoded_dict(bencoded_value):
    decoded_dict: dict = {}
    decoded_list: list = []
    i=1
    j=0
    while i <len(bencoded_value) and chr(bencoded_value[i])!='e':
        if(chr(bencoded_value[i]).isdigit()):
            size: int = 0
            while(chr(bencoded_value[i]).isdigit()):
                size = size*10 + (bencoded_value[i]-48)
                i +=1
            i -=1
            decoded_str = decode_bencode_str(bencoded_value[i:i+2+size])
            decoded_list.append(decoded_str)
            i = i+2+size
        elif(chr(bencoded_value[i])=='i'):
            end_index = bencoded_value[i:].find(b"e")
            decoded_int = decode_bencode_int(bencoded_value[i:i+1+end_index])
            decoded_list.append(decoded_int)
            i = i+end_index+1
        elif(chr(bencoded_value[i])=='l'):
            lst,pointer = decode_bencode_list(bencoded_value[i:])
            decoded_list.append(lst)
            i = i + pointer + 1
        elif(chr(bencoded_value[i])=='d'):
            dt, pointer = decode_bencoded_dict(bencoded_value[i:])
            decoded_list.append(dt)
            i = i + pointer +1
    while j<len(decoded_list):
        if(type(decoded_list[j])!=int):
            decoded_dict[decoded_list[j].decode('utf-8')] = decoded_list[j+1]
        else:
            decoded_dict[decoded_list[j]] = decoded_list[j+1]
        j += 2
    return decoded_dict,i

def bencode(data):
    """
    Bencodes a Python object into a byte string.

    Args:
        data: The Python object to bencode. Can be bytes, int, list, or dict.

    Returns:
        bytes: The bencoded representation of the data.

    Raises:
        TypeError: If the data type is not supported.
    """
    if isinstance(data, bytes):
        # Byte string: <length>:<string>
        return str(len(data)).encode('utf-8') + b':' + data
    elif isinstance(data, int):
        # Integer: i<integer>e
        return b'i' + str(data).encode('utf-8') + b'e'
    elif isinstance(data, list):
        # List: l<bencoded_element1><bencoded_element2>...e
        encoded_elements = [bencode(item) for item in data]
        return b'l' + b''.join(encoded_elements) + b'e'
    elif isinstance(data, dict):
        # Dictionary: d<bencoded_key1><bencoded_value1><bencoded_key2><bencoded_value2>...e
        # Keys must be byte strings and sorted lexicographically
        encoded_items = []
        # Sort keys lexicographically (important for standard Bencoding)
        for key in sorted(data.keys()):
            if not isinstance(key, bytes): 
                encoded_items.append(bencode(key.encode('utf-8')))
            else:
                encoded_items.append(bencode(key))
            encoded_items.append(bencode(data[key]))
        return b'd' + b''.join(encoded_items) + b'e'
    else:
        raise TypeError(f"Unsupported data type for bencoding: {type(data)}")

def main():
    command = sys.argv[1]

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    if command == "decode":
        bencoded_value = sys.argv[2].encode()

        # json.dumps() can't handle bytes, but bencoded "strings" need to be
        # bytestrings since they might contain non utf-8 characters.
        #
        # Let's convert them to strings for printing to the console.
        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode()

            raise TypeError(f"Type not serializable: {type(data)}")

        # Uncomment this block to pass the first stage
        print(json.dumps(decode_bencode(bencoded_value), default=bytes_to_str))
    elif command == "info":
        torrent_file = sys.argv[2]
        try:
            with open(torrent_file, 'rb') as f: #open the file in binary read mode ('rb') to ensure you're reading the raw byte content 
                bencoded_data = f.read()
            decoded_file = decode_bencode(bencoded_data)
            #print(decoded_file["info"])
            bencoded_info_dict = bencode(decoded_file["info"])
            #print(str.encode(bencoded_info_dict))
            #decoded_info,sz = decode_bencoded_dict(str.encode(bencoded_info_dict))
            #print(bencoded_info_dict)
            #print(bencoded_data)
            print("Tracker URL:", decoded_file["announce"].decode())
            print("Length:", decoded_file["info"]["length"])
            print("Info Hash:", hashlib.sha1(bencoded_info_dict).hexdigest())
            print("Piece Length:", decoded_file["info"]["piece length"])
            print("Pieces Hashes:")
            index=0
            while index<60:
                #print(decoded_file["info"]["pieces"][index:index+20])
                print(decoded_file["info"]["pieces"][index:index+20].hex())
                index += 20
        except FileNotFoundError:
            print(f"Error: File not found at {torrent_file}")
            raise Exception

    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
