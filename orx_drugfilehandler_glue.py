import sys
from datetime import datetime
from awsglue.utils import getResolvedOptions
import boto3
import psycopg2
import pandas as pd
from io import BytesIO
import openpyxl
import uuid
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import traceback

args = getResolvedOptions(sys.argv,
                          ["file_name", "region", "bucket_name", "receiverEmails", "senderEmail", "returnPathArn",
                           "sourceArn", "dbhost", "dbname", "username", "password", "deltaReportMaxLimitMB"])

bucket_name = args['bucket_name']
region = args['region']
receiverEmails = args['receiverEmails']
senderEmail = args['senderEmail']
returnPathArn = args['returnPathArn']
sourceArn = args['sourceArn']
latest_file_path = args['file_name']
delta_report_max_limit_mb = int(args['deltaReportMaxLimitMB'])

# PostgreSQL connection details
db_host = args['dbhost']
db_name = args['dbname']
db_user = args['username']
db_password = args['password']

# S3 folder paths
ORX_S3_PREFIX = "drugfile/ORx/"
FEOPS_S3_PREFIX = "feops/"
DELTA_ORX_VS_ORX_S3_PREFIX = "delta/ORx/ORx_vs_ORx"
DELTA_ORX_VS_FEOPS_S3_PREFIX = "delta/ORx/ORx_vs_FeOps"
ARCHIVE_S3_PREFIX = "archive/"

# Initialize S3 client
s3_client = boto3.client('s3')

# Columns to compare
key_col = "NDC"
orx_vs_orx_compare_column = ["HAZMAT_ITEM", "DEA_SCHEDULE", "STATUS", "LTOOS", "Shipping Condition"]
valid_status = ["A", "PS"]

# Column name constants
CHANGE_DETECTED_COL = "Change Detected"
COLUMNS_UPDATED_COL = "Columns Updated"

# ORx Drug File column names
ORX_COLUMN_NAMES = ["LOB", "NDC", "PACK_SIZE", "UOM", "SPECIALTY_FLAG", "MANUFACTURER",
                    "BRAND_GENERIC_IND", "HAZMAT_ITEM", "DEA_SCHEDULE", "A_B_RATING",
                    "ITEM_DESCRIPTION", "NDC_SUB_TYPE", "NDC_FORM", "NDC_ROUTE", "NDC_PACKAGEIND",
                    "NDC_METRIC_STREINGTH", "NDC_STREINGTH_UNITS", "STATUS", "WARNING",
                    "PILL_DESCRIPTION", "GPI", "LTOOS", "Patient Drug Storage Condition",
                    "Shipping Condition", "Pharmacy Storage Condition"]

baseLine_file_missing = "baseLine_file_missing"
PASSED = "PASSED"
FAILED = "FAILED"

run_date = datetime.now().strftime("%m/%d/%Y")
run_timestamp = datetime.now().strftime("%H%M%S")
run_date_timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")


def main():
    print(f"latest_file_path : {latest_file_path}")
    latest_file_name = latest_file_path.split('/')[-1].replace('.csv', '')
    print(f"file_name: {latest_file_name}")

    try:
        print("calling glue job start time...", datetime.now())

        invalid_rows, validation_passed = drugfilevalidations()
        if not validation_passed:
            print("Drug file Validation failed, delta report generation skipped")
            return

        orx_vs_orx_delta_report_summary = {}
        orx_vs_feops_delta_report_summary = {}
        orx_vs_orx_delta = None
        orx_vs_feops_delta = None

        try:
            orx_vs_orx_delta_report_status, orx_vs_orx_delta_report_summary, orx_vs_orx_delta = generate_ORx_vs_ORx_delta_Report(invalid_rows)

        except Exception as e:
            error_message = str(e)
            print(f"orx_vs_orx_delta_report generation job failed with error: {error_message}")
            traceback_str = traceback.format_exc()
            print(f"orx_vs_orx_delta_report generation error Traceback: {traceback_str}")
            orx_vs_orx_delta_report_status = {"status": FAILED, "error_message": error_message}

        print("orx_vs_orx_delta_report_status: ", orx_vs_orx_delta_report_status)
        print("orx_vs_orx_delta_report_summary: ", orx_vs_orx_delta_report_summary)

        try:
            orx_vs_feops_delta_report_status, orx_vs_feops_delta_report_summary, orx_vs_feops_delta = generate_ORx_vs_FEOPS_delta_Report()

        except Exception as e:
            error_message = str(e)
            print(f"orx vs feops delta_report generation job failed with error: {error_message}")
            traceback_str = traceback.format_exc()
            print(f"orx vs feops delta_report generation error Traceback: {traceback_str}")
            orx_vs_feops_delta_report_status = {"status": FAILED, "error_message": error_message}

        print("orx_vs_feops_delta_report_status: ", orx_vs_feops_delta_report_status)
        print("orx_vs_feops_delta_report_summary: ", orx_vs_feops_delta_report_summary)

        # Get baseline_exists from orx_vs_orx_delta (or default to True if not available)
        baseline_exists = orx_vs_orx_delta.get('baseline_exists', True) if orx_vs_orx_delta else True

        orx_status = orx_vs_orx_delta_report_status.get('status')
        feops_status = orx_vs_feops_delta_report_status.get('status')
        if orx_vs_orx_delta_report_status['status'] == baseLine_file_missing and orx_vs_feops_delta_report_status['status'] == PASSED:
            print("orx_vs_orx_delta_report_status : baseLine_file_missing and orx_vs_feops_delta_report_status : passed")
            send_orx_baseline_missing_feops_sucess_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_summary,
                                                         orx_vs_orx_delta, orx_vs_feops_delta, baseline_exists)

        elif orx_vs_orx_delta_report_status['status'] == baseLine_file_missing and orx_vs_feops_delta_report_status['status'] == FAILED:
            print("orx_vs_orx_delta_report_status == baseLine_file_missing and orx_vs_feops_delta_report_status == FAILED")
            send_orx_baseline_missing_feops_failed_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_status,
                                                         orx_vs_orx_delta, orx_vs_feops_delta, baseline_exists)

        status_handlers = {
            (baseLine_file_missing, PASSED): (
                "ORx baseline missing, FEOps passed",
                lambda: send_orx_baseline_missing_feops_sucess_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_summary)
            ),
            (baseLine_file_missing, FAILED): (
                "ORx baseline missing, FEOps failed",
                lambda: send_orx_baseline_missing_feops_failed_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_status)
            ),
            (PASSED, PASSED): (
                "ORx passed, FEOps passed",
                lambda: send_orx_vs_orx_success_orx_vs_feops_success_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_summary)
            ),
            (PASSED, FAILED): (
                "ORx passed, FEOps failed",
                lambda: send_orx_vs_orx_success_orx_vs_feops_failed_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_status)
            ),
            (FAILED, PASSED): (
                "ORx failed, FEOps passed",
                lambda: send_orx_vs_orx_failed_orx_vs_feops_success_email(orx_vs_orx_delta_report_status, orx_vs_feops_delta_report_summary)
            ),
            (FAILED, FAILED): (
                "ORx failed, FEOps failed",
                None
            )
        }

        status_key = (orx_status, feops_status)
        if status_key in status_handlers:
            message, handler = status_handlers[status_key]
            print(f"Delta Report Status: {message}")
            if handler:
                handler()
        else:
            print(f"Unexpected status combination: ORx={orx_status}, FEOps={feops_status}")

        print("End OF execution")

    except Exception as e:
        error_message = str(e)
        print(f"Glue job failed with error: {error_message}")

        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")

        send_glue_job_failure_email(latest_file_name, error_message)
        raise


