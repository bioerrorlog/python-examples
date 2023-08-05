from typing import Dict, List
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3


def create_dummy_data(rows: int = 1000) -> pd.DataFrame:
    data: Dict[str, List] = {
        'id': range(1, rows + 1),
        'name': [f'name_{i}' for i in range(1, rows + 1)],
        'value': [i * 100 for i in range(1, rows + 1)]
    }
    return pd.DataFrame(data)


def save_gz_parquet(df: pd.DataFrame, file_path: str) -> None:
    table: pa.Table = pa.Table.from_pandas(df)
    pq.write_table(table, file_path, compression='gzip')


def upload_to_s3(bucket: str, s3_key: str, file_path: str) -> None:
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket, s3_key)


def main() -> None:
    dummy_data: pd.DataFrame = create_dummy_data()

    file_path: str = 'dummy_data.parquet.gz'
    save_gz_parquet(dummy_data, file_path)

    bucket_name: str = 'your-bucket-name'
    # ".parquet.gz" doesn't work in S3 select.
    s3_key: str = 'path/to/dummy_data.gz.parquet'
    upload_to_s3(bucket_name, s3_key, file_path)


if __name__ == '__main__':
    main()
