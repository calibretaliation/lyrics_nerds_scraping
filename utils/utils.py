import hashlib

def hash_string_to_number(string):
    # Create an SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Convert the string to bytes and update the hash object
    sha256_hash.update(string.encode('utf-8'))

    # Get the hexadecimal representation of the hash value
    hash_value = sha256_hash.hexdigest()

    # Convert the hexadecimal hash value to an integer
    hash_int = int(hash_value, 16)

    # Map the integer to an 8-digit number within the desired range
    mapped_number = hash_int % 100000000

    return mapped_number