def drugfilevalidations():
    """Handle drug file validation, processing, and data persistence."""
    file_path = args['file_name']
    file_name = file_path.split('/')[-1].replace('.txt', '').replace('.csv', '')
    print(f"file_name: {file_name}")

    df = read_csv_from_s3(bucket_name, file_path)
    file_content = s3_client.get_object(Bucket=bucket_name, Key=file_path)['Body'].read().decode('utf-8')
    lines = df.apply(lambda row: '|'.join(row.astype(str)), axis=1).tolist()

    print(f"Validating drug file '{file_name}': calculating error records and threshold percentage...")
    total_rows, error_rows, error_pct, invalid_rows = calculate_error_metrics(df, lines)

    error_key = upload_error_file(invalid_rows)

    validation_passed = handle_validation_result(file_name, file_path, total_rows, error_rows, error_pct, error_key)

    if not validation_passed:
        return invalid_rows, validation_passed

    data_to_insert = prepare_data_for_insert(df, file_name)

    persistData(data_to_insert, file_content, file_name)

    return invalid_rows, validation_passed


def calculate_error_metrics(df, lines):
    """Calculate error metrics from validation results."""
    invalid_rows, total_rows = dataValidation(df, lines)
    error_rows = len(invalid_rows)

    if total_rows > 0:
        error_pct = (error_rows / total_rows) * 100
    else:
        error_pct = 0.0

    print(f"Total Rows  = {total_rows}")
    print(f"Error Rows  = {error_rows}")
    print(f"Error Percentage  = {error_pct}")

    return total_rows, error_rows, error_pct, invalid_rows


def upload_error_file(invalid_rows):
    """Upload error file to S3 if there are invalid rows."""
    if len(invalid_rows) > 0:
        print("Uploading error file to S3...")
        timestamp_for_error = datetime.now().strftime("%m%d%Y_%H%M%S")
        error_file_name = f"DP_ORx_Drug_File_Error_{timestamp_for_error}.csv"
        error_key = f"error/{error_file_name}"

        df = pd.DataFrame(invalid_rows, columns=["raw_line", "error_reason"])
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)

        s3client = boto3.client("s3")
        s3client.put_object(
            Bucket=bucket_name,
            Key=error_key,
            Body=csv_buffer.getvalue()
        )
        print("Error file uploaded to S3: ", error_key)
        return error_key
    return None


def handle_validation_result(file_name, file_path, total_rows, error_rows, error_pct, error_key):
    """Handle validation result - log status and send email based on error percentage."""
    if error_pct > 5.0:
        persistDataInLogTable(file_name, 'FAILED', total_rows, error_rows)
        sendErrorSummaryEmail(
            file_name=file_name,
            total_rows=total_rows,
            error_rows=error_rows,
            error_pct=error_pct,
            error_file_path=error_key,
            is_failure=True
        )
        move_file_to_error(file_path)
        return False  # Validation failed

    else:
        persistDataInLogTable(file_name, 'COMPLETE', total_rows, error_rows)
        sendErrorSummaryEmail(
            file_name=file_name,
            total_rows=total_rows,
            error_rows=error_rows,
            error_pct=error_pct,
            error_file_path=error_key,
            is_failure=False
        )
        return True  # Validation passed


