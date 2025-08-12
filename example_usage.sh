#!/bin/bash

# Example script showing how to use the standalone encryption script
# This replaces the aws-encryption-cli approach

# Set your KMS key ARN
KMS_KEY_ARN="<KEY_ARN>"

# Example file to encrypt
INPUT_FILE="<FILE_NAME>"

# Example bucket name
BUCKET_NAME="<BUCKET_NAME>"

echo "=== Example: Encrypting $INPUT_FILE ==="

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found"
    exit 1
fi

echo "Input file: $INPUT_FILE"
echo "KMS Key: $KMS_KEY_ARN"
echo

# Encrypt the file and capture metadata
echo "Encrypting $INPUT_FILE..."
metadata=$(python encrypt_standalone.py "$INPUT_FILE" "$KMS_KEY_ARN")

# Check if encryption was successful
if [ $? -ne 0 ]; then
    echo "Error: Encryption failed"
    exit 1
fi

echo "Encryption successful!"
echo "Output file: $INPUT_FILE.enc"
echo

# Display the metadata that would be used with aws s3 cp
echo "Metadata for aws s3 cp:"
echo "$metadata"
echo

# Example of how you would use this with aws s3 cp
echo "Example S3 upload command:"
echo "aws s3 cp $INPUT_FILE.enc $BUCKET_NAME \\"
echo "    --metadata \"$metadata\""
echo

# Verify the encrypted file was created
if [ -f "$INPUT_FILE.enc" ]; then
    echo "✓ Encrypted file created: $INPUT_FILE.enc"
    echo "  Original size: $(stat -c%s "$INPUT_FILE") bytes"
    echo "  Encrypted size: $(stat -c%s "$INPUT_FILE.enc") bytes"
else
    echo "✗ Encrypted file not found"
    exit 1
fi

echo
echo "=== Example completed successfully ==="
