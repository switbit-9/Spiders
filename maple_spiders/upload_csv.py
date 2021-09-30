import boto3

s3_client = boto3.client(
    "s3",
    aws_access_key_id="AKIAVMNGS2XJ4PBRXQ2C",
    aws_secret_access_key="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",
)
bucketname = "consultant-mehmet-output-bucket"


for key in s3_client.list_objects(Bucket=bucketname, MaxKeys=10, Prefix="hunan/csvs")[
    "Contents"
]:

    print(key["Key"])
    # break

# object_name = "hunan/csvs/output_20200907.csv"
# path = "output/output_20200907.csv"
# s3_client.upload_file(path, bucketname, object_name)


print("Done")


# s3_client.delete_object(Bucket=bucketname, Key=key['Key'])