def prepare_data_for_insert(df, file_name):
    """Prepare data rows for database insertion using pandas."""
    default_value_for_Column_one = "SYSTEM"

    print("Preparing data for insert")

    if df.empty:
        return []

    # Create a copy to avoid modifying original
    df = df.copy()

    # Remove first line (header) and last line (EOF)
    df = df.iloc[1:-1]

    if df.empty:
        return []

    # Replace empty strings with None
    df = df.replace('', None)

    # Remove last row if all columns are empty/None
    if df.iloc[-1].isna().all() or df.iloc[-1].isnull().all():
        df = df.iloc[:-1]

    if df.empty:
        return []

    # Add metadata columns
    df['_uuid'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['_file_name'] = file_name
    df['_created_dtm'] = datetime.now()
    df['_created_by'] = default_value_for_Column_one
    df['_updated_dtm'] = datetime.now()
    df['_updated_by'] = default_value_for_Column_one

    # Build data rows in the order expected by the insert query

    data_to_insert = []

    for idx, row in df.iterrows():
        data_row = (
            row['_uuid'],
            row['_file_name'],
            row.get('LOB'),
            row.get('NDC'),
            row.get('PACK_SIZE'),
            row.get('UOM'),
            row.get('SPECIALTY_FLAG'),
            row.get('MANUFACTURER'),
            row.get('BRAND_GENERIC_IND'),
            row.get('HAZMAT_ITEM'),
            row.get('DEA_SCHEDULE'),
            row.get('A_B_RATING'),
            row.get('ITEM_DESCRIPTION'),
            row.get('NDC_SUB_TYPE'),
            row.get('NDC_FORM'),
            row.get('NDC_ROUTE'),
            row.get('NDC_PACKAGEIND'),
            row.get('NDC_METRIC_STREINGTH'),
            row.get('NDC_STREINGTH_UNITS'),
            row.get('STATUS'),
            row.get('WARNING'),
            row.get('PILL_DESCRIPTION'),
            row.get('GPI'),
            row['_created_dtm'],
            row['_created_by'],
            row['_updated_dtm'],
            row['_updated_by'],
            row.get('LTOOS'),
            row.get('Patient Drug Storage Condition'),
            row.get('Shipping Condition'),
            row.get('Pharmacy Storage Condition')
        )
        data_to_insert.append(data_row)

    print(f"Prepared {len(data_to_insert)} rows for insert")
    return data_to_insert


def dataValidation(df, original_lines):
    invalid_rows = []

    if df.empty:
        return invalid_rows, 0

    # Store original lines for error reporting
    df = df.copy()
    df['_original_line'] = original_lines[:len(df)]

    # Get all data columns (excluding internal columns)
    all_cols_except_internal = [col for col in df.columns if not col.startswith('_')]

    # Remove first row (header)
    if len(df) > 0:
        df = df.iloc[1:]

    # Remove last row if it contains EOF marker (check if last row has 'EOF' in any column)
    if len(df) > 0:
        last_row = df.iloc[-1][all_cols_except_internal]
        if last_row.astype(str).str.contains('EOF', case=False, na=False).any():
            df = df.iloc[:-1]
            # Check if the row before EOF is empty and remove it
            if len(df) > 0:
                second_last_row = df.iloc[-1][all_cols_except_internal]
                if second_last_row.replace('', pd.NA).isna().all():
                    df = df.iloc[:-1]

    # Remove last row if all columns are empty/None (similar to data insertion logic)
    if len(df) > 0:
        last_row = df.iloc[-1][all_cols_except_internal]
        if last_row.replace('', pd.NA).isna().all():
            df = df.iloc[:-1]

    # Calculate total rows after cleaning (excluding header, EOF, and empty rows)
    total_rows = len(df)

    if df.empty:
        return invalid_rows, total_rows

    # Validate NDC: Required and must be exactly 11 characters
    ndc_invalid = (df['NDC'].isna()) | (df['NDC'] == '') | (df['NDC'].str.len() != 11)

    # Validate STATUS: Required field
    status_invalid = (df['STATUS'].isna()) | (df['STATUS'] == '')

    # Build error reasons using vectorized operations
    ndc_error_msg = ndc_invalid.map(lambda x: "NDC is Required Field and its length must be exactly 11" if x else "")
    status_error_msg = status_invalid.map(lambda x: "STATUS is Required Field" if x else "")

    # Combine error messages with separator
    df['_error_reason'] = ndc_error_msg.str.cat(status_error_msg, sep="; ").str.strip("; ")

    # Filter rows with errors
    has_error = ndc_invalid | status_invalid
    error_df = df[has_error]

    if not error_df.empty:
        invalid_rows = list(zip(error_df['_original_line'], error_df['_error_reason']))

    return invalid_rows, total_rows


def sendErrorSummaryEmail(file_name, total_rows, error_rows, error_pct, error_file_path, is_failure):
    ses = boto3.client('ses', region_name=region)
    email_list = receiverEmails.split(',')

    status_text = "FAILED" if is_failure else "COMPLETED"
    subject = f"ORx Drug File Processing {status_text}"

    body = ""
    body += f"Drug File processing {status_text}.<br><br>"
    body += f"<b>Filename: </b>{file_name}<br>"
    body += f"<b>Total Rows: </b>{total_rows}<br>"
    body += f"<b>Error Rows: </b>{error_rows}<br>"
    body += f"<b>Error Percentage: </b>{error_pct:.2f}%<br>"

    if error_file_path:
        body += f"<b>Error File: </b>{error_file_path}<br>"

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    # Attach error file if it exists
    if error_file_path:
        try:
            error_file_obj = s3_client.get_object(Bucket=bucket_name, Key=error_file_path)
            error_file_bytes = error_file_obj['Body'].read()
            attachment = MIMEApplication(error_file_bytes)
            attachment.add_header('Content-Disposition', 'attachment', filename=error_file_path.split('/')[-1])
            msg.attach(attachment)
        except Exception as e:
            print(f"Error attaching error file: {e}")

    raw_message = msg.as_string()
    ses.send_raw_email(
        Source=senderEmail,
        Destinations=email_list,
        RawMessage={'Data': raw_message}
    )


def persistDataInLogTable(file_name, status, total_rows=0, error_rows=0):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode='require'
        )

        print("Pushing data to Log Table")
        print(f"status: {status}, total_rows: {total_rows}, error_rows: {error_rows}")
        cursor = conn.cursor()

        data_row = (str(uuid.uuid4()),
                    file_name,
                    status,
                    datetime.now(),
                    total_rows, 0, 0, 0, error_rows, 0, 0, 0, 0,
                    "N/A",
                    datetime.now(),
                    "SYSTEM",
                    datetime.now(),
                    "SYSTEM")

        insert_query = "INSERT INTO intelengine.ie_inboud_file_prcs_log(ie_inbnd_file_prcs_log_id, file_nm, prcs_stts_cd, prcs_dtm, totl_rcrd_cnt, hdr_rcrd_cnt, ftr_rcrd_cnt, dtl_rcrd_cnt, err_rcrd_cnt, add_rcrd_cnt, no_chng_rcrd_cnt, chng_rcrd_cnt, del_rcrd_cnt, err_desc, creat_dtm, creat_nm, updt_dtm, updt_nm) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, data_row)
        conn.commit()

    except Exception as e:
        print("Error:", e)
        if conn is not None:
            conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def persistData(data_to_insert, file_content, file_name):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode='require'
        )

        if conn is not None and not conn.closed:
            print("Connection has established with databse")
        else:
            print("Connection is closed")

        cursor = conn.cursor()

        delete_query = f"DELETE From intelengine.ie_inbnd_orx_drug_file_stg"

        cursor.execute(delete_query)

        print("Inserting data into Staging table : ie_inbnd_orx_drug_file_stg")

        insert_query = "INSERT INTO intelengine.ie_inbnd_orx_drug_file_stg(ie_inbnd_orx_drug_file_stg_id, file_nm, lob, ndc, pack_size, uom, spclty_flag, mnfctrr, brnd_gnrc_id, hezmat_item, dea_schdl, a_b_ratg, item_desc, ndc_sub_type, ndc_form, ndc_rte, ndc_pkg_ind, ndc_mtrc_strngth, ndc_strngth_units, stts, warng, pill_desc, gpi, creat_dtm, creat_nm, updt_dtm, updt_nm, ltoos, patnt_drug_strg_cndtn, shpng_cndtn, phrmcy_strg_cndtn) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        for data_row in data_to_insert:
            cursor.execute(insert_query, data_row)
        conn.commit()

        print("Data persisted Successfully in Staging table")

        invokeProcedure(file_name)

    except Exception as e:
        print("Error:", e)
        if conn is not None:
            conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    print("successfully deleted the data and saved the file data to database")


def invokeProcedure(file_name):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database=db_name,
            user=db_user,
            password=db_password,
            sslmode='require'
        )

        print("Invoking stored procedure: intelengine.ie_orx_drug_file_load")

        print(file_name)
        cursor = conn.cursor()
        outputparam = ''

        cursor.execute('CALL intelengine.ie_orx_drug_file_load(%s, %s)', (file_name, outputparam))
        outputparam = cursor.fetchone()[0]
        conn.commit()

        print("Stored procedure call :", outputparam)

    except Exception as e:
        print("Error:", e)
        if conn is not None:
            conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def archive_file(file_content, file_name):
    """Archive the file to S3 archive folder after successful validation and data persistence"""
    try:
        s3clienttodest = boto3.client('s3')
        response = s3clienttodest.put_object(
            Body=file_content,
            Bucket=bucket_name,
            Key="archive/" + file_name
        )
        print("File uploaded to archive and now removing from Drugfile")
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            s3clienttodest.delete_object(
                Bucket=bucket_name,
                Key="drugfile/ORx/" + file_name + ".csv"
            )
        print("File Removed From Drug Folder")
    except Exception as e:
        print(e.__cause__)
        print("Error in archiving the file")


