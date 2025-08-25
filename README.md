# Standalone Encryption Script

This script replaces the `aws-encryption-cli` functionality with **built-in encryption capabilities**. It's completely self-contained with no external dependencies beyond standard Python modules.

## Key Features

- **Truly standalone**: No external encryption libraries needed
- **Built-in encryption**: All encryption code is included in the script
- **Proper IV handling**: The IV is correctly included in the metadata
- **S3-ready output**: Metadata formatted for `aws s3 cp` command

## Dependencies

**Required:**
- Python 3.6+
- boto3 (for AWS KMS integration)

**Included in script (no external installation needed):**
- AES-GCM encryption implementation
- KMS data key generation
- Metadata formatting
- All encryption constants and logic

## Usage

### Basic Usage
```bash
python encrypt_standalone.py input_file [kms_key_arn]
```

### With Environment Variable
```bash
export KMS_KEY_ARN="arn:aws:kms:us-east-1:123456789012:key/your-key-id"
python encrypt_standalone.py input_file
```

### In Bash Script (replacing aws-encryption-cli)
```bash
#!/bin/bash

# Your original script:
# aws-encryption-cli --encrypt \
#     --input "$new_file" \
#     --output "$new_file".enc \
#     --wrapping-keys key="$KMS_KEY_ARN" \
#     --encryption-context purpose=vendor-file-transfer \
#     --metadata-output metadata.json

# New approach using the standalone script:
echo "Encrypting $new_file"

# Encrypt and capture metadata
metadata=$(python encrypt_standalone.py "$new_file" "$KMS_KEY_ARN")

# Upload to S3 with metadata
aws s3 cp "$new_file".enc s3://your-bucket/path/ \
    --metadata="$metadata

## Output Format

The script outputs metadata to stdout in the format required by `aws s3 cp`:

```
x-amz-cek-alg=AES/GCM/NoPadding,x-amz-wrap-alg=kms,x-amz-tag-len=128,x-amz-unencrypted-content-length=99,x-amz-iv=YEP,x-amz-matdesc={"kms_cmk_id": "arn:aws:kms:..."},x-amz-key-v2=LOTSOFCHAARACTERS==
```

## Advantages over aws-encryption-cli

1. **Proper IV handling**: The IV is correctly included in the metadata
2. **No external dependencies**: All encryption code is built-in
3. **Consistent format**: Metadata format matches what's expected by S3
4. **Reliable**: No need to parse binary files or extract IVs
5. **Portable**: Single script that can be deployed anywhere

## Technical Details

The script implements:
- **AES-256-GCM encryption** with random IV generation
- **KMS integration** for secure key management
- **Proper metadata generation** following AWS S3 standards
- **Error handling** with appropriate exit codes

## Requirements

- Python 3.6+
- boto3
- AWS credentials configured
- KMS key ARN

## Error Handling

- Script exits with code 1 on errors
- Error messages are written to stderr
- Success output (metadata) is written to stdout
- Status messages are written to stderr
