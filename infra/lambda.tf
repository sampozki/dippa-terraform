resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 30
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name = "${var.name}-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [

      # CloudWatch logs
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "${aws_cloudwatch_log_group.lambda.arn}:*"
      },

      # Allow Terraform S3 backend to discover and read the monitored state.
      {
        Effect = "Allow",
        Action = ["s3:ListBucket"],
        Resource = "arn:aws:s3:::${var.state_bucket}"
      },

      # Read only specific Terraform state file
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:HeadObject"
        ],
        Resource = "arn:aws:s3:::${var.state_bucket}/${var.state_key}"
      },

      # SNS publish
      {
        Effect = "Allow",
        Action = ["sns:Publish"],
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_lambda_function" "this" {
  function_name = var.name
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = var.ecr_image_uri

  timeout     = 900
  memory_size = 512

  environment {
    variables = {
      STATE_BUCKET   = var.state_bucket
      STATE_KEY      = var.state_key
      STATE_REGION   = var.state_region
      SNS_TOPIC_ARN  = aws_sns_topic.alerts.arn
      RESULTS_BUCKET = var.results_bucket
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda
  ]
}