def move_file_to_error(source_key):
    """Move file to error folder when validation fails"""
    dest_key = f"error/{source_key.split('/')[-1]}"

    copy_source = {
        'Bucket': bucket_name,
        'Key': source_key
    }

    s3_client.copy_object(
        Bucket=bucket_name,
        Key=dest_key,
        CopySource=copy_source
    )
    s3_client.delete_object(
        Bucket=bucket_name,
        Key=source_key
    )
    print(f"File moved to error folder: {dest_key}")


def generate_ORx_vs_ORx_delta_Report(invalid_rows):
    print("Starting ORx vs ORx delta glue job")

    delta_rows = []
    # Initialize counters
    latest_file_count = 0
    baseline_file_count = 0
    add_count = 0
    update_count = 0
    delete_count = 0
    no_change_count = 0
    latest_file_duplicate_count = 0
    baseline_file_duplicate_count = 0
    error_count = len(invalid_rows)
    invalid_status_count = 0
    total_evaluated_count = 0
    orx_vs_orx_delta_report_status = {"status": "PASSED", "message": "ORx vs ORx delta report generated"}
    orx_vs_orx_delta_report_summary = {}

    # Load the latest file from S3
    latest_file_df = read_csv_from_s3(bucket_name, latest_file_path)

    baseline_file_path = get_second_latest_file(bucket_name, ORX_S3_PREFIX)
    print(f"Second latest file path: {baseline_file_path}")

    if baseline_file_path == "":
        print("Warning: Baseline file not found ")
        print("All rows from latest file will be marked as ADD")
        orx_vs_orx_delta_report_status = {"status": baseLine_file_missing, "message": "Baseline file not found"}
        baseline_file_df = pd.DataFrame()
    else:
        # Load the baseline file
        print(f"Loading baseline file: {baseline_file_path}")
        baseline_file_df = read_csv_from_s3(bucket_name, baseline_file_path)

    latest_file_count = len(latest_file_df)
    baseline_file_count = len(baseline_file_df)
    print(f"loaded latest file with rows : {latest_file_count}")
    print(f"loaded baseline file with rows : {baseline_file_count}")

    # Calculate duplicate count before removing duplicates
    latest_file_duplicate_count = int(latest_file_df[key_col].duplicated().sum())
    print(f"Duplicate NDC count in latest file: {latest_file_duplicate_count}")

    baseline_file_duplicate_count = int(baseline_file_df[key_col].duplicated().sum())
    print(f"Duplicate NDC count in baseline file: {baseline_file_duplicate_count}")

    # Remove duplicate NDC rows, keeping the first occurrence
    latest_file_df = latest_file_df.drop_duplicates(subset=[key_col], keep='first')
    print(f"After removing duplicates, latest file has {len(latest_file_df)} rows")

    baseline_file_df = baseline_file_df.drop_duplicates(subset=[key_col], keep='first')
    print(f"After removing duplicates, baseline file has {len(baseline_file_df)} rows")

    # Remove the error ndcs from the latest file df
    error_ndcs = [row[key_col] for row in invalid_rows]
    latest_file_df = latest_file_df[latest_file_df[key_col].isin(error_ndcs) == False]

    # Set index for fast lookup
    print("Setting index for fast lookup")
    if not baseline_file_df.empty:
        baseline_file_df = baseline_file_df.set_index(key_col)
    if not latest_file_df.empty:
        latest_file_df = latest_file_df.set_index(key_col)

    # ADD and UPDATED
    print("Processing ADD and UPDATED")
    for ndc, latest_row in latest_file_df.iterrows():
        if baseline_file_df.empty or ndc not in baseline_file_df.index:
            if latest_row["STATUS"] not in valid_status:
                invalid_status_count += 1
                continue
            row_dict = {
                CHANGE_DETECTED_COL: "ADD",
                COLUMNS_UPDATED_COL: "",
                key_col: ndc,
            }
            row_dict.update(latest_row.to_dict())
            delta_rows.append(row_dict)
            add_count += 1
        else:
            if latest_row["STATUS"] not in valid_status and baseline_file_df.loc[ndc, "STATUS"] not in valid_status:
                invalid_status_count += 1
                continue
            updated_cols = [
                col for col in orx_vs_orx_compare_column
                if latest_row[col] != baseline_file_df.loc[ndc, col]
            ]
            if updated_cols:
                row_dict = {
                    CHANGE_DETECTED_COL: "UPDATED",
                    COLUMNS_UPDATED_COL: ", ".join(updated_cols),
                    key_col: ndc,
                }
                row_dict.update(latest_row.to_dict())
                delta_rows.append(row_dict)
                update_count += 1
            else:
                no_change_count += 1

    print("ADD Count: ", add_count)
    print("UPDATE Count: ", update_count)
    print("NO CHANGE Count: ", no_change_count)

    # DELETE (only if baseline file exists)
    print("Processing DELETE")
    if not baseline_file_df.empty:
        for ndc, baseline_row in baseline_file_df.iterrows():
            if baseline_row["STATUS"] not in valid_status:
                continue
            if ndc not in latest_file_df.index:
                row_dict = {
                    CHANGE_DETECTED_COL: "DELETE",
                    COLUMNS_UPDATED_COL: "",
                    key_col: ndc,
                }
                row_dict.update(baseline_row.to_dict())
                delta_rows.append(row_dict)
                delete_count += 1

    print("DELETE Count: ", delete_count)

    # Create DataFrame for delta
    print("Creating DataFrame for delta")
    if delta_rows:
        df_delta = pd.DataFrame(delta_rows)
    else:
        print("No changes detected")
        df_delta = pd.DataFrame()

    # Calculate total count
    total_evaluated_count = add_count + update_count + delete_count + no_change_count
    print("Total Count: ", total_evaluated_count)

    # Save to S3
    print("Saving to S3")
    orx_vs_orx_delta_report_file_name = generate_output_filename("Delta_ORx_vs_ORx")
    print("orx_vs_orx_delta_report_file_name: ", orx_vs_orx_delta_report_file_name)

    baseline_exists = not baseline_file_df.empty
    file_content = None

    if not df_delta.empty:
        file_content = upload_delta_report_to_s3(bucket_name, DELTA_ORX_VS_ORX_S3_PREFIX, orx_vs_orx_delta_report_file_name, df_delta)
        print(f"orx vs orx Delta report generated: {orx_vs_orx_delta_report_file_name}")
    else:
        print("No differences found between the files.")
        orx_vs_orx_delta_report_status = {"status": FAILED, "message": "No differences found between the files."}
        orx_vs_orx_delta = {'file_content': None, 'file_name': orx_vs_orx_delta_report_file_name, 'baseline_exists': baseline_exists}
        return orx_vs_orx_delta_report_status, orx_vs_orx_delta_report_summary, orx_vs_orx_delta

    orx_vs_orx_delta = {'file_content': file_content, 'file_name': orx_vs_orx_delta_report_file_name, 'baseline_exists': baseline_exists}

    # Create summary dictionary
    orx_vs_orx_delta_report_summary = dict(latest_file_count=latest_file_count, baseline_file_count=baseline_file_count,
                                           add_count=add_count, update_count=update_count, delete_count=delete_count,
                                           no_change_count=no_change_count,
                                           latest_file_duplicate_count=latest_file_duplicate_count,
                                           baseline_file_duplicate_count=baseline_file_duplicate_count,
                                           error_count=error_count, invalid_status_count=invalid_status_count,
                                           total_evaluated_count=total_evaluated_count,
                                           orx_vs_orx_delta_report_file_name=orx_vs_orx_delta_report_file_name,
                                           baseline_file_name=baseline_file_path, latest_file_name=latest_file_path)
    return orx_vs_orx_delta_report_status, orx_vs_orx_delta_report_summary, orx_vs_orx_delta


