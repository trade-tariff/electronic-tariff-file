import sys
from classes.aws_bucket import AwsBucket


if len(sys.argv) > 1:
    pattern = sys.argv[1]
else:
    print("Please specify a pattern")
    sys.exit()
aws_bucket = AwsBucket()
aws_bucket.delete_by_pattern(pattern)