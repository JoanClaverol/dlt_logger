"""Athena upload functionality for tp-logger."""

from datetime import datetime

import dlt
from loguru import logger

from .config import get_config


def upload_to_athena() -> bool:
    """
    Upload data from local DuckDB to AWS Athena.

    Reads logs from the local DuckDB and uploads them to Athena using the
    configuration parameters set in LoggerConfig.

    Returns:
        bool: True if successful, False otherwise

    Raises:
        ValueError: If Athena configuration is not properly set
    """
    config = get_config()

    if not config.athena_destination:
        raise ValueError("athena_destination must be True to upload to Athena")

    # Validate required Athena configuration
    if not all(
        [config.aws_region, config.athena_database, config.athena_s3_staging_bucket]
    ):
        raise ValueError(
            "aws_region, athena_database, and athena_s3_staging_bucket are required for Athena upload"
        )

    try:
        # Source pipeline: Read from local DuckDB
        duckdb_pipeline = dlt.pipeline(
            pipeline_name=config.pipeline_name,
            dataset_name=config.dataset_name,
            destination=dlt.destinations.duckdb(
                credentials=f"duckdb:///{config.db_path}"
            ),
            progress="enlighten",
        )

        # Destination pipeline: Write to Athena
        athena_destination = dlt.destinations.athena(
            aws_region=config.aws_region,
            athena_database=config.athena_database,
            s3_staging_bucket=config.athena_s3_staging_bucket,
        )

        final_pipeline = dlt.pipeline(
            pipeline_name=f"athena_upload_pipeline_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            dataset_name=config.dataset_name,
            destination=athena_destination,
            progress="enlighten",
            staging="filesystem",
        )

        # Get dataset from DuckDB
        duckdb_dataset = duckdb_pipeline.dataset()

        # Upload each table to Athena
        for table_name in duckdb_dataset.schema.tables.keys():
            if table_name.startswith("_dlt"):
                continue  # Skip DLT internal tables

            try:
                logger.info(f"Uploading table {table_name} to Athena")

                final_pipeline.run(
                    duckdb_dataset[table_name].arrow(),
                    table_name=table_name,
                    table_format="iceberg",
                    primary_key="_dlt_id",
                )

                logger.info(f"Successfully uploaded table {table_name} to Athena")

            except Exception as e:
                logger.error(f"Error uploading table {table_name} to Athena: {str(e)}")
                return False

        logger.info("Successfully completed Athena upload")
        return True

    except Exception as e:
        logger.error(f"Error during Athena upload: {str(e)}")
        return False