def generate_ORx_vs_FEOPS_delta_Report():
    print("Starting ORx vs FEOps delta glue job")
    missing_ndc_count = 0
    orx_vs_feops_delta_report_status = {}
    orx_vs_feops_delta_report_summary = {}

    # Load ORx file (pipe-delimited CSV)
    orx_df = read_csv_from_s3(bucket_name, latest_file_path)
    print(f"ORx file loaded with {len(orx_df)} records")

    # Get and load FEOps file (Excel)
    feops_key = get_latest_file(bucket_name, FEOPS_S3_PREFIX)
    if feops_key == "":
        print("No FEOps file found")
        orx_vs_feops_delta_report_status = {"status": FAILED, "message": "No FEOps file found"}
        orx_vs_feops_delta = {'file_content': None, 'file_name': None}
        return orx_vs_feops_delta_report_status, orx_vs_feops_delta_report_summary, orx_vs_feops_delta
    feops_df = read_excel_from_s3(bucket_name, feops_key)
    print(f"FEOps file loaded with {len(feops_df)} records")

    # Find NDCs present in ORx but missing from FeOps
    orx_ndcs = set(orx_df[key_col].astype(str))
    feops_ndcs = set(feops_df[key_col].astype(str))
    missing_ndcs = orx_ndcs - feops_ndcs
    print(f"Missing NDC count: {len(missing_ndcs)}")

    # Create and upload delta report
    orx_vs_feops_delta_report_file_name = generate_output_filename("Delta_ORx_vs_SubList")
    file_content = None

    if missing_ndcs:
        delta_df = pd.DataFrame({"NDC": list(missing_ndcs)})
        file_content = upload_delta_report_to_s3(bucket_name, DELTA_ORX_VS_FEOPS_S3_PREFIX, orx_vs_feops_delta_report_file_name, delta_df)
        print(f"Delta report generated with {len(missing_ndcs)} missing NDCs")
    else:
        print("No missing NDCs found")
        orx_vs_feops_delta_report_status = {"status": PASSED, "message": "No missing NDCs found"}
        orx_vs_feops_delta = {'file_content': None, 'file_name': orx_vs_feops_delta_report_file_name}
        return orx_vs_feops_delta_report_status, orx_vs_feops_delta_report_summary, orx_vs_feops_delta

    orx_vs_feops_delta = {'file_content': file_content, 'file_name': orx_vs_feops_delta_report_file_name}
    orx_vs_feops_delta_report_summary = dict(missing_ndc_count=missing_ndc_count,
                                             orx_vs_feops_delta_report_file_name=orx_vs_feops_delta_report_file_name,
                                             latest_file_name=latest_file_path,
                                             feops_file_name=feops_key)
    orx_vs_feops_delta_report_status = {"status": PASSED, "message": "ORx vs FEOps delta job completed"}
    print("ORx vs FEOps delta job completed")
    return orx_vs_feops_delta_report_status, orx_vs_feops_delta_report_summary, orx_vs_feops_delta


