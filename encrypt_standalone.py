#!/usr/bin/env python3
"""
Standalone encryption script with built-in encryption functionality.
Replaces aws-encryption-cli functionality and outputs metadata for aws s3 cp.

Usage: python encrypt_standalone.py input_file [kms_key_arn]

No external dependencies beyond standard Python modules and boto3.
"""

import sys
import os
import base64
import json
import secrets
import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# S3 Object Metadata Keys (copied from TNC library)
HEADER_ALG = "x-amz-cek-alg"
HEADER_WRAP_ALG = "x-amz-wrap-alg"
HEADER_TAG_LEN = "x-amz-tag-len"
HEADER_KEY = "x-amz-key-v2"
HEADER_IV = "x-amz-iv"
HEADER_MATDESC = "x-amz-matdesc"
HEADER_CONTENT_LENGTH = "x-amz-unencrypted-content-length"

# S3 Metadata Default Values (copied from TNC library)
HEADER_ALG_VALUE = "AES/GCM/NoPadding"
HEADER_WRAP_ALG_VALUE = "kms"
HEADER_TAG_LEN_VALUE = 128


def get_encryption_aes_key(kms_client, kms_key):
    """
    Generate a key to encrypt the data.
    Copied from TNC library.
    """
    encryption_context = {'kms_cmk_id': kms_key}

    kms_resp = kms_client.generate_data_key(
        KeyId=kms_key,
        EncryptionContext=encryption_context,
        KeySpec='AES_256'
    )

    key_metadata = base64.b64encode(kms_resp['CiphertextBlob']).decode()

    return kms_resp['Plaintext'], encryption_context, key_metadata


def encrypt_data(file_input, kms_client, kms_key):
    """
    Encrypt the contents of a file and produce associated metadata.
    Copied from TNC library.
    """
    # Generate a random 12-byte IV for AES-GCM
    iv = secrets.token_bytes(12)

    # Get encryption key from KMS
    aes_key, matdesc_metadata, key_metadata = get_encryption_aes_key(
        kms_client=kms_client,
        kms_key=kms_key
    )

    # Create AES-GCM cipher
    aesgcm = AESGCM(aes_key)

    # Encrypt the data
    encrypted_body = aesgcm.encrypt(iv, file_input, None)

    # Create metadata
    metadata = {
        HEADER_ALG: HEADER_ALG_VALUE,
        HEADER_WRAP_ALG: HEADER_WRAP_ALG_VALUE,
        HEADER_TAG_LEN: str(HEADER_TAG_LEN_VALUE),
        HEADER_CONTENT_LENGTH: str(len(file_input)),
        HEADER_IV: base64.b64encode(iv).decode(),
        HEADER_MATDESC: json.dumps(matdesc_metadata),
        HEADER_KEY: key_metadata
    }

    return encrypted_body, metadata


def encrypt_file(input_file, kms_key_arn):
    """
    Encrypt a file using the built-in encryption functionality.
    
    Args:
        input_file: Path to input file
        kms_key_arn: KMS key ARN for encryption
        
    Returns:
        tuple: (success, metadata_dict, error_message)
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            return False, None, f"Input file not found: {input_file}"
        
        # Read the input file
        with open(input_file, 'rb') as f:
            file_content = f.read()
        
        # Create KMS client
        kms_client = boto3.client('kms')
        
        # Encrypt the file using built-in function
        encrypted_body, metadata = encrypt_data(file_content, kms_client, kms_key_arn)
        
        # Write encrypted content to output file
        output_file = input_file + '.enc'
        with open(output_file, 'wb') as f:
            f.write(encrypted_body)
        
        return True, metadata, None
        
    except Exception as e:
        return False, None, str(e)


def format_metadata_for_s3_cp(metadata):
    """
    Format metadata for use with aws s3 cp command.
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        String in format: KeyName1=string,KeyName2=string
    """
    formatted_pairs = []
    
    for key, value in metadata.items():
        # Convert value to string and escape any commas
        value_str = str(value).replace(',', '\\,')
        formatted_pairs.append(f"{key}={value_str}")
    
    return ','.join(formatted_pairs)


def main():
    """Main function."""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python encrypt_standalone.py input_file [kms_key_arn]", 
              file=sys.stderr)
        print("If kms_key_arn is not provided, KMS_KEY_ARN environment variable will be used", 
              file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Get KMS key ARN from command line or environment
    if len(sys.argv) >= 3:
        kms_key_arn = sys.argv[2]
    else:
        kms_key_arn = os.getenv('KMS_KEY_ARN')
        if not kms_key_arn:
            print("Error: KMS key ARN not provided and KMS_KEY_ARN environment variable not set", 
                  file=sys.stderr)
            sys.exit(1)
    
    # Encrypt the file
    success, metadata, error = encrypt_file(input_file, kms_key_arn)
    
    if not success:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Output the metadata in the format needed for aws s3 cp
    metadata_string = format_metadata_for_s3_cp(metadata)
    print(metadata_string)
    
    # Also output some info to stderr for user feedback
    output_file = input_file + '.enc'
    print(f"File encrypted successfully: {output_file}", file=sys.stderr)
    print(f"Metadata: {len(metadata)} tags", file=sys.stderr)


if __name__ == "__main__":
    main()
