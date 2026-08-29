# lib-x-assetlake

A lightweight Python library for managing **data assets** and **compute jobs** across local filesystems, AWS, and Alibaba Cloud.

Think of it as a unified way to describe "what data lives where" and "what jobs run where" — without writing different code for each platform.

---

## Install

```bash
pip install lib-x-assetlake           # core (local filesystem + DuckDB)
pip install "lib-x-assetlake[aws]"    # + AWS (S3, Glue, Step Functions)
pip install "lib-x-assetlake[aliyun]" # + Alibaba Cloud (OSS)
```

---

## Concepts

Three building blocks:

| Concept | What it is |
|---------|-----------|
| **Access** | Credentials for a platform (local, AWS, Aliyun) |
| **Asset** | A dataset described by a glob path (e.g. `s3://bucket/data/**/*.parquet`) |
| **Compute** | A job or script that can be triggered or monitored (Glue, Step Functions, local Python) |

---

## Access — credentials

An Access object holds the credentials needed to talk to a platform. Create one and pass it to assets or compute jobs.

```python
from assetlake import LocalAccess, AWSAccess, AliyunAccess

# Local — no credentials needed
local = LocalAccess(name="my-local")

# AWS — uses boto3 credential chain by default (env vars, ~/.aws, IAM role)
aws = AWSAccess(name="prod-aws", region="us-east-1")

# AWS — explicit keys
aws = AWSAccess(
    name="prod-aws",
    access_key_id="AKIA...",
    access_key_secret="...",
    region="us-east-1",
)

# Alibaba Cloud
aliyun = AliyunAccess(
    name="prod-oss",
    access_key_id="LTAI...",
    access_key_secret="...",
)

# Load from a dict (useful when config comes from a file or env)
from assetlake import AccessFactory

aws = AccessFactory.load({"platform": "aws", "name": "prod", "region": "us-east-1"})

# Inspect without exposing secrets
print(aws.describe())  # keys are masked: "AKID******"
```

---

## Asset — datasets

An Asset describes a collection of files using a glob pattern. You can list what files exist, filter by time, and run quality checks.

### Local files

```python
from assetlake import LocalAsset

asset = LocalAsset(
    glob="/data/exports/**/*.parquet",
    name="daily-exports",
    owner="xing",
)

# List all matching files, newest first
objects = asset.inspect()
for obj in objects:
    print(obj.uri, obj.size, obj.modified_at)

# Filter by time
from datetime import datetime, timezone

objects = asset.inspect(
    since=datetime(2024, 1, 1, tzinfo=timezone.utc),
    limit=10,
)

# Data quality check (parquet only) — returns row counts, null rates, etc.
stats = asset.quality()
```

### S3 (AWS)

```python
from assetlake import S3Asset, AWSAccess

asset = S3Asset(
    glob="s3://my-bucket/warehouse/orders/**/*.parquet",
    name="orders",
    region="us-east-1",
)
access = AWSAccess(name="prod")

objects = asset.inspect(access=access)
stats = asset.quality(access=access)
```

### OSS (Alibaba Cloud)

```python
from assetlake import OSSAsset, AliyunAccess

asset = OSSAsset(
    glob="oss://my-bucket/data/**/*.parquet",
    region="cn-hangzhou",
    name="raw-events",
)
access = AliyunAccess(name="prod", access_key_id="...", access_key_secret="...")

objects = asset.inspect(access=access)
```

### Factory — load an asset from a dict

Useful when asset definitions come from a config file or database.

```python
from assetlake import AssetFactory

asset = AssetFactory.load(
    {
        "filesystem": "s3",
        "glob": "s3://my-bucket/data/**/*.parquet",
        "region": "us-east-1",
    }
)
```

### Partitioned assets

If your paths encode partition keys (e.g. `year=2024/month=01`), they are automatically extracted.

```python
asset = S3Asset(glob="s3://bucket/events/year=*/month=*/*.parquet")

objects = asset.inspect(access=access)
for obj in objects:
    print(obj.partitions)  # {"year": "2024", "month": "01"}
```

---

## Compute — jobs

A Compute object represents a job that can be triggered or monitored.

### Local Python function

Run a Python function in-process or in a background subprocess.

```python
from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

job = PyEntrypointCompute(
    name="my-etl",
    entrypoint="mypackage.jobs.etl.run",  # dotted import path to a callable
)

# Run synchronously and get the result
result = job.execute(params={"date": "2024-01-01"})

# Run in a background subprocess and get a handle
handle = job.submit(params={"date": "2024-01-01"})
result = handle.result(timeout=60)  # blocks until done
```

### AWS Glue

```python
from assetlake.control.compute.glue import GlueJobCompute
from assetlake import AWSAccess

job = GlueJobCompute(name="my-glue-job", region="us-east-1")
access = AWSAccess(name="prod")

# Trigger the job
job.execute(params={"--date": "2024-01-01"}, access=access)

# List recent runs
runs = job.inspect(access=access, limit=10)
for run in runs:
    print(run["run_id"], run["state"], run["started_on"])
```

### AWS Step Functions

```python
from assetlake.control.compute.stepfunction import StepFunctionCompute
from assetlake import AWSAccess

sfn = StepFunctionCompute(
    name="my-pipeline",
    arn="arn:aws:states:us-east-1:123456789:stateMachine:my-pipeline",
)
access = AWSAccess(name="prod")

# Start an execution
sfn.execute(params={"date": "2024-01-01"}, access=access)

# List recent executions
runs = sfn.inspect(access=access, limit=5)
```

---

## Development

```bash
make install   # install dependencies
make test      # run tests
make lint      # format + lint with ruff
make build     # build wheel for distribution
make upload    # upload to PyPI
```