def read_csv_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """
    Read CSV file from S3 bucket.
    Args:
        bucket: S3 bucket name
        key: S3 object key (file path)
    Returns:
        DataFrame containing the Excel data
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_data = response['Body'].read()
        df = pd.read_csv(BytesIO(file_data), sep='|', dtype=str).fillna("")
        return df
    except Exception as e:
        print(f"Error reading file from S3: {bucket}/{key}")
        raise e


def read_excel_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """
    Read Excel(FeOps) file from S3 bucket.
    Args:
        bucket: S3 bucket name
        key: S3 object key (file path)
    Returns:
        DataFrame containing the Excel data
    """
    try:
        print(f"Reading Excel file from s3://{bucket}/{key}")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_data = response['Body'].read()
        df = pd.read_excel(BytesIO(file_data), dtype=str).fillna("")
        return df
    except Exception as e:
        print(f"Error reading Excel file from S3: {bucket}/{key}")
        raise e


def get_latest_file(bucket, prefix):
    """Get the file key from S3 folder."""
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' not in response:
        print(f"No files found in : {bucket}/{prefix}")
        return ""

    files = [obj["Key"] for obj in response.get("Contents", []) if not obj["Key"].endswith("/")]
    if not files:
        print(f"No files found in : {bucket}/{prefix}")
        return ""
    print(f"Found file: {files[0]}")
    return files[0]


def get_second_latest_file(bucket: str, prefix: str):
    """
    get second latest  file from S3 bucket based on timestamp in the file name.
    Args:
        bucket: S3 bucket name
        prefix: S3 prefix/folder path
    Returns:
        second latest file name
    """
    print(f"Getting second latest file from s3://{bucket}/{prefix}")
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    print(f"response : {response}")

    if 'Contents' not in response:
        print(f"No files found in : {bucket}/{prefix}")
        return ""
    else:
        # Filter text files and sort by LastModified in descending order
        file_contents = [obj for obj in response['Contents']
                         if obj['Key'].endswith('.csv') and obj['Key'] != latest_file_path]
        print(f"file_contents : {file_contents}")

    if len(file_contents) == 0:
        print(f"No files found in: {bucket}/{prefix}")
        return ""
    elif len(file_contents) == 1:
        second_latest_file_key = file_contents[0]['Key']
        print(f"Only one file found in: {bucket}/{prefix}, so it will be base line file")
        return second_latest_file_key

    def extract_timestamp(file_obj):
        try:
            filename = file_obj['Key'].split('/')[-1]  # Get filename from full S3 key
            # Extract timestamp from filename: DP_ORx_Drug_File_01192026_000000.csv -> 01192026_000000
            timestamp_str = "_".join(filename.split("_")[-2:]).replace(".csv", "")
            print(f"timestamp_str : {timestamp_str}")
            return datetime.strptime(timestamp_str, "%m%d%Y_%H%M%S")
        except Exception as e:
            print(f"Error extracting timestamp from filename: {file_obj['Key']}, error: {e}")
            return datetime.min  # Return minimum date if parsing fails

    sorted_files = sorted(file_contents, key=extract_timestamp, reverse=True)
    print(f"sorted_files : {sorted_files}")

    # Skip the latest file and read the second latest file
    if len(sorted_files) >= 1:
        second_latest_file = sorted_files[0]
        second_latest_file_key = second_latest_file['Key']
        return second_latest_file_key
    else:
        return ""


def upload_delta_report_to_s3(bucket, prefix, file_name, delta_df):
    """ upload delta report to S3 as Excel."""
    print("Uploading delta report to S3")
    output_key = f"{prefix}/{file_name}"

    buffer = BytesIO()
    delta_df.to_excel(buffer, index=False)
    buffer.seek(0)
    file_bytes = buffer.getvalue()

    s3_client.put_object(Bucket=bucket, Key=output_key, Body=file_bytes)
    print(f"Delta report uploaded to s3://{bucket}/{output_key}")
    return file_bytes


def generate_output_filename(file_name: str):
    """Generate output filename with timestamp."""
    return f"{file_name}_{run_date_timestamp}.xlsx"

def send_email(msg):
    ses = boto3.client('ses', region_name=region)
    response = ses.send_raw_email(
        Source=senderEmail,
        Destinations=receiverEmails.split(','),
        ReturnPathArn=returnPathArn,
        SourceArn=sourceArn,
        RawMessage={'Data': msg.as_string()}
    )
    print("Email sent")
    return response


def send_glue_job_failure_email(inbound_file, error_message):
    """
    Send failure notification email when Glue job fails before delta report generation.
    """
    print("Sending glue job failure email")
    subject = f"ORx Delta Reports - FAILED - {run_date} - {run_timestamp}"

    body = (
        "<b>ORx Delta Report Generation Failed</b><br><br>"
        f"<b>Run Date          :</b> {run_date}<br>"
        "<b>DP                :</b> ORx<br>"
        f"<b>Inbound Drug File :</b> {inbound_file}<br><br>"
        "<b>Status:</b><br>"
        "- Glue job failed before delta report generation completed.<br><br>"
        "<b>Error Summary:</b><br>"
        f"{error_message}<br><br>"
        "<b>Next Steps:</b><br>"
        "- Review Glue logs in CloudWatch.<br>"
        "- Re-run job after resolving issue.<br>"
        "- Inbound file remains in drugfile/ for retry (no cleanup performed).<br><br>"
        "<b>Thanks,</b><br>"
        "Intel Engine<br>"
    )

    send_email(
        subject=subject,
        body=body,
        receiver_emails=receiverEmails,
        region=region,
        return_path_arn=returnPathArn,
        source_arn=sourceArn,
        sender_email=senderEmail
    )
    print(f"Failure notification email sent for file: {inbound_file}")

def send_orx_baseline_missing_feops_sucess_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_summary,
                                                  orx_vs_orx_delta, orx_vs_feops_delta, baseline_exists):

    subject = f"ORx Delta Reports - INFO - {run_date} - {run_timestamp}"

    body = ("<b>ORx Daily Delta Reports Generated (Baseline Missing)</b><br><br>"
            f"<b>Run Date :</b>  {run_date} <br>"
            "<b>DP: </b> ORx<br>"
            f"<b>Inbound Drug File : </b>{orx_vs_orx_delta_report_summary['latest_file_name']}<br>"
            "<b>Baseline Drug File : </b> NOT FOUND (first run or baseline not available)<br>"
            f"<b>FE Ops Sub List : </b>{orx_vs_feops_delta_report_summary['feops_file_name']}<br><br><br>"
            "<b>Report 1: ORx vs ORx</b><br>"
            f"<b>Delta File Name   :  </b>{orx_vs_orx_delta_report_summary['orx_vs_orx_delta_report_file_name']}<br><br>"
            "<b>Summary (ORx vs ORx)</b><br>"
            f"<b>ADD               : </b>{orx_vs_orx_delta_report_summary['add_count']}<br>"
            "<b>DELETE            : </b>0<br>"
            "<b>UPDATED           : </b>0<br>"
            "<b>NO CHANGE         : </b>0<br>"
            "<b>ERROR             : </b>0<br>"
            "<b>STATUS            : </b>0<br>"
            "<b>DUPLICATE         : </b>0<br>"
            f"<b>TOTAL EVALUATED   : </b>{orx_vs_orx_delta_report_summary['total_evaluated_count']}<br><br>"
            "<b>Report 2: ORx vs FE Ops (New NDCs Only)</b><br>"
            f"<b>Delta File Name   : </b>{orx_vs_feops_delta_report_summary['orx_vs_feops_delta_report_file_name']}<br>"
            f"<b>NEW NDC COUNT     : </b>{orx_vs_feops_delta_report_summary['missing_ndc_count']}<br><br>"
            "<b>Notes:</b><br>"
            "- Baseline was not available. ORx vs ORx report treats baseline as empty, therefore all rows are marked ADD.<br><br>"
            "<b>Thanks,</b><br>"
            "Intel Engine<br>"
            )

    email_list = receiverEmails.split(',')
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = senderEmail
    msg['To'] = ', '.join(email_list)
    msg.attach(MIMEText(body, 'html'))

    # Helper to attach delta file if conditions are met
    def attach_delta_file(delta_dict, report_name):
        if not delta_dict or not delta_dict.get('file_content'):
            return
        if not baseline_exists:
            print(f"Skipped {report_name} attachment (baseline missing - first run)")
            return
        file_size_mb = len(delta_dict['file_content']) / (1024 * 1024)
        if file_size_mb == 0:
            print(f"Skipped {report_name} attachment (file is empty)")
        elif file_size_mb > delta_report_max_limit_mb:
            print(f"Skipped {report_name} attachment (size {file_size_mb:.2f} MB > {delta_report_max_limit_mb} MB limit)")
        else:
            attachment = MIMEApplication(delta_dict['file_content'])
            attachment.add_header('Content-Disposition', 'attachment', filename=delta_dict['file_name'])
            msg.attach(attachment)
            print(f"Attached {report_name} delta: {delta_dict['file_name']} ({file_size_mb:.2f} MB)")

    attach_delta_file(orx_vs_orx_delta, "ORx vs ORx")
    attach_delta_file(orx_vs_feops_delta, "ORx vs FeOps")


    print("ORx baseline missing feops success email sent.")

def send_orx_baseline_missing_feops_failed_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_status,
                                                  orx_vs_orx_delta=None, orx_vs_feops_delta=None, baseline_exists=True):

    subject = f"ORx Delta Reports - INFO - {run_date} - {run_timestamp}"

    body = ("<b>ORx Daily Delta Reports Generated (Baseline Missing)</b><br><br>"
            f"<b>Run Date :</b>  {run_date} <br>"
            "<b>DP: </b> ORx<br>"
            f"<b>Inbound Drug File : </b>{orx_vs_orx_delta_report_summary['latest_file_name']}<br>"
            "<b>Baseline Drug File : </b> NOT FOUND (first run or baseline not available)<br>"
            f"<b>FE Ops Sub List : </b>  <br><br><br>"
            "<b>Report 1: ORx vs ORx</b><br>"
            f"<b>Delta File Name   :  </b>{orx_vs_orx_delta_report_summary['orx_vs_orx_delta_report_file_name']}<br><br>"
            "<b>Summary (ORx vs ORx)</b><br>"
            f"<b>ADD               : </b>{orx_vs_orx_delta_report_summary['add_count']}<br>"
            "<b>DELETE            : </b>0<br>"
            "<b>UPDATED           : </b>0<br>"
            "<b>NO CHANGE         : </b>0<br>"
            "<b>ERROR             : </b>0<br>"
            "<b>STATUS            : </b>0<br>"
            "<b>DUPLICATE         : </b>0<br>"
            f"<b>TOTAL EVALUATED   : </b>{orx_vs_orx_delta_report_summary['total_evaluated_count']}<br><br>"
            f"<b>Report 2: ORx vs FE Ops delta report generation failed, reason : {orx_vs_feops_delta_report_status['error_message']}</b><br><br>"
            "<b>Notes:</b><br>"
            "- Baseline was not available. ORx vs ORx report treats baseline as empty, therefore all rows are marked ADD.<br><br>"
            "<b>Thanks,</b><br>"
            "Intel Engine<br>"
            )

    email_list = receiverEmails.split(',')
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = senderEmail
    msg['To'] = ', '.join(email_list)
    msg.attach(MIMEText(body, 'html'))

    # Helper to attach delta file if conditions are met
    def attach_delta_file(delta_dict, report_name):
        if not delta_dict or not delta_dict.get('file_content'):
            return
        if not baseline_exists:
            print(f"Skipped {report_name} attachment (baseline missing - first run)")
            return
        file_size_mb = len(delta_dict['file_content']) / (1024 * 1024)
        if file_size_mb == 0:
            print(f"Skipped {report_name} attachment (file is empty)")
        elif file_size_mb > delta_report_max_limit_mb:
            print(f"Skipped {report_name} attachment (size {file_size_mb:.2f} MB > {delta_report_max_limit_mb} MB limit)")
        else:
            attachment = MIMEApplication(delta_dict['file_content'])
            attachment.add_header('Content-Disposition', 'attachment', filename=delta_dict['file_name'])
            msg.attach(attachment)
            print(f"Attached {report_name} delta: {delta_dict['file_name']} ({file_size_mb:.2f} MB)")

    attach_delta_file(orx_vs_orx_delta, "ORx vs ORx")
    attach_delta_file(orx_vs_feops_delta, "ORx vs FeOps")

    ses = boto3.client('ses', region_name=region)
    ses.send_raw_email(
        Source=senderEmail,
        Destinations=email_list,
        RawMessage={'Data': msg.as_string()}
    )
    print("ORx baseline missing feops failed email sent.")


def send_orx_vs_orx_success_orx_vs_feops_success_email(orx_vs_orx_delta_report_summary, orx_vs_feops_delta_report_summary):
    """
    Send email with ORx vs ORx and ORx vs FE Ops delta report data.
    Args:
        orx_vs_orx_delta_report_summary (dict): Dictionary containing all ORx vs ORx delta report data
        orx_vs_feops_delta_report_summary (dict): Dictionary containing all ORx vs FE Ops delta report data
    """
    print("Sending ORx vs ORx and ORx vs FE Ops delta report email.")

    error_count = orx_vs_orx_delta_report_summary.get("error_count", 0)
    invalid_status_count = orx_vs_orx_delta_report_summary.get("invalid_status_count", 0)
    duplicate_count = orx_vs_orx_delta_report_summary.get("latest_file_duplicate_count", 0)

    subject = f"ORx Delta Reports - {run_date} - {run_timestamp}"

    body = ("<b>ORx Daily Delta Reports Generated</b><br><br>"
            f"<b>Run Date :</b>  {run_date} <br>"
            "<b>DP: </b> ORx<br>"
            f"<b>Inbound Drug File : </b>{orx_vs_orx_delta_report_summary.get("latest_file_name", "")}<br>"
            f"<b>Baseline Drug File : </b>{orx_vs_orx_delta_report_summary.get("baseline_file_name", "")}<br>"
            f"<b>FE Ops Sub List : </b>{orx_vs_feops_delta_report_summary.get("feops_file_name", "")}<br><br><br>"
            "<b>Report 1: ORx vs ORx</b><br>"
            f"<b>Delta File Name   :  </b>{orx_vs_orx_delta_report_summary.get("orx_vs_orx_delta_report_file_name", "")}<br><br>"
            "<b>Summary (ORx vs ORx)</b><br>"
            f"<b>ADD               : </b>{orx_vs_orx_delta_report_summary.get("add_count", 0)}<br>"
            f"<b>DELETE            : </b>{orx_vs_orx_delta_report_summary.get("delete_count", 0)}<br>"
            f"<b>UPDATED           : </b>{orx_vs_orx_delta_report_summary.get("update_count", 0)}<br>"
            f"<b>NO CHANGE         : </b>{orx_vs_orx_delta_report_summary.get("no_change_count", 0)}<br>"
            )

    # Add ERROR line only if error_count > 0
    if error_count > 0:
        body += f"<b>ERROR             : </b>{error_count}<br>"

    # Add STATUS line only if invalid_status_count > 0
    if invalid_status_count > 0:
        body += f"<b>INVALID STATUS    : </b>{invalid_status_count}<br>"

    if duplicate_count > 0:
        body += f"<b>DUPLICATE         : </b>{duplicate_count}<br>"

    body += f"<b>TOTAL EVALUATED   : </b>{orx_vs_orx_delta_report_summary.get("total_evaluated_count", 0)}<br><br>"
    body += (f"<b>Report 2: ORx vs FE Ops (New NDCs Only)</b><br>"
             f"<b>Delta File Name   : </b>{orx_vs_feops_delta_report_summary.get("orx_vs_feops_delta_report_file_name", "")}<br>"
             f"<b>NEW NDC COUNT     : </b>{orx_vs_feops_delta_report_summary.get("new_ndc_count", 0)}<br><br>"
             "<b>Notes:</b><br>"
             "- UPDATED rows include the list of changed columns in the 'Columns Updated' field.<br>"
             "- This email is sent for daily monitoring.<br><br>"
             "<b>Thanks,</b><br>"
             "Intel Engine<br>"
             )

    send_email(
        subject=subject,
        body=body,
        receiver_emails=receiverEmails,
        region=region,
        return_path_arn=returnPathArn,
        source_arn=sourceArn,
        sender_email=senderEmail
    )
    print("ORx vs ORx and ORx vs FE Ops delta report email sent.")


def send_orx_vs_orx_success_orx_vs_feops_failed_email(orx_vs_orx_delta_report_summary,
                                                      orx_vs_feops_delta_report_status):
    """
    Send email with ORx vs ORx success and ORx vs FE Ops failed delta report data.
    Args:
        orx_vs_orx_delta_report_summary (dict): Dictionary containing all ORx vs ORx delta report data
        orx_vs_feops_delta_report_status (dict): Status of ORx vs FE Ops delta report
    """
    print("Sending ORx vs ORx success and ORx vs FE Ops failed delta report email.")

    error_count = orx_vs_orx_delta_report_summary.get("error_count", 0)
    invalid_status_count = orx_vs_orx_delta_report_summary.get("invalid_status_count", 0)
    duplicate_count = orx_vs_orx_delta_report_summary.get("latest_file_duplicate_count", 0)

    subject = f"ORx Delta Reports - {run_date} - {run_timestamp}"

    body = ("<b>ORx Daily Delta Reports Generated</b><br><br>"
            f"<b>Run Date :</b>  {run_date} <br>"
            "<b>DP: </b> ORx<br>"
            f"<b>Inbound Drug File : </b>{orx_vs_orx_delta_report_summary.get("latest_file_name", "")}<br>"
            f"<b>Baseline Drug File : </b>{orx_vs_orx_delta_report_summary.get("baseline_file_name", "")}<br>"
            f"<b>FE Ops Sub List : </b> <br><br><br>"
            "<b>Report 1: ORx vs ORx</b><br>"
            f"<b>Delta File Name   :  </b>{orx_vs_orx_delta_report_summary.get("orx_vs_orx_delta_report_file_name", "")}<br><br>"
            "<b>Summary (ORx vs ORx)</b><br>"
            f"<b>ADD               : </b>{orx_vs_orx_delta_report_summary.get("add_count", 0)}<br>"
            f"<b>DELETE            : </b>{orx_vs_orx_delta_report_summary.get("delete_count", 0)}<br>"
            f"<b>UPDATED           : </b>{orx_vs_orx_delta_report_summary.get("update_count", 0)}<br>"
            f"<b>NO CHANGE         : </b>{orx_vs_orx_delta_report_summary.get("no_change_count", 0)}<br>"
            )

    # Add ERROR line only if error_count > 0
    if error_count > 0:
        body += f"<b>ERROR             : </b>{error_count}<br>"

    # Add STATUS line only if invalid_status_count > 0
    if invalid_status_count > 0:
        body += f"<b>INVALID STATUS    : </b>{invalid_status_count}<br>"

    if duplicate_count > 0:
        body += f"<b>DUPLICATE         : </b>{duplicate_count}<br>"

    body += f"<b>TOTAL EVALUATED   : </b>{orx_vs_orx_delta_report_summary.get("total_evaluated_count", 0)}<br><br>"

    body += (
        f"<b>Report 2: ORx vs FE Ops delta report generation failed, reason : {orx_vs_feops_delta_report_status.get("error_message", "")}</b><br><br>"
        "<b>Notes:</b><br>"
        "- UPDATED rows include the list of changed columns in the 'Columns Updated' field.<br>"
        "- This email is sent for daily monitoring.<br><br>"
        "<b>Thanks,</b><br>"
        "Intel Engine<br>"
        )

    send_email(
        subject=subject,
        body=body,
        receiver_emails=receiverEmails,
        region=region,
        return_path_arn=returnPathArn,
        source_arn=sourceArn,
        sender_email=senderEmail
    )
    print("ORx vs ORx success and ORx vs FE Ops failed delta report email sent.")


def send_orx_vs_orx_failed_orx_vs_feops_success_email(orx_vs_orx_delta_report_status,
                                                      orx_vs_feops_delta_report_summary):
    """
    Send email with ORx vs ORx failed and ORx vs FE Ops success delta report data.
    Args:
        orx_vs_orx_delta_report_status (dict): Dictionary containing status of ORx vs ORx delta report
        orx_vs_feops_delta_report_summary (dict): Dictionary containing all ORx vs FE Ops delta report data
    """
    print("Sending ORx vs ORx failed and ORx vs FE Ops success delta report email.")

    subject = f"ORx Delta Reports - {run_date} - {run_timestamp}"

    body = ("<b>ORx Daily Delta Reports Generated</b><br><br>"
            f"<b>Run Date :</b>  {run_date} <br>"
            "<b>DP: </b> ORx<br>"
            f"<b>Inbound Drug File : </b>{latest_file_path}<br>"
            f"<b>Baseline Drug File : </b> <br>"
            f"<b>FE Ops Sub List : </b>{orx_vs_feops_delta_report_summary.get("feops_file_name", "")}<br><br><br>"
            f"<b>Report 1: ORx vs ORx delta report generation failed, reason : {orx_vs_orx_delta_report_status.get("error_message", "")}</b><br><br>"
            f"<b>Report 2: ORx vs FE Ops (New NDCs Only)</b><br>"
            f"<b>Delta File Name   : </b>{orx_vs_feops_delta_report_summary.get("orx_vs_feops_delta_report_file_name", "")}<br>"
            f"<b>NEW NDC COUNT     : </b>{orx_vs_feops_delta_report_summary.get("new_ndc_count", 0)}<br><br>"
            "<b>Notes:</b><br>"
            "- UPDATED rows include the list of changed columns in the 'Columns Updated' field.<br>"
            "- This email is sent for daily monitoring.<br><br>"
            "<b>Thanks,</b><br>"
            "Intel Engine<br>"
            )

    send_email(
        subject=subject,
        body=body,
        receiver_emails=receiverEmails,
        region=region,
        return_path_arn=returnPathArn,
        source_arn=sourceArn,
        sender_email=senderEmail
    )
    print("ORx vs ORx failed and ORx vs FE Ops success delta report email sent.")


if __name__ == "__main__":
    main()
