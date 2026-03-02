resource "aws_s3_bucket" "demo" {
  bucket = "drift-demo-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_versioning" "demo_versioning" {
  bucket = aws_s3_bucket.demo.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}